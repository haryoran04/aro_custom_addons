# -*- coding: utf-8 -*-
###############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015-Today NextHope Business Solutions <contact@nexthope.net>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###########################################################################
from openerp import fields, models, api
from openerp.exceptions import Warning, ValidationError, except_orm
import openerp.addons.decimal_precision as dp
from datetime import datetime


######## ACCOUNT INVOICE ###########
class account_invoice(models.Model):
    _inherit = 'account.invoice'     
    
    tva_assurance = fields.Float(string='Tva assurance ARO', digits=dp.get_precision('Account'),
        store=True, readonly=False)
    
    
    ######## Rewrite by HH to compute amount total by adding tva_assurance #########
#     @api.one
#     @api.depends('invoice_line.price_subtotal', 'tax_line.amount')
#     def _compute_amount(self):        
#         self.amount_untaxed = sum(line.price_subtotal for line in self.invoice_line)
#         self.amount_tax = sum(line.amount for line in self.tax_line)                       
#         self.amount_total = self.amount_untaxed + self.amount_tax + self.tva_assurance
#         
#         
#         
#     @api.multi
#     def action_move_create(self):
#         """ Creates invoice related analytics and financial move lines """
#         account_invoice_tax = self.env['account.invoice.tax']
#         account_move = self.env['account.move']
# 
#         for inv in self:
#             if not inv.journal_id.sequence_id:
#                 raise except_orm(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
#             if not inv.invoice_line:
#                 raise except_orm(_('No Invoice Lines!'), _('Please create some invoice lines.'))
#             if inv.move_id:
#                 continue
# 
#             ctx = dict(self._context, lang=inv.partner_id.lang)
# 
#             if not inv.date_invoice:
#                 inv.with_context(ctx).write({'date_invoice': fields.Date.context_today(self)})
#             date_invoice = inv.date_invoice
# 
#             company_currency = inv.company_id.currency_id
#             # create the analytical lines, one move line per invoice line
#             iml = inv._get_analytic_lines()
#             # check if taxes are all computed
#             compute_taxes = account_invoice_tax.compute(inv.with_context(lang=inv.partner_id.lang))
#             inv.check_tax_lines(compute_taxes)
# 
#             # I disabled the check_total feature
#             if self.env['res.users'].has_group('account.group_supplier_inv_check_total'):
#                 if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding / 2.0):
#                     raise except_orm(_('Bad Total!'), _('Please verify the price of the invoice!\nThe encoded total does not match the computed total.'))
# 
#             if inv.payment_term:
#                 total_fixed = total_percent = 0
#                 for line in inv.payment_term.line_ids:
#                     if line.value == 'fixed':
#                         total_fixed += line.value_amount
#                     if line.value == 'procent':
#                         total_percent += line.value_amount
#                 total_fixed = (total_fixed * 100) / (inv.amount_total or 1.0)
#                 if (total_fixed + total_percent) > 100:
#                     raise except_orm(_('Error!'), _("Cannot create the invoice.\nThe related payment term is probably misconfigured as it gives a computed amount greater than the total invoiced amount. In order to avoid rounding issues, the latest line of your payment term must be of type 'balance'."))
# 
#             # one move line per tax line
#             iml += account_invoice_tax.move_line_get(inv.id)              
# 
#             if inv.type in ('in_invoice', 'in_refund'):
#                 ref = inv.reference
#             else:
#                 ref = inv.number
# 
#             diff_currency = inv.currency_id != company_currency
#             # create one move line for the total and possibly adjust the other lines amount
#             total, total_currency, iml = inv.with_context(ctx).compute_invoice_totals(company_currency, ref, iml)          
#             ###### Creer par HH pour calculer dans l'ecriture la taxe ###################
#             ##### Append Tva assurance in journal by HH ################################                
#             if self.tva_assurance:
#                 tva_assurance_amount = -self.tva_assurance
#                 if self.type == 'out_refund':
#                     tva_assurance_amount = self.tva_assurance                               
#                 iml.append({'uos_id': 5, 
#                             'account_id': 976, 
#                             'price_unit': self.tva_assurance, 
#                             'currency_id': False, 
#                             'name': 'Tva assurance ARO', 
#                             'tax_amount': 0.0, 
#                             'product_id': 10688,
#                             'ref': False, 
#                             'taxes': False,                                            
#                             'account_analytic_id': False, 
#                             'amount_currency': False, 
#                             'type': 'src', 
#                             'price': tva_assurance_amount, 
#                             'quantity': 1.0                            
#                             })   
#             ############################################################################
#             ############################################################################
#             name = inv.supplier_invoice_number or inv.name or '/'
#             totlines = []
#             if inv.payment_term:
#                 totlines = inv.with_context(ctx).payment_term.compute(total, date_invoice)[0]
#             if totlines:
#                 res_amount_currency = total_currency
#                 ctx['date'] = date_invoice
#                 for i, t in enumerate(totlines):
#                     if inv.currency_id != company_currency:
#                         amount_currency = company_currency.with_context(ctx).compute(t[1], inv.currency_id)
#                     else:
#                         amount_currency = False
# 
#                     # last line: add the diff
#                     res_amount_currency -= amount_currency or 0
#                     if i + 1 == len(totlines):
#                         amount_currency += res_amount_currency
# 
#                     iml.append({
#                         'type': 'dest',
#                         'name': name,
#                         'price': t[1],
#                         'account_id': inv.account_id.id,
#                         'date_maturity': t[0],
#                         'amount_currency': diff_currency and amount_currency,
#                         'currency_id': diff_currency and inv.currency_id.id,
#                         'ref': ref,
#                     })       
#                     
#             else:
#                 if self.tva_assurance:
#                     total += self.tva_assurance
#                 iml.append({
#                     'type': 'dest',
#                     'name': name,
#                     'price': total,
#                     'account_id': inv.account_id.id,
#                     'date_maturity': inv.date_due,
#                     'amount_currency': diff_currency and total_currency,
#                     'currency_id': diff_currency and inv.currency_id.id,
#                     'ref': ref
#                 })          
#                        
#             date = date_invoice
# 
#             part = self.env['res.partner']._find_accounting_partner(inv.partner_id)
# 
#             line = [(0, 0, self.line_get_convert(l, part.id, date)) for l in iml]
#              
#             line = inv.group_lines(iml, line)
# 
#             journal = inv.journal_id.with_context(ctx)
#             if journal.centralisation:
#                 raise except_orm(_('User Error!'),
#                         _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))
# 
#             line = inv.finalize_invoice_move_lines(line)
# 
#             move_vals = {
#                 'ref': inv.reference or inv.name,
#                 'line_id': line,
#                 'journal_id': journal.id,
#                 'date': inv.date_invoice,
#                 'narration': inv.comment,
#                 'company_id': inv.company_id.id,
#             }
#             ctx['company_id'] = inv.company_id.id
#             period = inv.period_id
#             if not period:
#                 period = period.with_context(ctx).find(date_invoice)[:1]
#             if period:
#                 move_vals['period_id'] = period.id
#                 for i in line:
#                     i[2]['period_id'] = period.id
# 
#             ctx['invoice'] = inv
#             ctx_nolang = ctx.copy()
#             ctx_nolang.pop('lang', None)
#             move = account_move.with_context(ctx_nolang).create(move_vals)
# 
#             # make the invoice point to that move
#             vals = {
#                 'move_id': move.id,
#                 'period_id': period.id,
#                 'move_name': move.name,
#             }
#             inv.with_context(ctx).write(vals)
#             # Pass invoice in context in method post: used if you want to get the same
#             # account move reference when creating the same invoice after a cancelled one:
#             move.post()
#         self._log_event()
#         return True
#     
#     
#     @api.multi
#     def compute_invoice_totals(self, company_currency, ref, invoice_move_lines):
#         total = 0
#         total_currency = 0
#         for line in invoice_move_lines:
#             if self.currency_id != company_currency:                
#                 currency = self.currency_id.with_context(date=self.date_invoice or fields.Date.context_today(self))
#                 line['currency_id'] = currency.id
#                 line['amount_currency'] = currency.round(line['price'])
#                 line['price'] = currency.compute(line['price'], company_currency)
#             else:               
#                 line['currency_id'] = False
#                 line['amount_currency'] = False
#                 line['price'] = self.currency_id.round(line['price'])
#             line['ref'] = ref
#             if self.type in ('out_invoice','in_refund'):                
#                 total += line['price']                           
#                 total_currency += line['amount_currency'] or line['price']
#                 line['price'] = - line['price']
#             else:                
#                 total -= line['price']
#                 total_currency -= line['amount_currency'] or line['price']
#         return total, total_currency, invoice_move_lines 
