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
#Import logger
import logging
import re
import json
#Get the logger
_logger = logging.getLogger(__name__)
#importing pypyodbc


class connecteur(models.Model):    
    _name = 'connecteur.aro'
    
    @api.multi
    def update_add_record(self):
        print "start"
        #connect to sql server
        connection = pypyodbc.connect('DRIVER=FreeTDS;SERVER=10.0.0.126;PORT=1433;DATABASE=aro;UID=sa;PWD=Aro1;TDS_Version=7.0') 
        
        #instance cursor SQL Server
        cursorSQLServer = connection.cursor()       
        #instance cursor Odoo Python
        cursorPOSTGRESOdoo = self.env.cr
        #instance objet dans odoo
        obj_f_polices = self.env['f.polices']
        obj_f_version_polices = self.env['f.version.police']
        obj_f_mouvement = self.env['f.mouvement']
        obj_f_mouvement = self.env['f.prime']
        
        #Toutes les etapes pour connecter V9 et Odoo:
        
        #ETAPE 1: Recuperation de l'identifiant du version police dans 
        #la table aro_nexthope
        # key = 2 =>  id version police
        # key = 3 => id prime      
        cursorSQLServer.execute("""SELECT  nxh_date_aro
                                          ,nxh_date_nexthope
                                          ,nxh_ver_ident
                                          ,nxh_prm_ident
                                          ,nxh_type_emission                                         
                                           
                                    FROM aro_nexthope_reprise WHERE  nxh_date_nexthope IS NULL """)         
        
               
        resultsSQLAroNextHope = cursorSQLServer.fetchall()             
        #test if resultsSQLAroNextHope
        if resultsSQLAroNextHope:            
            for field_aro_nexthope in resultsSQLAroNextHope:
                id_version_police = field_aro_nexthope[2]         
                id_prime = field_aro_nexthope[3]
                typemission = field_aro_nexthope[4]
                if typemission in ['AFN','AVT','RES','TER','REV']:
                    ####### TRAITEMENT NORMAL #############
                    self.traitement_normal(id_version_police,id_prime,cursorSQLServer,cursorPOSTGRESOdoo,connection)
                    ######## FIN TRAITEMENT NORMAL ########
                else:
                    if typemission == 'SUS':
                        self.suspension(connection,cursorSQLServer,cursorPOSTGRESOdoo,id_version_police)
                    if typemission == 'RAN':
                        print 'RAN'
                    if typemission == 'SNF':
                        print 'SNF'                                           
                                                 
                
        #Ferme la connexion SQL Server
        connection.close()                              
        print "end all insert"  
    
    def sanseffet(self,connection,cursorSQLServer,cursorPOSTGRESOdoo,id_version_police):
        if id_version_police:
            cursorSQLServer.execute(""" SELECT "POL_IDENT", "POL_CODETAT" FROM 
                                        F_POLICES
                                        INNER JOIN
                                        F_VERSION_POLICE on F_POLICES."POL_IDENT" = F_VERSION_POLICE."VER_PTRPOLID" """)
            resultsSQLPol = cursorSQLServer.fetchall()
            if resultsSQLPol:
                pol_ident = resultsSQLPol[0][0]
                pol_codetat = resultsSQLPol[0][1]                
                if pol_codetat == '96':
                    cursorPOSTGRESOdoo.execute(""" UPDATE f_ploices SET "POL_CODETAT" = %s WHERE id = %s """ % ('96',pol_ident))
                    cursorPOSTGRESOdoo.execute(""" UPDATE f_version_police SET "VER_TYPEMISSION" = %s WHERE id = %s """ % ('SNF',id_version_police))
                else:
                    cursorPOSTGRESOdoo.execute(""" DELETE FROM f_version_police WHERE id = %s """ % (id_version_police))
                    cursorPOSTGRESOdoo.execute(""" SELECT MAX("VER_IDENT") FROM f_version_police WHERE "VER_PTRPOLID" = %s  """,(pol_ident))
                    resultsOdooMaxVerIdent = cursorPOSTGRESOdoo.fetchall()
                    if maxveridentdata:
                        maxverident = resultsOdooMaxVerIdent[0][0]
                        cursorPOSTGRESOdoo.execute(""" UPDATE f_version_police SET "VER_PTRSUIVID" = %s WHERE "VER_IDENT" """,(0,maxverident))
                        
                    
                    
                    
                
            
            
        
    def suspension(self,connection,cursorSQLServer,cursorPOSTGRESOdoo,id_version_police):
        if id_version_police:
            #Recuperation de l'id police dans la table Version_police                    
            cursorSQLServer.execute(""" SELECT "VER_PTRPOLID" FROM F_VERSION_POLICE WHERE "VER_IDENT" = %s """ % (id_version_police))
            resultsSQLPolicesId = cursorSQLServer.fetchall()
            if resultsSQLPolicesId:
                cursorPOSTGRESOdoo.execute("""UPDATE f_polices SET "POL_CODETAT" = %s WHERE id = %s """ % ('3',resultsSQLPolicesId[0][0]))
                ############################## ERCIRE F_VERSION_POLICE DANS Odoo ##########################################################
                cursorSQLServer.execute("""SELECT "VER_DATEFIN",
                                                  "VER_DATEDEB",
                                                  "VER_TYPEMISSION", 
                                                  "VER_PTRPRMID",  
                                                  "VER_PTRPOLID",
                                                  "VER_IDENT" 
                                         FROM F_VERSION_POLICE WHERE "VER_IDENT" = %s """ % (id_version_police))
                resultsSQLFVersionPolices = cursorSQLServer.fetchall()
                if resultsSQLFVersionPolices:
                    #Creation f_version_police
                    VER_DATEFIN = self.parse_date(resultsSQLFVersionPolices[0][0])
                    VER_DATEDEB = self.parse_date(resultsSQLFVersionPolices[0][1])
                    VER_TYPEMISSION = self.cast_to_string(resultsSQLFVersionPolices[0][2])
                    VER_PTRPRMID = self.none_value(resultsSQLFVersionPolices[0][3])
                    VER_PTRPOLID = self.none_value(resultsSQLFVersionPolices[0][4])
                    VER_IDENT =   resultsSQLFVersionPolices[0][5]                                
                    #Inserer la version police dans Odoo
                    #On utilise la methode cr.execute car la fonction create d'odoo cree automatiquement la cle primaire
                    cursorPOSTGRESOdoo.execute(""" INSERT INTO f_version_police (                                                                                            
                                                                                  id,
                                                                                  create_uid,
                                                                                  "VER_DATEFIN", 
                                                                                  "VER_DATEDEB" ,
                                                                                  "VER_TYPEMISSION",
                                                                                  write_date,
                                                                                  "VER_PTRPRMID",
                                                                                  create_date,
                                                                                  write_uid,
                                                                                  "VER_PTRPOLID"                                                                                          
                                                                                ) VALUES (%s,%s,%s,%s,'%s','%s',%s,'%s',%s,%s)
                                     
                                                """ % (id_version_police,1,VER_DATEFIN,VER_DATEDEB,VER_TYPEMISSION,datetime.datetime.now(),VER_PTRPRMID,datetime.datetime.now(),1,VER_PTRPOLID))
                ############################ Fin Insertion f_version_police dans odoo ############################################################################################
        
            cursorSQLServer.execute("""UPDATE aro_nexthope SET nxh_date_nexthope =?   WHERE nxh_ver_ident= ? """,(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),id_version_police))
            connection.commit()
               
                
            
            
        
        
          
        
        
    def traitement_normal(self,id_version_police,id_prime,cursorSQLServer,cursorPOSTGRESOdoo,connection):
        #instance objet dans odoo
        obj_f_polices = self.env['f.polices']
        obj_f_version_polices = self.env['f.version.police']
        obj_f_mouvement = self.env['f.mouvement']
        obj_f_mouvement = self.env['f.prime']
        #ETAPE 2: Recuperer la police correspodante, si aucune police alors on cree dans Odoo
        #Sinon on met a jour la police dans Odoo
        if id_version_police:
            #Recuperation de l'id police dans la table Version_police                    
            cursorSQLServer.execute(""" SELECT "VER_PTRPOLID" FROM F_VERSION_POLICE WHERE "VER_IDENT" = %s """ % (id_version_police))
            resultsSQLPolicesId = cursorSQLServer.fetchall()                    
            if resultsSQLPolicesId:
                id_polices = resultsSQLPolicesId[0][0]
                #Lire dans la table f_polices dans Odoo si la police existe
                id_police_odoo = obj_f_polices.search([('id','=',id_polices)])                                               
                #Lire dans f_prime
                id_f_prime_odoo = obj_f_mouvement.search([('id','=',id_prime)])
                id_odoo_version_police = obj_f_version_polices.search([('id','=',id_version_police)])
                # Test si la version police et la prime existe deja dans odoo
                # On echappe et passe au traitement suivant                
                 
                #Si la ploice existe alors on fait le traitement                        
                if id_police_odoo:
                    id_police_existant_odoo = id_police_odoo.id                                            
                    #Etape A-1                            
                    #recuperation Version Police dans SQL Server
                    cursorSQLServer.execute("""SELECT "VER_DATEFIN",
                                                      "VER_DATEDEB",
                                                      "VER_TYPEMISSION", 
                                                      "VER_PTRPRMID",  
                                                      "VER_PTRPOLID",
                                                      "VER_IDENT" 
                                             FROM F_VERSION_POLICE WHERE "VER_IDENT" = %s """ % (id_version_police))
                    resultsSQLFVersionPolices = cursorSQLServer.fetchall()
                    if resultsSQLFVersionPolices:
                        #Creation f_version_police
                        VER_DATEFIN = self.parse_date(resultsSQLFVersionPolices[0][0])
                        VER_DATEDEB = self.parse_date(resultsSQLFVersionPolices[0][1])
                        VER_TYPEMISSION = self.cast_to_string(resultsSQLFVersionPolices[0][2])
                        VER_PTRPRMID = self.none_value(resultsSQLFVersionPolices[0][3])
                        VER_PTRPOLID = self.none_value(resultsSQLFVersionPolices[0][4])
                        VER_IDENT =   resultsSQLFVersionPolices[0][5]                                
                        #Inserer la version police dans Odoo
                        #On utilise la methode cr.execute car la fonction create d'odoo cree automatiquement la cle primaire
                        cursorPOSTGRESOdoo.execute(""" INSERT INTO f_version_police (                                                                                            
                                                                                      id,
                                                                                      create_uid,
                                                                                      "VER_DATEFIN", 
                                                                                      "VER_DATEDEB" ,
                                                                                      "VER_TYPEMISSION",
                                                                                      write_date,
                                                                                      "VER_PTRPRMID",
                                                                                      create_date,
                                                                                      write_uid,
                                                                                      "VER_PTRPOLID"                                                                                          
                                                                                    ) VALUES (%s,%s,%s,%s,'%s','%s',%s,'%s',%s,%s)
                                         
                                                    """ % (id_version_police,1,VER_DATEFIN,VER_DATEDEB,VER_TYPEMISSION,datetime.datetime.now(),VER_PTRPRMID,datetime.datetime.now(),1,VER_PTRPOLID))
                        ############################ Fin Insertion f_version_police dans odoo ############################################################################################                     
                        
                        ### ruperation de PAS_PTRBASID : BRANCHE et test si PAS_PTRBASID = 1003
                        PAS_PTRBASID =  obj_f_polices.browse([id_police_existant_odoo]).POL_PTRPASID.PAS_PTRBASID.id
                        ############################################################################################
                        #### F_MOUVEMENT, SOR ######################################################################
                        SOR_IDENT = self.mouvement_sor(cursorSQLServer,cursorPOSTGRESOdoo,id_version_police)                                                            
                        if PAS_PTRBASID ==  18003:
                            if  SOR_IDENT:                                        
                                self.maladie_adher_ayant_droit(cursorSQLServer,cursorPOSTGRESOdoo,id_version_police,SOR_IDENT)  
                                                                                                          
                        else:
                             #Recuperation et insertion dans f_mouvement, desc_stat_100,clause_dyn,garantie_dyn
                             if SOR_IDENT:                                                                             
                                 self.mouvement_desc100_clause_garantie(cursorSQLServer,cursorPOSTGRESOdoo,id_version_police,SOR_IDENT) 
                                 
                                                                                                                                                                    
                        #######################################################################################################################                                                                
                                     
                #Si la police n'existe pas alors on cree dans odoo    
                else:                                   
                    print "new Police"
                    ### LIRE F_POLICE dans SQLServer
                    self.create_police(cursorSQLServer,cursorPOSTGRESOdoo,id_version_police,id_polices)
                    ############################## ERCIRE F_VERSION_POLICE DANS Odoo ##########################################################
                    cursorSQLServer.execute("""SELECT "VER_DATEFIN",
                                                      "VER_DATEDEB",
                                                      "VER_TYPEMISSION", 
                                                      "VER_PTRPRMID",  
                                                      "VER_PTRPOLID",
                                                      "VER_IDENT" 
                                             FROM F_VERSION_POLICE WHERE "VER_IDENT" = %s """ % (id_version_police))
                    resultsSQLFVersionPolices = cursorSQLServer.fetchall()
                    if resultsSQLFVersionPolices:
                        #Creation f_version_police
                        VER_DATEFIN = self.parse_date(resultsSQLFVersionPolices[0][0])
                        VER_DATEDEB = self.parse_date(resultsSQLFVersionPolices[0][1])
                        VER_TYPEMISSION = self.cast_to_string(resultsSQLFVersionPolices[0][2])
                        VER_PTRPRMID = self.none_value(resultsSQLFVersionPolices[0][3])
                        VER_PTRPOLID = self.none_value(resultsSQLFVersionPolices[0][4])
                        VER_IDENT =   resultsSQLFVersionPolices[0][5]                                
                        #Inserer la version police dans Odoo
                        #On utilise la methode cr.execute car la fonction create d'odoo cree automatiquement la cle primaire
                        cursorPOSTGRESOdoo.execute(""" INSERT INTO f_version_police (                                                                                            
                                                                                      id,
                                                                                      create_uid,
                                                                                      "VER_DATEFIN", 
                                                                                      "VER_DATEDEB" ,
                                                                                      "VER_TYPEMISSION",
                                                                                      write_date,
                                                                                      "VER_PTRPRMID",
                                                                                      create_date,
                                                                                      write_uid,
                                                                                      "VER_PTRPOLID"                                                                                          
                                                                                    ) VALUES (%s,%s,%s,%s,'%s','%s',%s,'%s',%s,%s)
                                         
                                                    """ % (id_version_police,1,VER_DATEFIN,VER_DATEDEB,VER_TYPEMISSION,datetime.datetime.now(),VER_PTRPRMID,datetime.datetime.now(),1,VER_PTRPOLID))
                        ############################ Fin Insertion f_version_police dans odoo ############################################################################################  
                        
                    ### ruperation de PAS_PTRBASID : BRANCHE et test si PAS_PTRBASID = 1003
                    PAS_PTRBASID =  obj_f_polices.browse([id_polices]).POL_PTRPASID.PAS_PTRBASID.id                            
                    #### F_MOUVEMENT, SOR ######################################################################
                    SOR_IDENT = self.mouvement_sor(cursorSQLServer,cursorPOSTGRESOdoo,id_version_police)                                                         
                    if PAS_PTRBASID ==  18003:
                        if  SOR_IDENT:                                    
                            self.maladie_adher_ayant_droit(cursorSQLServer,cursorPOSTGRESOdoo,id_version_police,SOR_IDENT)                                                                                                        
                    else:
                         #Recuperation et insertion dans f_mouvement, desc_stat_100,clause_dyn,garantie_dyn
                         if SOR_IDENT:                                                                
                             self.mouvement_desc100_clause_garantie(cursorSQLServer,cursorPOSTGRESOdoo,id_version_police,SOR_IDENT) 
                             
                                                                                                                                                                 
                    ####################################################################################################################### 
                    #Recuperation du client
                    #recuperation de l'intermediaire
                    #recuperation de l'apporteur
                    #recuperation du version police                            
                    
        ########################################################################################################################################
        #### ETAPE 3: INSERTION F_PRIME ET F_PRIME LIGNE #################################################################    ##################
        ########################################################################################################################################                
        if id_version_police and id_prime:
            self.f_prime_prime_ligne(cursorSQLServer,cursorPOSTGRESOdoo,id_version_police,id_prime)
            #print "prime"
            
        ##### Mettre a jour le sql server pour renseigner une date ##########################
        if id_version_police:
            cursorSQLServer.execute("""UPDATE aro_nexthope SET nxh_date_nexthope =?   WHERE nxh_ver_ident= ? AND nxh_prm_ident = ? """,(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),id_version_police,id_prime))
            connection.commit()  
    
    
    
    def cast_to_string(self,param):
        if param is None:
            return "''" 
        a = param      
        return str(a.replace("'",r"''"))
		
	def modification_escape_string(self,param):
	    if param is None:
		    return "''"
        a = param
        return "'" + str(replace("'",r"''")) + "'"
		
    
    
    def none_value(self,param):        
        if param is None:            
            return 'null'        
        return param
    
    def cast_opt_string(self,param):
        if param is None:
            return 'null'
        #return "\"" + re.escape(str(param)) + "\""                 
        #return  "'"+ str(param.replace("'",r"\'"))+ "'"
        #\"%s\"
        return "'" + str(param) + "'"
    
    def cast_opt_string_rpl(self,param):
        if param is None:
            return 'null'
        else:
            a = param.replace("'","''")
            return "'"+str(a)+"'"
        
        
    
    def parse_date(self,param):
        if param is None:
            return 'null'
        return "'"+ str(param) +"'"
    
    def parse_date_cast(self,param):
        if param is None:
            return None
        else:
            return "'"+ str(param) +"'"
    
    def create_police(self,cursorSQLServer,cursorPOSTGRESOdoo,id_version_police,id_polices):
        cursorSQLServer.execute(""" SELECT     "POL_DATEFINREGUL"
                                              ,"POL_DATDERAVT"
                                              ,"POL_IDENT"
                                              ,"POL_PREAV_RESIL"
                                              ,"POL_CRIDAT2"
                                              ,"POL_CARLIBRE1"
                                              ,"POL_REGAVT"
                                              ,"POL_ANCNOMCIE"
                                              ,"POL_REFCP"
                                              ,"POL_INT_LOT_EXP"
                                              ,"POL_REGLEUR_AFN"
                                              ,"POL_SEQUENTIEL"
                                              ,"POL_COASS_GEST"
                                              ,"POL_FRACTION"
                                              ,"POL_COMDEDUITE_AFN"
                                              ,"POL_STOP_TERME"
                                              ,"POL_REVIS_ASSIET"
                                              ,"POL_GERE_PRODUC"
                                              ,"POL_COMDE_TOT_RS"
                                              ,"POL_BMACTUEL"
                                              ,"POL_ACOMPTE_CLI"
                                              ,"POL_REGRS"
                                              ,"POL_OPTION"
                                              ,"POL_TAUX_APPEL"
                                              ,"POL_COMMENTAIRES"
                                              ,"POL_INT_LOT_IMP"
                                              ,"POL_POLL_ACC"
                                              ,"POL_NUMPOL"
                                              ,"POL_PTRCONVID"
                                              ,"POL_POLL_REF"
                                              ,"POL_COMDEDUITE_AVT"
                                              ,"POL_CRIAL3"
                                              ,"POL_ANCNUMPOL"
                                              ,"POL_IDENT_DPT"
                                              ,"POL_HEURE_EFFET"
                                              ,"POL_INDICEPREC"
                                              ,"POL_COMDE_TOT_TE"
                                              ,"POL_BCR_SIN"
                                              ,"POL_REFCS"
                                              ,"POL_GESTPRO"
                                              ,"POL_ASSURE"
                                              ,"POL_REMPLACANTE"
                                              ,"POL_REFCG"
                                              ,"POL_PTRINID"
                                              ,"POL_CODE_CONT"
                                              ,"POL_CRIAL4"
                                              ,"POL_NUMDEVIS"
                                              ,"POL_JOUR_RECOUV"
                                              ,"POL_DATDEB"
                                              ,"POL_CRIAL1"
                                              ,"POL_MAJO_FRACT"
                                              ,"POL_ORIGINESAISIE"
                                              ,"POL_COMDEDUITE_TER"
                                              ,"POL_REGLEUR_TER"
                                              ,"POL_CODECHPRIN"
                                              ,"POL_PRIME_PROVIS"
                                              ,"POL_VALEUR_ASSIE"
                                              ,"POL_CODETAT"
                                              ,"POL_CONFIE"
                                              ,"POL_REGLE_COM_INTER"
                                              ,"POL_REVIS_SURV"
                                              ,"POL_TERFISC"
                                              ,"POL_COEF_COMM"
                                              ,"POL_PTRTPEIDENT"
                                              ,"POL_REGTER"
                                              ,"POL_DUREE"
                                              ,"POL_COAREP_SIN"
                                              ,"POL_NUM_DOSSIER"
                                              ,"POL_COMAPETX"
                                              ,"POL_CRINU1"
                                              ,"POL_DATCRE"
                                              ,"POL_COAREP_PRM"
                                              ,"POL_DATECHPRO"
                                              ,"POL_DATE_HEURE_EFFET"
                                              ,"POL_CRINU2"
                                              ,"POL_STOP_MAJO"
                                              ,"POL_JOUR_PRELEVEMENT"
                                              ,"POL_CRINU3"
                                              ,"POL_RESIL_RECOUV"
                                              ,"POL_CODECHPRO"
                                              ,"POL_SANTE_NONRESP"
                                              ,"POL_DATSUSPENS"
                                              ,"POL_DEROG_RECOUV"
                                              ,"POL_CHARGECLIENT"
                                              ,"POL_AJUST_PCPM"
                                              ,"POL_CRIAL5"
                                              ,"POL_CRIND6"
                                              ,"POL_REGLEUR_RS"
                                              ,"POL_COAGEST"
                                              ,"POL_DCPRGSMODE"
                                              ,"POL_CODRESIL"
                                              ,"POL_JUSTIFSIN"
                                              ,"POL_DATRESIL"
                                              ,"POL_DATE_ASSIETT"
                                              ,"POL_BMPREC"
                                              ,"POL_INDICEACTU"
                                              ,"POL_BCR"
                                              ,"POL_CRINU5"
                                              ,"POL_COMDE_TOT_EV"
                                              ,"POL_REGCPT"
                                              ,"POL_COEFAJUST"
                                              ,"POL_DATFIN"
                                              ,"POL_DATEFIN_GRATUIT"
                                              ,"POL_CHARGE_CLI"
                                              ,"POL_DATREACT"
                                              ,"POL_PTRCOID"
                                              ,"POL_PTRAPID"
                                              ,"POL_NUMDERAVT"
                                              ,"POL_CRIAL2"
                                              ,"POL_TAUX_COM_INTER"
                                              ,"POL_REGLEUR_AVT"
                                              ,"POL_CODINDICE"
                                              ,"POL_JUSTIFPRM"
                                              ,"POL_LST_TAUX_ECH"
                                              ,"POL_ANCDATDEB"
                                              ,"POL_CRINU4"
                                              ,"POL_DATETAT"
                                              ,"POL_CRIDAT1"
                                              ,"POL_POLICE_REGUL"
                                              ,"POL_COMDE_TOT_AN"
                                              ,"POL_PTRMONPROV"
                                              ,"POL_SERVICES"
                                              ,"POL_TAUX_COM_TOTAL"
                                              ,"POL_UNITE_CARENCE"
                                              ,"POL_CODSUSPENS"
                                              ,"POL_DATE_AVT_MINI"
                                              ,"POL_CODE_SOCIETE"
                                              ,"POL_DATINDIC"
                                              ,"POL_DATMAJ"
                                              ,"POL_CODE_ETABL"
                                              ,"POL_REVISABLE"
                                              ,"POL_DCPRGSBENEF"
                                              ,"POL_PTRCONVID_IJ"
                                              ,"POL_PTRPASID"
                                              ,"POL_PTRCLID"
                                              ,"POL_INDEXABLE"
                                              ,"POL_COMDEDUITE_RS"
                                              ,"POL_REFECHO"
                                              ,"POL_CRIND7"
                                              ,"POL_GESTSIN"
                                              ,"POL_PTRREPID"
                                              ,"POL_CRIDAT3"
                                              ,"POL_NB_ECH"
                                              ,"POL_CARENCE"
                                              ,"POL_TAUX_AJUST"
                                              ,"POL_BUDGET"
                                              ,"POL_DATE_CONT"
                                          FROM F_POLICES  WHERE "POL_IDENT" = %s """ % (id_polices))
        resultsSQLFPolice = cursorSQLServer.fetchall()
        if resultsSQLFPolice :                    
            POL_DATEFINREGUL = resultsSQLFPolice[0][0]
            POL_DATDERAVT = resultsSQLFPolice[0][1]
            POL_IDENT = self.none_value(resultsSQLFPolice[0][2])
            POL_PREAV_RESIL = resultsSQLFPolice[0][3]
            POL_CRIDAT2 = resultsSQLFPolice[0][4]
            POL_CARLIBRE1 = resultsSQLFPolice[0][5]
            POL_REGAVT = resultsSQLFPolice[0][6]
            POL_ANCNOMCIE = resultsSQLFPolice[0][7]
            POL_REFCP = resultsSQLFPolice[0][8]
            POL_INT_LOT_EXP = resultsSQLFPolice[0][9]
            POL_REGLEUR_AFN = resultsSQLFPolice[0][10]
            POL_SEQUENTIEL =resultsSQLFPolice[0][11]
            POL_COASS_GEST = resultsSQLFPolice[0][12]
            POL_FRACTION = resultsSQLFPolice[0][13]
            POL_COMDEDUITE_AFN = resultsSQLFPolice[0][14]
            POL_STOP_TERME = resultsSQLFPolice[0][15]
            POL_REVIS_ASSIET = resultsSQLFPolice[0][16]
            POL_GERE_PRODUC = resultsSQLFPolice[0][17]
            POL_COMDE_TOT_RS = resultsSQLFPolice[0][18]
            POL_BMACTUEL = resultsSQLFPolice[0][19]
            POL_ACOMPTE_CLI = resultsSQLFPolice[0][20]
            POL_REGRS = resultsSQLFPolice[0][21]
            POL_OPTION = resultsSQLFPolice[0][22]
            POL_TAUX_APPEL = resultsSQLFPolice[0][23]
            POL_COMMENTAIRES = resultsSQLFPolice[0][24]
            POL_INT_LOT_IMP = resultsSQLFPolice[0][25]
            POL_POLL_ACC = resultsSQLFPolice[0][26]
            POL_NUMPOL = resultsSQLFPolice[0][27]
            POL_PTRCONVID = resultsSQLFPolice[0][28]
            POL_POLL_REF = resultsSQLFPolice[0][29]
            POL_COMDEDUITE_AVT = resultsSQLFPolice[0][30]
            POL_CRIAL3 = resultsSQLFPolice[0][31]
            POL_ANCNUMPOL = resultsSQLFPolice[0][32]
            POL_IDENT_DPT = resultsSQLFPolice[0][33]
            POL_HEURE_EFFET = resultsSQLFPolice[0][34]
            POL_INDICEPREC = resultsSQLFPolice[0][35]
            POL_COMDE_TOT_TE = resultsSQLFPolice[0][36]
            POL_BCR_SIN = resultsSQLFPolice[0][37]
            POL_REFCS = resultsSQLFPolice[0][38]
            POL_GESTPRO = resultsSQLFPolice[0][39]
            POL_ASSURE = resultsSQLFPolice[0][40]
            POL_REMPLACANTE = resultsSQLFPolice[0][41]
            POL_REFCG = resultsSQLFPolice[0][42]
            POL_PTRINID = resultsSQLFPolice[0][43]
            #POL_PTRINID = 49006
            POL_CODE_CONT = resultsSQLFPolice[0][44]
            POL_CRIAL4 = resultsSQLFPolice[0][45]
            POL_NUMDEVIS = resultsSQLFPolice[0][46]
            POL_JOUR_RECOUV = resultsSQLFPolice[0][47]
            POL_DATDEB = resultsSQLFPolice[0][48]
            POL_CRIAL1 = resultsSQLFPolice[0][49]
            POL_MAJO_FRACT = resultsSQLFPolice[0][50]
            POL_ORIGINESAISIE = resultsSQLFPolice[0][51]
            POL_COMDEDUITE_TER = resultsSQLFPolice[0][52]
            POL_REGLEUR_TER = resultsSQLFPolice[0][53]
            POL_CODECHPRIN = self.cast_opt_string(resultsSQLFPolice[0][54])
            POL_PRIME_PROVIS = resultsSQLFPolice[0][55]
            POL_VALEUR_ASSIE = resultsSQLFPolice[0][56]
            POL_CODETAT = resultsSQLFPolice[0][57]
            POL_CONFIE = resultsSQLFPolice[0][58]
            POL_REGLE_COM_INTER = resultsSQLFPolice[0][59]
            POL_REVIS_SURV = resultsSQLFPolice[0][60]
            POL_TERFISC = resultsSQLFPolice[0][61]
            POL_COEF_COMM = resultsSQLFPolice[0][62]
            POL_PTRTPEIDENT = resultsSQLFPolice[0][63]
            POL_REGTER = resultsSQLFPolice[0][64]
            POL_DUREE = resultsSQLFPolice[0][65]
            POL_COAREP_SIN = resultsSQLFPolice[0][66]
            POL_NUM_DOSSIER = resultsSQLFPolice[0][67]
            POL_COMAPETX = resultsSQLFPolice[0][68]
            POL_CRINU1 = resultsSQLFPolice[0][69]
            POL_DATCRE = resultsSQLFPolice[0][70]
            POL_COAREP_PRM = resultsSQLFPolice[0][71]
            POL_DATECHPRO = resultsSQLFPolice[0][72]
            POL_DATE_HEURE_EFFET =  resultsSQLFPolice[0][73]
            POL_CRINU2 = resultsSQLFPolice[0][74]
            POL_STOP_MAJO = resultsSQLFPolice[0][75]
            POL_JOUR_PRELEVEMENT = resultsSQLFPolice[0][76]
            POL_CRINU3 = resultsSQLFPolice[0][77]
            POL_RESIL_RECOUV = resultsSQLFPolice[0][78]
            POL_CODECHPRO = resultsSQLFPolice[0][79]
            POL_SANTE_NONRESP = resultsSQLFPolice[0][80]
            POL_DATSUSPENS = resultsSQLFPolice[0][81]
            POL_DEROG_RECOUV = resultsSQLFPolice[0][82]
            POL_CHARGECLIENT = resultsSQLFPolice[0][83]
            POL_AJUST_PCPM = resultsSQLFPolice[0][84]
            POL_CRIAL5 = resultsSQLFPolice[0][85]
            POL_CRIND6 = resultsSQLFPolice[0][86]
            POL_REGLEUR_RS = resultsSQLFPolice[0][87]
            POL_COAGEST = resultsSQLFPolice[0][88]
            POL_DCPRGSMODE = resultsSQLFPolice[0][89]
            POL_CODRESIL = resultsSQLFPolice[0][90]
            POL_JUSTIFSIN = resultsSQLFPolice[0][91]
            POL_DATRESIL = resultsSQLFPolice[0][92]
            POL_DATE_ASSIETT = resultsSQLFPolice[0][93]
            POL_BMPREC = resultsSQLFPolice[0][94]
            POL_INDICEACTU = resultsSQLFPolice[0][95]
            POL_BCR = resultsSQLFPolice[0][96]
            POL_CRINU5 = resultsSQLFPolice[0][97]
            POL_COMDE_TOT_EV = resultsSQLFPolice[0][98]
            POL_REGCPT = resultsSQLFPolice[0][99]
            POL_COEFAJUST = resultsSQLFPolice[0][100]
            POL_DATFIN = resultsSQLFPolice[0][101]
            POL_DATEFIN_GRATUIT = resultsSQLFPolice[0][102]
            POL_CHARGE_CLI = resultsSQLFPolice[0][103]
            POL_DATREACT = resultsSQLFPolice[0][104]
            POL_PTRCOID = resultsSQLFPolice[0][105]
            POL_PTRAPID =resultsSQLFPolice[0][106]
            #POL_PTRAPID = 247005
            POL_NUMDERAVT = self.none_value(resultsSQLFPolice[0][107])
            POL_CRIAL2 = resultsSQLFPolice[0][108]
            POL_TAUX_COM_INTER = resultsSQLFPolice[0][109]
            POL_REGLEUR_AVT = resultsSQLFPolice[0][110]
            POL_CODINDICE = resultsSQLFPolice[0][111]
            POL_JUSTIFPRM = resultsSQLFPolice[0][112]
            POL_LST_TAUX_ECH = resultsSQLFPolice[0][113]
            POL_ANCDATDEB = resultsSQLFPolice[0][114]
            POL_CRINU4 = resultsSQLFPolice[0][115]
            POL_DATETAT = resultsSQLFPolice[0][116]
            POL_CRIDAT1 = resultsSQLFPolice[0][117]
            POL_POLICE_REGUL = resultsSQLFPolice[0][118]
            POL_COMDE_TOT_AN = resultsSQLFPolice[0][119]
            POL_PTRMONPROV = resultsSQLFPolice[0][120]
            POL_SERVICES = resultsSQLFPolice[0][121]
            POL_TAUX_COM_TOTAL = resultsSQLFPolice[0][122]
            POL_UNITE_CARENCE = self.cast_opt_string(resultsSQLFPolice[0][123])
            POL_CODSUSPENS = resultsSQLFPolice[0][124]
            POL_DATE_AVT_MINI = resultsSQLFPolice[0][125]
            POL_CODE_SOCIETE = resultsSQLFPolice[0][126]
            POL_DATINDIC = resultsSQLFPolice[0][127]
            POL_DATMAJ = resultsSQLFPolice[0][128]
            POL_CODE_ETABL = resultsSQLFPolice[0][129]
            POL_REVISABLE = resultsSQLFPolice[0][130]
            POL_DCPRGSBENEF = resultsSQLFPolice[0][131]
            POL_PTRCONVID_IJ = self.none_value(resultsSQLFPolice[0][132])
            POL_PTRPASID = resultsSQLFPolice[0][133]
            POL_PTRCLID = resultsSQLFPolice[0][134]
            POL_INDEXABLE = resultsSQLFPolice[0][135]
            POL_COMDEDUITE_RS = resultsSQLFPolice[0][136]
            POL_REFECHO = resultsSQLFPolice[0][137]
            POL_CRIND7 = resultsSQLFPolice[0][138]
            POL_GESTSIN = resultsSQLFPolice[0][139]
            POL_PTRREPID = resultsSQLFPolice[0][140]
            POL_CRIDAT3 = resultsSQLFPolice[0][141]
            POL_NB_ECH = resultsSQLFPolice[0][142]
            POL_CARENCE = resultsSQLFPolice[0][143]
            POL_TAUX_AJUST = resultsSQLFPolice[0][144]
            POL_BUDGET = resultsSQLFPolice[0][145]
            POL_DATE_CONT = resultsSQLFPolice[0][146]           
            
            
            state = 'brouillon'
            if POL_CODETAT == '1':
                state = 'encours'
            
            if POL_CODETAT == '96' or POL_CODETAT == '95':
                state = 'annule'
                
            if POL_CODETAT == '3':
                state = 'suspension'
            
            name = 'POLICE -' +POL_NUMPOL
            ajout_risque = False        
            
            ### Test SI client existe dans Odoo POL_PTRCLID
            
            #### RECUPERATION F_P_C_CLIENT DANS ODOO
            obj_f_p_c_client  =  self.env['f.p.c.client'].search([('id','=',POL_PTRCLID)])
            if not obj_f_p_c_client:
                self.insert_client_personne(cursorSQLServer,cursorPOSTGRESOdoo,id_polices,POL_PTRCLID)
