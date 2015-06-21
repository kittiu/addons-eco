# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today Ecosoft (<http://www.ecosoft.co.th>)
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from datetime import datetime
from datetime import date, timedelta

from dateutil.relativedelta import relativedelta
from openerp.tools.translate import _
from .. import format_common

import xlwt
import cStringIO
import base64

from openerp.osv import osv, fields
from account_cash_projection.report import account_cash_projection_report

class account_cash_projection_balance(osv.osv_memory):
    _inherit = 'account.common.partner.report'
    _name = 'account.cash.projection'
    _description = 'Account Cash Projection Report'

    def _get_period(self, cr, uid, context=None):
        """Return default period value"""
        ctx = dict(context or {}, account_period_prefer_normal=True)
        period_ids = self.pool.get('account.period').find(cr, uid, context=ctx)
        return period_ids and period_ids[0] or False

    _columns = {
        'period_id': fields.many2one('account.period', 'Start Period', required=True),
        'period_length': fields.selection([('day', 'Day'),
                                        ('week', 'Week'),
                                        ], 'Length', required=True),
        'period_length_day':fields.integer('Length (days)', readonly=False),
        'no_columns':fields.integer('Number of Columns', readonly=False, required=True),
        'journal_ids': fields.many2many('account.journal', 'account_cash_projection_balance_journal_rel', 'account_id', 'journal_id', 'Journals', required=True),
        'cash_in_op': fields.many2many('account.account', 'account_cash_projection_balance_cash_in_rel', 'cash_id', 'account_id', 'Cash Inflow Accounts (Operating)', required=True, domain=[('type', '=', 'receivable')]),
        'cash_out_op': fields.many2many('account.account', 'account_cash_projection_balance_cash_out_rel', 'cash_id', 'account_id', 'Cash Outflow Accounts (Operating)', required=True, domain=[('type', '=', 'payable')]),
        'cash_in_finance': fields.many2many('account.account', 'account_cash_projection_balance_cash_in_f_rel', 'cash_id', 'account_id', 'Cash Accounts (Financing)', required=True, domain=[('type','<>','receivable'),('type','<>','payable'),('type','<>','view'), ('type', '<>', 'closed')]),
        'cash_in_invest': fields.many2many('account.account', 'account_cash_projection_balance_cash_in_invest_rel', 'cash_id', 'account_id', 'Cash Accounts (Investing)', required=True, domain=[('type','<>','receivable'),('type','<>','payable'),('type','<>','view'), ('type', '<>', 'closed')]),
        'cash_in_bank': fields.many2many('account.account', 'account_cash_projection_balance_cash_in_bank_rel', 'cash_id', 'account_id', 'Bank Accounts', required=True, domain=[('type','<>','receivable'),('type','<>','payable'),('type','<>','view'), ('type', '<>', 'other')]),
    }
    
    def get_date(self, cr, uid, context):
        d = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        return d

    _defaults = {
        'period_id': _get_period,
        'period_length': 'day',
        'period_length_day': 1,
        'no_columns': 30,
        'date_from': get_date,
    }
    
    def onchange_period(self, cr, uid, ids, period_id, period_length, context=None):
        v = {}
        period = self.pool.get('account.period').browse(cr, uid, period_id, context=context)
        if period.date_start:
            v['date_from'] = period.date_start
        if period_length == 'day':
            start = datetime.strptime(period.date_start, "%Y-%m-%d")
            stop = datetime.strptime(period.date_stop, "%Y-%m-%d")
            diff = stop - start
            v['no_columns'] = diff.days + 1
            v['period_length_day'] = 1
        elif period_length == 'week':
            v['no_columns'] = 5
            v['period_length_day'] = 7
        return {'value': v}

    def _print_report(self, cr, uid, ids, data, context=None):
        res = {}
        if context is None:
            context = {}

        data = self.pre_print_report(cr, uid, ids, data, context=context)
        data['form'].update(self.read(cr, uid, ids, ['cash_in_bank','no_columns','period_length_day','cash_in_op','cash_out_op','cash_in_finance','cash_in_invest'])[0])

        period_length_day = data['form']['period_length_day']
        if period_length_day<=0:
            raise osv.except_osv(_('User Error!'), _('You must set a period length greater than 0.'))
        if not data['form']['date_from']:
            raise osv.except_osv(_('User Error!'), _('You must set a start date.'))

        start = datetime.strptime(data['form']['date_from'], "%Y-%m-%d")
        
        self.no_columns = data['form']['no_columns']

        for i in range(self.no_columns):
            stop = start + relativedelta(days=period_length_day)
            res[str(self.no_columns-(i+1))] = {
                'name': (i!=self.no_columns - 1 and str((i) * period_length_day)+'-' + str((i+1) * period_length_day) or ('+'+str((self.no_columns - 1) * period_length_day))),
                'start': start.strftime('%Y-%m-%d'),
                'stop': (i!=self.no_columns - 1 and stop.strftime('%Y-%m-%d') or False),
            }
            start = stop + relativedelta(days=1)
        
        
        self.res = res
        data['form'].update(res)
        if data.get('form',False):
            data['ids']=[data['form'].get('chart_account_id',False)]
            
        obj_gl = account_cash_projection_report.cash_projection_report(cr, uid, 'report.account.cash_projection_balance', context=context)
        a_ids = self.pool.get('account.account').search(cr, uid, [], context=context)
        objects = self.pool.get('account.account').browse(cr, uid, a_ids, context=context)
        obj_gl.set_context(objects, data, data['ids'], report_type='pdf')
        
        res_payable = {}
        res_receivable = {}

        res_receivable = obj_gl._get_lines_accounts_inflow(data['form'], account_type=['receivable'], account_ids=data['form']['cash_in_op'])
        res_payable = obj_gl._get_lines_accounts_inflow(data['form'], account_type=['payable'], account_ids=data['form']['cash_out_op'])
        res_in_finance = obj_gl._get_lines_accounts_inflow_finance(data['form'], account_type=['receivable','payable'], account_ids=data['form']['cash_in_finance'])
        res_out_finanace = obj_gl._get_lines_accounts_outflow_finance(data['form'], account_type=['receivable','payable'], account_ids=data['form']['cash_in_finance'])
        res_in_invest = obj_gl._get_lines_accounts_inflow_finance(data['form'], account_type=['receivable','payable'], account_ids=data['form']['cash_in_invest'])
        res_out_invest = obj_gl._get_lines_accounts_outflow_finance(data['form'], account_type=['receivable','payable'], account_ids=data['form']['cash_in_invest'])

        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('Cash Projection Report')
        sheet.row(0).height = 256*3
        
        M_header_style = format_common.font_style(position='center', bold=1, border=1, fontos='black', font_height=200)
        D_header_style = format_common.font_style(position='left', bold=1, border=1, fontos='black', font_height=180, color='grey')
        T_header_style = format_common.font_style(position='center', bold=1, border=1, fontos='black', font_height=180, color='grey')
        T1_header_style = format_common.font_style(position='left', bold=1, border=1, fontos='black', font_height=180, color='yellow')
        V_style = format_common.font_style(position='right', bold=1, fontos='black', font_height=180)
        
        self.netcash = dict((x,0) for x in range(0,self.no_columns))
        self.netcash['netdue'] = 0
        self.netcash['nettotal'] = 0
        
        self.netfin = dict((x,0) for x in range(0,self.no_columns))
        self.netfin['netdue'] = 0
        self.netfin['nettotal'] = 0

        self.netinv = dict((x,0) for x in range(0,self.no_columns))
        self.netinv['netdue'] = 0
        self.netinv['nettotal'] = 0
        
        self.netoper = dict((x,0) for x in range(0,self.no_columns))
        self.netoper['netdue'] = 0
        self.netoper['nettotal'] = 0
        
        sheet.write_merge(0, 0, 0, 6, 'Cash Projection Report\n Start Date:' + str(data['form']['date_from']) + '\n Period Length: '+ str(data['form']['period_length_day']), M_header_style)
        sheet.col(0).width = 256*40
        row = self.render_header(sheet, first_row=5, style=D_header_style)
        
        sheet.write(row, 0, 'Cash Flow From Operating Activities', T_header_style)
        row += 2
        sheet.write(row, 0, 'Cash Inflow Accounts', T_header_style)
        row = self.output_vals(sheet, res_receivable, row=row+1, op_type='oper', style=V_style)
        row += 2
        sheet.write(row, 0, 'Cash Outflow Accounts', T_header_style)
        row = self.output_vals(sheet, res_payable, type='out', op_type='oper', row = row+1, style=V_style)
        row += 2
        sheet.write(row, 0, 'Net Cash Flow (Operation)', T1_header_style)
        col = 0
        for val in range(self.no_columns)[::-1]:
            col += 1
            sheet.write(row, col, self.netoper[val], V_style)
        sheet.write(row, col+1, self.netoper['nettotal'], V_style)
        
        row += 2
        sheet.write(row, 0, 'Cash Flow From Financing Activities', T_header_style)
        row += 2
        sheet.write(row, 0, 'Cash Inflow Accounts', T_header_style)
        row = self.output_vals(sheet, res_in_finance, row=row+1, op_type='fin', style=V_style)
        row += 2
        sheet.write(row, 0, 'Cash Outflow Accounts', T_header_style)
        row = self.output_vals(sheet, res_out_finanace, type='out', op_type='fin', row = row+1, style=V_style)
        row += 2
        sheet.write(row, 0, 'Net Cash Flow (Financing)', T1_header_style)
        col = 0
        for val in range(self.no_columns)[::-1]:
            col += 1
            sheet.write(row, col, self.netfin[val], V_style)
        sheet.write(row, col+1, self.netfin['nettotal'], V_style)

        
        row += 2
        sheet.write(row, 0, 'Cash Flow From Investing Activities', T_header_style)
        row += 2
        sheet.write(row, 0, 'Cash Inflow Accounts', T_header_style)
        row = self.output_vals(sheet, res_in_invest, row=row+1, op_type='inv', style=V_style)
        row += 2
        sheet.write(row, 0, 'Cash Outflow Accounts', T_header_style)
        row = self.output_vals(sheet, res_out_invest, type='out', op_type='inv', row = row+1, style=V_style)
        row += 2
        sheet.write(row, 0, 'Net Cash Flow (Investing)', T1_header_style)
        col = 0
        for val in range(self.no_columns)[::-1]:
            col += 1
            sheet.write(row, col, self.netinv[val], V_style)
        sheet.write(row, col+1, self.netinv['nettotal'], V_style)


        #this is total of all activities.
        row = row + 1
        row = row + 1
        col= 0
        T3_header_style = format_common.font_style(position='left', bold=1, border=1, fontos='black', font_height=180, color='grey')
        sheet.write(row, col, 'Net Increase / (Decrease) In Cash', T3_header_style)
        col = 0
        for val in range(self.no_columns)[::-1]:
            col += 1
            sheet.write(row, col, self.netcash[val], V_style)
        sheet.write(row, col+1, self.netcash['nettotal'], V_style)


