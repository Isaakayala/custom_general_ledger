from odoo import http
from odoo.http import request

class CustomGeneralLedgerController(http.Controller):

    @http.route('/LibroMayor', auth='user')
    def libro_mayor(self, **kw):
        action = request.env.ref(
            'custom_general_ledger.action_custom_general_ledger'
        ).id

        return request.redirect(f'/odoo/action-{action}')
    