#             else:                
#                 if not obj_f_p_c_client.BPCL_PTRBPPIDENT:
#                     #self.insert_client_personne(cursorSQLServer,cursorPOSTGRESOdoo,id_polices,POL_PTRCLID)
#                     print "test"                    
            ##### END F_P_C_CLIENT ########################################################################
            ##### ECRIRE F_INTERMEDIAIRE DANS LA POLICE ODOO ##################################################
            if POL_PTRINID is not None:                                                   
                obj_f_intermediaire = self.env['f.intermediaire'].search([('id','=',POL_PTRINID)])                
                if not obj_f_intermediaire:                    
                    self.insert_f_intermediaire(cursorSQLServer,cursorPOSTGRESOdoo,id_polices,POL_PTRINID)
            ###### END F_INTERMEDIAIRE #######################################################################
            
            #### ECRIRE F_APPORTEUR ##########################################################################
            if POL_PTRAPID is not None:                               
                obj_f_apporteur = self.env['f.apporteur'].search([('id','=',POL_PTRAPID)])
                if not obj_f_apporteur:
                    self.insert_f_apporteur(cursorSQLServer,cursorPOSTGRESOdoo,id_polices,POL_PTRAPID)
            ##### END F_APPORTEUR ############################################################################
            
            
            ## ECRIRE F_POLICES DANS ODOO
            cursorPOSTGRESOdoo.execute(""" INSERT INTO f_polices (id,
                                                                  "POL_PTRCONVID_IJ",
                                                                  create_date,
                                                                  "POL_PTRAPID",
                                                                  "POL_CODECHPRIN",
                                                                  "POL_UNITE_CARENCE",
                                                                  write_uid,
                                                                  "POL_FRACTION",
                                                                  "POL_INDICEACTU" ,
                                                                  "POL_SANTE_NONRESP",
                                                                  create_uid,
                                                                  "POL_CHARGECLIENT",
                                                                  "POL_PTRCLID",
                                                                  state,
                                                                  "POL_JOUR_PRELEVEMENT",
                                                                  "POL_PTRPASID",
                                                                  "POL_COMMENTAIRES",
                                                                  "POL_CODINDICE",
                                                                  "POL_COAREP_PRM",
                                                                  ajout_risque,
                                                                  "POL_DATEFIN_GRATUIT",
                                                                  "POL_PTRCOID",
                                                                  "POL_NUM_DOSSIER",
                                                                  "POL_COEF_COMM",
                                                                  "POL_CARENCE",
                                                                  "POL_CODETAT",
                                                                  write_date,
                                                                  "POL_DATE_HEURE_EFFET",
                                                                  "POL_CODE_SOCIETE",
                                                                  "POL_ASSURE",
                                                                  "POL_COAREP_SIN",
                                                                  "POL_DATFIN",
                                                                  name,
                                                                  "POL_DUREE",
                                                                  "POL_TERFISC",
                                                                  "POL_OPTION",
                                                                  "POL_CODE_ETABL",
                                                                  "POL_PTRINID",
                                                                  "POL_TAUX_APPEL",
                                                                  "POL_COMAPETX",
                                                                  "POL_NUMPOL") VALUES (%s,%s,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                                                                       %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'%s',%s,%s,%s,
                                                                                       %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
                                                                   """ % (POL_IDENT,POL_PTRCONVID_IJ,datetime.datetime.now(),self.none_value(POL_PTRAPID),POL_CODECHPRIN,POL_UNITE_CARENCE,1,
                                                                          self.cast_opt_string(POL_FRACTION),self.cast_opt_string(POL_INDICEACTU),self.cast_opt_string(POL_SANTE_NONRESP),1,self.cast_opt_string(POL_CHARGECLIENT),self.none_value(POL_PTRCLID),
                                                                          self.cast_opt_string(state),self.cast_opt_string(POL_JOUR_PRELEVEMENT),self.none_value(POL_PTRPASID),self.modification_escape_string(POL_COMMENTAIRES),self.cast_opt_string(POL_CODINDICE),self.cast_opt_string(POL_COAREP_PRM),
                                                                          ajout_risque,self.parse_date(POL_DATEFIN_GRATUIT),self.none_value(POL_PTRCOID),self.cast_opt_string(POL_NUM_DOSSIER),self.cast_opt_string(POL_COEF_COMM),self.cast_opt_string(POL_CARENCE),
                                                                          self.cast_opt_string(POL_CODETAT),datetime.datetime.now(),self.parse_date(POL_DATE_HEURE_EFFET),self.cast_opt_string(POL_CODE_SOCIETE),self.cast_opt_string(POL_ASSURE),self.cast_opt_string(POL_COAREP_SIN),
                                                                          self.parse_date(POL_DATFIN),self.cast_opt_string(name),self.cast_opt_string(POL_DUREE),self.cast_opt_string(POL_TERFISC),self.cast_opt_string(POL_OPTION),self.cast_opt_string(POL_CODE_ETABL),self.none_value(POL_PTRINID),self.none_value(POL_TAUX_APPEL),
                                                                          self.none_value(POL_COMAPETX),self.cast_opt_string(POL_NUMPOL)))
            
            print "police inserted"
        #####################################################################################################################################################
            
        
    def insert_client_personne(self,cursorSQLServer,cursorPOSTGRESOdoo,id_polices,POL_PTRCLID):
        ## LIRE F_P_C_CLIENT #####################################################################
        cursorSQLServer.execute(""" SELECT            "BPCL_CRIAL31"
                                                      ,"BPCL_CRIAL20"
                                                      ,"BPCL_PTRBPBIDENT"
                                                      ,"BPCL_CRIAL39"
                                                      ,"BPCL_PTRBPAIDENT"
                                                      ,"BPCL_CRIAL9"
                                                      ,"BPCL_CRIAL36"
                                                      ,"BPCL_G_TAUXREMISE"
                                                      ,"BPCL_CRIDAT1"
                                                      ,"BPCL_CRIAL19"
                                                      ,"BPCL_CRINU3"
                                                      ,"BPCL_R_SS_FAM"
                                                      ,"BPCL_CRINU1"
                                                      ,"BPCL_CRIAL26"
                                                      ,"BPCL_CRIDAT3"
                                                      ,"BPCL_CRIAL21"
                                                      ,"BPCL_CRIAL32"
                                                      ,"BPCL_MAJ_DATE"
                                                      ,"BPCL_CRIAL3"
                                                      ,"BPCL_CRIDAT4"
                                                      ,"BPCL_CRIAL7"
                                                      ,"BPCL_CRIAL38"
                                                      ,"BPCL_CRIAL16"
                                                      ,"BPCL_CRIAL8"
                                                      ,"BPCL_CRT_DATE"
                                                      ,"BPCL_R_COLL_COM"
                                                      ,"BPCL_G_CPTAUX_DEROG"
                                                      ,"BPCL_PTRBPPIDENT"
                                                      ,"BPCL_CLE"
                                                      ,"BPCL_INT_IDENT_DPT"
                                                      ,"BPCL_CRIAL15"
                                                      ,"BPCL_CODE_AUXIL"
                                                      ,"BPCL_CRIDAT5"
                                                      ,"BPCL_R_REGROUP3"
                                                      ,"BPCL_G_RECOUV_DEROG"
                                                      ,"BPCL_CRINU2"
                                                      ,"BPCL_R_REGROUP2"
                                                      ,"BPCL_CRIAL28"
                                                      ,"BPCL_CRIAL17"
                                                      ,"BPCL_CRIAL1"
                                                      ,"BPCL_G_MODEREGL"
                                                      ,"BPCL_CRT_USER"
                                                      ,"BPCL_CRIAL40"
                                                      ,"BPCL_R_SECTEUR"
                                                      ,"BPCL_CRIAL34"
                                                      ,"BPCL_CRIAL18"
                                                      ,"BPCL_R_REGROUP1"
                                                      ,"BPCL_CRIAL12"
                                                      ,"BPCL_CRIAL14"
                                                      ,"BPCL_INT_LOTEXP"
                                                      ,"BPCL_CRIAL4"
                                                      ,"BPCL_CRIAL33"
                                                      ,"BPCL_DATE_CLO_CPT"
                                                      ,"BPCL_CRIAL11"
                                                      ,"BPCL_CRIAL6"
                                                      ,"BPCL_CRIAL25"
                                                      ,"BPCL_CRIAL10"
                                                      ,"BPCL_REFECHO"
                                                      ,"BPCL_G_TYPE_PREL"
                                                      ,"BPCL_CRIAL27"
                                                      ,"BPCL_CRIAL24"
                                                      ,"BPCL_CRINU5"
                                                      ,"BPCL_CRIDAT2"
                                                      ,"BPCL_MAJ_USER"
                                                      ,"BPCL_CRIAL2"
                                                      ,"BPCL_R_FAMILLE"
                                                      ,"BPCL_CRINU4"
                                                      ,"BPCL_IDENT"
                                                      ,"BPCL_CRIAL30"
                                                      ,"BPCL_DATE_OUV_CPT"
                                                      ,"BPCL_CRIAL5"
                                                      ,"BPCL_CRIAL23"
                                                      ,"BPCL_CRIAL29"
                                                      ,"BPCL_INT_LOTIMP"
                                                      ,"BPCL_CRIAL37"
                                                      ,"BPCL_CRIAL22"
                                                      ,"BPCL_CRIAL13"
                                                      ,"BPCL_CRIAL35"
                                                      ,"BPCL_PTRRIBIDENT"
                                                      ,"BPCL_R_COLL_CPT"
                                                      ,"BPCL_COTE"
                                                  FROM F_P_C_CLIENT WHERE "BPCL_IDENT" = %s """  % (POL_PTRCLID))
        resultsSQLFPCClient = cursorSQLServer.fetchall()
        if resultsSQLFPCClient:
            BPCL_CRIAL31 = resultsSQLFPCClient[0][0]
            BPCL_CRIAL20 = resultsSQLFPCClient[0][1]
            BPCL_PTRBPBIDENT = resultsSQLFPCClient[0][2]
            BPCL_CRIAL39 = resultsSQLFPCClient[0][3]
            BPCL_PTRBPAIDENT = resultsSQLFPCClient[0][4]
            BPCL_CRIAL9 = resultsSQLFPCClient[0][5]
            BPCL_CRIAL36 = resultsSQLFPCClient[0][6]
            BPCL_G_TAUXREMISE = resultsSQLFPCClient[0][7]
            BPCL_CRIDAT1 = resultsSQLFPCClient[0][8]
            BPCL_CRIAL19 = resultsSQLFPCClient[0][9]
            BPCL_CRINU3 = resultsSQLFPCClient[0][10]
            BPCL_R_SS_FAM = resultsSQLFPCClient[0][11]
            BPCL_CRINU1 = resultsSQLFPCClient[0][12]
            BPCL_CRIAL26 = resultsSQLFPCClient[0][13]
            BPCL_CRIDAT3 = resultsSQLFPCClient[0][14]
            BPCL_CRIAL21 = resultsSQLFPCClient[0][15]
            BPCL_CRIAL32 = resultsSQLFPCClient[0][16]
            BPCL_MAJ_DATE = resultsSQLFPCClient[0][17]
            BPCL_CRIAL3 = resultsSQLFPCClient[0][18]
            BPCL_CRIDAT4 = resultsSQLFPCClient[0][19]
            BPCL_CRIAL7 = resultsSQLFPCClient[0][20]
            BPCL_CRIAL38 = resultsSQLFPCClient[0][21]
            BPCL_CRIAL16 = resultsSQLFPCClient[0][22]
            BPCL_CRIAL8 = resultsSQLFPCClient[0][23]
            BPCL_CRT_DATE = resultsSQLFPCClient[0][24]
            BPCL_R_COLL_COM = resultsSQLFPCClient[0][25]
            BPCL_G_CPTAUX_DEROG = resultsSQLFPCClient[0][26]
            BPCL_PTRBPPIDENT = resultsSQLFPCClient[0][27]
            BPCL_CLE = resultsSQLFPCClient[0][28]
            BPCL_INT_IDENT_DPT = resultsSQLFPCClient[0][29]
            BPCL_CRIAL15 = resultsSQLFPCClient[0][30]
            BPCL_CODE_AUXIL = resultsSQLFPCClient[0][31]
            BPCL_CRIDAT5 = resultsSQLFPCClient[0][32]
            BPCL_R_REGROUP3 = resultsSQLFPCClient[0][33]
            BPCL_G_RECOUV_DEROG = resultsSQLFPCClient[0][34]
            BPCL_CRINU2 = resultsSQLFPCClient[0][35]
            BPCL_R_REGROUP2 = resultsSQLFPCClient[0][36]
            BPCL_CRIAL28 = resultsSQLFPCClient[0][37]
            BPCL_CRIAL17 = resultsSQLFPCClient[0][38]
            BPCL_CRIAL1 = resultsSQLFPCClient[0][39]
            BPCL_G_MODEREGL = resultsSQLFPCClient[0][40]
            BPCL_CRT_USER = resultsSQLFPCClient[0][41]
            BPCL_CRIAL40 = resultsSQLFPCClient[0][42]
            BPCL_R_SECTEUR = resultsSQLFPCClient[0][43]
            BPCL_CRIAL34 = resultsSQLFPCClient[0][44]
            BPCL_CRIAL18 = resultsSQLFPCClient[0][45]
            BPCL_R_REGROUP1 = resultsSQLFPCClient[0][46]
            BPCL_CRIAL12 = resultsSQLFPCClient[0][47]
            BPCL_CRIAL14 = resultsSQLFPCClient[0][48]
            BPCL_INT_LOTEXP = resultsSQLFPCClient[0][49]
            BPCL_CRIAL4 = resultsSQLFPCClient[0][50]
            BPCL_CRIAL33 = resultsSQLFPCClient[0][51]
            BPCL_DATE_CLO_CPT = resultsSQLFPCClient[0][52]
            BPCL_CRIAL11 = resultsSQLFPCClient[0][53]
            BPCL_CRIAL6 = resultsSQLFPCClient[0][54]
            BPCL_CRIAL25 = resultsSQLFPCClient[0][55]
            BPCL_CRIAL10 = resultsSQLFPCClient[0][56]
            BPCL_REFECHO = resultsSQLFPCClient[0][57]
            
            BPCL_G_TYPE_PREL = resultsSQLFPCClient[0][58]
            if BPCL_G_TYPE_PREL == 0:
                BPCL_G_TYPE_PREL = 'par_prime'
                
            BPCL_CRIAL27 = resultsSQLFPCClient[0][59]
            BPCL_CRIAL24 = resultsSQLFPCClient[0][60]
            BPCL_CRINU5 = resultsSQLFPCClient[0][61]
            BPCL_CRIDAT2 = resultsSQLFPCClient[0][62]
            BPCL_MAJ_USER = resultsSQLFPCClient[0][63]
            BPCL_CRIAL2 = resultsSQLFPCClient[0][64]
            BPCL_R_FAMILLE = resultsSQLFPCClient[0][65]
            BPCL_CRINU4 = resultsSQLFPCClient[0][66]
            BPCL_IDENT = resultsSQLFPCClient[0][67]
            BPCL_CRIAL30 = resultsSQLFPCClient[0][68]
            BPCL_DATE_OUV_CPT = resultsSQLFPCClient[0][69]
            BPCL_CRIAL5 = resultsSQLFPCClient[0][70]
            BPCL_CRIAL23 = resultsSQLFPCClient[0][71]
            BPCL_CRIAL29 = resultsSQLFPCClient[0][72]
            BPCL_INT_LOTIMP = resultsSQLFPCClient[0][73]
            BPCL_CRIAL37 = resultsSQLFPCClient[0][74]
            BPCL_CRIAL22 = resultsSQLFPCClient[0][75]
            BPCL_CRIAL13 = resultsSQLFPCClient[0][76]
            BPCL_CRIAL35 = resultsSQLFPCClient[0][77]
            BPCL_PTRRIBIDENT = resultsSQLFPCClient[0][78]
            BPCL_R_COLL_CPT = resultsSQLFPCClient[0][79]
            BPCL_COTE = resultsSQLFPCClient[0][80]
            ## LIRE F_PERSONNE DANS SQLSserver ########################################################       
            cursorSQLServer.execute(""" SELECT         "BPP_PP_RANG_NAISS"
                                                      ,"BPP_PM_NO_SIRET"
                                                      ,"BPP_PP_NB_ENFANTS"
                                                      ,"BPP_LANGUE_CODE"
                                                      ,"BPP_TEL_FAX"
                                                      ,"BPP_EMAIL"
                                                      ,"BPP_PM_DEST2"
                                                      ,"BPP_TEL_3"
                                                      ,"BPP_PP_R_CATPROF"
                                                      ,"BPP_PP_CLE_SOCIAL"
                                                      ,"BPP_PP_SITMATR"
                                                      ,"BPP_PP_NAIS_DPT"
                                                      ,"BPP_PP_NAIS_VILLE"
                                                      ,"BPP_NOM_2"
                                                      ,"BPP_TEL_3_POSTE"
                                                      ,"BPP_PASSWORD"
                                                      ,"BPP_NOM_APPEL"
                                                      ,"BPP_TEL_TELEX"
                                                      ,"BPP_PM_CA_VALEUR"
                                                      ,"BPP_CRT_DATE"
                                                      ,"BPP_MAJ_USER"
                                                      ,"BPP_NOM_ALIAS"
                                                      ,"BPP_EMAIL_2"
                                                      ,"BPP_PP_SEXE"
                                                      ,"BPP_PM_FORMJUR"
                                                      ,"BPP_FISC_TVA_LOC"
                                                      ,"BPP_REFECHO"
                                                      ,"BPP_SITE_WEB"
                                                      ,"BPP_CRT_USER"
                                                      ,"BPP_LANGUE_LIBEL"
                                                      ,"BPP_PP_NO_SOCIAL"
                                                      ,"BPP_MAILING"
                                                      ,"BPP_IDENT"
                                                      ,"BPP_PM_NO_SIREN"
                                                      ,"BPP_REF_EXTERNE"
                                                      ,"BPP_PM_CA_TRANCHE"
                                                      ,"BPP_PP_REV_TRANCHE"
                                                      ,"BPP_PP_NAIS_PAY_CODE"
                                                      ,"BPP_PM_DEST1_TEL"
                                                      ,"BPP_INT_LOTEXP"
                                                      ,"BPP_SLIDENTIF"
                                                      ,"BPP_PM_DEST3"
                                                      ,"BPP_FISC_STAT2"
                                                      ,"BPP_COMMENTAIRE"
                                                      ,"BPP_PM_DEST1_FONCT"
                                                      ,"BPP_TEL_1"
                                                      ,"BPP_FISC_TERR"
                                                      ,"BPP_TYPE"
                                                      ,"BPP_NOM_1"
                                                      ,"BPP_PM_DEST1"
                                                      ,"BPP_PM_DEST1_EMAIL"
                                                      ,"BPP_PM_CODE_NAF"
                                                      ,"BPP_PP_SIGNALEMENT"
                                                      ,"BPP_PP_NAIS_VIL_INSEE"
                                                      ,"BPP_FISC_TVA_PTRDOM"
                                                      ,"BPP_INT_LOTIMP"
                                                      ,"BPP_DEVISE"
                                                      ,"BPP_REPERTOIRES"
                                                      ,"BPP_PM_NOTATION"
                                                      ,"BPP_PP_R_PROF_CODE"
                                                      ,"BPP_MAJ_INFO"
                                                      ,"BPP_NOM_3"
                                                      ,"BPP_PM_EFF_NOMBRE"
                                                      ,"BPP_PP_NAIS_DATE"
                                                      ,"BPP_PM_CAPITAL"
                                                      ,"BPP_FISC_STAT1"
                                                      ,"BPP_SOCIETE"
                                                      ,"BPP_MAJ_DATE"
                                                      ,"BPP_PP_REV_VALEUR"
                                                      ,"BPP_PM_NO_NACE"
                                                      ,"BPP_REGIME_SALARIE"
                                                      ,"BPP_TITRE"
                                                      ,"BPP_PM_EFF_TRANCHE"
                                                      ,"BPP_PP_NOM_JF"
                                                      ,"BPP_NO_SOCIETAIRE"
                                                      ,"BPP_FISC_TVA_NO"
                                                      ,"BPP_PP_DECES_DATE"
                                                      ,"BPP_TEL_2"
                                                      ,"BPP_PM_NO_APE"
                                                      ,"BPP_PP_MRGDVRC_DATE"
                                                      ,"BPP_ETABLISSEMENT"
                                                      ,"BPP_PM_GERANCE"
                                                  FROM F_P_PERSONNE WHERE "BPP_IDENT" = %s """ % (BPCL_PTRBPPIDENT))            
            resultsSQLFPPersonne = cursorSQLServer.fetchall()
            if resultsSQLFPPersonne:                
                BPP_PP_RANG_NAISS = resultsSQLFPPersonne[0][0]
                BPP_PM_NO_SIRET = resultsSQLFPPersonne[0][1]
                BPP_PP_NB_ENFANTS= resultsSQLFPPersonne[0][2]
                BPP_LANGUE_CODE= resultsSQLFPPersonne[0][3]
                BPP_TEL_FAX= resultsSQLFPPersonne[0][4]
                BPP_EMAIL= resultsSQLFPPersonne[0][5]
                BPP_PM_DEST2= resultsSQLFPPersonne[0][6]
                BPP_TEL_3= resultsSQLFPPersonne[0][7]
                BPP_PP_R_CATPROF= resultsSQLFPPersonne[0][8]
                BPP_PP_CLE_SOCIAL= resultsSQLFPPersonne[0][9]
                BPP_PP_SITMATR= resultsSQLFPPersonne[0][10]
                BPP_PP_NAIS_DPT= resultsSQLFPPersonne[0][11]
                BPP_PP_NAIS_VILLE= resultsSQLFPPersonne[0][12]
                BPP_NOM_2= resultsSQLFPPersonne[0][13]
                BPP_TEL_3_POSTE= resultsSQLFPPersonne[0][14]
                BPP_PASSWORD= resultsSQLFPPersonne[0][15]
                BPP_NOM_APPEL= resultsSQLFPPersonne[0][16]
                BPP_TEL_TELEX= resultsSQLFPPersonne[0][17]
                BPP_PM_CA_VALEUR= resultsSQLFPPersonne[0][18]
                BPP_CRT_DATE= resultsSQLFPPersonne[0][19]
                BPP_MAJ_USER= resultsSQLFPPersonne[0][20]
                BPP_NOM_ALIAS= resultsSQLFPPersonne[0][21]
                BPP_EMAIL_2= resultsSQLFPPersonne[0][22]
                BPP_PP_SEXE= resultsSQLFPPersonne[0][23]
                BPP_PM_FORMJUR= resultsSQLFPPersonne[0][24]
                BPP_FISC_TVA_LOC= resultsSQLFPPersonne[0][25]
                BPP_REFECHO= resultsSQLFPPersonne[0][26]
                BPP_SITE_WEB= resultsSQLFPPersonne[0][27]
                BPP_CRT_USER= resultsSQLFPPersonne[0][28]
                BPP_LANGUE_LIBEL= resultsSQLFPPersonne[0][29]
                BPP_PP_NO_SOCIAL= resultsSQLFPPersonne[0][30]
                BPP_MAILING= resultsSQLFPPersonne[0][31]
                BPP_IDENT= resultsSQLFPPersonne[0][32]
                BPP_PM_NO_SIREN= resultsSQLFPPersonne[0][33]
                BPP_REF_EXTERNE= resultsSQLFPPersonne[0][34]
                BPP_PM_CA_TRANCHE= resultsSQLFPPersonne[0][35]
                BPP_PP_REV_TRANCHE= resultsSQLFPPersonne[0][36]
                BPP_PP_NAIS_PAY_CODE= resultsSQLFPPersonne[0][37]
                BPP_PM_DEST1_TEL= resultsSQLFPPersonne[0][38]
                BPP_INT_LOTEXP= resultsSQLFPPersonne[0][39]
                BPP_SLIDENTIF= resultsSQLFPPersonne[0][40]
                BPP_PM_DEST3= resultsSQLFPPersonne[0][41]
                BPP_FISC_STAT2= resultsSQLFPPersonne[0][42]
                BPP_COMMENTAIRE= resultsSQLFPPersonne[0][43]
                BPP_PM_DEST1_FONCT= resultsSQLFPPersonne[0][44]
                BPP_TEL_1= resultsSQLFPPersonne[0][45]
                BPP_FISC_TERR= resultsSQLFPPersonne[0][46]
                BPP_TYPE= resultsSQLFPPersonne[0][47]
                BPP_NOM_1= resultsSQLFPPersonne[0][48]
                BPP_PM_DEST1= resultsSQLFPPersonne[0][49]
                BPP_PM_DEST1_EMAIL= resultsSQLFPPersonne[0][50]
                BPP_PM_CODE_NAF= resultsSQLFPPersonne[0][51]
                BPP_PP_SIGNALEMENT= resultsSQLFPPersonne[0][52]
                BPP_PP_NAIS_VIL_INSEE= resultsSQLFPPersonne[0][53]
                BPP_FISC_TVA_PTRDOM= resultsSQLFPPersonne[0][54]
                BPP_INT_LOTIMP= resultsSQLFPPersonne[0][55]
                BPP_DEVISE= resultsSQLFPPersonne[0][56]
                BPP_REPERTOIRES= resultsSQLFPPersonne[0][57]
                BPP_PM_NOTATION= resultsSQLFPPersonne[0][58]
                BPP_PP_R_PROF_CODE= resultsSQLFPPersonne[0][59]
                BPP_MAJ_INFO= resultsSQLFPPersonne[0][60]
                BPP_NOM_3= resultsSQLFPPersonne[0][61]
                BPP_PM_EFF_NOMBRE= resultsSQLFPPersonne[0][62]
                BPP_PP_NAIS_DATE= resultsSQLFPPersonne[0][63]
                BPP_PM_CAPITAL= resultsSQLFPPersonne[0][64]
                BPP_FISC_STAT1= resultsSQLFPPersonne[0][65]
                BPP_SOCIETE= resultsSQLFPPersonne[0][66]
                BPP_MAJ_DATE= resultsSQLFPPersonne[0][67]
                BPP_PP_REV_VALEUR= resultsSQLFPPersonne[0][68]
                BPP_PM_NO_NACE= resultsSQLFPPersonne[0][69]
                BPP_REGIME_SALARIE= resultsSQLFPPersonne[0][70]
                BPP_TITRE= resultsSQLFPPersonne[0][71]
                BPP_PM_EFF_TRANCHE= resultsSQLFPPersonne[0][72]
                BPP_PP_NOM_JF= resultsSQLFPPersonne[0][73]
                BPP_NO_SOCIETAIRE= resultsSQLFPPersonne[0][74]
                BPP_FISC_TVA_NO= resultsSQLFPPersonne[0][75]
                BPP_PP_DECES_DATE= resultsSQLFPPersonne[0][76]
                BPP_TEL_2= resultsSQLFPPersonne[0][77]
                BPP_PM_NO_APE= resultsSQLFPPersonne[0][78]
                BPP_PP_MRGDVRC_DATE= resultsSQLFPPersonne[0][79]
                BPP_ETABLISSEMENT= resultsSQLFPPersonne[0][80]
                BPP_PM_GERANCE= resultsSQLFPPersonne[0][81]
                
                ######## LIRE F_P_ADRESSE DANS SQLServer ######################
                cursorSQLServer.execute(""" SELECT  "BPA_INT_LOTEXP"
                                                    ,"BPA_CRT_DATE"
                                                    ,"BPA_AD_LIG2"
                                                    ,"BPA_PTRBPPIDENT"
                                                    ,"BPA_AD_PAYS_LIBEL"
                                                    ,"BPA_IDENT"
                                                    ,"BPA_AD_LIG3"
                                                    ,"BPA_AD_PAYS_CODE"
                                                    ,"BPA_DATE_FIN_VALID"
                                                    ,"BPA_DATE_DEB_VALID"
                                                    ,"BPA_MAJ_USER"
                                                    ,"BPA_ADR_ERR"
                                                    ,"BPA_AD_CODPOST"
                                                    ,"BPA_INT_LOTIMP"
                                                    ,"BPA_AD_LOCALITE"
                                                    ,"BPA_ADR_TYPE"
                                                    ,"BPA_ADR_NUM"
                                                    ,"BPA_REFECHO"
                                                    ,"BPA_MAJ_DATE"
                                                    ,"BPA_AD_LIG1"
                                                    ,"BPA_AD_VILLE"
                                                    ,"BPA_AD_CEDEX"
                                                    ,"BPA_CRT_USER"
                                                    ,"BPA_BPPSLIDENTIF"
                                                    ,"BPA_ADR_PRINCI"
                                          FROM F_P_ADRESSE WHERE "BPA_PTRBPPIDENT" = %s""" % (BPP_IDENT))
                resultsSQLFPAdresse = cursorSQLServer.fetchall()
                BPA_AD_LIG1 = ''
                BPA_AD_VILLE = ''
                BPA_AD_CODPOST = ''
                if resultsSQLFPAdresse:
                    BPA_INT_LOTEXP = resultsSQLFPAdresse[0][0]
                    BPA_CRT_DATE = resultsSQLFPAdresse[0][1]
                    BPA_AD_LIG2 = resultsSQLFPAdresse[0][2]
                    BPA_PTRBPPIDENT = resultsSQLFPAdresse[0][3]
                    BPA_AD_PAYS_LIBEL = resultsSQLFPAdresse[0][4]
                    BPA_IDENT = resultsSQLFPAdresse[0][5]
                    BPA_AD_LIG3 = resultsSQLFPAdresse[0][6]
                    BPA_AD_PAYS_CODE = resultsSQLFPAdresse[0][7]
                    BPA_DATE_FIN_VALID = resultsSQLFPAdresse[0][8]
                    BPA_DATE_DEB_VALID = resultsSQLFPAdresse[0][9]
                    BPA_MAJ_USER = resultsSQLFPAdresse[0][10]
                    BPA_ADR_ERR = resultsSQLFPAdresse[0][11]
                    BPA_AD_CODPOST = resultsSQLFPAdresse[0][12]
                    BPA_INT_LOTIMP = resultsSQLFPAdresse[0][13]
                    BPA_AD_LOCALITE = resultsSQLFPAdresse[0][14]
                    BPA_ADR_TYPE = resultsSQLFPAdresse[0][15]
                    BPA_ADR_NUM = resultsSQLFPAdresse[0][16]
                    BPA_REFECHO = resultsSQLFPAdresse[0][17]
                    BPA_MAJ_DATE = resultsSQLFPAdresse[0][18]
                    BPA_AD_LIG1 = resultsSQLFPAdresse[0][19]
                    BPA_AD_VILLE = resultsSQLFPAdresse[0][20]
                    BPA_AD_CEDEX = resultsSQLFPAdresse[0][21]
                    BPA_CRT_USER = resultsSQLFPAdresse[0][22]
                    BPA_BPPSLIDENTIF = resultsSQLFPAdresse[0][23]
                    BPA_ADR_PRINCI = resultsSQLFPAdresse[0][24]
                    
                    cursorPOSTGRESOdoo.execute(""" INSERT INTO f_p_adresse (id,
                                                                            create_uid,                                                                            
                                                                            "BPA_AD_CEDEX",
                                                                            "BPA_AD_LOCALITE",                                                                            
                                                                            "BPA_AD_CODPOST",
                                                                            write_uid,
                                                                            "BPA_AD_VILLE",
                                                                            "BPA_PTRBPPIDENT",
                                                                            "BPA_ADR_TYPE",
                                                                            write_date,
                                                                            "BPA_AD_PAYS_CODE",
                                                                            "BPA_AD_PAYS_LIBEL",
                                                                            create_date,
                                                                            "BPA_AD_LIG1")
                                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) """,
                                                (BPA_IDENT,1,BPA_AD_CEDEX,BPA_AD_LOCALITE,BPA_AD_CODPOST,1,
                                                 BPA_AD_VILLE,BPA_PTRBPPIDENT,BPA_ADR_TYPE,datetime.datetime.now(),BPA_AD_PAYS_CODE,
                                                 BPA_AD_PAYS_LIBEL,datetime.datetime.now(),BPA_AD_LIG1))                    
                                    
                ########### END F_P_ADRESSE ##############################################################################################
                
                ####### LIRE DANS F_P_CORD_BNQ #########################################################################################
                cursorSQLServer.execute(""" SELECT  "BPB_SLCRDBNQ"
                                                    ,"BPB_IBAN"
                                                    ,"BPB_MAJ_USER"
                                                    ,"BPB_RIBF_COMPTE"
                                                    ,"BPB_CRT_USER"
                                                    ,"BPB_SLEMETTEUR"
                                                    ,"BPB_PTRBPPIDENT"
                                                    ,"BPB_DATE_FIN_VALID"
                                                    ,"BPB_INT_LOTEXP"
                                                    ,"BPB_RIBF_LIBELLE"
                                                    ,"BPB_SWIFT"
                                                    ,"BPB_CRT_DATE"
                                                    ,"BPB_CRD_NUM"
                                                    ,"BPB_BPPSLIDENTIF"
                                                    ,"BPB_RIBF_GUICHET"
                                                    ,"BPB_DATE_DEB_VALID"
                                                    ,"BPB_ISO_PAYS"
                                                    ,"BPB_MAJ_DATE"
                                                    ,"BPB_RIBF_CLE"
                                                    ,"BPB_INT_LOTIMP"
                                                    ,"BPB_RIBF_TITULAIRE"
                                                    ,"BPB_REFECHO"
                                                    ,"BPB_IDENT"
                                                    ,"BPB_RIBF_BANQUE"
                                                    FROM F_P_CORD_BNQ  WHERE "BPB_PTRBPPIDENT"=%s """ % (BPP_IDENT))
                resultsSQLFPCordBanq = cursorSQLServer.fetchall()
                if resultsSQLFPCordBanq:
                    BPB_SLCRDBNQ = resultsSQLFPCordBanq[0][0]
                    BPB_IBAN = resultsSQLFPCordBanq[0][1]
                    BPB_MAJ_USER = resultsSQLFPCordBanq[0][2]
                    BPB_RIBF_COMPTE = resultsSQLFPCordBanq[0][3]
                    BPB_CRT_USER = resultsSQLFPCordBanq[0][4]
                    BPB_SLEMETTEUR = resultsSQLFPCordBanq[0][5]
                    BPB_PTRBPPIDENT = resultsSQLFPCordBanq[0][6]
                    BPB_DATE_FIN_VALID = resultsSQLFPCordBanq[0][7]
                    BPB_INT_LOTEXP = resultsSQLFPCordBanq[0][8]
                    BPB_RIBF_LIBELLE = resultsSQLFPCordBanq[0][9]
                    BPB_SWIFT = resultsSQLFPCordBanq[0][10]
                    BPB_CRT_DATE = resultsSQLFPCordBanq[0][11]
                    BPB_CRD_NUM = resultsSQLFPCordBanq[0][12]
                    BPB_BPPSLIDENTIF = resultsSQLFPCordBanq[0][13]
                    BPB_RIBF_GUICHET = resultsSQLFPCordBanq[0][14]
                    BPB_DATE_DEB_VALID = resultsSQLFPCordBanq[0][15]
                    BPB_ISO_PAYS = resultsSQLFPCordBanq[0][16]
                    BPB_MAJ_DATE = resultsSQLFPCordBanq[0][17]
                    BPB_RIBF_CLE = resultsSQLFPCordBanq[0][18]
                    BPB_INT_LOTIMP = resultsSQLFPCordBanq[0][19]
                    BPB_RIBF_TITULAIRE = resultsSQLFPCordBanq[0][20]
                    BPB_REFECHO = resultsSQLFPCordBanq[0][21]
                    BPB_IDENT = resultsSQLFPCordBanq[0][22]
                    BPB_RIBF_BANQUE = resultsSQLFPCordBanq[0][23]                    
                    cursorPOSTGRESOdoo.execute(""" INSERT INTO f_p_cord_bnq (id,
                                                                        create_uid,
                                                                        "BPB_ISO_PAYS",                                                                       
                                                                        "BPB_SWIFT",
                                                                        "BPB_RIBF_GUICHET",
                                                                        write_uid,
                                                                        "BPB_RIBF_LIBELLE",
                                                                        "BPB_PTRBPPIDENT",
                                                                        write_date,
                                                                        "BPB_IBAN",
                                                                        create_date,
                                                                        "BPB_RIBF_TITULAIRE",
                                                                        "BPB_RIBF_COMPTE",
                                                                        "BPB_RIBF_BANQUE")
                                                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
                                               """, (BPB_IDENT,1,BPB_ISO_PAYS,BPB_SWIFT,BPB_RIBF_GUICHET,1,BPB_RIBF_LIBELLE,BPB_PTRBPPIDENT,
                                                     datetime.datetime.now(),BPB_IBAN,datetime.datetime.now(),BPB_RIBF_TITULAIRE,
                                                     BPB_RIBF_COMPTE,BPB_RIBF_BANQUE))              
                ####### END F_P_CORD_BNQ ###############################################################################################
                
                
                ### INSERT F_P_PERSONNE DANS RES_PARTNER DE Odoo ######
                country = 0
                if BPA_AD_PAYS_LIBEL == 'Madagascar':
                    country = 142
                    
                vals = {'name':BPP_NOM_APPEL,'mobile':BPP_TEL_1,'email':BPP_EMAIL,'fax':BPP_TEL_FAX,'street':BPA_AD_LIG1,'city':BPA_AD_VILLE,
                        'zip':BPA_AD_CODPOST,'country_id':country,'id_f_p_c_client':BPCL_IDENT,'partner_type':'client'}
                id_partner = self.env['res.partner'].create(vals)  
                                 
                partner_id = id_partner.id
                 
                PHYSIQUE = False
                if BPP_TITRE in ('MME','MR','MLLE','M'):
                    PHYSIQUE = True    
                     
                MORALE = False                
                if BPP_TITRE not in ('MME','MR','MLLE','M'):
                    MORALE = True
     
                EST_CLIENT = False
                if BPCL_PTRBPPIDENT:
                    EST_CLIENT = True
                     
                name= BPP_NOM_APPEL                
                 
                #### ECRIRE F_p_personne dans Odoo
                cursorPOSTGRESOdoo.execute(""" INSERT INTO f_p_personne (id,
                                                                        "BPP_NOM_3",
                                                                        "BPP_NOM_2",
                                                                        create_date,
                                                                        "BPP_PM_EFF_NOMBRE",
                                                                        "BPP_PM_NO_SIREN",
                                                                        "BPP_MAJ_INFO",
                                                                        "BPP_PM_DEST1_EMAIL",
                                                                        "BPP_TEL_1",
                                                                        "BPP_PM_NO_APE",
                                                                        "BPP_TEL_3",
                                                                        "BPP_LANGUE_LIBEL",
                                                                        "BPP_PP_NAIS_VILLE",
                                                                        partner_id,
                                                                        "BPP_PM_DEST1_TEL",
                                                                        create_uid,
                                                                        "BPP_PM_DEST1_FONCT",
                                                                        "BPP_TEL_3_POSTE",
                                                                        "BPP_CRT_DATE",
                                                                        "BPP_PM_NO_SIRET",
                                                                         "BPP_EMAIL",
                                                                         "BPP_PM_CAPITAL",
                                                                        "BPP_PM_FORMJUR",
                                                                        "BPP_FISC_TERR",
                                                                        "BPP_PP_NAIS_PAY_CODE",
                                                                        "BPP_PM_NOTATION",
                                                                        "BPP_NOM_APPEL",
                                                                        "BPP_TEL_TELEX",
                                                                        "BPP_EMAIL_2",
                                                                        "BPP_TEL_FAX",
                                                                        "BPP_PP_DECES_DATE",
                                                                        "BPP_PP_R_PROF_CODE",
                                                                        "BPP_NOM_ALIAS" ,
                                                                        "BPP_COMMENTAIRE",
                                                                        "BPP_PP_SIGNALEMENT",
                                                                        "BPP_PP_SEXE",
                                                                        "BPP_PP_NAIS_DPT",
                                                                        "BPP_PP_REV_TRANCHE",
                                                                        "BPP_PP_NO_SOCIAL",
                                                                        "BPP_LANGUE_CODE",
                                                                        "MORALE",
                                                                        write_date,
                                                                        "BPP_PP_REV_VALEUR",
                                                                        "BPP_PM_CODE_NAF",
                                                                        write_uid,
                                                                        "BPP_PP_R_CATPROF",
                                                                        "BPP_PP_SITMATR",
                                                                        "BPP_PM_NO_NACE",
                                                                        "BPP_TITRE",
                                                                        name,
                                                                        "BPP_PP_NAIS_DATE",
                                                                        "BPP_PM_EFF_TRANCHE",
                                                                        "BPP_REF_EXTERNE",
                                                                        "PHYSIQUE",
                                                                        "BPP_TEL_2",
                                                                        "BPP_SITE_WEB",
                                                                        "BPP_PM_CA_TRANCHE",
                                                                        "BPP_PM_DEST3",
                                                                        "BPP_PM_DEST2",
                                                                        "EST_CLIENT",
                                                                        "BPP_PP_NAIS_VIL_INSEE",
                                                                        "BPP_PP_NB_ENFANTS",
                                                                        "BPP_PP_RANG_NAISS",
                                                                        "BPP_PM_CA_VALEUR"                                                                     
                                                                        )
                                                                        
                                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                                    %s,%s,%s,%s) """,
                                                    (BPP_IDENT,BPP_NOM_3,BPP_NOM_2,datetime.datetime.now(),BPP_PM_EFF_NOMBRE,
                                                    BPP_PM_NO_SIREN,BPP_MAJ_INFO,BPP_PM_DEST1_EMAIL,BPP_TEL_1,BPP_PM_NO_APE,
                                                    BPP_TEL_3,BPP_LANGUE_LIBEL,BPP_PP_NAIS_VILLE,partner_id,BPP_PM_DEST1_TEL,1,BPP_PM_DEST1_FONCT,
                                                    BPP_TEL_3_POSTE,BPP_CRT_DATE,BPP_PM_NO_SIRET,BPP_EMAIL,BPP_PM_CAPITAL,BPP_PM_FORMJUR,BPP_FISC_TERR,BPP_PP_NAIS_PAY_CODE,
                                                    BPP_PM_NOTATION,BPP_NOM_APPEL,BPP_TEL_TELEX,BPP_EMAIL_2,BPP_TEL_FAX,BPP_PP_DECES_DATE,BPP_PP_R_PROF_CODE,BPP_NOM_ALIAS,
                                                    BPP_COMMENTAIRE,BPP_PP_SIGNALEMENT,BPP_PP_SEXE,BPP_PP_NAIS_DPT,BPP_PP_REV_TRANCHE,BPP_PP_NO_SOCIAL,BPP_LANGUE_CODE,
                                                    MORALE,datetime.datetime.now(),BPP_PP_REV_VALEUR,BPP_PM_CODE_NAF,1,BPP_PP_R_CATPROF,BPP_PP_SITMATR,BPP_PM_NO_NACE,BPP_TITRE,
                                                    name,BPP_PP_NAIS_DATE,BPP_PM_EFF_TRANCHE,BPP_REF_EXTERNE,PHYSIQUE,BPP_TEL_2,BPP_SITE_WEB,BPP_PM_CA_TRANCHE,BPP_PM_DEST3,
                                                    BPP_PM_DEST2,EST_CLIENT,BPP_PP_NAIS_VIL_INSEE,BPP_PP_NB_ENFANTS,BPP_PP_RANG_NAISS,BPP_PM_CA_VALEUR)
                                                    )
                ########## FIN F_p_personne ############################################################################################################
                
                ##### ECRIRE DANS F_P_C_CLIENT ##########################################################################################################
                cursorPOSTGRESOdoo.execute(""" INSERT INTO f_p_c_client (id,
                                                                        "BPCL_COTE",
                                                                        "BPCL_R_SS_FAM",
                                                                        "BPCL_R_REGROUP3",
                                                                        create_date,
                                                                        write_uid,
                                                                        "BPCL_G_TYPE_PREL",
                                                                        create_uid,
                                                                        "BPCL_PTRBPPIDENT",
                                                                        "BPCL_R_REGROUP2",                                                                        
                                                                        "BPCL_R_FAMILLE",
                                                                        "BPCL_R_SECTEUR",
                                                                        "BPCL_DATE_OUV_CPT",
                                                                        write_date,
                                                                        "BPCL_DATE_CLO_CPT",
                                                                        "BPCL_R_REGROUP1",
                                                                        "BPCL_CODE_AUXIL",
                                                                        "BPCL_G_MODEREGL",
                                                                        name)
                                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) """ ,
                                            (BPCL_IDENT,BPCL_COTE,BPCL_R_SS_FAM,BPCL_R_REGROUP3,
                                             datetime.datetime.now(),1,BPCL_G_TYPE_PREL,1,BPCL_PTRBPPIDENT,BPCL_R_REGROUP2,
                                             BPCL_R_FAMILLE,BPCL_R_SECTEUR,BPCL_DATE_OUV_CPT,
                                             datetime.datetime.now(),BPCL_DATE_CLO_CPT,BPCL_R_REGROUP1,BPCL_CODE_AUXIL,
                                             BPCL_G_MODEREGL, name
                                             ))
                #########################################################################################################################################
              
    def insert_f_intermediaire(self,cursorSQLServer,cursorPOSTGRESOdoo,id_polices,POL_PTRINID):
        ### Recuperation f_intermediaire
        cursorSQLServer.execute(""" SELECT     "IN_NUMAUTO"
                                              ,"IN_SERVICES"
                                              ,"IN_RIB_LIBELLE"
                                              ,"IN_RIB_NUMCPTE"
                                              ,"IN_CA"
                                              ,"IN_NOM_SUITE"
                                              ,"IN_REFCHO"
                                              ,"IN_FORMEJURIDIQUE"
                                              ,"IN_ADRESSE"
                                              ,"IN_DATDEBCOMPTE"
                                              ,"IN_JOUR_RGT"
                                              ,"IN_WEBSITE"
                                              ,"IN_CRIAL01"
                                              ,"IN_DEROG_RECOUV"
                                              ,"IN_TELEPHONE2"
                                              ,"IN_COMMISSION01"
                                              ,"IN_TELECOPIEUR"
                                              ,"IN_SLREGLECOM03"
                                              ,"IN_GARFI"
                                              ,"IN_RIB_CODBQ"
                                              ,"IN_ADRES2"
                                              ,"IN_CODE"
                                              ,"IN_EN_GERANCE"
                                              ,"IN_CODE_SOCIETE"
                                              ,"IN_ENCCONF_NON"
                                              ,"IN_RCPRO"
                                              ,"IN_CRINU01"
                                              ,"IN_PTRCIE1"
                                              ,"IN_ENCAISS_CONF"
                                              ,"IN_MODEREG"
                                              ,"IN_CODE_ETAT"
                                              ,"IN_STOP_MAJO"
                                              ,"IN_GARFIDATFIN"
                                              ,"IN_NOCLIENT"
                                              ,"IN_STOP_REVERSEMENT"
                                              ,"IN_SLREGLECOM02"
                                              ,"IN_TRANCHEFF"
                                              ,"IN_TELEPHONE"
                                              ,"IN_CRIAL03"
                                              ,"IN_TITRE"
                                              ,"IN_UTILMODIF"
                                              ,"IN_PTRDEVCODE"
                                              ,"IN_LANGUE"
                                              ,"IN_MOTIF_FIN"
                                              ,"IN_AUTORISATION"
                                              ,"IN_DATFINCOMPTE"
                                              ,"IN_CRIAL13"
                                              ,"IN_SEQUENTIEL"
                                              ,"IN_SL_CODE"
                                              ,"IN_RIB_TITULAIRE"
                                              ,"IN_CRIAL05"
                                              ,"IN_CRINU10"
                                              ,"IN_RESPPROD"
                                              ,"IN_REPARTITION"
                                              ,"IN_SIREN"
                                              ,"IN_CRINU09"
                                              ,"IN_CRIAL04"
                                              ,"IN_CRIAL15"
                                              ,"IN_SLREGLECOM01"
                                              ,"IN_CAPITALSOCIAL"
                                              ,"IN_GARFINUMPOL"
                                              ,"IN_COTE"
                                              ,"IN_SIRET"
                                              ,"IN_REGROUP1"
                                              ,"IN_REGISTRE_COM"
                                              ,"IN_TYPE"
                                              ,"IN_CRIAL19"
                                              ,"IN_CRIAL02"
                                              ,"IN_CRINU08"
                                              ,"IN_TRANCHECA"
                                              ,"IN_PAYS"
                                              ,"IN_GESTION_DIRECTE"
                                              ,"IN_CRIAL10"
                                              ,"IN_CRIAL06"
                                              ,"IN_CRINU05"
                                              ,"IN_RCPRODATFIN"
                                              ,"IN_UTILCREATEUR"
                                              ,"IN_VILLE"
                                              ,"IN_CRINU02"
                                              ,"IN_CRIAL08"
                                              ,"IN_ZONECOM"
                                              ,"IN_CODE_PAYS"
                                              ,"IN_CRIAL20"
                                              ,"IN_CRINU03"
                                              ,"IN_CP"
                                              ,"IN_CRIAL16"
                                              ,"IN_TELEPHONE3"
                                              ,"IN_CRIAL14"
                                              ,"IN_PTRCIEGF"
                                              ,"IN_PTRCIE3"
                                              ,"IN_EFFECTIF"
                                              ,"IN_LOT_EXP"
                                              ,"IN_EMAIL"
                                              ,"IN_NOMCOMPLET"
                                              ,"IN_RCPRONUMPOL"
                                              ,"IN_RGL_COMM"
                                              ,"IN_RESP"
                                              ,"IN_PTRCIERCP"
                                              ,"IN_ADRES3"
                                              ,"IN_CRINU07"
                                              ,"IN_PTRCIE2"
                                              ,"IN_DATEMODIF"
                                              ,"IN_CODE_LANGUE"
                                              ,"IN_LOT_IMP"
                                              ,"IN_TELEX"
                                              ,"IN_CODE_ETABL"
                                              ,"IN_RESP_PRENOM"
                                              ,"IN_COMMENTAIRES"
                                              ,"IN_CRIAL11"
                                              ,"IN_GARFICIE"
                                              ,"IN_CRIAL09"
                                              ,"IN_RESPCOMPTA"
                                              ,"IN_RCPRODATDEB"
                                              ,"IN_RIB_CLE"
                                              ,"IN_RIB_NOMBNQ"
                                              ,"IN_RIB_CODGUI"
                                              ,"IN_SLSOLDE"
                                              ,"IN_IDENT"
                                              ,"IN_CRIAL07"
                                              ,"IN_CRINU04"
                                              ,"IN_RESPSINIS"
                                              ,"IN_DATECREATION"
                                              ,"IN_CRIAL18"
                                              ,"IN_SL_SUPERIEUR"
                                              ,"IN_CPTAUX_DEROG"
                                              ,"IN_STOP_PAIEMENT"
                                              ,"IN_GARFIDATDEB"
                                              ,"IN_NOMAPPEL"
                                              ,"IN_CODE_INSEE"
                                              ,"IN_NOMANIMATEUR"
                                              ,"IN_RIB_IBAN"
                                              ,"IN_LOCALITE"
                                              ,"IN_RCPROCIE"
                                              ,"IN_CRINU06"
                                              ,"IN_CRIAL12"
                                              ,"IN_CRIAL17"
                                          FROM F_INTERMEDIAIRE WHERE "IN_IDENT" = %s""" % (POL_PTRINID))
        resultsSQLFIntermediaire = cursorSQLServer.fetchall()       
        if resultsSQLFIntermediaire:
            IN_NUMAUTO = resultsSQLFIntermediaire[0][0]
            IN_SERVICES = resultsSQLFIntermediaire[0][1]
            IN_RIB_LIBELLE = resultsSQLFIntermediaire[0][2]
            IN_RIB_NUMCPTE = resultsSQLFIntermediaire[0][3]
            IN_CA = resultsSQLFIntermediaire[0][4]
            IN_NOM_SUITE = resultsSQLFIntermediaire[0][5]
            IN_REFCHO = resultsSQLFIntermediaire[0][6]
            IN_FORMEJURIDIQUE = resultsSQLFIntermediaire[0][7]
            IN_ADRESSE = resultsSQLFIntermediaire[0][8]
            IN_DATDEBCOMPTE = resultsSQLFIntermediaire[0][9]
            IN_JOUR_RGT = resultsSQLFIntermediaire[0][10]
            IN_WEBSITE = resultsSQLFIntermediaire[0][11]
            IN_CRIAL01 = resultsSQLFIntermediaire[0][12]
            IN_DEROG_RECOUV = resultsSQLFIntermediaire[0][13]
            IN_TELEPHONE2 = resultsSQLFIntermediaire[0][14]
            IN_COMMISSION01 = resultsSQLFIntermediaire[0][15]
            IN_TELECOPIEUR = resultsSQLFIntermediaire[0][16]
            IN_SLREGLECOM03 = resultsSQLFIntermediaire[0][17]
            IN_GARFI = resultsSQLFIntermediaire[0][18]
            IN_RIB_CODBQ = resultsSQLFIntermediaire[0][19]
            IN_ADRES2 = resultsSQLFIntermediaire[0][20]
            IN_CODE = resultsSQLFIntermediaire[0][21]
            IN_EN_GERANCE = resultsSQLFIntermediaire[0][22]
            IN_CODE_SOCIETE = resultsSQLFIntermediaire[0][23]
            IN_ENCCONF_NON = resultsSQLFIntermediaire[0][24]
            IN_RCPRO = resultsSQLFIntermediaire[0][25]
            IN_CRINU01 = resultsSQLFIntermediaire[0][26]
            IN_PTRCIE1 = resultsSQLFIntermediaire[0][27]
            IN_ENCAISS_CONF = resultsSQLFIntermediaire[0][28]
            IN_MODEREG = resultsSQLFIntermediaire[0][29]
            IN_CODE_ETAT = resultsSQLFIntermediaire[0][30]
            IN_STOP_MAJO = resultsSQLFIntermediaire[0][31]
            IN_GARFIDATFIN = resultsSQLFIntermediaire[0][32]
            IN_NOCLIENT = resultsSQLFIntermediaire[0][33]
            IN_STOP_REVERSEMENT = resultsSQLFIntermediaire[0][34]
            IN_SLREGLECOM02 = resultsSQLFIntermediaire[0][35]
            IN_TRANCHEFF = resultsSQLFIntermediaire[0][36]
            IN_TELEPHONE = resultsSQLFIntermediaire[0][37]
            IN_CRIAL03 = resultsSQLFIntermediaire[0][38]
            IN_TITRE = resultsSQLFIntermediaire[0][39]
            IN_UTILMODIF = resultsSQLFIntermediaire[0][40]
            IN_PTRDEVCODE = resultsSQLFIntermediaire[0][41]
            IN_LANGUE = resultsSQLFIntermediaire[0][42]
            IN_MOTIF_FIN = resultsSQLFIntermediaire[0][43]
            IN_AUTORISATION = resultsSQLFIntermediaire[0][44]
            IN_DATFINCOMPTE = resultsSQLFIntermediaire[0][45]
            IN_CRIAL13 = resultsSQLFIntermediaire[0][46]
            IN_SEQUENTIEL = resultsSQLFIntermediaire[0][47]
            IN_SL_CODE = resultsSQLFIntermediaire[0][48]
            IN_RIB_TITULAIRE = resultsSQLFIntermediaire[0][49]
            IN_CRIAL05 = resultsSQLFIntermediaire[0][50]
            IN_CRINU10 = resultsSQLFIntermediaire[0][51]
            IN_RESPPROD = resultsSQLFIntermediaire[0][52]
            IN_REPARTITION = resultsSQLFIntermediaire[0][53]
            IN_SIREN = resultsSQLFIntermediaire[0][54]
            IN_CRINU09 = resultsSQLFIntermediaire[0][55]
            IN_CRIAL04 = resultsSQLFIntermediaire[0][56]
            IN_CRIAL15 = resultsSQLFIntermediaire[0][57]
            IN_SLREGLECOM01 = resultsSQLFIntermediaire[0][58]
            IN_CAPITALSOCIAL = resultsSQLFIntermediaire[0][59]
            IN_GARFINUMPOL = resultsSQLFIntermediaire[0][60]
            IN_COTE = resultsSQLFIntermediaire[0][61]
            IN_SIRET = resultsSQLFIntermediaire[0][62]
            IN_REGROUP1 = resultsSQLFIntermediaire[0][63]
            IN_REGISTRE_COM = resultsSQLFIntermediaire[0][64]
            IN_TYPE = resultsSQLFIntermediaire[0][65]
            IN_CRIAL19 = resultsSQLFIntermediaire[0][66]
            IN_CRIAL02 = resultsSQLFIntermediaire[0][67]
            IN_CRINU08 = resultsSQLFIntermediaire[0][68]
            IN_TRANCHECA = resultsSQLFIntermediaire[0][69]
            IN_PAYS = resultsSQLFIntermediaire[0][70]
            IN_GESTION_DIRECTE = resultsSQLFIntermediaire[0][71]
            IN_CRIAL10 = resultsSQLFIntermediaire[0][72]
            IN_CRIAL06 = resultsSQLFIntermediaire[0][73]
            IN_CRINU05 = resultsSQLFIntermediaire[0][74]
            IN_RCPRODATFIN = resultsSQLFIntermediaire[0][75]
            IN_UTILCREATEUR = resultsSQLFIntermediaire[0][76]
            IN_VILLE = resultsSQLFIntermediaire[0][77]
            IN_CRINU02 = resultsSQLFIntermediaire[0][78]
            IN_CRIAL08 = resultsSQLFIntermediaire[0][79]
            IN_ZONECOM = resultsSQLFIntermediaire[0][80]
            IN_CODE_PAYS = resultsSQLFIntermediaire[0][81]
            IN_CRIAL20 = resultsSQLFIntermediaire[0][82]
            IN_CRINU03 = resultsSQLFIntermediaire[0][83]
            IN_CP = resultsSQLFIntermediaire[0][84]
            IN_CRIAL16 = resultsSQLFIntermediaire[0][85]
            IN_TELEPHONE3 = resultsSQLFIntermediaire[0][86]
            IN_CRIAL14 = resultsSQLFIntermediaire[0][87]
            IN_PTRCIEGF = resultsSQLFIntermediaire[0][88]
            IN_PTRCIE3 = resultsSQLFIntermediaire[0][89]
            IN_EFFECTIF = resultsSQLFIntermediaire[0][90]
            IN_LOT_EXP = resultsSQLFIntermediaire[0][91]
            IN_EMAIL = resultsSQLFIntermediaire[0][92]
            IN_NOMCOMPLET = resultsSQLFIntermediaire[0][93]
            IN_RCPRONUMPOL = resultsSQLFIntermediaire[0][94]
            IN_RGL_COMM = resultsSQLFIntermediaire[0][95]
            IN_RESP = resultsSQLFIntermediaire[0][96]
            IN_PTRCIERCP = resultsSQLFIntermediaire[0][97]
            IN_ADRES3 = resultsSQLFIntermediaire[0][98]
            IN_CRINU07 = resultsSQLFIntermediaire[0][99]
            IN_PTRCIE2 = resultsSQLFIntermediaire[0][100]
            IN_DATEMODIF = resultsSQLFIntermediaire[0][101]
            IN_CODE_LANGUE = resultsSQLFIntermediaire[0][102]
            IN_LOT_IMP = resultsSQLFIntermediaire[0][103]
            IN_TELEX = resultsSQLFIntermediaire[0][104]
            IN_CODE_ETABL = resultsSQLFIntermediaire[0][105]
            IN_RESP_PRENOM = resultsSQLFIntermediaire[0][106]
            IN_COMMENTAIRES = resultsSQLFIntermediaire[0][107]
            IN_CRIAL11 = resultsSQLFIntermediaire[0][108]
            IN_GARFICIE = resultsSQLFIntermediaire[0][109]
            IN_CRIAL09 = resultsSQLFIntermediaire[0][110]
            IN_RESPCOMPTA = resultsSQLFIntermediaire[0][111]
            IN_RCPRODATDEB = resultsSQLFIntermediaire[0][112]
            IN_RIB_CLE = resultsSQLFIntermediaire[0][113]
            IN_RIB_NOMBNQ = resultsSQLFIntermediaire[0][114]
            IN_RIB_CODGUI = resultsSQLFIntermediaire[0][115]
            IN_SLSOLDE = resultsSQLFIntermediaire[0][116]
            IN_IDENT = resultsSQLFIntermediaire[0][117]
            IN_CRIAL07 = resultsSQLFIntermediaire[0][118]
            IN_CRINU04 = resultsSQLFIntermediaire[0][119]
            IN_RESPSINIS = resultsSQLFIntermediaire[0][120]
            IN_DATECREATION = resultsSQLFIntermediaire[0][121]
            IN_CRIAL18 = resultsSQLFIntermediaire[0][122]
            IN_SL_SUPERIEUR = resultsSQLFIntermediaire[0][123]
            IN_CPTAUX_DEROG = resultsSQLFIntermediaire[0][124]
            IN_STOP_PAIEMENT = resultsSQLFIntermediaire[0][125]
            IN_GARFIDATDEB = resultsSQLFIntermediaire[0][126]
            IN_NOMAPPEL = resultsSQLFIntermediaire[0][127]
            IN_CODE_INSEE = resultsSQLFIntermediaire[0][128]
            IN_NOMANIMATEUR = resultsSQLFIntermediaire[0][129]
            IN_RIB_IBAN = resultsSQLFIntermediaire[0][130]
            IN_LOCALITE = resultsSQLFIntermediaire[0][131]
            IN_RCPROCIE = resultsSQLFIntermediaire[0][132]
            IN_CRINU06 = resultsSQLFIntermediaire[0][133]
            IN_CRIAL12 = resultsSQLFIntermediaire[0][134]
            IN_CRIAL17 = resultsSQLFIntermediaire[0][135]
            name = IN_NOMAPPEL
            ### ECRIRE f_intermediaire dans Odoo
            cursorPOSTGRESOdoo.execute(""" INSERT INTO f_intermediaire (id,
                                                                        create_uid,
                                                                        create_date,
                                                                        name,
                                                                        "IN_VILLE",
                                                                        "IN_SL_CODE",
                                                                        write_uid,
                                                                        write_date,                                                                        
                                                                        "IN_TYPE") 
                                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) """,
                                            (IN_IDENT,1,datetime.datetime.now(),name,IN_VILLE,IN_SL_CODE,1,datetime.datetime.now(),IN_TYPE
                                             ))
        
    def insert_f_apporteur(self,cursorSQLServer,cursorPOSTGRESOdoo,id_polices,POL_PTRAPID):
        cursorSQLServer.execute(""" SELECT "AP_CODE_LANGUE"
                                          ,"AP_TR1_MAXI"
                                          ,"AP_DATECREATION"
                                          ,"AP_ANONYME_6"
                                          ,"AP_RETRO_PN"
                                          ,"AP_TR3_MAXI"
                                          ,"AP_C5"
                                          ,"AP_DATEFIN"
                                          ,"AP_TR5_MINI"
                                          ,"AP_TR4_MINI"
                                          ,"AP_NOMDE2"
                                          ,"AP_TR2_MINI"
                                          ,"AP_TR3_TAUX"
                                          ,"AP_C13"
                                          ,"AP_C1"
                                          ,"AP_TELECOPIEUR"
                                          ,"AP_UTILMODIF"
                                          ,"AP_CODE_SOCIETE"
                                          ,"AP_SIREN"
                                          ,"AP_DATEDEB"
                                          ,"AP_LOT_IMP"
                                          ,"AP_TELEPHONE"
                                          ,"AP_CODEPAYS"
                                          ,"AP_ANONYME_3"
                                          ,"AP_ANONYME_4"
                                          ,"AP_ADRESSE2"
                                          ,"AP_UTILCREATEUR"
                                          ,"AP_TR2_MAXI"
                                          ,"AP_C10"
                                          ,"AP_C3"
                                          ,"AP_C6"
                                          ,"AP_LOCALITE"
                                          ,"AP_DATEMODIF"
                                          ,"AP_TR5_TAUX"
                                          ,"AP_ADRESSE1"
                                          ,"AP_TELEPHONE2"
                                          ,"AP_SIRET"
                                          ,"AP_TITRE"
                                          ,"AP_TR4_TAUX"
                                          ,"AP_TR5_MAXI"
                                          ,"AP_IDENT"
                                          ,"AP_ANONYME_8"
                                          ,"AP_C2"
                                          ,"AP_TR2_TAUX"
                                          ,"AP_WEB"
                                          ,"AP_CODE_ETABL"
                                          ,"AP_ANONYME_7"
                                          ,"AP_ADRESSE3"
                                          ,"AP_TELEX"
                                          ,"AP_RETRO_CN"
                                          ,"AP_COMMENTAIRE"
                                          ,"AP_C11"
                                          ,"AP_C8"
                                          ,"AP_TELEPHONE3"
                                          ,"AP_CODEPOSTAL"
                                          ,"AP_ANONYME_9"
                                          ,"AP_CODEINSEE"
                                          ,"AP_LANGUE"
                                          ,"AP_C7"
                                          ,"AP_C4"
                                          ,"AP_LOTEXP"
                                          ,"AP_EMAIL"
                                          ,"AP_C9"
                                          ,"AP_SECTEUR"
                                          ,"AP_TR4_MAXI"
                                          ,"AP_TR3_MINI"
                                          ,"AP_SERVICES"
                                          ,"AP_NOMAPPEL"
                                          ,"AP_CODE"
                                          ,"AP_VILLE"
                                          ,"AP_ANONYME_5"
                                          ,"AP_PAYS"
                                          ,"AP_C12"
                                          ,"AP_SEQUENTIEL"
                                          ,"AP_MOTIFFIN"
                                          ,"AP_NOMDE1"
                                          ,"AP_C14"
                                          ,"AP_REGROUPEMENT"
                                          ,"AP_REFECHO"
                                          ,"AP_TR1_MINI"
                                          ,"AP_LOTIMP"
                                          ,"AP_TR1_TAUX"
                                          ,"AP_ANONYME_10"
                                      FROM F_APPORTEUR  WHERE "AP_IDENT"= %s """ %(POL_PTRAPID))
        resultSQLFapporteur = cursorSQLServer.fetchall()
        if resultSQLFapporteur:
            AP_CODE_LANGUE = resultSQLFapporteur[0][0]
            AP_TR1_MAXI = resultSQLFapporteur[0][1]
            AP_DATECREATION = resultSQLFapporteur[0][2]
            AP_ANONYME_6 = resultSQLFapporteur[0][3]
            AP_RETRO_PN = resultSQLFapporteur[0][4]
            AP_TR3_MAXI = resultSQLFapporteur[0][5]
            AP_C5 = resultSQLFapporteur[0][6]
            AP_DATEFIN = resultSQLFapporteur[0][7]
            AP_TR5_MINI = resultSQLFapporteur[0][8]
            AP_TR4_MINI = resultSQLFapporteur[0][9]
            AP_NOMDE2 = resultSQLFapporteur[0][10]
            AP_TR2_MINI = resultSQLFapporteur[0][11]
            AP_TR3_TAUX = resultSQLFapporteur[0][12]
            AP_C13 = resultSQLFapporteur[0][13]
            AP_C1 = resultSQLFapporteur[0][14]
            AP_TELECOPIEUR = resultSQLFapporteur[0][15]
            AP_UTILMODIF = resultSQLFapporteur[0][16]
            AP_CODE_SOCIETE = resultSQLFapporteur[0][17]
            AP_SIREN = resultSQLFapporteur[0][18]
            AP_DATEDEB = resultSQLFapporteur[0][19]
            AP_LOT_IMP = resultSQLFapporteur[0][20]
            AP_TELEPHONE = resultSQLFapporteur[0][21]
            AP_CODEPAYS = resultSQLFapporteur[0][22]
            AP_ANONYME_3 = resultSQLFapporteur[0][23]
            AP_ANONYME_4 = resultSQLFapporteur[0][24]
            AP_ADRESSE2 = resultSQLFapporteur[0][25]
            AP_UTILCREATEUR = resultSQLFapporteur[0][26]
            AP_TR2_MAXI = resultSQLFapporteur[0][27]
            AP_C10 = resultSQLFapporteur[0][28]
            AP_C3 = resultSQLFapporteur[0][29]
            AP_C6 = resultSQLFapporteur[0][30]
            AP_LOCALITE = resultSQLFapporteur[0][31]
            AP_DATEMODIF = resultSQLFapporteur[0][32]
            AP_TR5_TAUX = resultSQLFapporteur[0][33]
            AP_ADRESSE1 = resultSQLFapporteur[0][34]
            AP_TELEPHONE2 = resultSQLFapporteur[0][35]
            AP_SIRET = resultSQLFapporteur[0][36]
            AP_TITRE = resultSQLFapporteur[0][37]
            AP_TR4_TAUX = resultSQLFapporteur[0][38]
            AP_TR5_MAXI = resultSQLFapporteur[0][39]
            AP_IDENT = resultSQLFapporteur[0][40]
            AP_ANONYME_8 = resultSQLFapporteur[0][41]
            AP_C2 = resultSQLFapporteur[0][42]
            AP_TR2_TAUX = resultSQLFapporteur[0][43]
            AP_WEB = resultSQLFapporteur[0][44]
            AP_CODE_ETABL = resultSQLFapporteur[0][45]
            AP_ANONYME_7 = resultSQLFapporteur[0][46]
            AP_ADRESSE3 = resultSQLFapporteur[0][47]
            AP_TELEX = resultSQLFapporteur[0][48]
            AP_RETRO_CN = resultSQLFapporteur[0][49]
            AP_COMMENTAIRE = resultSQLFapporteur[0][50]
            AP_C11 = resultSQLFapporteur[0][51]
            AP_C8 = resultSQLFapporteur[0][52]
            AP_TELEPHONE3 = resultSQLFapporteur[0][53]
            AP_CODEPOSTAL = resultSQLFapporteur[0][54]
            AP_ANONYME_9 = resultSQLFapporteur[0][55]
            AP_CODEINSEE = resultSQLFapporteur[0][56]
            AP_LANGUE = resultSQLFapporteur[0][57]
            AP_C7 = resultSQLFapporteur[0][58]
            AP_C4 = resultSQLFapporteur[0][59]
            AP_LOTEXP = resultSQLFapporteur[0][60]
            AP_EMAIL = resultSQLFapporteur[0][61]
            AP_C9 = resultSQLFapporteur[0][62]
            AP_SECTEUR = resultSQLFapporteur[0][63]
            AP_TR4_MAXI = resultSQLFapporteur[0][64]
            AP_TR3_MINI = resultSQLFapporteur[0][65]
            AP_SERVICES = resultSQLFapporteur[0][66]
            AP_NOMAPPEL = resultSQLFapporteur[0][67]
            AP_CODE = resultSQLFapporteur[0][68]
            AP_VILLE = resultSQLFapporteur[0][69]
            AP_ANONYME_5 = resultSQLFapporteur[0][70]
            AP_PAYS = resultSQLFapporteur[0][71]
            AP_C12 = resultSQLFapporteur[0][72]
            AP_SEQUENTIEL = resultSQLFapporteur[0][73]
            AP_MOTIFFIN = resultSQLFapporteur[0][74]
            AP_NOMDE1 = resultSQLFapporteur[0][75]
            AP_C14 = resultSQLFapporteur[0][76]
            AP_REGROUPEMENT = resultSQLFapporteur[0][77]
            AP_REFECHO = resultSQLFapporteur[0][78]
            AP_TR1_MINI = resultSQLFapporteur[0][79]
            AP_LOTIMP = resultSQLFapporteur[0][80]
            AP_TR1_TAUX = resultSQLFapporteur[0][81]
            AP_ANONYME_10 = resultSQLFapporteur[0][82]
            name = AP_NOMAPPEL
                        
            cursorPOSTGRESOdoo.execute(""" INSERT  INTO f_apporteur (id,
                                                                    create_uid,
                                                                    "AP_VILLE",
                                                                    create_date,
                                                                    name,                                                                    
                                                                    write_uid,
                                                                    "AP_PAYS",
                                                                    "AP_CODE",
                                                                    write_date) 
                                      VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) """,
                                      (AP_IDENT,1,AP_VILLE,datetime.datetime.now(),name,1
                                      ,AP_PAYS,AP_CODE,datetime.datetime.now()
                                      ))       
        
        
    
    def mouvement_sor(self,cursorSQLServer,cursorPOSTGRESOdoo,id_version_police):
        #Recuperation f_mouvement dans SQL SERVER
        cursorSQLServer.execute(""" SELECT    "MVT_SEQUENTIEL"
                                              ,"MVT_IDENT"
                                              ,"MVT_PTRVERID"
                                              ,"MVT_PTRSUIVANTID"
                                              ,"MVT_INT_LOT_EXP"
                                              ,"MVT_REFECHO"
                                              ,"MVT_PTRPRECEDENTID"
                                              ,"MVT_NON_REGULARISE"
                                              ,"MVT_CODETYPE"
                                              ,"MVT_ZONEMODIFIEE"
                                              ,"MVT_ANCIENNEVALEUR"
                                              ,"MVT_AVTSOR"
                                              ,"MVT_DATEDEFFET"
                                              ,"MVT_PTRSCOSUIVID"
                                              ,"MVT_SERVICES"
                                              ,"MVT_PTRSCOPRECID"
                                              ,"MVT_INT_LOT_IMP"
                                              ,"MVT_PTRPOLID"
                                    FROM F_MOUVEMENT                                                                      
                                    WHERE "MVT_PTRVERID" = %s AND "MVT_CODETYPE"='SOR' """ % (id_version_police))
        resultsSQLFMouvement =  cursorSQLServer.fetchall()        
        #Insertion de  f_mouvement dans Odoo
        if resultsSQLFMouvement:
            MVT_IDENT = resultsSQLFMouvement[0][1]
            MVT_CODETYPE   = self.cast_to_string(resultsSQLFMouvement[0][8])
            MVT_ZONEMODIFIEE =  self.cast_to_string(resultsSQLFMouvement[0][9])
            MVT_DATEDEFFET = self.parse_date(resultsSQLFMouvement[0][12])
            MVT_AVTSOR = self.cast_opt_string(resultsSQLFMouvement[0][11])                                    
            MVT_PTRVERID = self.none_value(resultsSQLFMouvement[0][2]) 
            MVT_PTRPOLID = self.none_value(resultsSQLFMouvement[0][16]) 
            MVT_PTRSOR_OBJET = self.none_value(resultsSQLFMouvement[0][3])
            MVT_PTRSUIVANTID =self.none_value(resultsSQLFMouvement[0][3])
            MVT_PTRPRECEDENTID = self.none_value(resultsSQLFMouvement[0][6])                                     
            ## Test si PREC ET SUIV existent: liaison pour le SOR
            state = 'suivant'
            if resultsSQLFMouvement[0][6] and not resultsSQLFMouvement[0][3]:
                MVT_PTRSOR_OBJET = self.none_value(resultsSQLFMouvement[0][6]) 
                state = 'precedent'                                 
                       
            cursorPOSTGRESOdoo.execute("""INSERT INTO f_mouvement   (id,create_uid,
                                                                    "MVT_ZONEMODIFIEE", 
                                                                    "MVT_CODETYPE", 
                                                                    "MVT_DATEDEFFET",
                                                                    "MVT_AVTSOR",
                                                                    write_uid,
                                                                    "MVT_PTRVERID" , 
                                                                    "MVT_PTRSOR_OBJET",   
                                                                    "MVT_PTRPOLID", 
                                                                    "MVT_PTRPRECEDENTID", 
                                                                    "MVT_PTRSUIVANTID",state) VALUES (%s,%s,'%s','%s',%s,%s,%s,%s,%s,%s,%s,%s,'%s')
                                                                           
                                     """ % (MVT_IDENT,1,MVT_ZONEMODIFIEE,MVT_CODETYPE,MVT_DATEDEFFET,MVT_AVTSOR,1,id_version_police,MVT_PTRSOR_OBJET,
                                         MVT_PTRPOLID,MVT_PTRPRECEDENTID,MVT_PTRSUIVANTID,state))
            ######################################### Fin insertion f_mouvement #####################################################################
            
            #Selection et Ajout Objet de Risque  dans V9                                   
            cursorSQLServer.execute("""SELECT     "SOR_IDENT",
                                                  "SOR_PTRPOLID", 
                                                  "SOR_TABLE",
                                                  "SOR_FORMULE",
                                                  "SOR_SERVICES",
                                                  "SOR_CODE_PRODUCT" ,
                                                  "SOR_VA_FORCEE"                                                                           
                                                  FROM F_SIT_OBJET_RISQUE
                                                  WHERE "SOR_IDENT" = %s """ % (MVT_PTRSOR_OBJET))
            
            resultsSQLFSitObjetRisque = cursorSQLServer.fetchall()
                                     
            ###INSERTION f_SIT_OBJET_RISQUE dans Odoo
            if resultsSQLFSitObjetRisque:
                SOR_IDENT = resultsSQLFSitObjetRisque[0][0]                                       
                SOR_PTRPOLID = self.none_value(resultsSQLFSitObjetRisque[0][1])
                SOR_TABLE = self.cast_to_string(resultsSQLFSitObjetRisque[0][2])
                SOR_FORMULE = self.cast_opt_string(resultsSQLFSitObjetRisque[0][3])
                SOR_SERVICES =  self.cast_to_string(resultsSQLFSitObjetRisque[0][4])
                SOR_CODE_PRODUCT = self.cast_to_string(resultsSQLFSitObjetRisque[0][5])
                SOR_VA_FORCEE = self.cast_to_string(resultsSQLFSitObjetRisque[0][6])                
                nameSor = ''
                if resultsSQLFSitObjetRisque[0][5] is not None:
                    nameSor = "RISQUE - " + resultsSQLFSitObjetRisque[0][5]
                if resultsSQLFSitObjetRisque[0][2] is not None:
                    nameSor += nameSor + resultsSQLFSitObjetRisque[0][2]
                    
                nameSoradd = ''
                if nameSor:
                    nameSoradd = nameSor.replace("'","''")
                                                       
                #name = "RISQUE - "  + resultsSQLFSitObjetRisque[0][5] + " - " + resultsSQLFSitObjetRisque[0][2]
                 
                #Insertion du f_sit_objet_risque dans Odoo ############################################################################
                cursorPOSTGRESOdoo.execute(""" INSERT INTO f_sit_objet_risque (
                                                             id, 
                                                             create_uid, 
                                                             "SOR_PTRPOLID", 
                                                             "SOR_TABLE", 
                                                             name,
                                                             "SOR_FORMULE",
                                                             "SOR_SERVICES" ,
                                                             write_date ,
                                                             "SOR_CODE_PRODUCT" ,
                                                             create_date,
                                                             write_uid, 
                                                             "SOR_VA_FORCEE"                                        
                                                             )
                                                                   
                                                 VALUES (%s,%s,%s,'%s','%s',%s,'%s','%s','%s','%s',%s,'%s')                                  
                                             """ % (SOR_IDENT,1,SOR_PTRPOLID,SOR_TABLE,nameSoradd,SOR_FORMULE,SOR_SERVICES,datetime.datetime.now(),
                                                  SOR_CODE_PRODUCT,datetime.datetime.now(),1,SOR_VA_FORCEE))
                
                return SOR_IDENT
        return None    
        ################### Fin insertion f_sit_objet_risque ###################################################################   
    
    def mouvement_desc100_clause_garantie(self,cursorSQLServer,cursorPOSTGRESOdoo,id_version_police,SOR_IDENT):        
            ### LIRE  F_DESC_STAT_100 dans V9 WHERE D100_PTRPSORID = SOR_IDENT                                        
            cursorSQLServer.execute(""" SELECT
                                                    "D100_DESC_00",
                                                    "D100_DESC_01",
                                                    "D100_DESC_02",
                                                    "D100_DESC_03",
                                                    "D100_DESC_04",
                                                    "D100_DESC_05",
                                                    "D100_DESC_06",
                                                    "D100_DESC_07",
                                                    "D100_DESC_08",
                                                    "D100_DESC_09",
                                                    "D100_DESC_10",                                                                                
                                                    "D100_DESC_11",
                                                    "D100_DESC_12",
                                                    "D100_DESC_13",
                                                    "D100_DESC_14",
                                                    "D100_DESC_15",
                                                    "D100_DESC_16",
                                                    "D100_DESC_17",
                                                    "D100_DESC_18",
                                                    "D100_DESC_19",
                                                    "D100_DESC_20",                                                                                
                                                    "D100_DESC_21",
                                                    "D100_DESC_22",
                                                    "D100_DESC_23",
                                                    "D100_DESC_24",
                                                    "D100_DESC_25",
                                                    "D100_DESC_26",
                                                    "D100_DESC_27",
                                                    "D100_DESC_28",
                                                    "D100_DESC_29",                                                                                
                                                    "D100_DESC_30",
                                                    "D100_DESC_31",
                                                    "D100_DESC_32",
                                                    "D100_DESC_33",
                                                    "D100_DESC_34",
                                                    "D100_DESC_35",
                                                    "D100_DESC_36",
                                                    "D100_DESC_37",
                                                    "D100_DESC_38",
                                                    "D100_DESC_39",                                                                                
                                                    "D100_DESC_40",
                                                    "D100_DESC_41",
                                                    "D100_DESC_42",
                                                    "D100_DESC_43",
                                                    "D100_DESC_44",
                                                    "D100_DESC_45",
                                                    "D100_DESC_46",
                                                    "D100_DESC_47",
                                                    "D100_DESC_48",
                                                    "D100_DESC_49",                                                                                
                                                    "D100_DESC_50",
                                                    "D100_DESC_51",
                                                    "D100_DESC_52",
                                                    "D100_DESC_53",
                                                    "D100_DESC_54",
                                                    "D100_DESC_55",
                                                    "D100_DESC_56",
                                                    "D100_DESC_57",
                                                    "D100_DESC_58",
                                                    "D100_DESC_59",                                                                                
                                                    "D100_DESC_60",
                                                    "D100_DESC_61",
                                                    "D100_DESC_62",
                                                    "D100_DESC_63",
                                                    "D100_DESC_64",
                                                    "D100_DESC_65",
                                                    "D100_DESC_66",
                                                    "D100_DESC_67",
                                                    "D100_DESC_68",
                                                    "D100_DESC_69",                                                                                
                                                    "D100_DESC_70",
                                                    "D100_DESC_71",
                                                    "D100_DESC_72",
                                                    "D100_DESC_73",
                                                    "D100_DESC_74",
                                                    "D100_DESC_75",
                                                    "D100_DESC_76",
                                                    "D100_DESC_77",
                                                    "D100_DESC_78",
                                                    "D100_DESC_79",                                                                                
                                                    "D100_DESC_80",
                                                    "D100_DESC_81",
                                                    "D100_DESC_82",
                                                    "D100_DESC_83",
                                                    "D100_DESC_84",
                                                    "D100_DESC_85",
                                                    "D100_DESC_86",
                                                    "D100_DESC_87",
                                                    "D100_DESC_88",
                                                    "D100_DESC_89",                                                                                
                                                    "D100_DESC_90",                                                                                
                                                    "D100_DESC_91",
                                                    "D100_DESC_92",
                                                    "D100_DESC_93",
                                                    "D100_DESC_94",
                                                    "D100_DESC_95",
                                                    "D100_DESC_96",
                                                    "D100_DESC_97",
                                                    "D100_DESC_98",
                                                    "D100_DESC_99",                                                                                                   
                                                    "D100_IDENT",
                                                    "D100_PTRSORID",
                                                    "D100_INT_LOT_EXP",
                                                    "D100_SEQUENTIEL",
                                                    "D100_INT_LOT_IMP"                                                                                                                              
                                                                                                                                                                                                                  
                                                    FROM F_DESC_STAT_100                                                                                
                                                    WHERE "D100_PTRSORID" = %s """ % (SOR_IDENT))
            
            resultsSQLFdescstat100 = cursorSQLServer.fetchall()      
                                        
            #### INSERTION dans F_DESC_STAT_100
            if resultsSQLFdescstat100:
                for i in range(0,len(resultsSQLFdescstat100)):                                          
                    D100_DESC_00 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][0])
                    D100_DESC_01 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][1])
                    D100_DESC_02 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][2])
                    D100_DESC_03 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][3])
                    D100_DESC_04 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][4])
                    D100_DESC_05 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][5])
                    D100_DESC_06 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][6])
                    D100_DESC_07 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][7])
                    D100_DESC_08 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][8])
                    D100_DESC_09 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][9])
                    
                    D100_DESC_10 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][10])
                    D100_DESC_11 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][11])
                    D100_DESC_12 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][12])
                    D100_DESC_13 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][13])
                    D100_DESC_14 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][14])
                    D100_DESC_15 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][15])
                    D100_DESC_16 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][16])
                    D100_DESC_17 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][17])
                    D100_DESC_18 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][18])
                    D100_DESC_19 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][19])
                    
                    D100_DESC_20 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][20])
                    D100_DESC_21 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][21])
                    D100_DESC_22 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][22])
                    D100_DESC_23 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][23])
                    D100_DESC_24 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][24])
                    D100_DESC_25 = self.cast_opt_string_rpl(resultsSQLFdescstat100[i][25])
                    D100_DESC_26 = self.cast_opt_string(resultsSQLFdescstat100[i][26])
                    D100_DESC_27 = self.cast_opt_string(resultsSQLFdescstat100[i][27])
                    D100_DESC_28 = self.cast_opt_string(resultsSQLFdescstat100[i][28])                                           
                    D100_DESC_29 = self.cast_opt_string(resultsSQLFdescstat100[i][29])
                    
                    D100_DESC_30 = self.cast_opt_string(resultsSQLFdescstat100[i][30])
                    D100_DESC_31 = self.cast_opt_string(resultsSQLFdescstat100[i][31])
                    D100_DESC_32 = self.cast_opt_string(resultsSQLFdescstat100[i][32])
                    D100_DESC_33 = self.cast_opt_string(resultsSQLFdescstat100[i][33])
                    D100_DESC_34 = self.cast_opt_string(resultsSQLFdescstat100[i][34])
                    D100_DESC_35 = self.cast_opt_string(resultsSQLFdescstat100[i][35])
                    D100_DESC_36 = self.cast_opt_string(resultsSQLFdescstat100[i][36])
                    D100_DESC_37 = self.cast_opt_string(resultsSQLFdescstat100[i][37])
                    D100_DESC_38 = self.cast_opt_string(resultsSQLFdescstat100[i][38])
                    D100_DESC_39 = self.cast_opt_string(resultsSQLFdescstat100[i][39])
                    
                    D100_DESC_40 = self.cast_opt_string(resultsSQLFdescstat100[i][40])
                    D100_DESC_41 = self.cast_opt_string(resultsSQLFdescstat100[i][41])
                    D100_DESC_42 = self.cast_opt_string(resultsSQLFdescstat100[i][42])
                    D100_DESC_43 = self.cast_opt_string(resultsSQLFdescstat100[i][43])
                    D100_DESC_44 = self.cast_opt_string(resultsSQLFdescstat100[i][44])
                    D100_DESC_45 = self.cast_opt_string(resultsSQLFdescstat100[i][45])
                    D100_DESC_46 = self.cast_opt_string(resultsSQLFdescstat100[i][46])
                    D100_DESC_47 = self.cast_opt_string(resultsSQLFdescstat100[i][47])
                    D100_DESC_48 = self.cast_opt_string(resultsSQLFdescstat100[i][48])
                    D100_DESC_49 = self.cast_opt_string(resultsSQLFdescstat100[i][49])
                    
                    D100_DESC_50 = self.cast_opt_string(resultsSQLFdescstat100[i][50])
                    D100_DESC_51 = self.cast_opt_string(resultsSQLFdescstat100[i][51])
                    D100_DESC_52 = self.cast_opt_string(resultsSQLFdescstat100[i][52])
                    D100_DESC_53 = self.cast_opt_string(resultsSQLFdescstat100[i][53])
                    D100_DESC_54 = self.cast_opt_string(resultsSQLFdescstat100[i][54])
                    D100_DESC_55 = self.cast_opt_string(resultsSQLFdescstat100[i][55])
                    D100_DESC_56 = self.cast_opt_string(resultsSQLFdescstat100[i][56])
                    D100_DESC_57 = self.cast_opt_string(resultsSQLFdescstat100[i][57])
                    D100_DESC_58 = self.cast_opt_string(resultsSQLFdescstat100[i][58])
                    D100_DESC_59 = self.cast_opt_string(resultsSQLFdescstat100[i][59])
                    
                    D100_DESC_60 = self.cast_opt_string(resultsSQLFdescstat100[i][60])
                    D100_DESC_61 = self.cast_opt_string(resultsSQLFdescstat100[i][61])
                    D100_DESC_62 = self.cast_opt_string(resultsSQLFdescstat100[i][62])
                    D100_DESC_63 = self.cast_opt_string(resultsSQLFdescstat100[i][63])
                    D100_DESC_64 = self.cast_opt_string(resultsSQLFdescstat100[i][64])
                    D100_DESC_65 = self.cast_opt_string(resultsSQLFdescstat100[i][65])
                    D100_DESC_66 = self.cast_opt_string(resultsSQLFdescstat100[i][66])
                    D100_DESC_67 = self.cast_opt_string(resultsSQLFdescstat100[i][67])
                    D100_DESC_68 = self.cast_opt_string(resultsSQLFdescstat100[i][68])
                    D100_DESC_69 = self.cast_opt_string(resultsSQLFdescstat100[i][69])
                    
                    D100_DESC_70 = self.cast_opt_string(resultsSQLFdescstat100[i][70])                                          
                    D100_DESC_71 = self.cast_opt_string(resultsSQLFdescstat100[i][71])
                    D100_DESC_72 = self.cast_opt_string(resultsSQLFdescstat100[i][72])
                    D100_DESC_73 = self.cast_opt_string(resultsSQLFdescstat100[i][73])
                    D100_DESC_74 = self.cast_opt_string(resultsSQLFdescstat100[i][74])
                    D100_DESC_75 = self.cast_opt_string(resultsSQLFdescstat100[i][75])
                    D100_DESC_76 = self.cast_opt_string(resultsSQLFdescstat100[i][76])
                    D100_DESC_77 = self.cast_opt_string(resultsSQLFdescstat100[i][77])
                    D100_DESC_78 = self.cast_opt_string(resultsSQLFdescstat100[i][78])
                    D100_DESC_79 = self.cast_opt_string(resultsSQLFdescstat100[i][79])                                         
                    
                    D100_DESC_80 = self.cast_opt_string(resultsSQLFdescstat100[i][80])
                    D100_DESC_81 = self.cast_opt_string(resultsSQLFdescstat100[i][81])
                    D100_DESC_82 = self.cast_opt_string(resultsSQLFdescstat100[i][82])
                    D100_DESC_83 = self.cast_opt_string(resultsSQLFdescstat100[i][83])
                    D100_DESC_84 = self.cast_opt_string(resultsSQLFdescstat100[i][84])
                    D100_DESC_85 = self.cast_opt_string(resultsSQLFdescstat100[i][85])
                    D100_DESC_86 = self.cast_opt_string(resultsSQLFdescstat100[i][86])
                    D100_DESC_87 = self.cast_opt_string(resultsSQLFdescstat100[i][87])
                    D100_DESC_88 = self.cast_opt_string(resultsSQLFdescstat100[i][88])
                    D100_DESC_89 = self.cast_opt_string(resultsSQLFdescstat100[i][89])
                    
                    D100_DESC_90 = self.cast_opt_string(resultsSQLFdescstat100[i][90])                                            
                    D100_DESC_91 = self.cast_opt_string(resultsSQLFdescstat100[i][91])
                    D100_DESC_92 = self.cast_opt_string(resultsSQLFdescstat100[i][92])
                    D100_DESC_93 = self.cast_opt_string(resultsSQLFdescstat100[i][93])
                    D100_DESC_94 = self.cast_opt_string(resultsSQLFdescstat100[i][94])
                    D100_DESC_95 = self.cast_opt_string(resultsSQLFdescstat100[i][95])
                    D100_DESC_96 = self.cast_opt_string(resultsSQLFdescstat100[i][96])
                    D100_DESC_97 = self.cast_opt_string(resultsSQLFdescstat100[i][97])
                    D100_DESC_98 = self.cast_opt_string(resultsSQLFdescstat100[i][98])
                    D100_DESC_99 = self.cast_opt_string(resultsSQLFdescstat100[i][99])
                    
                    D100_IDENT = self.none_value(resultsSQLFdescstat100[i][100])
                    D100_PTRSORID = self.none_value(resultsSQLFdescstat100[i][101])
                    D100_INT_LOT_EXP = self.cast_opt_string(resultsSQLFdescstat100[i][102])                                            
                    D100_SEQUENTIEL = self.none_value(resultsSQLFdescstat100[i][103])
                    D100_INT_LOT_IMP =  self.cast_opt_string(resultsSQLFdescstat100[i][104])
                    
                    name_desc_stat = ''
                    
                    if resultsSQLFdescstat100[i][0] is not None:
                        name_desc_stat = resultsSQLFdescstat100[i][0]
                    if resultsSQLFdescstat100[i][1] is not None:
                        name_desc_stat += " / "  + resultsSQLFdescstat100[i][1]
                    if resultsSQLFdescstat100[i][2] is not None:
                        name_desc_stat += " / " + resultsSQLFdescstat100[i][2]
                       
                    name_desc_statadd = '' 
                    if name_desc_stat:
                        name_desc_statadd = name_desc_stat.replace("'", "''")
                                                                
                    #name_desc_stat = resultsSQLFdescstat100[i][0] + "/ " + resultsSQLFdescstat100[i][1] + "/ " + resultsSQLFdescstat100[i][2]                             
                    ##ECRIRE DANS F_DESC_STAT_100 dans Odoo                                           
                    cursorPOSTGRESOdoo.execute(""" INSERT INTO f_desc_stat_100 (    id,
                                                                                    create_date, 
                                                                                    write_uid,
                                                                                    create_uid,
                                                                                    write_date,
                                                                                    name, 
                                                                                    "D100_DESC_00" ,
                                                                                    "D100_DESC_01",
                                                                                    "D100_DESC_02" ,
                                                                                    "D100_DESC_03" ,
                                                                                    "D100_DESC_04" ,
                                                                                    "D100_DESC_05" ,
                                                                                    "D100_DESC_06" ,
                                                                                    "D100_DESC_07", 
                                                                                    "D100_DESC_08",
                                                                                    "D100_DESC_09",
                                                                                    "D100_DESC_10",
                                                                                    "D100_DESC_11",
                                                                                    "D100_DESC_12",
                                                                                    
                                                                                    "D100_DESC_13",
                                                                                    "D100_DESC_14",
                                                                                    "D100_DESC_15",
                                                                                    "D100_DESC_16",
                                                                                    "D100_DESC_17",
                                                                                    "D100_DESC_18",
                                                                                    "D100_DESC_19",
                                                                                    "D100_DESC_20",
                                                                                    "D100_DESC_21",
                                                                                    "D100_DESC_22",
                                                                                    "D100_PTRSORID",
                                                                                      
                                                                                      
                                                                                    "D100_DESC_23",
                                                                                    "D100_DESC_24",
                                                                                    "D100_DESC_25",
                                                                                    "D100_DESC_26",
                                                                                    "D100_DESC_27",
                                                                                    "D100_DESC_28",
                                                                                    "D100_DESC_29",
                                                                                    "D100_DESC_30",
                                                                                    "D100_DESC_31",
                                                                                    "D100_DESC_32",
                                                                                    "D100_DESC_33",
                                                                                    "D100_DESC_34",
                                                                                    "D100_DESC_35",
                                                                                    "D100_DESC_36",
                                                                                    "D100_DESC_37",
                                                                                    "D100_DESC_38",
                                                                                    "D100_DESC_39",
                                                                                    "D100_DESC_40",
                                                                                    "D100_DESC_41",
                                                                                    "D100_DESC_42",
                                                                                    "D100_DESC_43",
                                                                                    "D100_DESC_44",
                                                                                    "D100_DESC_45",
                                                                                    "D100_DESC_46",
                                                                                    "D100_DESC_47",
                                                                                    "D100_DESC_48",
                                                                                    "D100_DESC_49",
                                                                                    "D100_DESC_50",
                                                                                    "D100_DESC_51",
                                                                                    "D100_DESC_52",
                                                                                    "D100_DESC_53",
                                                                                    "D100_DESC_54",
                                                                                    "D100_DESC_55",
                                                                                    
                                                                                    "D100_DESC_56",
                                                                                    "D100_DESC_57",
                                                                                    "D100_DESC_58",
                                                                                    "D100_DESC_59",
                                                                                    "D100_DESC_60",
                                                                                    "D100_DESC_61",
                                                                                    "D100_DESC_62",
                                                                                    "D100_DESC_63",
                                                                                    "D100_DESC_64",
                                                                                    "D100_DESC_65",
                                                                                    "D100_DESC_66",
                                                                                    "D100_DESC_67",
                                                                                    "D100_DESC_68",
                                                                                    "D100_DESC_69",
                                                                                    "D100_DESC_70",
                                                                                    "D100_DESC_71",
                                                                                    "D100_DESC_72",
                                                                                    "D100_DESC_73",
                                                                                    "D100_DESC_74",
                                                                                    "D100_DESC_75",
                                                                                    "D100_DESC_76",
                                                                                    "D100_DESC_77",
                                                                                    "D100_DESC_78",
                                                                                    "D100_DESC_79",
                                                                                    "D100_DESC_80",
                                                                                    "D100_DESC_81",
                                                                                    "D100_DESC_82",
                                                                                    "D100_DESC_83",
                                                                                    "D100_DESC_84",
                                                                                    "D100_DESC_85",
                                                                                    "D100_DESC_86",
                                                                                    "D100_DESC_87",
                                                                                    "D100_DESC_88",
                                                                                    "D100_DESC_89",
                                                                                    "D100_DESC_90",
                                                                                    
                                                                                    "D100_DESC_91",
                                                                                    "D100_DESC_92",
                                                                                    "D100_DESC_93",
                                                                                    "D100_DESC_94",
                                                                                    "D100_DESC_95",
                                                                                    "D100_DESC_96",
                                                                                    "D100_DESC_97",
                                                                                    "D100_DESC_98",
                                                                                    "D100_DESC_99"                                                                                                                                                                  
                                                                                   
                                                                                ) 
                                              VALUES (%s,'%s',%s,%s,'%s','%s',%s,%s,%s,%s,%s,%s,
                                                      %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                                      %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                                      %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                                      %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                                      %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                                      %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                                      %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                                      %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                                      %s,%s,%s,%s,%s,%s,%s)
                                              """ % (D100_IDENT,datetime.datetime.now(),1,1,datetime.datetime.now(),name_desc_statadd, D100_DESC_00, D100_DESC_01,
                                                     D100_DESC_02,D100_DESC_03,D100_DESC_04,D100_DESC_05,
                                                     D100_DESC_06 ,
                                                     D100_DESC_07, 
                                                     D100_DESC_08,
                                                     D100_DESC_09,
                                                     D100_DESC_10,
                                                     D100_DESC_11,
                                                     D100_DESC_12,
                                                     D100_DESC_13,
                                                     D100_DESC_14,
                                                     D100_DESC_15,
                                                     D100_DESC_16,
                                                     D100_DESC_17,
                                                     D100_DESC_18,
                                                     D100_DESC_19,
                                                     D100_DESC_20,
                                                     D100_DESC_21,
                                                     D100_DESC_22,
                                                     SOR_IDENT,
                                                     D100_DESC_23,
                                                    D100_DESC_24,
                                                    D100_DESC_25,
                                                    D100_DESC_26,
                                                    D100_DESC_27,
                                                    D100_DESC_28,
                                                    D100_DESC_29,
                                                    D100_DESC_30,
                                                    D100_DESC_31,
                                                    D100_DESC_32,
                                                    D100_DESC_33,
                                                    D100_DESC_34,
                                                    D100_DESC_35,
                                                    D100_DESC_36,
                                                    D100_DESC_37,
                                                    D100_DESC_38,
                                                    D100_DESC_39,
                                                    D100_DESC_40,
                                                    D100_DESC_41,
                                                    D100_DESC_42,
                                                    D100_DESC_43,
                                                    D100_DESC_44,
                                                    D100_DESC_45,
                                                    D100_DESC_46,
                                                    D100_DESC_47,
                                                    D100_DESC_48,
                                                    D100_DESC_49,
                                                    D100_DESC_50,
                                                    D100_DESC_51,
                                                    D100_DESC_52,
                                                    D100_DESC_53,
                                                    D100_DESC_54,
                                                    D100_DESC_55,
                                                    
                                                    D100_DESC_56,
                                                    D100_DESC_57,
                                                    D100_DESC_58,
                                                    D100_DESC_59,
                                                    D100_DESC_60,
                                                    D100_DESC_61,
                                                    D100_DESC_62,
                                                    D100_DESC_63,
                                                    D100_DESC_64,
                                                    D100_DESC_65,
                                                    D100_DESC_66,
                                                    D100_DESC_67,
                                                    D100_DESC_68,
                                                    D100_DESC_69,
                                                    D100_DESC_70,
                                                    D100_DESC_71,
                                                    D100_DESC_72,
                                                    D100_DESC_73,
                                                    D100_DESC_74,
                                                    D100_DESC_75,
                                                    D100_DESC_76,
                                                    D100_DESC_77,
                                                    D100_DESC_78,
                                                    D100_DESC_79,
                                                    D100_DESC_80,
                                                    D100_DESC_81,
                                                    D100_DESC_82,
                                                    D100_DESC_83,
                                                    D100_DESC_84,
                                                    D100_DESC_85,
                                                    D100_DESC_86,
                                                    D100_DESC_87,
                                                    D100_DESC_88,
                                                    D100_DESC_89,
                                                    D100_DESC_90,
                                                    
                                                    D100_DESC_91,
                                                    D100_DESC_92,
                                                    D100_DESC_93,
                                                    D100_DESC_94,
                                                    D100_DESC_95,
                                                    D100_DESC_96,
                                                    D100_DESC_97,
                                                    D100_DESC_98,
                                                    D100_DESC_99))
                
                
