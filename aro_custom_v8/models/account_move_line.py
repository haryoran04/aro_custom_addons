# -*- coding: utf-8 -*-

from openerp import models, fields


class account_move_line(models.Model):
    _inherit='account.move.line'

    analytic1 = fields.Char(string='Analytique 1',size=128)
    analytic2 = fields.Char(string='Analytique 2',size=128)
    check_number = fields.Char(string=u'Chèque',size=128)
    session = fields.Char(string='Session',size=128)
    piece = fields.Char(string=u'Pièce',size=128)
    line = fields.Char(string='Ligne',size=128)
    emp_contrat = fields.Char(string='Contrat',size=128)
    emp_police = fields.Char(string='Police',size=128)
    emp_folio = fields.Char(string='Folio',size=128)
    emp_quittance = fields.Char(string='Quittance',size=128)
    emp_effet = fields.Char(string='Effet',size=128)
    emp_emission = fields.Char(string='Emission',size=128)
    emp_unite = fields.Char(string=u'Unité',size=128)
    emp_datfact = fields.Date(string='Date facture',size=128)
    emp_datech = fields.Date(string=u'Date échéance',size=128)
    emp_libana = fields.Char(string=u'Libellé analytique',size=128)
    emp_fluxtres = fields.Char(string=u'Flux trésorerie',size=128)
    emp_as400_compte = fields.Char(string='AS400 compte',size=128)
    emp_as400_ses = fields.Float(string='AS400 ses')
    emp_as400_pie = fields.Float(string='AS400 pie')
    emp_as400_lig = fields.Float(string='AS400 lig')
#    agency_id = fields.Many2one('res.agency',string='Agence')
