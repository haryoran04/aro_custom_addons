# -*- coding: utf-8 -*-
from openerp import http

# class AccountJournalAgency(http.Controller):
#     @http.route('/account_journal_agency/account_journal_agency/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/account_journal_agency/account_journal_agency/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('account_journal_agency.listing', {
#             'root': '/account_journal_agency/account_journal_agency',
#             'objects': http.request.env['account_journal_agency.account_journal_agency'].search([]),
#         })

#     @http.route('/account_journal_agency/account_journal_agency/objects/<model("account_journal_agency.account_journal_agency"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('account_journal_agency.object', {
#             'object': obj
#         })