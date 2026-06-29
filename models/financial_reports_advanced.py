from odoo import fields, models, tools, api
from datetime import datetime, timedelta
from decimal import Decimal


class FinancialReportLine(models.Model):
    """Línea individual de reporte financiero con analítica"""
    _name = "financial.report.line"
    _description = "Financial Report Line with Analytics"
    _auto = False

    # Información básica
    report_id = fields.Many2one("financial.report", string="Reporte", readonly=True)
    company_id = fields.Many2one("res.company", string="Empresa", readonly=True)
    report_type = fields.Selection(
        [('income', 'Estado de Resultados'), ('balance', 'Balance General'), ('cashflow', 'Flujo de Caja')],
        string="Tipo de Reporte",
        readonly=True
    )
    
    # Período
    date_start = fields.Date(string="Fecha Inicio", readonly=True)
    date_end = fields.Date(string="Fecha Fin", readonly=True)
    
    # Cuenta contable
    account_id = fields.Many2one("account.account", string="Cuenta", readonly=True)
    account_code = fields.Char(string="Código Cuenta", readonly=True)
    account_name = fields.Char(string="Nombre Cuenta", readonly=True)
    account_type = fields.Selection([
        ('asset', 'Activo'),
        ('liability', 'Pasivo'),
        ('equity', 'Patrimonio'),
        ('income', 'Ingreso'),
        ('expense', 'Gasto'),
    ], string="Tipo Cuenta", readonly=True)
    
    # Cuenta analítica
    analytic_account_id = fields.Many2one("account.analytic.account", string="Cuenta Analítica", readonly=True)
    analytic_code = fields.Char(string="Código Analítica", readonly=True)
    analytic_name = fields.Char(string="Nombre Analítica", readonly=True)
    
    # Valores
    debit = fields.Monetary(string="Débito", readonly=True, currency_field="currency_id")
    credit = fields.Monetary(string="Crédito", readonly=True, currency_field="currency_id")
    balance = fields.Monetary(string="Saldo", readonly=True, currency_field="currency_id")
    
    currency_id = fields.Many2one("res.currency", string="Moneda", readonly=True)
    
    # Para colorear negativos
    balance_color = fields.Char(string="Color Saldo", readonly=True, compute="_compute_balance_color")
    
    @api.depends('balance')
    def _compute_balance_color(self):
        for record in self:
            if record.balance < 0:
                record.balance_color = 'red'
            else:
                record.balance_color = 'black'


