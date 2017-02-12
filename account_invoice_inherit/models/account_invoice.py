# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields
# from _dbus_bindings import String


class account_invoice(models.Model):

    _inherit = "account.invoice"

    pol_numpol = fields.Char(string="Numero Police")
    prm_datedeb = fields.Date(string="Date Effet")
    prm_datefin = fields.Date(string="Date Echéance")
    prm_numero_quittance = fields.Char(string="Numero Quittance")
    prm_ident_invoice = fields.Float()
