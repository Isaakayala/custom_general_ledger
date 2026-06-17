from odoo import fields, models, tools, api


class CustomGeneralLedger(models.Model):
    _name = "custom.general.ledger"
    _description = "Custom General Ledger"
    _auto = False
    _rec_name = "move_name"
    _order = "account_id, date, id"

    date = fields.Date(string="Fecha",readonly=True,)

    move_id = fields.Many2one(
        "account.move",
        string="Asiento",
        readonly=True,
    )

    move_name = fields.Char(
        string="Número Asiento",
        readonly=True,
    )

    account_id = fields.Many2one(
        "account.account",
        string="Cuenta",
        readonly=True,
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Contacto",
        readonly=True,
    )

    journal_id = fields.Many2one(
        "account.journal",
        string="Diario",
        readonly=True,
    )

    ref = fields.Char(
        string="Referencia",
        readonly=True,
    )

    debit = fields.Monetary(
        string="Débito",
        currency_field="company_currency_id",
        readonly=True,
    )

    credit = fields.Monetary(
        string="Crédito",
        currency_field="company_currency_id",
        readonly=True,
    )

    balance = fields.Monetary(
        string="Balance",
        currency_field="company_currency_id",
        readonly=True,
    )

    company_currency_id = fields.Many2one(
        "res.currency",
        readonly=True,
    )

    def action_open_move(self):
        """Abrir el asiento contable desde el reporte"""
        self.ensure_one()
        if self.move_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Asiento Contable',
                'res_model': 'account.move',
                'res_id': self.move_id.id,
                'view_mode': 'form',
                'view_id': self.env.ref('account.view_move_form').id,
                'target': 'current',
            }
        return {'type': 'ir.actions.act_window_close'}

    def init(self):
        tools.drop_view_if_exists(
            self.env.cr,
            self._table
        )

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW custom_general_ledger AS (

                SELECT
                    aml.id,
                    aml.date,

                    am.id AS move_id,
                    am.name AS move_name,

                    aml.account_id,
                    aml.partner_id,
                    aml.journal_id,
                    aml.ref,

                    aml.debit,
                    aml.credit,

                    SUM(
                        aml.debit - aml.credit
                    ) OVER (
                        PARTITION BY aml.account_id
                        ORDER BY aml.date, aml.id
                    ) AS balance,

                    c.currency_id AS company_currency_id

                FROM account_move_line aml

                INNER JOIN account_move am
                    ON am.id = aml.move_id

                INNER JOIN res_company c
                    ON c.id = aml.company_id

                WHERE aml.parent_state = 'posted'

            )
        """)