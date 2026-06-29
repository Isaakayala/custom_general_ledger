from odoo import fields, models, tools, api
from datetime import datetime, timedelta
from decimal import Decimal


class IncomeStatement(models.Model):
    """Estado de Resultados - Income Statement"""
    _name = "financial.income.statement"
    _description = "Income Statement / Estado de Resultados"
    _auto = False
    _rec_name = "name"

    name = fields.Char(string="Descripción", readonly=True)
    date_start = fields.Date(string="Fecha Inicio", readonly=True)
    date_end = fields.Date(string="Fecha Fin", readonly=True)
    company_id = fields.Many2one("res.company", string="Compañía", readonly=True)
    
    # Income Section
    revenue = fields.Monetary(string="Ingresos", readonly=True, currency_field="currency_id")
    cost_of_sales = fields.Monetary(string="Costo de Ventas", readonly=True, currency_field="currency_id")
    gross_profit = fields.Monetary(string="Ganancia Bruta", readonly=True, currency_field="currency_id")
    
    # Operating Expenses
    operating_expenses = fields.Monetary(string="Gastos Operativos", readonly=True, currency_field="currency_id")
    operating_income = fields.Monetary(string="Ingreso Operativo", readonly=True, currency_field="currency_id")
    
    # Other Income/Expenses
    other_income = fields.Monetary(string="Otros Ingresos", readonly=True, currency_field="currency_id")
    other_expenses = fields.Monetary(string="Otros Gastos", readonly=True, currency_field="currency_id")
    
    # Net Income
    net_income = fields.Monetary(string="Ingreso Neto", readonly=True, currency_field="currency_id")
    
    currency_id = fields.Many2one("res.currency", string="Moneda", readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW financial_income_statement AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY c.id) as id,
                    'Estado de Resultados - ' || COALESCE(c.name, 'Compañía') as name,
                    CURRENT_DATE as date_start,
                    CURRENT_DATE as date_end,
                    c.id as company_id,
                    c.currency_id,
                    
                    -- Ingresos
                    COALESCE((
                        SELECT SUM(aml.credit - aml.debit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        JOIN account_move am ON am.id = aml.move_id
                        WHERE aa.internal_type = 'income'
                        AND am.state = 'posted'
                        AND aml.company_id = c.id
                    ), 0) as revenue,
                    
                    -- Costo de Ventas
                    COALESCE((
                        SELECT SUM(aml.debit - aml.credit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        JOIN account_move am ON am.id = aml.move_id
                        WHERE aa.internal_type = 'expense'
                        AND aa.code LIKE '5%'
                        AND am.state = 'posted'
                        AND aml.company_id = c.id
                    ), 0) as cost_of_sales,
                    
                    -- Ganancia Bruta
                    COALESCE((
                        SELECT SUM(aml.credit - aml.debit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        JOIN account_move am ON am.id = aml.move_id
                        WHERE aa.internal_type = 'income'
                        AND am.state = 'posted'
                        AND aml.company_id = c.id
                    ), 0) - COALESCE((
                        SELECT SUM(aml.debit - aml.credit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        JOIN account_move am ON am.id = aml.move_id
                        WHERE aa.internal_type = 'expense'
                        AND aa.code LIKE '5%'
                        AND am.state = 'posted'
                        AND aml.company_id = c.id
                    ), 0) as gross_profit,
                    
                    -- Gastos Operativos
                    COALESCE((
                        SELECT SUM(aml.debit - aml.credit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        JOIN account_move am ON am.id = aml.move_id
                        WHERE aa.internal_type = 'expense'
                        AND NOT aa.code LIKE '5%'
                        AND am.state = 'posted'
                        AND aml.company_id = c.id
                    ), 0) as operating_expenses,
                    
                    -- Ingreso Operativo
                    COALESCE((
                        SELECT SUM(aml.credit - aml.debit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        JOIN account_move am ON am.id = aml.move_id
                        WHERE aa.internal_type = 'income'
                        AND am.state = 'posted'
                        AND aml.company_id = c.id
                    ), 0) - COALESCE((
                        SELECT SUM(aml.debit - aml.credit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        JOIN account_move am ON am.id = aml.move_id
                        WHERE aa.internal_type = 'expense'
                        AND am.state = 'posted'
                        AND aml.company_id = c.id
                    ), 0) as operating_income,
                    
                    0 as other_income,
                    0 as other_expenses,
                    
                    -- Ingreso Neto
                    COALESCE((
                        SELECT SUM(aml.credit - aml.debit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        JOIN account_move am ON am.id = aml.move_id
                        WHERE aa.internal_type = 'income'
                        AND am.state = 'posted'
                        AND aml.company_id = c.id
                    ), 0) - COALESCE((
                        SELECT SUM(aml.debit - aml.credit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        JOIN account_move am ON am.id = aml.move_id
                        WHERE aa.internal_type = 'expense'
                        AND am.state = 'posted'
                        AND aml.company_id = c.id
                    ), 0) as net_income
                    
                FROM res_company c
            )
        """)

    @api.model
    def get_income_statement(self, date_start, date_end, company_id=None):
        """Obtener estado de resultados para un período"""
        if not company_id:
            company_id = self.env.company.id
        
        domain = [('company_id', '=', company_id)]
        return self.search(domain)


class BalanceSheet(models.Model):
    """Balance General - Balance Sheet"""
    _name = "financial.balance.sheet"
    _description = "Balance Sheet / Balance General"
    _auto = False
    _rec_name = "name"

    name = fields.Char(string="Descripción", readonly=True)
    date = fields.Date(string="Fecha", readonly=True)
    company_id = fields.Many2one("res.company", string="Compañía", readonly=True)
    
    # Assets
    current_assets = fields.Monetary(string="Activos Corrientes", readonly=True, currency_field="currency_id")
    non_current_assets = fields.Monetary(string="Activos No Corrientes", readonly=True, currency_field="currency_id")
    total_assets = fields.Monetary(string="Total Activos", readonly=True, currency_field="currency_id")
    
    # Liabilities
    current_liabilities = fields.Monetary(string="Pasivos Corrientes", readonly=True, currency_field="currency_id")
    non_current_liabilities = fields.Monetary(string="Pasivos No Corrientes", readonly=True, currency_field="currency_id")
    total_liabilities = fields.Monetary(string="Total Pasivos", readonly=True, currency_field="currency_id")
    
    # Equity
    total_equity = fields.Monetary(string="Total Patrimonio", readonly=True, currency_field="currency_id")
    
    # Verification
    total_liabilities_equity = fields.Monetary(string="Total Pasivos + Patrimonio", readonly=True, currency_field="currency_id")
    
    currency_id = fields.Many2one("res.currency", string="Moneda", readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW financial_balance_sheet AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY c.id) as id,
                    'Balance General - ' || COALESCE(c.name, 'Compañía') as name,
                    CURRENT_DATE as date,
                    c.id as company_id,
                    c.currency_id,
                    
                    -- Activos Corrientes
                    COALESCE((
                        SELECT SUM(aml.debit - aml.credit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.internal_type = 'asset'
                        AND aa.code LIKE '1%'
                        AND aml.parent_state = 'posted'
                    ), 0) as current_assets,
                    
                    -- Activos No Corrientes
                    COALESCE((
                        SELECT SUM(aml.debit - aml.credit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.internal_type = 'asset'
                        AND aa.code LIKE '16%'
                        AND aml.parent_state = 'posted'
                    ), 0) as non_current_assets,
                    
                    -- Total Activos
                    COALESCE((
                        SELECT SUM(aml.debit - aml.credit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.internal_type = 'asset'
                        AND aml.parent_state = 'posted'
                    ), 0) as total_assets,
                    
                    -- Pasivos Corrientes
                    COALESCE((
                        SELECT SUM(aml.credit - aml.debit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.internal_type = 'liability'
                        AND aa.code LIKE '2%'
                        AND aml.parent_state = 'posted'
                    ), 0) as current_liabilities,
                    
                    -- Pasivos No Corrientes
                    COALESCE((
                        SELECT SUM(aml.credit - aml.debit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.internal_type = 'liability'
                        AND aa.code LIKE '27%'
                        AND aml.parent_state = 'posted'
                    ), 0) as non_current_liabilities,
                    
                    -- Total Pasivos
                    COALESCE((
                        SELECT SUM(aml.credit - aml.debit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.internal_type = 'liability'
                        AND aml.parent_state = 'posted'
                    ), 0) as total_liabilities,
                    
                    -- Total Patrimonio
                    COALESCE((
                        SELECT SUM(aml.credit - aml.debit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.internal_type = 'equity'
                        AND aml.parent_state = 'posted'
                    ), 0) as total_equity,
                    
                    -- Total Pasivos + Patrimonio
                    COALESCE((
                        SELECT SUM(aml.credit - aml.debit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.internal_type IN ('liability', 'equity')
                        AND aml.parent_state = 'posted'
                    ), 0) as total_liabilities_equity
                    
                FROM res_company c
            )
        """)

    @api.model
    def get_balance_sheet(self, date, company_id=None):
        """Obtener balance general a una fecha específica"""
        if not company_id:
            company_id = self.env.company.id
        
        domain = [('company_id', '=', company_id)]
        return self.search(domain)


class CashFlow(models.Model):
    """Flujo de Caja - Cash Flow Statement"""
    _name = "financial.cash.flow"
    _description = "Cash Flow Statement / Estado de Flujo de Caja"
    _auto = False
    _rec_name = "name"

    name = fields.Char(string="Descripción", readonly=True)
    date_start = fields.Date(string="Fecha Inicio", readonly=True)
    date_end = fields.Date(string="Fecha Fin", readonly=True)
    company_id = fields.Many2one("res.company", string="Compañía", readonly=True)
    
    # Operating Activities
    net_income = fields.Monetary(string="Ingreso Neto", readonly=True, currency_field="currency_id")
    adjustments = fields.Monetary(string="Ajustes", readonly=True, currency_field="currency_id")
    cash_from_operations = fields.Monetary(string="Efectivo de Operaciones", readonly=True, currency_field="currency_id")
    
    # Investing Activities
    capital_expenditure = fields.Monetary(string="Gastos de Capital", readonly=True, currency_field="currency_id")
    cash_from_investing = fields.Monetary(string="Efectivo de Inversiones", readonly=True, currency_field="currency_id")
    
    # Financing Activities
    debt_payments = fields.Monetary(string="Pagos de Deuda", readonly=True, currency_field="currency_id")
    equity_changes = fields.Monetary(string="Cambios en Patrimonio", readonly=True, currency_field="currency_id")
    cash_from_financing = fields.Monetary(string="Efectivo de Financiamiento", readonly=True, currency_field="currency_id")
    
    # Net Change
    net_change_cash = fields.Monetary(string="Cambio Neto en Efectivo", readonly=True, currency_field="currency_id")
    beginning_cash = fields.Monetary(string="Efectivo Inicial", readonly=True, currency_field="currency_id")
    ending_cash = fields.Monetary(string="Efectivo Final", readonly=True, currency_field="currency_id")
    
    currency_id = fields.Many2one("res.currency", string="Moneda", readonly=True)
    
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW financial_cash_flow AS (
                SELECT
                    ROW_NUMBER() OVER (ORDER BY c.id) as id,
                    'Flujo de Caja - ' || COALESCE(c.name, 'Compañía') as name,
                    CURRENT_DATE as date_start,
                    CURRENT_DATE as date_end,
                    c.id as company_id,
                    c.currency_id,
                    
                    -- Ingreso Neto
                    COALESCE((
                        SELECT SUM(aml.credit - aml.debit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.internal_type = 'income'
                        AND aml.parent_state = 'posted'
                    ), 0) - COALESCE((
                        SELECT SUM(aml.debit - aml.credit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.internal_type = 'expense'
                        AND aml.parent_state = 'posted'
                    ), 0) as net_income,
                    
                    -- Ajustes (Depreciación, etc)
                    COALESCE((
                        SELECT SUM(aml.debit - aml.credit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.code LIKE '681%' OR aa.code LIKE '682%'
                        AND aml.parent_state = 'posted'
                    ), 0) as adjustments,
                    
                    -- Efectivo de Operaciones
                    COALESCE((
                        SELECT SUM(aml.credit - aml.debit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.internal_type = 'income'
                        AND aml.parent_state = 'posted'
                    ), 0) - COALESCE((
                        SELECT SUM(aml.debit - aml.credit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.internal_type = 'expense'
                        AND aml.parent_state = 'posted'
                    ), 0) as cash_from_operations,
                    
                    -- Gastos de Capital
                    COALESCE((
                        SELECT SUM(aml.debit - aml.credit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.code LIKE '16%'
                        AND aml.parent_state = 'posted'
                    ), 0) as capital_expenditure,
                    
                    0 as cash_from_investing,
                    0 as debt_payments,
                    0 as equity_changes,
                    0 as cash_from_financing,
                    
                    -- Cambio Neto en Efectivo
                    COALESCE((
                        SELECT SUM(aml.debit - aml.credit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.code LIKE '1011%' OR aa.code LIKE '1012%'
                        AND aml.parent_state = 'posted'
                    ), 0) as net_change_cash,
                    
                    -- Efectivo Inicial
                    COALESCE((
                        SELECT aml.debit - aml.credit
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE (aa.code LIKE '1011%' OR aa.code LIKE '1012%')
                        AND aml.parent_state = 'posted'
                        ORDER BY aml.date ASC
                        LIMIT 1
                    ), 0) as beginning_cash,
                    
                    -- Efectivo Final
                    COALESCE((
                        SELECT SUM(aml.debit - aml.credit)
                        FROM account_move_line aml
                        JOIN account_account aa ON aa.id = aml.account_id
                        WHERE aa.code LIKE '1011%' OR aa.code LIKE '1012%'
                        AND aml.parent_state = 'posted'
                    ), 0) as ending_cash
                    
                FROM res_company c
            )
        """)

    @api.model
    def get_cash_flow(self, date_start, date_end, company_id=None):
        """Obtener flujo de caja para un período"""
        if not company_id:
            company_id = self.env.company.id
        
        domain = [('company_id', '=', company_id)]
        return self.search(domain)