#                                             
            #############################################################################################################
            #LIRE DANS F_CLAUSE_DYN ET INSERTION
            #LIRE DANS F_CLAUSE_DYN dans SQL SERVER
            cursorSQLServer.execute(""" SELECT 
                                                  "CLD_TABLE"
                                                  ,"CLD_INT_LOT_EXP"
                                                  ,"CLD_IDENT"
                                                  ,"CLD_REFECHO"
                                                  ,"CLD_PTRSSRID"
                                                  ,"CLD_SEQUENTIEL"
                                                  ,"CLD_CHAPITRE"
                                                  ,"CLD_S_CHAPITRE"
                                                  ,"CLD_TYPE"
                                                  ,"CLD_INT_LOT_IMP"
                                                  ,"CLD_CODE"
                                                  ,"CLD_SERVICES"
                                                  ,"CLD_SS_CHAPITRE"
                                                  ,"CLD_LIBRE"
                                                  ,"CLD_ORDRE"
                                                  ,"CLD_TEXTE"
                                                  ,"CLD_PTRSORID"
                                                                                                                                
                                                  FROM F_CLAUSE_DYN
                                                  WHERE "CLD_PTRSORID" = %s """ % (SOR_IDENT))
            
            resultsSQLFClausedyn = cursorSQLServer.fetchall() 
                                        
            if resultsSQLFClausedyn:
                for i in range(0, len(resultsSQLFClausedyn)):
                    CLD_TABLE = self.cast_opt_string(resultsSQLFClausedyn[i][0])
                    CLD_INT_LOT_EXP = self.cast_opt_string(resultsSQLFClausedyn[i][1])
                    CLD_IDENT = self.none_value(resultsSQLFClausedyn[i][2])
                    CLD_REFECHO = self.cast_opt_string(resultsSQLFClausedyn[i][3])
                    CLD_PTRSSRID = self.none_value(resultsSQLFClausedyn[i][4])
                    CLD_SEQUENTIEL = self.none_value(resultsSQLFClausedyn[i][5])
                    CLD_CHAPITRE = self.cast_opt_string(resultsSQLFClausedyn[i][6])
                    CLD_S_CHAPITRE = self.cast_opt_string(resultsSQLFClausedyn[0][7])
                    CLD_TYPE = self.none_value(resultsSQLFClausedyn[i][8])
                    CLD_INT_LOT_IMP = self.cast_opt_string(resultsSQLFClausedyn[i][9])
                    CLD_CODE = self.cast_opt_string(resultsSQLFClausedyn[i][10])
                    CLD_SERVICES = self.cast_opt_string(resultsSQLFClausedyn[i][11])
                    CLD_SS_CHAPITRE = self.cast_opt_string(resultsSQLFClausedyn[i][12])
                    CLD_LIBRE = self.none_value(resultsSQLFClausedyn[i][13])
                    CLD_ORDRE = self.none_value(resultsSQLFClausedyn[i][14])
                    CLD_TEXTE = ''
                    if resultsSQLFClausedyn[i][15] is not None:
                        Texte = resultsSQLFClausedyn[i][15].replace("'","''")
                        CLD_TEXTE = self.cast_opt_string(Texte)
                    
                    #CLD_TEXTE = self.cast_opt_string(resultsSQLFClausedyn[i][15])
                    CLD_PTRSORID = self.none_value(resultsSQLFClausedyn[i][16])  
                            
                                                        
                    #INSERTION dans F_CLAUSE_DYN Odoo             
                    cursorPOSTGRESOdoo.execute(""" INSERT INTO f_clause_dyn         (id,
                                                                                    create_date,
                                                                                    "CLD_INT_LOT_EXP",
                                                                                    write_uid,
                                                                                    "CLD_LIBRE",
                                                                                    create_uid,
                                                                                    "CLD_REFECHO",
                                                                                    "CLD_CODE",
                                                                                    "CLD_TYPE",
                                                                                    "CLD_SEQUENTIEL",
                                                                                    "CLD_SERVICES",
                                                                                    write_date,
                                                                                    "CLD_S_CHAPITRE",
                                                                                    "CLD_CHAPITRE",
                                                                                    "CLD_INT_LOT_IMP", 
                                                                                    "CLD_TABLE",                                                                                                            
                                                                                    "CLD_SS_CHAPITRE",
                                                                                    "CLD_ORDRE",
                                                                                    "CLD_PTRSSRID",
                                                                                    "CLD_PTRSORID",
                                                                                    "CLD_IDENT",
                                                                                    "CLD_TEXTE"                                                                                                                                                                                                                                 
                                                                                   )
                                                                                    
                                                    VALUES (%s,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,'%s',%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                                """ % (CLD_IDENT,datetime.datetime.now(),CLD_INT_LOT_EXP,1,CLD_LIBRE,1,CLD_REFECHO
                                                       ,CLD_CODE,CLD_TYPE,CLD_SEQUENTIEL,CLD_SERVICES,datetime.datetime.now(),
                                                       CLD_S_CHAPITRE,CLD_CHAPITRE,CLD_INT_LOT_IMP,CLD_TABLE,CLD_SS_CHAPITRE,
                                                       CLD_ORDRE,CLD_PTRSSRID,SOR_IDENT,CLD_IDENT,CLD_TEXTE))      
            #############################################################################################################
            
            ##############################################################################################################
            #LIRE DANS F_GARANTIES_DYN ET INSERTION                                        
            cursorSQLServer.execute(""" SELECT           "GAD_INT_LOT_IMP"
                                                          ,"GAD_COEFTARIF"
                                                          ,"GAD_VA_BRUTE"
                                                          ,"GAD_LIMGAR_UNITE"
                                                          ,"GAD_MOUVEMENT"
                                                          ,"GAD_NB_AVENANT"
                                                          ,"GAD_ZONE4"
                                                          ,"GAD_ORIGPTR"
                                                          ,"GAD_MT_ASSIETTE"
                                                          ,"GAD_LIMGAR_DUREE"
                                                          ,"GAD_CODE"
                                                          ,"GAD_LIMGAR2_VAL"
                                                          ,"GAD_ZONE1"
                                                          ,"GAD_COEFCOM"
                                                          ,"GAD_LIMGAR_VAL2"
                                                          ,"GAD_DATE_FIN"
                                                          ,"GAD_DTCRE"
                                                          ,"GAD_ZONE5"
                                                          ,"GAD_DTMAJ"
                                                          ,"GAD_SERVICES"
                                                          ,"GAD_CODE_FISCAL"
                                                          ,"GAD_IDENT"
                                                          ,"GAD_REVISABLE"
                                                          ,"GAD_FRAN_LIM_UN"
                                                          ,"GAD_CODECOMPAGNIE"
                                                          ,"GAD_TAUX_COM"
                                                          ,"GAD_PTREMPID"
                                                          ,"GAD_LIMGAR_LIBE"
                                                          ,"GAD_PRMPAYTYP"
                                                          ,"GAD_DATE_DEBUT"
                                                          ,"GAD_SOUSCRIPTION"
                                                          ,"GAD_FRAN_MIN"
                                                          ,"GAD_FRAN_MAX"
                                                          ,"GAD_LIMGAR2_UNITE"
                                                          ,"GAD_VA_MINI"
                                                          ,"GAD_TYPE_REVISAB"
                                                          ,"GAD_INT_LOT_EXP"
                                                          ,"GAD_PTRSORID"
                                                          ,"GAD_PTRAYID"
                                                          ,"GAD_INDEXE"
                                                          ,"GAD_TAUX1"
                                                          ,"GAD_TAUX3"
                                                          ,"GAD_TAUX2"
                                                          ,"GAD_TAXES"
                                                          ,"GAD_LIBELLE"
                                                          ,"GAD_SEQUENTIEL"
                                                          ,"GAD_ZONE6"
                                                          ,"GAD_CAPITAL"
                                                          ,"GAD_FRAN_OPTION"
                                                          ,"GAD_PRIME_NETTE" 
                                                          ,"GAD_NB_TERME"
                                                          ,"GAD_FRANCHISE"
                                                          ,"GAD_LIMGAR_VAL"
                                                          ,"GAD_COMMENT"
                                                          ,"GAD_REFECHO"
                                                          ,"GAD_FRAN_UNITE"
                                                          ,"GAD_LIMGAR2_LIBE"
                                                          ,"GAD_ZONE3"
                                                          ,"GAD_INDICE"
                                                          ,"GAD_POPTR"
                                                          ,"GAD_ZONE2"
                                                          ,"GAD_LIMGAR_VAL3"
                                                          ,"GAD_OPTION"
                                                          
                                                          FROM F_GARANTIE_DYN
                                                          WHERE GAD_PTRSORID = %s """ % (SOR_IDENT))
            
            resultsSQLFGarantiedyn = cursorSQLServer.fetchall() 
            
            if resultsSQLFGarantiedyn:                                            
                for i in range(0,len(resultsSQLFGarantiedyn)):                                                                                               
                    GAD_PRIME_NETTE = self.none_value(resultsSQLFGarantiedyn[i][49])
                    GAD_CODE_FISCAL = self.cast_opt_string(resultsSQLFGarantiedyn[i][20])
                    GAD_SOUSCRIPTION =self.cast_opt_string(resultsSQLFGarantiedyn[i][30])
                    GAD_CODE = self.cast_opt_string(resultsSQLFGarantiedyn[i][10])
                    GAD_PTRSORID = self.none_value(resultsSQLFGarantiedyn[i][37])
                    GAD_TAXES = self.none_value(resultsSQLFGarantiedyn[i][43])
                    GAD_IDENT = self.none_value(resultsSQLFGarantiedyn[i][21])
                    name_gad = self.none_value(GAD_CODE)
                    
                    cursorPOSTGRESOdoo.execute(""" INSERT INTO f_garantie_dyn ( id,
                                                                                create_uid,
                                                                                create_date, 
                                                                                name, 
                                                                                "GAD_PRIME_NETTE" ,
                                                                                "GAD_CODE_FISCAL", 
                                                                                "GAD_SOUSCRIPTION", 
                                                                                "GAD_CODE" ,
                                                                                "GAD_PTRSORID" ,
                                                                                "GAD_TAXES" ,
                                                                                write_date, 
                                                                                write_uid 
                                                                               )
                                                    VALUES (%s,%s,'%s',%s,%s,%s,%s,%s,%s,%s,'%s',%s) """
                                                    % (GAD_IDENT,1,datetime.datetime.now(),name_gad,GAD_PRIME_NETTE,GAD_CODE_FISCAL,
                                                       GAD_SOUSCRIPTION,GAD_CODE,SOR_IDENT,GAD_TAXES,datetime.datetime.now(),1));                                                                                                                      
            #######################################################################################################################
             
    ####### SI PAS_PTRBASID = 18003   
    def maladie_adher_ayant_droit(self,cursorSQLServer,cursorPOSTGRESOdoo,id_version_police,SOR_IDENT):        
        ## LIRE F_MALADIE_ADHER dans V9
        cursorSQLServer.execute(""" SELECT         
                                                  "AD_NOMAPPEL"
                                                  ,"AD_TITRE"
                                                  ,"AD_NOMDE1"
                                                  ,"AD_NOMDE2"
                                                  ,"AD_NUM_SS"
                                                  ,"AD_CLE_SECU"
                                                  ,"AD_DATNAISS"
                                                  ,"AD_SEXE"
                                                  ,"AD_COMMENT"
                                                  ,"AD_TELEPHONE"
                                                  ,"AD_TELEPHONE2"
                                                  ,"AD_TELEPHONE3"
                                                  ,"AD_TELECOPIEUR"
                                                  ,"AD_LANGUE"
                                                  ,"AD_CODE_LANGUE"
                                                  ,"AD_EMAIL"
                                                  ,"AD_WEB"
                                                  ,"AD_PASSWORD"
                                                  ,"AD_NB_CHARGE"
                                                  ,"AD_CATPROF"
                                                  ,"AD_PROFESSION"
                                                  ,"AD_SALAIRANN"
                                                  ,"AD_MATRI"
                                                  ,"AD_REFECHO"
                                                  ,"AD_MONN_PAYMENT"
                                                  ,"AD_CODE"
                                                  ,"AD_DTCRE"
                                                  ,"AD_UTCRE"
                                                  ,"AD_INT_LOT_EXP"
                                                  ,"AD_INT_LOT_IMP"
                                                  ,"AD_UTMAJ"
                                                  ,"AD_DTMAJ"
                                                  ,"AD_PTRBPPIDENT"
                                                  ,"AD_PTRBPAIDENT"
                                                  ,"AD_ADRES1"
                                                  ,"AD_ADRES2"
                                                  ,"AD_ADRES3"
                                                  ,"AD_LOCALITE"
                                                  ,"AD_CODPOST"
                                                  ,"AD_VILLE"
                                                  ,"AD_CEDEX"
                                                  ,"AD_PAYS"
                                                  ,"AD_CODE_PAYS"
                                                  ,"AD_PTRBPBIDENT"
                                                  ,"AD_DOMI_CODBQ"
                                                  ,"AD_DOMI_CODGUI"
                                                  ,"AD_DOMI_NUMCPTE"
                                                  ,"AD_DOMI_CLERIB"
                                                  ,"AD_DOMI_TITULAIRE"
                                                  ,"AD_DOMI_LIBEL"
                                                  ,"AD_PTRBPASSIDENT"
                                                  ,"AD_PTRRIBIDENT"
                                                  ,"AD_MADELIN_EXERC_DEB"
                                                  ,"AD_MADELIN_EXERC_FIN"
                                                  ,"AD_MADELIN_DATEDEB"
                                                  ,"AD_MADELIN_DATEFIN"
                                                  ,"AD_LOI_MADELIN"
                                                  ,"AD_ASSURE_AVANT"
                                                  ,"AD_TIERS_PAYANTS"
                                                  ,"AD_RISQUE_AGRAV"
                                                  ,"AD_MODEREGL"
                                                  ,"AD_TXT_ALERT"
                                                  ,"AD_CAISSASS"
                                                  ,"AD_SS"
                                                  ,"AD_PTRSORID"
                                                  ,"AD_ZONE1"
                                                  ,"AD_ZONE2"
                                                  ,"AD_ZONE3"
                                                  ,"AD_ZONE4"
                                                  ,"AD_ZONE5"
                                                  ,"AD_ZONE6"
                                                  ,"AD_ZONE7"
                                                  ,"AD_ZONE8"
                                                  ,"AD_ZONE9"
                                                  ,"AD_ZONE10"
                                                  ,"AD_ZONE11"
                                                  ,"AD_ZONE12"
                                                  ,"AD_ZONE13"
                                                  ,"AD_ZONE14"
                                                  ,"AD_ZONE15"
                                                  ,"AD_IDENT"
                                                
                                              FROM F_MALADIE_ADHER  WHERE "AD_PTRSORID" = %s """ % (SOR_IDENT))
        
        resultSQLFMaladieAdher = cursorSQLServer.fetchall()
        if resultSQLFMaladieAdher:
            for i in range(0,len(resultSQLFMaladieAdher)):
                AD_NOMAPPEL = self.cast_to_string(resultSQLFMaladieAdher[i][0])
                AD_TITRE =  self.cast_to_string(resultSQLFMaladieAdher[i][1])
                AD_NOMDE1 = self.cast_to_string(resultSQLFMaladieAdher[i][2])               
                AD_NOMDE2 = self.cast_to_string(resultSQLFMaladieAdher[i][3])
                AD_NUM_SS = resultSQLFMaladieAdher[i][4]  
                AD_CLE_SECU = resultSQLFMaladieAdher[i][5]    
                AD_DATNAISS = self.parse_date_cast(resultSQLFMaladieAdher[i][6])
                AD_SEXE =  self.cast_to_string(resultSQLFMaladieAdher[i][7])
                AD_COMMENT =  self.cast_to_string(resultSQLFMaladieAdher[i][8])
                AD_TELEPHONE = self.cast_to_string(resultSQLFMaladieAdher[i][9])
                AD_TELEPHONE2 =  resultSQLFMaladieAdher[i][10] 
                AD_TELEPHONE3 =  resultSQLFMaladieAdher[i][11]
                AD_TELECOPIEUR = resultSQLFMaladieAdher[i][12] 
                AD_LANGUE = resultSQLFMaladieAdher[i][13]  
                AD_CODE_LANGUE = resultSQLFMaladieAdher[i][14]
                AD_EMAIL =  resultSQLFMaladieAdher[i][15]
                AD_WEB =  resultSQLFMaladieAdher[i][16]
                AD_PASSWORD = resultSQLFMaladieAdher[i][17] 
                AD_NB_CHARGE = resultSQLFMaladieAdher[i][18] 
                AD_CATPROF =  resultSQLFMaladieAdher[i][19] 
                AD_PROFESSION = resultSQLFMaladieAdher[i][20]
                AD_SALAIRANN = resultSQLFMaladieAdher[i][21]
                AD_MATRI = resultSQLFMaladieAdher[i][22]
                AD_REFECHO =  resultSQLFMaladieAdher[i][23]
                AD_MONN_PAYMENT = resultSQLFMaladieAdher[i][24]                                                      
                AD_CODE =  resultSQLFMaladieAdher[i][25]
                AD_DTCRE = resultSQLFMaladieAdher[i][26]
                AD_UTCRE = resultSQLFMaladieAdher[i][27]
                AD_INT_LOT_EXP = resultSQLFMaladieAdher[i][28]  
                AD_INT_LOT_IMP = resultSQLFMaladieAdher[i][29]
                AD_UTMAJ = resultSQLFMaladieAdher[i][30]
                AD_DTMAJ =  resultSQLFMaladieAdher[i][31]
                AD_PTRBPPIDENT = resultSQLFMaladieAdher[i][32]
                AD_PTRBPAIDENT =  resultSQLFMaladieAdher[i][33]
                AD_ADRES1 = resultSQLFMaladieAdher[i][34] 
                AD_ADRES2 =  resultSQLFMaladieAdher[i][35]  
                AD_ADRES3 =  resultSQLFMaladieAdher[i][36]
                AD_LOCALITE = resultSQLFMaladieAdher[i][37]
                AD_CODPOST = resultSQLFMaladieAdher[i][38]
                AD_VILLE =  resultSQLFMaladieAdher[i][39]
                AD_CEDEX = resultSQLFMaladieAdher[i][40]
                AD_PAYS = resultSQLFMaladieAdher[i][41] 
                AD_CODE_PAYS =  resultSQLFMaladieAdher[i][42]
                AD_PTRBPBIDENT =  resultSQLFMaladieAdher[i][43]
                AD_DOMI_CODBQ =  resultSQLFMaladieAdher[i][44]
                AD_DOMI_CODGUI = resultSQLFMaladieAdher[i][45]
                AD_DOMI_NUMCPTE = resultSQLFMaladieAdher[i][46]
                AD_DOMI_CLERIB47 = resultSQLFMaladieAdher[i][47]
                AD_DOMI_TITULAIRE = resultSQLFMaladieAdher[i][48]
                AD_DOMI_LIBEL =  resultSQLFMaladieAdher[i][49]
                AD_PTRBPASSIDENT =  resultSQLFMaladieAdher[i][50]
                AD_PTRRIBIDENT = resultSQLFMaladieAdher[i][51]                
                AD_MADELIN_EXERC_DEB =  resultSQLFMaladieAdher[i][52]
                AD_MADELIN_EXERC_FIN =  resultSQLFMaladieAdher[i][53]
                AD_MADELIN_DATEDEB = resultSQLFMaladieAdher[i][54]
                AD_MADELIN_DATEFIN =  resultSQLFMaladieAdher[i][55]
                AD_LOI_MADELIN = resultSQLFMaladieAdher[i][56]
                AD_ASSURE_AVANT = resultSQLFMaladieAdher[i][57]
                AD_TIERS_PAYANTS = resultSQLFMaladieAdher[i][58]
                AD_RISQUE_AGRAV =  resultSQLFMaladieAdher[i][59]
                AD_MODEREGL = resultSQLFMaladieAdher[i][60]
                AD_TXT_ALERT = resultSQLFMaladieAdher[i][61]
                AD_CAISSASS = resultSQLFMaladieAdher[i][62]
                AD_SS = resultSQLFMaladieAdher[i][63]
                AD_PTRSORID =resultSQLFMaladieAdher[i][64]
                AD_ZONE1 = self.cast_to_string(resultSQLFMaladieAdher[i][65])
                AD_ZONE2 =  self.cast_to_string(resultSQLFMaladieAdher[i][66])
                AD_ZONE3 =  self.cast_to_string(resultSQLFMaladieAdher[i][67])
                AD_ZONE4 = self.cast_to_string(resultSQLFMaladieAdher[i][68])
                AD_ZONE5 = self.cast_to_string(resultSQLFMaladieAdher[i][69])
                AD_ZONE6 = self.cast_to_string(resultSQLFMaladieAdher[i][70])
                AD_ZONE7 =  self.cast_to_string(resultSQLFMaladieAdher[i][71])
                AD_ZONE8 =  self.cast_to_string(resultSQLFMaladieAdher[i][72])
                AD_ZONE9 =  self.cast_to_string(resultSQLFMaladieAdher[i][73])
                AD_ZONE10 = self.cast_to_string(resultSQLFMaladieAdher[i][74])
                AD_ZONE11 =  self.cast_to_string(resultSQLFMaladieAdher[i][75])
                AD_ZONE12 =  self.cast_to_string(resultSQLFMaladieAdher[i][76])
                AD_ZONE13 = self.cast_to_string(resultSQLFMaladieAdher[i][77])
                AD_ZONE14 = self.cast_to_string(resultSQLFMaladieAdher[i][78])
                AD_ZONE15 = self.cast_to_string(resultSQLFMaladieAdher[i][79])
                AD_IDENT = resultSQLFMaladieAdher[i][80]
                
                ### Ecrire F_MALADIE_ADHER dans Odoo
                cursorPOSTGRESOdoo.execute(""" INSERT INTO f_maladie_adher (id,
                                                                            create_uid,
                                                                            create_date, 
                                                                            "AD_PTRBPASSIDENT",
                                                                            "AD_IDENT",
                                                                            "AD_PTRRIBIDENT",
                                                                            "AD_COMMENT",
                                                                            "AD_PTRSORID",
                                                                            "AD_NOMAPPEL",
                                                                            "AD_TELEPHONE",
                                                                            write_uid, 
                                                                            "AD_NOMDE2",
                                                                            "AD_TITRE",
                                                                            "AD_NOMDE1",
                                                                            "AD_SEXE",
                                                                            "AD_PTRBPPIDENT",
                                                                            "AD_DATNAISS",
                                                                            write_date,
                                                                            "AD_PTRBPAIDENT"
                                                            ) 
                                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) 
                                           """,(AD_IDENT,1,datetime.datetime.now(),AD_PTRBPASSIDENT,AD_IDENT,AD_PTRRIBIDENT,AD_COMMENT,AD_PTRSORID,
                                                AD_NOMAPPEL,AD_TELEPHONE,1,AD_NOMDE2,AD_TITRE,AD_NOMDE1,AD_SEXE,AD_PTRBPPIDENT,AD_DATNAISS,
                                                datetime.datetime.now(),AD_PTRBPAIDENT))
                
                #### LIRE f_maladie_ay_dr dans SQL Server
                cursorSQLServer.execute(""" SELECT    
                                                      "AY_PTRADID"
                                                      ,"AY_ORIGPTR"
                                                      ,"AY_PTRSORIDENT"
                                                      ,"AY_PTRBPPIDENT"
                                                      ,"AY_NOMAPPEL"
                                                      ,"AY_NOM"
                                                      ,"AY_PRENOM"
                                                      ,"AY_NUM_SS"
                                                      ,"AY_CLE_NUM_SS"
                                                      ,"AY_DATE_NAISS"
                                                      ,"AY_SEXE"
                                                      ,"AY_COMMENTAIRE"
                                                      ,"AY_NOM2"
                                                      ,"AY_INT_LOT_EXP"
                                                      ,"AY_INT_LOT_IMP"
                                                      ,"AY_DTCRE"
                                                      ,"AY_LASER"
                                                      ,"AY_DTMAJ"
                                                      ,"AY_REFECHO"
                                                      ,"AY_REGIME_SALARIE"
                                                      ,"AY_PTRBPASSIDENT"
                                                      ,"AY_NOEMIE"
                                                      ,"AY_TP_PHARMA"
                                                      ,"AY_REMB_SS"
                                                      ,"AY_TYPE_TAUX_SS"
                                                      ,"AY_DATEDEBUT"
                                                      ,"AY_DATEFIN"
                                                      ,"AY_SS"
                                                      ,"AY_PTRCONVID"
                                                      ,"AY_PTRCONVID_IJ"
                                                      ,"AY_CENTRE"
                                                      ,"AY_OPTPHARMA"
                                                      ,"AY_QUALITE"
                                                      ,"AY_TRANCHE_AGE"
                                                      ,"AY_CPAM"
                                                      ,"AY_ZONE1"
                                                      ,"AY_ZONE2"
                                                      ,"AY_ZONE3"
                                                      ,"AY_ZONE4"
                                                      ,"AY_ZONE5"
                                                      ,"AY_ZONE6"
                                                      ,"AY_ZONE7"
                                                      ,"AY_ZONE8"
                                                      ,"AY_ZONE9"
                                                      ,"AY_ZONE10"
                                                      ,"AY_OPTION_GTIE"
                                                      ,"AY_REGIME_GTIE"
                                                      ,"AY_PB_SANTE"
                                                      ,"AY_NO_ATTENTE"
                                                      ,"AY_MODEREGL"
                                                      ,"AY_IDENT",
                                                      2+2
                                              FROM F_MALADIE_AY_DR WHERE "AY_PTRADID" = %s""" % (AD_IDENT))
                resultSQLFMaladieAyDr = cursorSQLServer.fetchall() 
                       
                if resultSQLFMaladieAyDr:
                    for i in range(0,len(resultSQLFMaladieAyDr)):
                        AY_PTRADID = resultSQLFMaladieAyDr[i][0]       
                        AY_ORIGPTR = resultSQLFMaladieAyDr[i][1] 
                        AY_PTRSORIDENT = resultSQLFMaladieAyDr[i][2]
                        AY_PTRBPPIDENT = resultSQLFMaladieAyDr[i][3]
                        AY_NOMAPPEL = resultSQLFMaladieAyDr[i][4]
                        AY_NOM  = resultSQLFMaladieAyDr[i][5]
                        AY_PRENOM =  resultSQLFMaladieAyDr[i][6]
                        AY_NUM_SS =  resultSQLFMaladieAyDr[i][7]
                        AY_CLE_NUM_SS =  resultSQLFMaladieAyDr[i][8]
                        AY_DATE_NAISS = resultSQLFMaladieAyDr[i][9]
                        AY_SEXE =  resultSQLFMaladieAyDr[i][10]
                        AY_COMMENTAIRE = resultSQLFMaladieAyDr[i][11]
                        AY_NOM2 =  resultSQLFMaladieAyDr[i][12]
                        AY_INT_LOT_EXP =  resultSQLFMaladieAyDr[i][13]
                        AY_INT_LOT_IMP = resultSQLFMaladieAyDr[i][14]
                        AY_DTCRE = resultSQLFMaladieAyDr[i][15]
                        AY_LASER = resultSQLFMaladieAyDr[i][16]
                        AY_DTMAJ =  resultSQLFMaladieAyDr[i][17]
                        AY_REFECHO =  resultSQLFMaladieAyDr[i][18]
                        AY_REGIME_SALARIE = resultSQLFMaladieAyDr[i][19]
                        AY_PTRBPASSIDENT = resultSQLFMaladieAyDr[i][20]
                        AY_NOEMIE = resultSQLFMaladieAyDr[i][21]
                        AY_TP_PHARMA =  resultSQLFMaladieAyDr[i][22]
                        AY_REMB_SS = resultSQLFMaladieAyDr[i][23]
                        AY_TYPE_TAUX_SS = resultSQLFMaladieAyDr[i][24]
                        AY_DATEDEBUT = resultSQLFMaladieAyDr[i][25]
                        AY_DATEFIN =  resultSQLFMaladieAyDr[i][26]
                        AY_SS = resultSQLFMaladieAyDr[i][27]
                        AY_PTRCONVID = resultSQLFMaladieAyDr[i][28]
                        AY_PTRCONVID_IJ = resultSQLFMaladieAyDr[i][29]
                        AY_CENTRE = resultSQLFMaladieAyDr[i][30]
                        AY_OPTPHARMA = resultSQLFMaladieAyDr[i][31]
                        AY_QUALITE = resultSQLFMaladieAyDr[i][32]
                        AY_TRANCHE_AGE = resultSQLFMaladieAyDr[i][33]
                        AY_CPAM = resultSQLFMaladieAyDr[i][34]
                        AY_ZONE1 = resultSQLFMaladieAyDr[i][35]
                        AY_ZONE2 = resultSQLFMaladieAyDr[i][36]
                        AY_ZONE3 =  resultSQLFMaladieAyDr[i][37]
                        AY_ZONE4 = resultSQLFMaladieAyDr[i][38]
                        AY_ZONE5 = resultSQLFMaladieAyDr[i][39]
                        AY_ZONE6 = resultSQLFMaladieAyDr[i][40]
                        AY_ZONE7 = resultSQLFMaladieAyDr[i][41]
                        AY_ZONE8 = resultSQLFMaladieAyDr[i][42]
                        AY_ZONE9 = resultSQLFMaladieAyDr[i][43]
                        AY_ZONE10 = resultSQLFMaladieAyDr[i][44]
                        AY_OPTION_GTIE = resultSQLFMaladieAyDr[i][45]
                        AY_REGIME_GTIE = resultSQLFMaladieAyDr[i][46]
                        AY_PB_SANTE = resultSQLFMaladieAyDr[i][47]
                        AY_NO_ATTENTE = resultSQLFMaladieAyDr[i][48]
                        AY_MODEREGL = resultSQLFMaladieAyDr[i][49]
                        AY_IDENT = resultSQLFMaladieAyDr[i][50]                                          
                        ## Ecrire f_maladie_ay_dr  dans Odoo                        
                        cursorPOSTGRESOdoo.execute(""" INSERT INTO f_maladie_ay_dr (
                                                                    id,
                                                                    create_date,
                                                                    "AY_PTRSORIDENT",
                                                                    "AY_REMB_SS",
                                                                    "AY_REGIME_SALARIE",
                                                                    "AY_NOEMIE",
                                                                    "AY_LASER",
                                                                    write_uid,
                                                                    "AY_DTMAJ",
                                                                    "AY_DATE_NAISS",
                                                                    "AY_INT_LOT_IMP",
                                                                    "AY_NOM2",
                                                                    "AY_PTRBPASSIDENT",
                                                                    "AY_IDENT",
                                                                    "AY_NOM",
                                                                    "AY_PTRADID",
                                                                    "AY_NOMAPPEL",
                                                                    "AY_DTCRE", 
                                                                    "AY_DATEDEBUT",
                                                                    "AY_PRENOM",
                                                                    "AY_REFECHO",
                                                                    "AY_PTRCONVID",
                                                                    "AY_NUM_SS",
                                                                    create_uid,
                                                                    "AY_INT_LOT_EXP",
                                                                    "AY_TYPE_TAUX_SS",
                                                                    write_date,
                                                                    "AY_CLE_NUM_SS",
                                                                    "AY_DATEFIN",
                                                                    "AY_PTRBPPIDENT",
                                                                    "AY_ORIGPTR",
                                                                    "AY_TP_PHARMA",
                                                                    "AY_COMMENTAIRE",
                                                                    "AY_SEXE",
                                                                    "AY_PTRCONVID_IJ",
                                                                    "AY_SS")
                                                                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
                                                                        %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                                  """,(AY_IDENT,datetime.datetime.now(),AY_PTRSORIDENT,AY_REMB_SS,AY_REGIME_SALARIE,
                                                       AY_NOEMIE,AY_LASER,1,AY_DTMAJ,AY_DATE_NAISS,AY_INT_LOT_IMP,AY_NOM2,AY_PTRBPASSIDENT,AY_IDENT,
                                                       AY_NOM,AY_PTRADID,AY_NOMAPPEL,AY_DTCRE,AY_DATEDEBUT,AY_PRENOM,AY_REFECHO,AY_PTRCONVID,
                                                       AY_NUM_SS,1,AY_INT_LOT_EXP,AY_TYPE_TAUX_SS,datetime.datetime.now(),AY_CLE_NUM_SS,AY_DATEFIN,
                                                       AY_PTRBPPIDENT,AY_ORIGPTR,AY_TP_PHARMA,AY_COMMENTAIRE,AY_SEXE,AY_PTRCONVID_IJ,AY_SS));
                        
                        ## LIRE ET ECRIRE DANS F_GARANTIE_DYN
                        ## LIRE DANS F_GARANTIES_DYN ET INSERTION                                        
                        cursorSQLServer.execute(""" SELECT           "GAD_INT_LOT_IMP"
                                                                      ,"GAD_COEFTARIF"
                                                                      ,"GAD_VA_BRUTE"
                                                                      ,"GAD_LIMGAR_UNITE"
                                                                      ,"GAD_MOUVEMENT"
                                                                      ,"GAD_NB_AVENANT"
                                                                      ,"GAD_ZONE4"
                                                                      ,"GAD_ORIGPTR"
                                                                      ,"GAD_MT_ASSIETTE"
                                                                      ,"GAD_LIMGAR_DUREE"
                                                                      ,"GAD_CODE"
                                                                      ,"GAD_LIMGAR2_VAL"
                                                                      ,"GAD_ZONE1"
                                                                      ,"GAD_COEFCOM"
                                                                      ,"GAD_LIMGAR_VAL2"
                                                                      ,"GAD_DATE_FIN"
                                                                      ,"GAD_DTCRE"
                                                                      ,"GAD_ZONE5"
                                                                      ,"GAD_DTMAJ"
                                                                      ,"GAD_SERVICES"
                                                                      ,"GAD_CODE_FISCAL"
                                                                      ,"GAD_IDENT"
                                                                      ,"GAD_REVISABLE"
                                                                      ,"GAD_FRAN_LIM_UN"
                                                                      ,"GAD_CODECOMPAGNIE"
                                                                      ,"GAD_TAUX_COM"
                                                                      ,"GAD_PTREMPID"
                                                                      ,"GAD_LIMGAR_LIBE"
                                                                      ,"GAD_PRMPAYTYP"
                                                                      ,"GAD_DATE_DEBUT"
                                                                      ,"GAD_SOUSCRIPTION"
                                                                      ,"GAD_FRAN_MIN"
                                                                      ,"GAD_FRAN_MAX"
                                                                      ,"GAD_LIMGAR2_UNITE"
                                                                      ,"GAD_VA_MINI"
                                                                      ,"GAD_TYPE_REVISAB"
                                                                      ,"GAD_INT_LOT_EXP"
                                                                      ,"GAD_PTRSORID"
                                                                      ,"GAD_PTRAYID"
                                                                      ,"GAD_INDEXE"
                                                                      ,"GAD_TAUX1"
                                                                      ,"GAD_TAUX3"
                                                                      ,"GAD_TAUX2"
                                                                      ,"GAD_TAXES"
                                                                      ,"GAD_LIBELLE"
                                                                      ,"GAD_SEQUENTIEL"
                                                                      ,"GAD_ZONE6"
                                                                      ,"GAD_CAPITAL"
                                                                      ,"GAD_FRAN_OPTION"
                                                                      ,"GAD_PRIME_NETTE" 
                                                                      ,"GAD_NB_TERME"
                                                                      ,"GAD_FRANCHISE"
                                                                      ,"GAD_LIMGAR_VAL"
                                                                      ,"GAD_COMMENT"
                                                                      ,"GAD_REFECHO"
                                                                      ,"GAD_FRAN_UNITE"
                                                                      ,"GAD_LIMGAR2_LIBE"
                                                                      ,"GAD_ZONE3"
                                                                      ,"GAD_INDICE"
                                                                      ,"GAD_POPTR"
                                                                      ,"GAD_ZONE2"
                                                                      ,"GAD_LIMGAR_VAL3"
                                                                      ,"GAD_OPTION"                                                                      
                                                                      FROM F_GARANTIE_DYN
                                                                      WHERE GAD_PTRAYID = %s """ % (AY_IDENT))
                        
                        resultsSQLFGarantiedyn = cursorSQLServer.fetchall()            
                        if resultsSQLFGarantiedyn:                                            
                            for i in range(0,len(resultsSQLFGarantiedyn)):                                                                                               
                                GAD_PRIME_NETTE = self.none_value(resultsSQLFGarantiedyn[i][49])
                                GAD_CODE_FISCAL = self.cast_opt_string(resultsSQLFGarantiedyn[i][20])
                                GAD_SOUSCRIPTION =self.cast_opt_string(resultsSQLFGarantiedyn[i][30])
                                GAD_CODE = self.cast_opt_string(resultsSQLFGarantiedyn[i][10])
                                GAD_PTRSORID = self.none_value(resultsSQLFGarantiedyn[i][37])
                                GAD_TAXES = self.none_value(resultsSQLFGarantiedyn[i][43])
                                GAD_IDENT = self.none_value(resultsSQLFGarantiedyn[i][21])
                                name_gad = self.none_value(GAD_CODE)
                                GAD_PTRAYID = self.none_value(resultsSQLFGarantiedyn[i][38])
                                
                                cursorPOSTGRESOdoo.execute(""" INSERT INTO f_garantie_dyn ( id,
                                                                                            create_uid,
                                                                                            create_date, 
                                                                                            name, 
                                                                                            "GAD_PRIME_NETTE" ,
                                                                                            "GAD_CODE_FISCAL", 
                                                                                            "GAD_SOUSCRIPTION", 
                                                                                            "GAD_CODE" ,
                                                                                            "GAD_PTRSORID" ,
                                                                                            "GAD_TAXES" ,
                                                                                            write_date, 
                                                                                            write_uid,
                                                                                            "GAD_PTRAYID"
                                                                                           )
                                                                VALUES (%s,%s,'%s',%s,%s,%s,%s,%s,%s,%s,'%s',%s,%s) """
                                                                % (GAD_IDENT,1,datetime.datetime.now(),name_gad,GAD_PRIME_NETTE,GAD_CODE_FISCAL,
                                                                   GAD_SOUSCRIPTION,GAD_CODE,SOR_IDENT,GAD_TAXES,datetime.datetime.now(),1,GAD_PTRAYID));
        print "ayant droit inserted"                                                                                                                      
        #######################################################################################################################
                        
    def f_prime_prime_ligne(self,cursorSQLServer,cursorPOSTGRESOdoo,id_version_police,id_prime):
        #### LIRE F_PRIME DANS SQL Server
        cursorSQLServer.execute(""" SELECT     "PRM_PTRAPPIDENT"
                                              ,"PRM_ORDRE_LC"
                                              ,"PRM_PTRTEMP"
                                              ,"PRM_AVENANTNUM"
                                              ,"PRM_EDITEE"
                                              ,"PRM_ETABLISSEMENT"
                                              ,"PRM_TAXFRACIEMT"
                                              ,"PRM_ECART_ARRONDI"
                                              ,"PRM_ENCPTRAUXIDE"
                                              ,"PRM_TAXFRACOUMT"
                                              ,"PRM_PIECE"
                                              ,"PRM_DATECHEANCE"
                                              ,"PRM_REJET_DATE"
                                              ,"PRM_PRNCNMT"
                                              ,"PRM_NATURE"
                                              ,"PRM_PTRPRAIDENT"
                                              ,"PRM_SEQUENTIEL"
                                              ,"PRM_COAREP_PRM"
                                              ,"PRM_JUSTIFS"
                                              ,"PRM_ENCSOLDE"
                                              ,"PRM_ENCAUXCOMPTE"
                                              ,"PRM_DATE"
                                              ,"PRM_ENCMODE"
                                              ,"PRM_TEXTE"
                                              ,"PRM_INT_LOT_IMP"
                                              ,"PRM_PTRPOLIDENT"
                                              ,"PRM_RTNTIEMT"
                                              ,"PRM_COMDE_TOT"
                                              ,"PRM_PTRASSIDENT"
                                              ,"PRM_REFECHO"
                                              ,"PRM_LIB01"
                                              ,"PRM_TAXCIEMT"
                                              ,"PRM_LIB06"
                                              ,"PRM_ENCPAYTYP"
                                              ,"PRM_DATDEBPER"
                                              ,"PRM_COMINTMT"
                                              ,"PRM_ENCDATPRV"
                                              ,"PRM_MOTIF_ANNUL"
                                              ,"PRM_ENCECART"
                                              ,"PRM_TAXINTMT"
                                              ,"PRM_DEST_RISTOURNE"
                                              ,"PRM_ENCMODPRV"
                                              ,"PRM_PTRINTIDENT"
                                              ,"PRM_REFEXTERNE"
                                              ,"PRM_DATCOMPTA"
                                              ,"PRM_BORDEREAU"
                                              ,"PRM_FRAAPPTX"
                                              ,"PRM_STOP_PAIEMENT"
                                              ,"PRM_COMNOUSMT"
                                              ,"PRM_REJET_MOTIF"
                                              ,"PRM_ETAMOTIF"
                                              ,"PRM_ENCECARTEURO"
                                              ,"PRM_REJET_NB"
                                              ,"PRM_ENCCUMENC"
                                              ,"PRM_PTRVERIDENT"
                                              ,"PRM_EXERCICE"
                                              ,"PRM_PTRCLIIDENT"
                                              ,"PRM_COMAPPMT"
                                              ,"PRM_SOCIETE"
                                              ,"PRM_PTRCIEIDENT"
                                              ,"PRM_TAXATTMT"
                                              ,"PRM_COMMENT"
                                              ,"PRM_PTRECNU"
                                              ,"PRM_IDENT"
                                              ,"PRM_FRACOUMT"
                                              ,"PRM_COMINTCP_MT"
                                              ,"PRM_ENCTOTALDU"
                                              ,"PRM_TAXASSMT"
                                              ,"PRM_DATFINPER"
                                              ,"PRM_SERVICES"
                                              ,"PRM_FRACIEMT"
                                              ,"PRM_ANNEXE"
                                              ,"PRM_TVA_CLIENT"
                                              ,"PRM_ETADATE"
                                              ,"PRM_POLL_TTC"
                                              ,"PRM_PTRVANIDENT"
                                              ,"PRM_ETACODE"
                                              ,"PRM_TRANSACTION"
                                              ,"PRM_DATVALID"
                                              ,"PRM_FRACTION"
                                              ,"PRM_PTRANNIDENT"
                                              ,"PRM_TAXCLIMT"
                                              ,"PRM_TTCCLIENT"
                                              ,"PRM_NUMERO"
                                              ,"PRM_COASS_GESTIO"
                                              ,"PRM_PRNTOTMT"
                                              ,"PRM_TAXTOTMT"
                                              ,"PRM_TYPE"
                                              ,"PRM_LIB03"
                                              ,"PRM_JOURNAL"
                                              ,"PRM_COMDEDUITE"
                                              ,"PRM_LIB04"
                                              ,"PRM_PTRTEMP2"
                                              ,"PRM_ENCDATE"
                                              ,"PRM_LIB05"
                                              ,"PRM_DATE_ORIG"
                                              ,"PRM_TAXEPRMT"
                                              ,"PRM_FRABCRTX"
                                              ,"PRM_INT_LOT_EXP"
                                              ,"PRM_MT_REJET"
                                              ,"PRM_NATURE_EMIS"
                                              ,"PRM_LIB02"
                                              ,"PRM_POLNUMERO"
                                              ,"PRM_FLAG"
                                              ,"PRM_DATE_ENVOI"
                                              ,"PRM_DATE_COMPTA"
                                          FROM F_PRIME  WHERE "PRM_IDENT" = %s """ % (id_prime))
        
        resultsSQLFPrime = cursorSQLServer.fetchall()
        if resultsSQLFPrime:
            for i in range(0,len(resultsSQLFPrime)):
                PRM_PTRAPPIDENT =  resultsSQLFPrime[i][0]
                PRM_ORDRE_LC = resultsSQLFPrime[i][1]
                PRM_PTRTEMP = resultsSQLFPrime[i][2]
                PRM_AVENANTNUM = resultsSQLFPrime[i][3]
                PRM_EDITEE = resultsSQLFPrime[i][4]
                PRM_ETABLISSEMENT = resultsSQLFPrime[i][5]
                PRM_TAXFRACIEMT =  resultsSQLFPrime[i][6]
                PRM_ECART_ARRONDI =resultsSQLFPrime[i][7]
                PRM_ENCPTRAUXIDE = resultsSQLFPrime[i][8]
                PRM_TAXFRACOUMT = resultsSQLFPrime[i][9]
                PRM_PIECE = resultsSQLFPrime[i][10]
                PRM_DATECHEANCE = resultsSQLFPrime[i][11]
                PRM_REJET_DATE = resultsSQLFPrime[i][12]
                PRM_PRNCNMT = resultsSQLFPrime[i][13]
                PRM_NATURE = resultsSQLFPrime[i][14]
                PRM_PTRPRAIDENT = resultsSQLFPrime[i][15]
                PRM_SEQUENTIEL =resultsSQLFPrime[i][16]
                PRM_COAREP_PRM =resultsSQLFPrime[i][17]
                PRM_JUSTIFS = resultsSQLFPrime[i][18] 
                PRM_ENCSOLDE = resultsSQLFPrime[i][19]
                PRM_ENCAUXCOMPTE = resultsSQLFPrime[i][20]
                PRM_DATE = resultsSQLFPrime[i][21]
                PRM_ENCMODE = resultsSQLFPrime[i][22]
                PRM_TEXTE = resultsSQLFPrime[i][23]
                PRM_INT_LOT_IMP = resultsSQLFPrime[i][24]
                PRM_PTRPOLIDENT = resultsSQLFPrime[i][25]
                PRM_RTNTIEMT =resultsSQLFPrime[i][26]
                PRM_COMDE_TOT = resultsSQLFPrime[i][27]
                PRM_PTRASSIDENT = resultsSQLFPrime[i][28]
                PRM_REFECHO = resultsSQLFPrime[i][29]
                PRM_LIB01 = resultsSQLFPrime[i][30]
                PRM_TAXCIEMT = resultsSQLFPrime[i][31]
                PRM_LIB06 = resultsSQLFPrime[i][32]
                PRM_ENCPAYTYP = resultsSQLFPrime[i][33]
                PRM_DATDEBPER = resultsSQLFPrime[i][34]
                PRM_COMINTMT = resultsSQLFPrime[i][35]
                PRM_ENCDATPRV = resultsSQLFPrime[i][36]
                PRM_MOTIF_ANNUL = resultsSQLFPrime[i][37]
                PRM_ENCECART = resultsSQLFPrime[i][38]
                PRM_TAXINTMT = resultsSQLFPrime[i][39]
                PRM_DEST_RISTOURNE = resultsSQLFPrime[i][40]
                PRM_ENCMODPRV = resultsSQLFPrime[i][41]
                PRM_PTRINTIDENT = resultsSQLFPrime[i][42]
                PRM_REFEXTERNE = resultsSQLFPrime[i][43]
                PRM_DATCOMPTA = resultsSQLFPrime[i][44]
                PRM_BORDEREAU = resultsSQLFPrime[i][45]
                PRM_FRAAPPTX = resultsSQLFPrime[i][46]
                PRM_STOP_PAIEMENT = resultsSQLFPrime[i][47]
                PRM_COMNOUSMT = resultsSQLFPrime[i][48]
                PRM_REJET_MOTIF = resultsSQLFPrime[i][49]
                PRM_ETAMOTIF = resultsSQLFPrime[i][50]
                PRM_ENCECARTEURO = resultsSQLFPrime[i][51]
                PRM_REJET_NB = resultsSQLFPrime[i][52]
                PRM_ENCCUMENC = resultsSQLFPrime[i][53]
                PRM_PTRVERIDENT = resultsSQLFPrime[i][54]
                PRM_EXERCICE = resultsSQLFPrime[i][55]
                PRM_PTRCLIIDENT = resultsSQLFPrime[i][56]
                PRM_COMAPPMT = resultsSQLFPrime[i][57]
                PRM_SOCIETE = resultsSQLFPrime[i][58]
                PRM_PTRCIEIDENT = resultsSQLFPrime[i][59]
                PRM_TAXATTMT = resultsSQLFPrime[i][60]
                PRM_COMMENT = resultsSQLFPrime[i][61]
                PRM_PTRECNU = resultsSQLFPrime[i][62]
                PRM_IDENT = resultsSQLFPrime[i][63]
                PRM_FRACOUMT = resultsSQLFPrime[i][64]
                PRM_COMINTCP_MT = resultsSQLFPrime[i][65]
                PRM_ENCTOTALDU = resultsSQLFPrime[i][66]
                PRM_TAXASSMT = resultsSQLFPrime[i][67]
                PRM_DATFINPER = resultsSQLFPrime[i][68]
                PRM_SERVICES = resultsSQLFPrime[i][69]
                PRM_FRACIEMT = resultsSQLFPrime[i][70]
                PRM_ANNEXE = resultsSQLFPrime[i][71]
                PRM_TVA_CLIENT =  resultsSQLFPrime[i][72]
                PRM_ETADATE = resultsSQLFPrime[i][73]
                PRM_POLL_TTC = resultsSQLFPrime[i][74]
                PRM_PTRVANIDENT = resultsSQLFPrime[i][75]
                PRM_ETACODE = resultsSQLFPrime[i][76] 
                PRM_TRANSACTION = resultsSQLFPrime[i][77]
                PRM_DATVALID = resultsSQLFPrime[i][78]
                PRM_FRACTION = resultsSQLFPrime[i][79]
                PRM_PTRANNIDENT = resultsSQLFPrime[i][80]
                PRM_TAXCLIMT = resultsSQLFPrime[i][81]
                PRM_TTCCLIENT = resultsSQLFPrime[i][82]
                PRM_NUMERO = resultsSQLFPrime[i][83]
                PRM_COASS_GESTIO = resultsSQLFPrime[i][84]
                PRM_PRNTOTMT = resultsSQLFPrime[i][85]
                PRM_TAXTOTMT = resultsSQLFPrime[i][86]
                PRM_TYPE = resultsSQLFPrime[i][87]
                PRM_LIB03 = resultsSQLFPrime[i][88]
                PRM_JOURNAL = resultsSQLFPrime[i][89]
                PRM_COMDEDUITE = resultsSQLFPrime[i][90]
                PRM_LIB04 = resultsSQLFPrime[i][91]
                PRM_PTRTEMP2 = resultsSQLFPrime[i][92]
                PRM_ENCDATE = resultsSQLFPrime[i][93]
                PRM_LIB05 = resultsSQLFPrime[i][94]
                PRM_DATE_ORIG = resultsSQLFPrime[i][95]
                PRM_TAXEPRMT = resultsSQLFPrime[i][96]
                PRM_FRABCRTX = resultsSQLFPrime[i][97]
                PRM_INT_LOT_EXP = resultsSQLFPrime[i][98]
                PRM_MT_REJET = resultsSQLFPrime[i][99]
                PRM_NATURE_EMIS = resultsSQLFPrime[i][100]
                PRM_LIB02 = resultsSQLFPrime[i][101]
                PRM_POLNUMERO = resultsSQLFPrime[i][102]
                PRM_FLAG = resultsSQLFPrime[i][103]
                PRM_DATE_ENVOI = resultsSQLFPrime[i][104]
                PRM_DATE_COMPTA = resultsSQLFPrime[i][105]              
                
                name_prime = 'PRIME ' + PRM_POLNUMERO +' ' +  PRM_NATURE        
                ### ECRIRE F_PRIME DANS ODOO
                cursorPOSTGRESOdoo.execute(""" INSERT INTO f_prime    (id,
                                                                      create_uid,
                                                                      "PRM_DATE",
                                                                      "PRM_NATURE",
                                                                      create_date,
                                                                      name,
                                                                      "PRM_TEXTE",
                                                                      write_uid,
                                                                      "PRM_PRNTOTMT",
                                                                      "PRM_ENCSOLDE",
                                                                      "PRM_DATDEBPER",
                                                                      write_date,
                                                                      "PRM_TTCCLIENT",
                                                                      "PRM_DATFINPER",
                                                                      "PRM_TAXTOTMT",
                                                                      "PRM_POLNUMERO")
                                                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                              """,(PRM_IDENT,1,PRM_DATE,PRM_NATURE,datetime.datetime.now(),name_prime,PRM_TEXTE,1,PRM_PRNTOTMT,
                                                   PRM_ENCSOLDE,PRM_DATDEBPER,datetime.datetime.now(),PRM_TTCCLIENT,PRM_DATFINPER,
                                                   PRM_TAXTOTMT,PRM_POLNUMERO))
                
                ### LIRE DANS F_PRIME_LIGNE de SQL Server
                cursorSQLServer.execute("""         SELECT    "LPR_REV_LIB02"
                                                              ,"LPR_ECART_EURO"
                                                              ,"LPR_COMINTMT"
                                                              ,"LPR_TVA_TERRFISCAL"
                                                              ,"LPR_COMNOUSMT"
                                                              ,"LPR_COMAPPRG"
                                                              ,"LPR_TVA_MT_APP"
                                                              ,"LPR_APERITEUR"
                                                              ,"LPR_HONINTRG"
                                                              ,"LPR_PRIMENETTE"
                                                              ,"LPR_REVTIETYP"
                                                              ,"LPR_COMAPPCR"
                                                              ,"LPR_REGREVCR"
                                                              ,"LPR_FRABCR"
                                                              ,"LPR_REV_LIB01"
                                                              ,"LPR_CODTECH"
                                                              ,"LPR_COMAPPTX"
                                                              ,"LPR_TVA_TAUX"
                                                              ,"LPR_TVA_MT_COUR"
                                                              ,"LPR_MODE_REVERS"
                                                              ,"LPR_COMINTRG"
                                                              ,"LPR_TAXASSMT"
                                                              ,"LPR_REV_LIB03"
                                                              ,"LPR_TAXCOU"
                                                              ,"LPR_PTRAUXIDENT"
                                                              ,"LPR_REVFAIT"
                                                              ,"LPR_COUPOLRG"
                                                              ,"LPR_SERVICES"
                                                              ,"LPR_NUMPOLCIE"
                                                              ,"LPR_COMNOUSTX"
                                                              ,"LPR_COMINTTX"
                                                              ,"LPR_TAXATT"
                                                              ,"LPR_IDENT"
                                                              ,"LPR_INT_LOT_IMP"
                                                              ,"LPR_SEQUENTIEL"
                                                              ,"LPR_REVTYPE"
                                                              ,"LPR_COMAPPMT"
                                                              ,"LPR_REVTOTAL"
                                                              ,"LPR_TAXEPRMT"
                                                              ,"LPR_PTRBRVID"
                                                              ,"LPR_REVRESTE"
                                                              ,"LPR_FRACIE"
                                                              ,"LPR_COMNOUSCR"
                                                              ,"LPR_POLL_CODEGAR"
                                                              ,"LPR_FRACOU"
                                                              ,"LPR_REFECHO"
                                                              ,"LPR_TVA_MT_NOUS"
                                                              ,"LPR_TAXASSTF"
                                                              ,"LPR_PTRPRMIDENT"
                                                              ,"LPR_TVA_CODE"
                                                              ,"LPR_COMINTCR"
                                                              ,"LPR_TVA_MT_INT"
                                                              ,"LPR_COMNOUSRG"
                                                              ,"LPR_ASSCODCPT"
                                                              ,"LPR_COMAPEMT"
                                                              ,"LPR_REFEXTERNE"
                                                              ,"LPR_RTNTIEMT"
                                                              ,"LPR_TAXASSTX"
                                                              ,"LPR_TVA_MT_CIE"
                                                              ,"LPR_INT_LOT_EXP"
                                                              ,"LPR_TAXASSCF"
                                                              ,"LPR_REVDATPREV"
                                                              
                                                          FROM F_PRIME_LIGNE  WHERE "LPR_PTRPRMIDENT" = %s """ % (PRM_IDENT))
                resultsSQLFPrimeLigne = cursorSQLServer.fetchall()
                if resultsSQLFPrimeLigne:
                    for i in range(0,len(resultsSQLFPrimeLigne)):                       
                        LPR_REV_LIB02 = resultsSQLFPrimeLigne[i][0]
                        LPR_ECART_EURO =resultsSQLFPrimeLigne[i][1]
                        LPR_COMINTMT = resultsSQLFPrimeLigne[i][2]
                        LPR_TVA_TERRFISCAL = resultsSQLFPrimeLigne[i][3]
                        LPR_COMNOUSMT = resultsSQLFPrimeLigne[i][4]
                        LPR_COMAPPRG = resultsSQLFPrimeLigne[i][5]
                        LPR_TVA_MT_APP = resultsSQLFPrimeLigne[i][6]
                        LPR_APERITEUR = resultsSQLFPrimeLigne[i][7]
                        LPR_HONINTRG  = resultsSQLFPrimeLigne[i][8]
                        LPR_PRIMENETTE = resultsSQLFPrimeLigne[i][9]                      
                        LPR_REVTIETYP = resultsSQLFPrimeLigne[i][10]                        
                        LPR_COMAPPCR = resultsSQLFPrimeLigne[i][11]
                        LPR_REGREVCR = resultsSQLFPrimeLigne[i][12]
                        LPR_FRABCR = resultsSQLFPrimeLigne[i][13]
                        LPR_REV_LIB01 = resultsSQLFPrimeLigne[i][14]
                        LPR_CODTECH = resultsSQLFPrimeLigne[i][15]
                        LPR_COMAPPTX = resultsSQLFPrimeLigne[i][16]
                        LPR_TVA_TAUX = resultsSQLFPrimeLigne[i][17]
                        LPR_TVA_MT_COUR = resultsSQLFPrimeLigne[i][18]
                        LPR_MODE_REVERS = resultsSQLFPrimeLigne[i][19]
                        LPR_COMINTRG = resultsSQLFPrimeLigne[i][20]
                        LPR_TAXASSMT = resultsSQLFPrimeLigne[i][21]
                        LPR_REV_LIB03 = resultsSQLFPrimeLigne[i][22]
                        LPR_TAXCOU = resultsSQLFPrimeLigne[i][23]
                        LPR_PTRAUXIDENT = resultsSQLFPrimeLigne[i][24]
                        LPR_REVFAIT = resultsSQLFPrimeLigne[i][25]
                        LPR_COUPOLRG = resultsSQLFPrimeLigne[i][26]
                        LPR_SERVICES = resultsSQLFPrimeLigne[i][27]
                        LPR_NUMPOLCIE = resultsSQLFPrimeLigne[i][28]
                        LPR_COMNOUSTX = resultsSQLFPrimeLigne[i][29]
                        LPR_COMINTTX = resultsSQLFPrimeLigne[i][30]
                        LPR_TAXATT = resultsSQLFPrimeLigne[i][31]
                        LPR_IDENT = resultsSQLFPrimeLigne[i][32]
                        LPR_INT_LOT_IMP = resultsSQLFPrimeLigne[i][33]
                        LPR_SEQUENTIEL = resultsSQLFPrimeLigne[i][34]
                        LPR_REVTYPE = resultsSQLFPrimeLigne[i][35]
                        LPR_COMAPPMT = resultsSQLFPrimeLigne[i][36]
                        LPR_REVTOTAL = resultsSQLFPrimeLigne[i][37]
                        LPR_TAXEPRMT = resultsSQLFPrimeLigne[i][38]
                        LPR_PTRBRVID = resultsSQLFPrimeLigne[i][39]
                        LPR_REVRESTE = resultsSQLFPrimeLigne[i][40]
                        LPR_FRACIE = resultsSQLFPrimeLigne[i][41]
                        LPR_COMNOUSCR = resultsSQLFPrimeLigne[i][42]
                        LPR_POLL_CODEGAR = resultsSQLFPrimeLigne[i][43]
                        LPR_FRACOU = resultsSQLFPrimeLigne[i][44]
                        LPR_REFECHO = resultsSQLFPrimeLigne[i][45]
                        LPR_TVA_MT_NOUS =resultsSQLFPrimeLigne[i][46]
                        LPR_TAXASSTF = resultsSQLFPrimeLigne[i][47]
                        LPR_PTRPRMIDENT = resultsSQLFPrimeLigne[i][48]
                        LPR_TVA_CODE = resultsSQLFPrimeLigne[i][49]
                        LPR_COMINTCR = resultsSQLFPrimeLigne[i][50]
                        LPR_TVA_MT_INT = resultsSQLFPrimeLigne[i][51]
                        LPR_COMNOUSRG = resultsSQLFPrimeLigne[i][52]
                        LPR_ASSCODCPT = resultsSQLFPrimeLigne[i][53]
                        LPR_COMAPEMT = resultsSQLFPrimeLigne[i][54]
                        LPR_REFEXTERNE = resultsSQLFPrimeLigne[i][55]
                        LPR_RTNTIEMT = resultsSQLFPrimeLigne[i][56]
                        LPR_TAXASSTX = resultsSQLFPrimeLigne[i][57]
                        LPR_TVA_MT_CIE = resultsSQLFPrimeLigne[i][58]
                        LPR_INT_LOT_EXP = resultsSQLFPrimeLigne[i][59]
                        LPR_TAXASSCF = resultsSQLFPrimeLigne[i][60]
                        LPR_REVDATPREV = resultsSQLFPrimeLigne[i][61]
                        
                        
                        ### ECRIRE F_PRIME_LIGNE DANS ODOO
                        cursorPOSTGRESOdoo.execute(""" INSERT INTO f_prime_ligne (    id,
                                                                        create_uid,
                                                                        "LPR_COMAPPCR",
                                                                        "LPR_REGREVCR",
                                                                        create_date,
                                                                        "LPR_REVTYP",
                                                                        "LPR_REVRESTE",
                                                                        "LPR_ASSCODCPT",
                                                                        "LPR_TAXASSTX",
                                                                        "LPR_REVTOTAL",
                                                                        write_uid,
                                                                        "LPR_REVTIETYP",
                                                                        "LPR_PTRPRMIDENT",
                                                                        "LPR_FRACIE",
                                                                        write_date,
                                                                        "LPR_PRIMENETTE",
                                                                        "LPR_TAXASSMT") 
                                                        
                                                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                                                     """, (LPR_IDENT,1,LPR_COMAPPCR,LPR_REGREVCR,datetime.datetime.now(),LPR_REVTYPE,LPR_REVRESTE,
                                                           LPR_ASSCODCPT,LPR_TAXASSTX,LPR_REVTOTAL,1,LPR_REVTIETYP,LPR_PTRPRMIDENT,LPR_FRACIE,datetime.datetime.now(),
                                                           LPR_PRIMENETTE,LPR_TAXASSMT))
                        
                        
                                                              
                    
                    
                
                
                
                
            
        
        
        
        
        
        