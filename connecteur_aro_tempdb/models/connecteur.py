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
import datetime
import pypyodbc
import logging
import re
import json

_logger = logging.getLogger(__name__)

class connecteur(models.Model):
    _name = 'connecteur.aro'

    @api.multi
    def update_add_record(self):

        print "Connection à SQL Server !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        connection = pypyodbc.connect("DRIVER=FreeTDS;SERVER=10.0.0.92;PORT=1433;DATABASE=dwh_stat;UID=sa;PWD=Aro1;TDS_Version=7.0")
        print "Connection établie !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

        numenreg = 0
        cursorSQLServer = connection.cursor()

        cursorSQLServer.execute(""" select top 100
                                           codeag,courtier1,courtier2,
                                           compte,titre,nom40,
                                           numpol,dateeffet,dateecheance,codebranc,codecateg,vtable,
                                           vdureectr,vdureepai,vmodepai,cpa,cpu,
                                           numaven,aarattach,mmrattach,aacpt,mmcpt,codecarte,ordre,codefic,
                                           num_primenet,num_access,num_te,num_tva,num_primetot,
                                           num_commag,num_commcrt1,num_commcrt2,num_interav,
                                           datecomptable,tmv, default_code
                                    from tempdb where  aacpt = 2015 """)
        resultsSQLtempdb = cursorSQLServer.fetchall()
        connection.close()
        print "Fermeture de la Connection SQL Server !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"

        for field_tempdb in resultsSQLtempdb:
            numenreg = numenreg + 1
            #print "Enregs traités " + str(numenreg)

            # Voir article
            article_cour = [tdb_tmv,tdb_codebranc,tdb_codecateg]
            id_article = self.voir_article(article_cour)
            articles = {'default_code': field_tempdb.get('default_code')}

            tdb_codeag = field_tempdb[0]
            tdb_courtier1 = field_tempdb[1]
            tdb_courtier2 = field_tempdb[2]
            tdb_compte = field_tempdb[3]
            tdb_titre = field_tempdb[4]
            tdb_nom40 = field_tempdb[5]
            tdb_numpol = field_tempdb[6]
            tdb_dateeffet = field_tempdb[7]
            tdb_dateecheance = field_tempdb[8]
            tdb_codebranc = field_tempdb[9]
            tdb_codecateg = field_tempdb[10]
            tdb_vtable = field_tempdb[11]
            tdb_vdureectr = field_tempdb[12]
            tdb_vdureepai = field_tempdb[13]
            tdb_modpai = field_tempdb[14]
            tdb_cpa = field_tempdb[15]
            tdb_cpu = field_tempdb[16]
            tdb_numaven = field_tempdb[17]
            tdb_aarattach = field_tempdb[18]
            tdb_mmrattach = field_tempdb[19]
            tdb_aacpt = field_tempdb[20]
            tdb_mmcpt = field_tempdb[21]
            tdb_codecarte = field_tempdb[22]
            tdb_ordre = field_tempdb[23]
            tdb_codefic = field_tempdb[24]
            tdb_primenet = field_tempdb[25]
            tdb_access = field_tempdb[26]
            tdb_te = field_tempdb[27]
            tdb_tva = field_tempdb[28]
            tdb_primetot = field_tempdb[29]
            tdb_commag = field_tempdb[30]
            tdb_commcrt1 = field_tempdb[31]
            tdb_commcrt2 = field_tempdb[32]
            tdb_interav = field_tempdb[33]
            tdb_datecomptable = field_tempdb[34]
            tdb_tmv = field_tempdb[35]

            # Voir courtiers
            id_crt1 = 0
            if tdb_courtier1 <> "000":
                courtier_cour = self.traiter_courtier(tdb_codeag,tdb_courtier1,cursorSQLServer,connection)
                id_crt1 = self.voir_f_apporteur(courtier_cour,tdb_courtier1,tdb_codeag)
            id_crt2 = 0
            if tdb_courtier2 <> "000":
                courtier_cour = self.traiter_courtier(tdb_codeag,tdb_courtier2,cursorSQLServer,connection)
                id_crt2 = self.voir_f_apporteur(courtier_cour,tdb_courtier2,tdb_codeag)

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
