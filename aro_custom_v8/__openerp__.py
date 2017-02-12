#-*- coding:utf-8 -*-

{
    'name': 'ARO Assurance Customisations',
    'version': '1.0',
    'author': 'OpenMind Ltd',
    'description': 'Module pour les besoins de ARO',
    'category': 'Departement',
    'website': 'http://www.omerp.net',
    'depends': ['base',
                'account',
                'hr', 'hr_holidays',
                'product'],
    'data': [
        #'views/hr_employee_view.xml',
        #'views/hr_view.xml',
        'views/res_partner.xml',
        #'views/aro_payment.xml',
        #'views/aro_type_contrat_view.xml',
        'views/account_move_line_view.xml',
        'views/product_category_view.xml',
        'views/product_template_view.xml',
        'views/res_apporteur_views.xml',
    ],
}
