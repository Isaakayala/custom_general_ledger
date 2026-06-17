{
    'name': 'Custom General Ledger',
    'summary': 'Custom General Legder for Odoo V.19',
    'description': 'General ledger with accumulated balance and groupings by accounting account.',
    'author': 'Isaac Ayala',
    'version': '19.0.1.0.0',
    'category': 'Accounting',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/general_ledger_views.xml',
    ],
    'images': ['static/description/banner.png'],
     
    'installable': True,
    
   
}
