# -*- coding: utf-8 -*-
###############################################################################
#
#    Odoo, Open Source Management Solution
#    Copyright (C) 2015-Today NextHope Business Solutions
#    <contact@nexthope.net>
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
from openerp import fields, models


class commission_commission(models.Model):
    _name = 'commission.commission'

    partner_commissioned = fields.Many2one('res.partner',
                                           string="commissionne")
    account_commission = fields.Many2one(
        'account.account',
        string="compte",
        domain=[('type', 'not in', ['view', 'closed'])])
    account_charge_commission = fields.Many2one(
        'account.account',
        string="compte de charge",
        domain=[('type', 'not in', ['view', 'closed'])])
    account_amount = fields.Float(string="montant")
    commission_invoice = fields.Many2one('account.invoice')


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    final_customer_id = fields.Many2one('res.partner', string='Client Final')
    commission_ids = fields.One2many('commission.commission',
                                     'commission_invoice', 'Commissions')


class res_partner(models.Model):
    # Inherits partner and adds invoice information in the partner form
    _inherit = 'res.partner'

    id_intermediaire = fields.Integer(string="Intermediaire")
    id_apporteur = fields.Integer(string="Apporteur")