#---------------------------------------------------------------------------------------
        # Start logic to get init balance for date - 1
        obj_move = self.pool.get('account.move.line')
        d = (datetime.strptime(data['form']['date_from'], "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")#The starting Cash is balance from selected bank accounts, 1 day before date's cash flow
        query = obj_move._query_get(cr, uid, obj='l', context=data['form'].get('used_context',{}))
        wheres = [""]
        query += ' and l.date <= %s' #The starting Cash is balance from selected bank accounts, 1 day before date's cash flow
        if query.strip():
            wheres.append(query.strip())
        filters = " AND ".join(wheres)
        request = ("SELECT l.account_id as id,  \
                   SUM(l.debit-l.credit) "\
                   " FROM account_move_line l" \
                   " WHERE l.account_id IN %s " \
                        + filters +
                   " GROUP BY l.account_id")
        params = (tuple(data['form']['cash_in_bank']),d,) 
        res = cr.execute(request,params)
        t = cr.fetchall()
        init_balance = 0.0
        if t:
            for amount in t:
                init_balance += amount[1]

        T2_header_style = format_common.font_style(position='left', bold=1, border=1, fontos='black', font_height=180, color='grey')
        row = row + 1
        row = row + 1
        col= 0
        sheet.write(row, col, 'Starting Cash', T2_header_style)
        row = row + 1
        sheet.write(row, col, 'Net Increase / (Decrease) In Cash', T2_header_style)
        row = row + 1
        sheet.write(row, col, 'Ending Cash', T2_header_style)
        col = 1
        row = row - 2
        sheet.write(row, col, init_balance, V_style)
        row = row + 1
        sheet.write(row, col, self.netcash['netdue'], V_style)
        row = row + 1
        sheet.write(row, col, init_balance+self.netcash['netdue'], V_style)
        for val in range(self.no_columns)[::-1]:
            row = row - 2
            col += 1
            sheet.write(row, col, init_balance, V_style)
            row = row + 1
            sheet.write(row, col, self.netcash[val], V_style)
            row = row + 1
            sheet.write(row, col, init_balance+self.netcash[val], V_style)
            init_balance = init_balance+self.netcash[val]

        stream = cStringIO.StringIO()
        workbook.save(stream)
        cr.execute(""" DELETE FROM output """)
        attach_id = self.pool.get('output').create(cr, uid, {'name':'Cash Projection Report.xls', 'xls_output': base64.encodestring(stream.getvalue())})
        return {
                'name': _('Notification'),
                'context': context,
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'output',
                'res_id':attach_id,
                'type': 'ir.actions.act_window',
                'target':'new'
                }
        
    def output_vals(self, ws, output_res, type='in', op_type='oper', row=0, style=False):
        col = 0
        due_total = 0
        daywise_total = dict((x,0) for x in range(0,self.no_columns))
        final_total = 0
        style1 = format_common.font_style(position='left', fontos='black', font_height=180)
        for main in output_res:
            ws.write(row, col, main['name'], style1)
            due_total += main['direction']
            main.has_key('direction') and main.pop('direction')
            for val in range(self.no_columns)[::-1]:
                col += 1
                daywise_total[val] += main[str(val)]
                ws.write(row, col, main[str(val)], style)
            col += 1
            
            ws.write(row, col, main['total'], style)
            final_total += main['total']
            col = 0
            row += 1
        col = 0
        label = 'Total Cash Inflow'
        if type == 'out':
            label = 'Total Cash Outflow'
        row += 1
        head_style = format_common.font_style(position='center', bold=1, border=1, fontos='black', font_height=180, color='grey')
        ws.write(row, col, label, head_style)
        self.netcash['netdue'] += due_total
        if op_type == 'oper':
            self.netoper['netdue'] += due_total
        if op_type == 'fin':
            self.netfin['netdue'] += due_total
        if op_type == 'inv':
                self.netinv['netdue'] += due_total
        for val in range(self.no_columns)[::-1]:
            col += 1
            ws.write(row, col, daywise_total[val], style)
            self.netcash[val] += daywise_total[val]
            if op_type == 'oper':
                self.netoper[val] += daywise_total[val]
            if op_type == 'fin':
                self.netfin[val] += daywise_total[val]
            if op_type == 'inv':
                self.netinv[val] += daywise_total[val]
        col += 1
        ws.write(row, col, final_total, style)
        self.netcash['nettotal'] += final_total
        if op_type == 'oper':
            self.netoper['nettotal'] += final_total
        if op_type == 'fin':
            self.netfin['nettotal'] += final_total
        if op_type == 'inv':
            self.netinv['nettotal'] += final_total
        return row
        
    def render_header(self, ws, first_row=0, style=False):
        ws.write(first_row, 0, 'Date/Day Number', style)
        col = 1
        for hdr in range(self.no_columns)[::-1]:
            hdr_real = self.res[str(hdr)]['start']
            if 'stop' in self.res[str(hdr)] and self.res[str(hdr)]['stop']:
                hdr_real +=  ' To ' + self.res[str(hdr)]['stop']
            ws.write(first_row, col, hdr_real, style)
            ws.col(col).width = len(hdr_real)*300
            col += 1
        ws.write(first_row, col, 'Total', style)
        return first_row + 2
        
account_cash_projection_balance()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
