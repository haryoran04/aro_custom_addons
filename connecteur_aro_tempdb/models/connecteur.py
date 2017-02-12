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
from openerp import models, api, exceptions, _

import datetime
import decimal
import pypyodbc
import logging
# import re
# import json

_logger = logging.getLogger(__name__)
DRIVER = 'FreeTDS'
SERVER = '192.168.56.1'
PORT = '1433'
DATABASE = 'dwh_stat'
UID = 'sa'
PWD = 'Aro1'
TDS_Version = '7.0'

map_gnrl = {}
"""
map_rqt = {
    '': ,
    '': ,
    '': ,
    '': ,
    '': ,
    '': ,
    '': ,
    '': ,
}
"""
request_apporteur = """select agence,old,new,titre,nom,prenom,statut
from tdc"""
map_app = {
    'agence': 'agency',
    'old': 'code',
    'new': '',
    'titre',
    'nom',
    'prenom',
    'statut'
}
request_sql = """ select top 10
                   codeag,courtier1,courtier2,
                   compte,titre,nom40,
                   numpol,dateeffet,dateecheance,codebranc,codecateg,vtable,
                   vdureectr,vdureepai,vmodepai,cpa,cpu,
                   numaven,aarattach,mmrattach,aacpt,mmcpt,codecarte,ordre,
                   codefic,num_primenet,num_access,num_te,num_tva,num_primetot,
                   num_commag,num_commcrt1,num_commcrt2,num_interav,
                   datecomptable,tmv
            from tempdb where  aacpt = 2015 """

request_sql2 = """ select
default_code, NUMPOL , DATEEFFET prm_datedeb, DATEECHEANCE prm_datefin,
rtrim(ltrim(MMCPT)) +'/'+rtrim(ltrim(str(AACPT))) period,
CODEAG, DATECOMPTABLE, ORDRE, COMPTE, TITRE, NOM40, ADRESSE1, ULIBELLE,
COURTIER1, COURTIER2, NUM_COMMCRT1, NUM_COMMCRT2, NUM_PRIMENET, NUM_ACCESS, NUM_TE, NUM_TVA,*
from tempdb_odoo where AACPT=2015
"""
map_sql2 = {
    'default_code': 'default_code',
    'NUMPOL': 'pol_numpol',
    'DATEEFFET': 'prm_datedeb',
    'DATEECHEANCE': 'prm_datefin',
    'period': 'period',
    'CODEAG': 'codeag',
    'DATECOMPTABLE' 'date_comptable',
    'ORDRE': 'ordre',
    'COMPTE': 'compte',
    'TITRE': 'title',
    'NOM40': 'name',
    'ADRESSE1': 'street',
    'ULIBELLE': 'city',
    'COURTIER1': 'app_a',
    'COURTIER2': 'app_b',
    'NUM_COMMCRT1': 'code_app_a',
    'NUM_COMMCRT2': 'code_app_b',
    'NUM_PRIMENET': 'price_unit',
    'NUM_ACCESS': 'access_amount',
    'NUM_TE': 'tax_te',
    'NUM_TVA': 'tax_tva',
}

