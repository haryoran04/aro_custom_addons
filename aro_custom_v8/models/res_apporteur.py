# -*- coding: utf-8 -*-

from openerp import models, api, fields, exceptions


class ResApporteur(models.Model):
    _name = 'res.apporteur'
    _inherits = {'res.partner': 'partner_id'}
    _description = ''

    partner_id = fields.Many2one('res.partner', string='Related Partner',
                                 required=True,
                                 ondelete='restrict', auto_join=True,
                                 help='Partner-related data of apporteur')
    name = fields.Char(related='partner_id.name', inherited=True)
    agency_id = fields.Many2one(related='partner_id.agency_id', inherited=True)
    title = fields.Many2one(related='partner_id.title', inherited=True)
    ap_code = fields.Char(string='AP code', size=8)
    serial_identification = fields.Char(string='Serial Id', size=8)
    statut = fields.Char(string='Statut', size=16)
