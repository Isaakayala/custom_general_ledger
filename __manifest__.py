{
    'name': 'Custom General Ledger & Financial Reports',
    'summary': 'Custom General Ledger and Financial Reports for Odoo V.19',
    'description': 'General ledger with accumulated balance and dynamic financial reports including Income Statement, Balance Sheet, and Cash Flow.',
    'author': 'Isaac Ayala',
    'version': '19.0.2.0.0',
    'category': 'Accounting',
    'license': 'LGPL-3',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/general_ledger_views.xml',
        'views/financial_reports_views.xml',
    ],
    'images': ['static/description/banner.png'],
     
    'installable': True,
    'auto_install': False,
}