class connecteur(models.Model):
    _name = 'connecteur.aro'

    @api.multi
    def map_data(self, datas):
        res = []
        if datas:
            for field_tempdb in datas:
                data = {}
                data = {
                    'tdb_codeag': field_tempdb[0],
                    'tdb_courtier1': field_tempdb[1],
                    'tdb_courtier2': field_tempdb[2],
                    'tdb_compte': field_tempdb[3],
                    'tdb_titre': field_tempdb[4],
                    'tdb_nom40': field_tempdb[5],
                    'tdb_numpol': field_tempdb[6],
                    'tdb_dateeffet': field_tempdb[7],
                    'tdb_dateecheance': field_tempdb[8],
                    'tdb_codebranc': field_tempdb[9],
                    'tdb_codecateg':  field_tempdb[10],
                    'tdb_vtable': field_tempdb[11],
                    'tdb_vdureectr': field_tempdb[12],
                    'tdb_vdureepai': field_tempdb[13],
                    'tdb_modpai': field_tempdb[14],
                    'tdb_cpa': field_tempdb[15],
                    'tdb_cpu': field_tempdb[16],
                    'tdb_numaven': field_tempdb[17],
                    'tdb_aarattach': field_tempdb[18],
                    'tdb_mmrattach': field_tempdb[19],
                    'tdb_aacpt': field_tempdb[20],
                    'tdb_mmcpt': field_tempdb[21],
                    'tdb_codecarte': field_tempdb[22],
                    'tdb_ordre': field_tempdb[23],
                    'tdb_codefic': field_tempdb[24],
                    'tdb_primenet': field_tempdb[25],
                    'tdb_access': field_tempdb[26],
                    'tdb_te': field_tempdb[27],
                    'tdb_tva': field_tempdb[28],
                    'tdb_primetot': field_tempdb[29],
                    'tdb_commag': field_tempdb[30],
                    'tdb_commcrt1': field_tempdb[31],
                    'tdb_commcrt2': field_tempdb[32],
                    'tdb_interav': field_tempdb[33],
                    'tdb_datecomptable': field_tempdb[34],
                    'tdb_tmv': field_tempdb[35]
                }
                res.append(data)
        return res

    @api.multi
    def dispatch_mapped_data(self, data):
        """
        :param: data: Is a dict
        """
        el_req = [
            'partner_title',
            'partner_customer',
            'partner_apporteur',
            'product',
            'tax_te',
            'tax_tva',
            'journal',
            'account',
        ]
        res = {}
        # res_partner_title
        res[el_req[0]] = {'name': data.get('tdb_titre', False),
                          'shortcut': data.get('tdb_titre', False)}
        # client_cour = [tdb_codeag,tdb_compte,tdb_titre,tdb_nom40,
        # tdb_datecomptable]
        # res_partner -> customer
        res[el_req[1]] = {
            'name': data.get('tdb_nom40'),
            'customer': True,
            'ref': '41' + data.get('tdb_codeag') + '' + data.get('tdb_compte'),
            'title': data.get('tdb_titre', False),
        }
        # product_product
        res[el_req[3]] = {
            'name': '',
            'default_code': data.get('tdb_tmv') + data.get('tdb_codebranc') +
            data.get('tdb_codecateg')
        }
        return res

    @api.multi
    def check_partner_title(self, data):
        opts = ['MR', 'MME', 'STE', '00000']
        # title_obj = self.env['res.partner.title']
        res = False
        if data.get('shortcut') == opts[0]:
            res = self.env.ref('base.res_partner_title_sir')
        elif data.get('shortcut') == opts[1]:
            res = self.env.ref('base.res_partner_title_madam')
        elif data.get('shortcut') == opts[2]:
            res = self.env.ref('base.res_partner_pvt_ltd')
        else:
            _logger.info('\n=== data = %s === \n' % data)
            return res
        return res

    @api.multi
    def check_partner_customer(self, data):
        res = False
        partner_obj = self.env['res.partner']
        if data.get('ref', False):
            partner_src = partner_obj.search([('ref', '=', data.get('ref'))])
            if partner_src and len(partner_src) > 1:
                raise exceptions.Warning(_('Error'),
                                         _('More than one partner found with \
                                           ref %s' % data.get('ref')))
            elif partner_src and len(partner_src) == 1:
                res = partner_src
            elif not partner_src:
                # create new partner
                comp = self.env.ref('base.res_partner_title_pvt_ltd')
                data['title'] = self.check_partner_title({
                    'name': data.get('title'), 'shortcut': data.get('title')})
                if data.get('title'):
                    if data.get('title') == comp:
                        data['is_company'] = True
                    data['title'] = data.get('title').id
                _logger.info('\n===customer data = %s === \n' % data)
                res = partner_obj.create(data)
            else:
                return res
        else:
            _logger.info('\n=== Can\'t create customer without ref ===\n')
            return res
        return res

    @api.multi
    def map_cursor_content(self, cursor_to_map, use_map={}):
        if not cursor_to_map:
            return False
        if not use_map:
            use_map = map_gnrl
        res = []
        columns = [column[0] for column in cursor_to_map.description]
        _logger.info('\n=== columns = %s === \n' % columns)
        for row in cursor_to_map:
            col_counter = 0
            data = {}
            for col in columns:
                #_logger.info('\n=== %s,%s,%s === ' % (col, row[col_counter],type(row[col_counter])))
                if type(row[col_counter]) == datetime.datetime:
                    data[col] = row[col_counter].strftime("%Y-%m-%d")
                elif type(row[col_counter]) == decimal.Decimal:
                    data[col] = float(row[col_counter])
                elif type(row[col_counter]) == int:
                    data[col] = int(row[col_counter])
                elif type(row[col_counter]) == str:
                    data[col] = str(row[col_counter])
                else:
                    data[col] = row[col_counter]
                col_counter += 1
            _logger.info('\n=== data = %s === ' % data)
            res.append(data)
        return res

    @api.model
    def update_add_record(self):

        _logger.info('\n=== Try Connect on SQL Server ===\n')
        connection = False
        cursorSQLServer = False
        prm = "DRIVER=%s;SERVER=%s;PORT=%s;DATABASE=%s;UID=%s;PWD=%s;\
                TDS_Version=%s" % (DRIVER, SERVER, PORT, DATABASE,
                                   UID, PWD, TDS_Version)
        try:
            #connection = pypyodbc.connect("DRIVER=FreeTDS;SERVER=10.0.0.92;
            # PORT=1433;DATABASE=dwh_stat;UID=sa;PWD=Aro1;TDS_Version=7.0")
            connection = pypyodbc.connect(prm)
            cursorSQLServer = connection.cursor()
            cursorSQLServer.execute(request_sql)
        except Exception, e:
            raise exceptions.Warning(_('Error'),
                                     _('Can\'t connect to SQL Server %s' % e))
        _logger.info('\n=== Connected  ===\n')

        # numenreg = 0
        correct_data = self.map_cursor_content(cursorSQLServer)
        resultsSQLtempdb = cursorSQLServer.fetchall()
        mapped_datas = self.map_data(resultsSQLtempdb)
        #_logger.info('\n=== mapped_datas = %s === \n' % type(mapped_datas))
        for mapped_data in mapped_datas:
            # we work only with one data, not with all of them
            invoice_vals = {'partner_id': False,
                            'invoice_line': [(6, 0, [False])]}
            dpt_datas = self.dispatch_mapped_data(mapped_data)
            #_logger.info('\n=== dpt_datas = %s === \n' % dpt_datas)
            # Check res_partner_title
            #partner_title = self.check_partner_title(dpt_datas.get('partner_title'))
            # Check if customer exist
            invoice_vals['partner_id'] = self.check_partner_customer(dpt_datas.get('partner_customer'))
            if invoice_vals.get('partner_id', False):
                invoice_vals['partner_id'] = invoice_vals.get('partner_id', False).id
            #_logger.info('\n=== invoice_vals = %s === \n' % invoice_vals)
            #partner_vals = {}
            #client_cour = [tdb_codeag,tdb_compte,tdb_titre,tdb_nom40,tdb_datecomptable]
            #id_client = self.voir_client(client_cour)
            # Voir courtiers
            """
            if mapped_data.get('tbd_courtier1') != "000":
                tdb_codeag = mapped_data.get('tdb_codeag')
                tdb_courtier1 = mapped_data.get('tdb_courtier1')
                courtier_cour = self.traiter_courtier(tdb_codeag,tdb_courtier1,cursorSQLServer,connection)
                _logger.info('\n=== courtier_cour = %s === \n' % courtier_cour)
                id_crt1 = self.voir_f_apporteur(courtier_cour,tdb_courtier1,tdb_codeag)
                _logger.info('\n=== id_crt1 = %s === \n' % id_crt1)
            """
            #if mapped_data.get('tbd_courtier2') != "000":
                #courtier_cour2 = self.traiter_courtier(tdb_codeag,tdb_courtier2,cursorSQLServer,connection)
                #_logger.info('\n=== courtier_cour2 = %s === \n' % courtier_cour2)
                #id_crt2 = self.voir_f_apporteur(courtier_cour2,tdb_courtier2,tdb_codeag)
            """
            id_crt1 = 0
            if tdb_courtier1 <> "000":
                courtier_cour = self.traiter_courtier(tdb_codeag,tdb_courtier1,cursorSQLServer,connection)
                id_crt1 = self.voir_f_apporteur(courtier_cour,tdb_courtier1,tdb_codeag)
            id_crt2 = 0
            if tdb_courtier2 <> "000":
                courtier_cour = self.traiter_courtier(tdb_codeag,tdb_courtier2,cursorSQLServer,connection)
                id_crt2 = self.voir_f_apporteur(courtier_cour,tdb_courtier2,tdb_codeag)
            """
            """
            # Voir clients
            client_cour = [tdb_codeag,tdb_compte,tdb_titre,tdb_nom40,tdb_datecomptable]
            id_client = self.voir_client(client_cour)

            # Voir article
            article_cour = [tdb_tmv,tdb_codebranc,tdb_codecateg]
            id_article = self.voir_article(article_cour)

            # Voir opération
            comptes_cour = self.voir_operation(tdb_tmv,tdb_codecarte)

            # Voir taxes
            id_taxe = self.voir_taxe(tdb_primenet,tdb_access,tdb_te,tdb_tva)

            # Génération factures
            avenant_cour = [tdb_numaven,tdb_aarattach,tdb_mmrattach,tdb_aacpt,tdb_mmcpt,tdb_codecarte,
                          tdb_ordre,tdb_codefic,tdb_primenet,tdb_access,tdb_te,tdb_tva,tdb_primetot,
                          tdb_commag,tdb_commcrt1,tdb_commcrt2,tdb_interav,tdb_numpol
                           ]
            # self.generer_facture(avenant_cour,
                                 # id_client,id_crt1,id_crt2,id_article,
                                 # tdb_codeag,tdb_numpol,id_taxe,comptes_cour)
            """
        connection.close()
        _logger.info('\n=== Close connection ===\n')


    def traiter_courtier(self,agence,courtier,cursorSQLServer,connection):
        cursorSQLServer.execute(""" select new,titre,nom,prenom,statut from tdc where agence='%s' and old='%s' """ % (agence,courtier))
        resultsSQLtdc = cursorSQLServer.fetchall()
        if resultsSQLtdc:
            tdc_new = resultsSQLtdc[0][0]
            tdc_titre = resultsSQLtdc[0][1]
            tdc_nom = resultsSQLtdc[0][2]
            tdc_prenom = resultsSQLtdc[0][3]
            tdc_statut = resultsSQLtdc[0][4]
            courtier_cour = [tdc_new,tdc_titre,tdc_nom,tdc_prenom,tdc_statut]
            return courtier_cour
        else:
            return self.creer_tdc(agence,courtier,cursorSQLServer,connection)

    def creer_tdc(self,agence,courtier,cursorSQLServer,connection):
        t_agence = agence
        t_old = courtier
        cursorSQLServer.execute(""" select max(new) from tdc where new like 'AL%' """)
        resultsSQLtdc = cursorSQLServer.fetchall()
        dernier_num = resultsSQLtdc[0][0]
        nouveau_num = int(dernier_num[2:]) + 1
        t_new = 'AL' + str(nouveau_num)
        t_titre = '   '
        t_nom = 'COURTIER '+agence+'/'+t_old
        t_prenom = '    '
        t_statut = '     '
        cursorSQLServer.execute(""" insert into tdc (agence,old,new,nom) values ('%s','%s','%s','%s') """ % (t_agence,t_old,t_new,t_nom))
        connection.commit()
        courtier_cour = [t_new,t_titre,t_nom,t_prenom,t_statut]

        return courtier_cour

    def voir_f_apporteur(self,courtier,old,ag):
        obj_f_apporteur = self.env['f.apporteur']
        apporteur = obj_f_apporteur.search([('ap_code','=',courtier[0])])
        if  apporteur:
            retour = apporteur.partner_id
            return retour
        else:
            retour = self.creer_f_apporteur(courtier,old,ag)

        return

    def creer_f_apporteur(self,courtier,old,ag):
        ref_courtier = '41' + ag + '2' + old
        nom = courtier[2]
        if courtier[3]:
            nom = nom + " " + courtier[3]
        vals = {
                'name':nom,
                'country_id':142,
                'ref':ref_courtier
                }
        id_partner = self.env['res.partner'].create(vals)
        partner_id = id_partner.id

        vals = {'name':nom,
                'titre':courtier[1],
                'ap_code':courtier[0],
                'partner_id':partner_id
               }
        id_apporteur = self.env['f.apporteur'].create(vals)

        return partner_id

    def voir_client(self,client):
        obj_client = self.env['f.client']
        cli = obj_client.search([('vcl_codeag','=',client[0]),('vcl_compte','=',client[1])])
        if not cli:
            retour = self.creer_client(client)
            return retour
        if cli.name <> client[3]:
            pointeur = cli.partner_id
            retour = self.maj_client(client,pointeur)
            return retour
        retour = cli.partner_id

        return retour

    def creer_client(self,client):
        ref_client = '41'+ client[0]+'1'+ client[1]
        vals = {
                'name':client[3],
                'country_id':142,
                'ref':ref_client
               }
        id_partner = self.env['res.partner'].create(vals)
        partner_id = id_partner.id

        vals = {'name':client[3],
                'vcl_titre':client[2],
                'vcl_codeag':client[0],
                'vcl_compte':client[1],
                'vcl_datecomptable':client[4],

                'partner_id':partner_id
               }
        id_client = self.env['f.client'].create(vals)
        retour = partner_id

        return retour

    def maj_client(self,client,pointeur):
        vals = {
                'name':client[3],
                'vcl_titre':client[2],
                'vcl_datecomptable':client[4],
               }
        id_client = self.env['f.client'].write(vals)

        obj_res_partner = self.env['res.partner']
        partner = obj_res_partner.search([('id','=',pointeur)])
        vals = {'name':client[3]
               }
        nouveau_nom = self.env['res.partner'].write(vals)

        return pointeur

    def voir_article(self, domain):
        obj_article = self.env['product.template']
        article = obj_article.search(domain)
        id_article = article.id
        return id_article

    def voir_operation(self,tmv,codecarte):


        d_client = 1
        c_client = 2
        d_agence = 3
        c_agence = 4
        d_crt1 = 5
        c_crt1 = 6
        d_crt2 = 7
        c_crt2 = 8


        retour = [d_client,c_client,d_agence,c_agence,c_crt1,d_crt1,d_crt2,c_crt2]

        return retour

    def voir_taxe(self,primenet,access,te,tva):

        pc_te = 0
        pc_tva = 0
        if (primenet + access <> 0):
            pc_te = (te * 100) / (primenet + access)
        if (primenet + access + te <> 0):
            pc_tva = (tva * 100) / (primenet + access + te)

        pc_te = round(pc_te,1)
        pc_tva = round(pc_tva,1)

        id_taxe = 0
        if (pc_te == 0):
            if (pc_tva == 0):
                id_taxe = 1
            if (pc_tva == 20):
                id_taxe = 2
        if (pc_te == 3):
            if (pc_tva == 0):
                id_taxe = 3
            if (pc_tva == 20):
                id_taxe = 4
        if (pc_te == 4):
            if (pc_tva == 0):
                id_taxe = 5
            if (pc_tva == 20):
                id_taxe = 6
        if (pc_te == 4.5):
            if (pc_tva == 0):
                id_taxe = '4.5/0'
            if (pc_tva == 20):
                id_taxe = 7
        if (pc_te == 14.5):
            if (pc_tva == 0):
                id_taxe = 8
            if (pc_tva == 20):
                id_taxe = 9

        if (id_taxe == 0):
            print "Taxe non trouvée..."
            print "TE = " + str(pc_te)
            print "TVA = " + str(pc_tva)

        return id_taxe

    ###################### GENERATION DE LA FACTURE ##################################

    def generer_facture(self,avenant,id_client,id_crt1,id_crt2,id_article,
                        agence,police,id_taxe,comptes):


        return
