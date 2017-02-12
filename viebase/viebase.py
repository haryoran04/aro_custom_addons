# -*- coding: utf-8 -*-

from openerp import models, api, fields
from openerp.exceptions import ValidationError


class f_client(models.Model):
    _name = 'f.client'
    _description = 'Fichier des clients'

    name = fields.Char(string="Nom client", size=40)
    vcl_codeag = fields.Char(string="Code agence", size=2)
    vcl_compte = fields.Char(string="Compte", size=5)
    vcl_titre = fields.Char(string="Titre", size=10)
    vcl_datecomptable = fields.Date(string="Date comptable")

    partner_id = fields.Integer(string="partner_id")

class f_apporteur(models.Model):
    _name = 'f.apporteur'
    _inherit = 'res.partner'
    _description = 'Fichier des courtiers'

    name = fields.Char(string="Nom apporteur", size=60)
    titre = fields.Char(string="Titre", size=10)
    ap_code = fields.Char(string="Code courtier", size=7)

    partner_id = fields.Integer(string="partner_id")

class f_anomalie(models.Model):
    _name = 'f.anomalie'
    _description = 'Fichier des anomalies'

    texte = fields.Char(string="Anomalie", size=60)