class FinancialReport(models.Model):
    """Reporte Financiero Dinámico Multi-Empresa"""
    _name = "financial.report"
    _description = "Financial Report with Analytics"
    _rec_name = "name"

    name = fields.Char(string="Nombre del Reporte", required=True)
    report_type = fields.Selection(
        [('income', 'Estado de Resultados'), ('balance', 'Balance General'), ('cashflow', 'Flujo de Caja')],
        string="Tipo de Reporte",
        required=True
    )
    
    # Período
    date_start = fields.Date(string="Fecha Inicio", required=True)
    date_end = fields.Date(string="Fecha Fin", required=True)
    
    # Empresa(s)
    company_ids = fields.Many2many(
        "res.company",
        string="Empresas",
        required=True,
        help="Selecciona las empresas a incluir en el reporte"
    )
    
    # Cuentas analíticas
    analytic_account_ids = fields.Many2many(
        "account.analytic.account",
        string="Cuentas Analíticas",
        help="Deja en blanco para incluir todas. Selecciona para filtrar por analítica."
    )
    
    # Opciones de reporte
    include_zero_lines = fields.Boolean(string="Incluir Líneas sin Movimiento", default=False)
    group_by_analytic = fields.Boolean(string="Agrupar por Cuenta Analítica", default=True)
    
    # Datos del reporte
    line_ids = fields.One2many("financial.report.line", "report_id", string="Líneas del Reporte", readonly=True)
    
    currency_id = fields.Many2one("res.currency", string="Moneda", readonly=True)
    
    # Resumen
    total_debit = fields.Monetary(string="Total Débito", readonly=True, currency_field="currency_id")
    total_credit = fields.Monetary(string="Total Crédito", readonly=True, currency_field="currency_id")
    total_balance = fields.Monetary(string="Total Saldo", readonly=True, currency_field="currency_id")
    
    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._generate_report_lines()\n        return record
    
    def _generate_report_lines(self):
        \"\"\"Generar líneas del reporte según tipo y filtros\"\"\"\n        self.ensure_one()
        
        # Eliminar líneas anteriores
        self.line_ids.unlink()
        
        if self.report_type == 'income':
            self._generate_income_statement_lines()
        elif self.report_type == 'balance':
            self._generate_balance_sheet_lines()
        elif self.report_type == 'cashflow':
            self._generate_cashflow_lines()
        
        # Calcular totales
        self._compute_totals()
    
    def _generate_income_statement_lines(self):
        \"\"\"Generar líneas para Estado de Resultados\"\"\"\n        for company in self.company_ids:
            # Obtener todas las cuentas de ingreso y gasto
            accounts = self.env['account.account'].search([
                ('company_id', '=', company.id),
                ('internal_type', 'in', ['income', 'expense']),
                ('deprecated', '=', False),
            ])\n            
            for account in accounts:
                self._create_report_lines_for_account(account, company)
    
    def _generate_balance_sheet_lines(self):
        \"\"\"Generar líneas para Balance General\"\"\"\n        for company in self.company_ids:
            # Obtener todas las cuentas de activo, pasivo y patrimonio
            accounts = self.env['account.account'].search([
                ('company_id', '=', company.id),
                ('internal_type', 'in', ['asset', 'liability', 'equity']),
                ('deprecated', '=', False),
            ])\n            
            for account in accounts:
                self._create_report_lines_for_account(account, company)
    
    def _generate_cashflow_lines(self):
        \"\"\"Generar líneas para Flujo de Caja\"\"\"\n        for company in self.company_ids:
            # Obtener cuentas de efectivo y equivalentes
            accounts = self.env['account.account'].search([
                ('company_id', '=', company.id),
                ('code', 'like', '101%'),  # Efectivo típicamente empieza con 101
                ('deprecated', '=', False),
            ])\n            
            for account in accounts:
                self._create_report_lines_for_account(account, company)
    
    def _create_report_lines_for_account(self, account, company):
        \"\"\"Crear líneas de reporte para una cuenta, agrupadas por analítica\"\"\"\n        
        # Obtener movimientos de la cuenta
        domain = [
            ('account_id', '=', account.id),
            ('company_id', '=', company.id),
            ('parent_state', '=', 'posted'),
            ('date', '>=', self.date_start),
            ('date', '<=', self.date_end),
        ]
        
        move_lines = self.env['account.move.line'].search(domain)
        
        if not move_lines and not self.include_zero_lines:
            return
        
        # Agrupar por cuenta analítica
        if self.group_by_analytic:
            grouped = {}
            for line in move_lines:
                analytic_id = line.analytic_account_id.id or 0
                if analytic_id not in grouped:
                    grouped[analytic_id] = self.env['account.move.line']
                grouped[analytic_id] |= line
            
            for analytic_id, lines in grouped.items():
                if not lines and not self.include_zero_lines:
                    continue
                
                debit = sum(lines.mapped('debit'))
                credit = sum(lines.mapped('credit'))
                balance = debit - credit
                
                if balance == 0 and not self.include_zero_lines:
                    continue
                
                # Obtener datos de analítica
                if analytic_id:
                    analytic = self.env['account.analytic.account'].browse(analytic_id)
                    analytic_code = analytic.code
                    analytic_name = analytic.name
                else:
                    analytic_code = 'SIN ANALÍTICA'
                    analytic_name = 'Sin Cuenta Analítica'
                
                # Crear línea
                self.env['financial.report.line'].create({
                    'report_id': self.id,
                    'company_id': company.id,
                    'report_type': self.report_type,
                    'date_start': self.date_start,
                    'date_end': self.date_end,
                    'account_id': account.id,
                    'account_code': account.code,
                    'account_name': account.name,
                    'account_type': account.internal_type,
                    'analytic_account_id': analytic_id or False,
                    'analytic_code': analytic_code,
                    'analytic_name': analytic_name,
                    'debit': debit,
                    'credit': credit,
                    'balance': balance,
                    'currency_id': company.currency_id.id,
                })
        else:
            # Sin agrupación por analítica
            debit = sum(move_lines.mapped('debit'))
            credit = sum(move_lines.mapped('credit'))
            balance = debit - credit
            
            if balance == 0 and not self.include_zero_lines:
                return
            
            self.env['financial.report.line'].create({
                'report_id': self.id,
                'company_id': company.id,
                'report_type': self.report_type,
                'date_start': self.date_start,
                'date_end': self.date_end,
                'account_id': account.id,
                'account_code': account.code,
                'account_name': account.name,
                'account_type': account.internal_type,
                'analytic_account_id': False,
                'analytic_code': 'SIN ANALÍTICA',
                'analytic_name': 'Sin Cuenta Analítica',
                'debit': debit,
                'credit': credit,
                'balance': balance,
                'currency_id': company.currency_id.id,
            })
    
    def _compute_totals(self):
        \"\"\"Calcular totales del reporte\"\"\"\n        self.total_debit = sum(self.line_ids.mapped('debit'))
        self.total_credit = sum(self.line_ids.mapped('credit'))
        self.total_balance = sum(self.line_ids.mapped('balance'))
    
    def action_refresh(self):
        \"\"\"Refrescar datos del reporte\"\"\"\n        self._generate_report_lines()
        return True


class FinancialReportPivot(models.Model):
    """Vista Pivot de Reporte Financiero con Cuentas Analíticas en Columnas"""
    _name = "financial.report.pivot"
    _description = "Financial Report Pivot View"
    _auto = False
    _rec_name = "account_name"
    _order = "account_code, company_id, account_name"

    # Información de cuenta
    account_id = fields.Many2one("account.account", string="Cuenta", readonly=True)
    account_code = fields.Char(string="Código", readonly=True)
    account_name = fields.Char(string="Cuenta", readonly=True)
    
    # Empresa
    company_id = fields.Many2one("res.company", string="Empresa", readonly=True)
    
    # Cuentas analíticas (dinámicas - las vamos a mostrar en columnas)
    analytic_data = fields.Json(string="Datos Analíticos", readonly=True)
    
    # Total sin analítica
    balance_without_analytic = fields.Monetary(
        string="Total",
        readonly=True,
        currency_field="currency_id"
    )
    
    currency_id = fields.Many2one("res.currency", string="Moneda", readonly=True)
    
    def init(self):
        # Esta vista será construida dinámicamente por reportes
        pass
