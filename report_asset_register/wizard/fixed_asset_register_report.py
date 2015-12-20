# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014-Today Ecosoft (<http://www.Ecosoft.co.th >)
#    Copyright (C) 2010-Today OpenERP SA (<http://www.openerp.com>)
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

import time
import xlwt
from xlwt import Workbook, XFStyle, Borders, Pattern, Font, Alignment, easyxf
import base64
import cStringIO
from datetime import datetime

from openerp.osv import fields, osv

class fixed_asset_register_report(osv.osv_memory):
    _name = 'fixed.asset.register.report'
    _description = 'Assets Register Report'
    
    def onchange_chart_id(self, cr, uid, ids, chart_account_id=False, context=None):
        res = {}
        
        if chart_account_id:
            company_id = self.pool.get('account.account').browse(cr, uid, chart_account_id, context=context).company_id.id
            now = time.strftime('%Y-%m-%d')
            domain = [('company_id', '=', company_id), ('date_start', '<', now), ('date_stop', '>', now)]
            fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, domain, limit=1)
            res['value'] = {'company_id': company_id, 'fiscalyear_id': fiscalyears and fiscalyears[0] or False}
        return res

    _columns = {
        'company_id': fields.many2one('res.company', string='Company', required=True),
        'fiscalyear_id': fields.many2one('account.fiscalyear', 'Fiscal Year', help='Keep empty for all open fiscal year'),
        'filter': fields.selection([('filter_no', 'No Filters'), ('filter_date', 'Date'), ('filter_period', 'Periods')], 'Filter by', required=True),
        'period_from': fields.many2one('account.period', 'Start Period'),
        'period_to': fields.many2one('account.period', 'End Period'),
        'date_from': fields.date('Start Date'),
        'date_to': fields.date('End Date'),
        'asset_categ_ids': fields.many2many('account.asset.category', string='Asset Categoires'),
        'excel_report': fields.boolean('Print Excel Report?', help='Tick this box if you want to export report in excel.')
    }
    
    def _get_account(self, cr, uid, context=None):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        accounts = self.pool.get('account.account').search(cr, uid, [('parent_id', '=', False), ('company_id', '=', user.company_id.id)], limit=1)
        return accounts and accounts[0] or False
    
    def _get_fiscalyear(self, cr, uid, context=None):
        if context is None:
            context = {}
        now = time.strftime('%Y-%m-%d')
        company_id = False
        ids = context.get('active_ids', [])
        if ids and context.get('active_model') == 'account.account':
            company_id = self.pool.get('account.account').browse(cr, uid, ids[0], context=context).company_id.id
        else:  # use current company id
            company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        domain = [('company_id', '=', company_id), ('date_start', '<', now), ('date_stop', '>', now)]
        fiscalyears = self.pool.get('account.fiscalyear').search(cr, uid, domain, limit=1)
        return fiscalyears and fiscalyears[0] or False
    
    _defaults = {
        'fiscalyear_id': _get_fiscalyear,
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'fixed.asset.register.report', context=c),
        'filter': 'filter_no',
    }
    
    def onchange_filter(self, cr, uid, ids, filter='filter_no', fiscalyear_id=False, context=None):
        res = {'value': {}}
        if filter == 'filter_no':
            res['value'] = {'period_from': False, 'period_to': False, 'date_from': False , 'date_to': False}
        if filter == 'filter_date':
            res['value'] = {'period_from': False, 'period_to': False, 'date_from': time.strftime('%Y-01-01'), 'date_to': time.strftime('%Y-%m-%d')}
        if filter == 'filter_period' and fiscalyear_id:
            start_period = end_period = False
            cr.execute('''
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND p.special = false
                               ORDER BY p.date_start ASC, p.special ASC
                               LIMIT 1) AS period_start
                UNION ALL
                SELECT * FROM (SELECT p.id
                               FROM account_period p
                               LEFT JOIN account_fiscalyear f ON (p.fiscalyear_id = f.id)
                               WHERE f.id = %s
                               AND p.date_start < NOW()
                               AND p.special = false
                               ORDER BY p.date_stop DESC
                               LIMIT 1) AS period_stop''', (fiscalyear_id, fiscalyear_id))
            periods = [i[0] for i in cr.fetchall()]
            if periods and len(periods) > 1:
                start_period = periods[0]
                end_period = periods[1]
            res['value'] = {'period_from': start_period, 'period_to': end_period, 'date_from': False, 'date_to': False}
        return res
    
    def print_report_excel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        
        asset_obj = self.pool.get('account.asset.asset')
        asset_categ_obj = self.pool.get('account.asset.category')
        company_obj = self.pool.get('res.company')
        year_obj = self.pool.get('account.fiscalyear')
        period_obj = self.pool.get('account.period')
        
        asset_depreciation_line_obj = self.pool.get('account.asset.depreciation.line')
        
        fnt = Font()
        fnt.name = 'Arial'
        fnt.height = 220
        
        fnt1 = Font()
        fnt1.name = 'Arial'
        fnt1.height = 220
        fnt1.bold = 'on'
        
        # Define the font attributes for header
        content_fnt = Font()
        content_fnt.name = 'Arial'
        content_fnt.height = 220
        align_content = Alignment()
        align_content.horz = Alignment.HORZ_LEFT

        borders = Borders()
        borders.left = 0x02
        borders.right = 0x02
        borders.top = 0x02
        borders.bottom = 0x02

        # The text should be centrally aligned
        align = Alignment()
        align.horz = Alignment.HORZ_LEFT
        align.vert = Alignment.VERT_TOP
        align.wrap = Alignment.WRAP_AT_RIGHT

        # The text should be right aligned
        align1 = Alignment()
        align1.horz = Alignment.HORZ_RIGHT
        align1.vert = Alignment.VERT_TOP
        align1.wrap = Alignment.WRAP_AT_RIGHT

        # The content should be left aligned
        align2 = Alignment()
        align2.horz = Alignment.HORZ_LEFT
        align2.vert = Alignment.VERT_TOP
        align2.wrap = Alignment.WRAP_AT_RIGHT

        # The content should be right aligned
        align3 = Alignment()
        align3.horz = Alignment.HORZ_RIGHT
        align3.vert = Alignment.VERT_TOP
        align3.wrap = Alignment.WRAP_AT_RIGHT
        
        # We set the backgroundcolour here
        pattern = Pattern()
        pattern.pattern = Pattern.SOLID_PATTERN
        pattern.pattern_fore_colour = 0x1F

        # We set the backgroundcolour here
        pattern1 = Pattern()
        pattern1.pattern = Pattern.SOLID_PATTERN
        pattern1.pattern_fore_colour = 0x17

        # We set the backgroundcolour here
        pattern2 = Pattern()
        pattern2.pattern = Pattern.SOLID_PATTERN
        pattern2.pattern_fore_colour = 0xFF

        # We set the backgroundcolour here
        pattern3 = Pattern()
        pattern3.pattern = Pattern.SOLID_PATTERN
        pattern3.pattern_fore_colour = 0xFF

        # apply the above settings to the row(0) header
        style_header = XFStyle()
        style_header.font = fnt1
        style_header.pattern = pattern
        style_header.borders = borders
        style_header.alignment = align
        
        
        style_header_right = XFStyle()
        style_header_right.font = fnt1
        style_header_right.pattern = pattern
        style_header_right.borders = borders
        style_header_right.alignment = align3

        # apply the above settings to the row(1) header
        style_header1 = XFStyle()
        style_header1.font = fnt
        style_header1.pattern = pattern1
        style_header1.borders = borders
        style_header1.alignment = align1

        # apply the above settings to the content
        style_content_left = XFStyle()
        style_content_left.font = fnt
        style_content_left.pattern = pattern2
        style_content_left.borders = borders
        style_content_left.alignment = align2

        style_content_right = XFStyle()
        style_content_right.font = fnt
        style_content_right.pattern = pattern3
        style_content_right.borders = borders
        style_content_right.alignment = align3

        style_content = XFStyle()
        style_content.alignment = align_content
        style_content.font = content_fnt
        
        wb = Workbook()
        ws = wb.add_sheet('Sheet 1')
        
        ws.row(0).height = 500
        
        ws.col(0).width = 6500
        ws.col(1).width = 6500
        ws.col(2).width = 6500
        ws.col(3).width = 6500
        ws.col(4).width = 6500
        ws.col(5).width = 6500
        ws.col(6).width = 6500
        ws.col(7).width = 6500
        ws.col(8).width = 6500
        ws.col(9).width = 6500
        ws.col(10).width = 6500
        ws.col(11).width = 6500
        ws.col(12).width = 6500
        ws.col(13).width = 6500
        
        style = xlwt.easyxf('font: bold on,height 240,color_index 0X36;' 'align: horiz center;')
        
        ws.write(0, 2, 'Asset Report', style)
        
        data = self.read(cr, uid, ids, [], context=context)[0]
        
        company = company_obj.browse(cr, uid, data['company_id'][0])
        
        
        if data['fiscalyear_id']:
            year = year_obj.browse(cr, uid, data['fiscalyear_id'][0]).name
        else:
            year = ''
        
        filter = ''
        if data['filter'] == 'filter_date':
            filter = 'Dates'
        elif data['filter'] == 'filter_period':
            filter = 'Periods'
        else:
            filter = 'No Filters'
        
        from_date = False
        to_date = False
        
        ws.row(2).height = 500
        ws.write(2, 0, 'Company Name', style_header)
        ws.write(2, 1, company.name, style_header)
        ws.row(3).height = 500
        ws.write(3, 0, 'Report Run', style_header)
        ws.write(3, 1, time.strftime('%Y-%m-%d %H:%M:%S'), style_header)
        ws.row(4).height = 500
        ws.write(4, 0, 'Fiscal Year', style_header)
        ws.write(4, 1, year, style_header)
        ws.row(5).height = 500
        ws.write(5, 0, 'Filters', style_header)
        ws.write(5, 1, filter, style_header)
        ws.row(6).height = 500

        if data['filter'] == 'filter_period':
            from_period_id = data['period_from'][0]
            to_period_id = data['period_to'][0]
            
            if from_period_id and to_period_id:
                from_date = period_obj.browse(cr, uid, from_period_id).date_start
                to_date = period_obj.browse(cr, uid, to_period_id).date_stop
                
            elif from_period_id and to_period_id:
                from_date = period_obj.browse(cr, uid, from_period_id).date_start
                to_date = period_obj.browse(cr, uid, from_period_id).date_stop
                
            ws.write(6, 0, 'Start Period', style_header)
            ws.write(6, 1, data['period_from'][1], style_header)
            ws.write(7, 0, 'End Period', style_header)
            ws.write(7, 1, data['period_to'][1], style_header)
                
        elif data['filter'] == 'filter_date':
            from_date = data['date_from']
            to_date = data['date_to']
            ws.write(6, 0, 'Start Date', style_header)
            ws.write(6, 1, datetime.strptime(data['date_from'], '%Y-%m-%d').strftime('%m/%d/%Y'), style_header)
            ws.write(7, 0, 'End Date', style_header)
            ws.write(7, 1, datetime.strptime(data['date_to'], '%Y-%m-%d').strftime('%m/%d/%Y'), style_header)

        row = 10
        from_date = False
        to_date = False
        
        if data['filter'] == 'filter_period':
            from_period_id = data['period_from'][0]
            to_period_id = data['period_to'][0]
            
            if from_period_id and to_period_id:
                from_date = period_obj.browse(cr, uid, from_period_id).date_start
                to_date = period_obj.browse(cr, uid, to_period_id).date_stop
                
            elif from_period_id and to_period_id:
                from_date = period_obj.browse(cr, uid, from_period_id).date_start
                to_date = period_obj.browse(cr, uid, from_period_id).date_stop
        elif data['filter'] == 'filter_date':
            from_date = data['date_from']
            to_date = data['date_to']
        else:
            if data['fiscalyear_id']:
                from_date = year_obj.browse(cr, uid, data['fiscalyear_id'][0]).date_start
                to_date = year_obj.browse(cr, uid, data['fiscalyear_id'][0]).date_stop
            else:
                pass
        
        if data['asset_categ_ids']:
            categories_ids = data['asset_categ_ids']
        else:
            categories_ids = asset_categ_obj.search(cr, uid, [])

        if data['company_id']:
            company_ids = [data['company_id'][0]]
        else:
            company_ids = company_obj.search(cr, uid, [])
        
        for categ_id in categories_ids:
            ws.row(row).height = 500
            domain = []
            if from_date and to_date:
                #domain.append(('purchase_date', '>=', from_date))
                #domain.append(('purchase_date', '<=', to_date))
                pass
            
            domain.append(('category_id', '=', categ_id))
            domain.append(('company_id', 'in', company_ids))
            domain.append(('state', '=', 'open'))
            asset_ids = asset_obj.search(cr, uid, domain)
            asset_categ = asset_categ_obj.browse(cr, uid, categ_id)
            
            count = 1
            
            ws.row(row).height = 800
            ws.write(row, 0, 'Asset Category:', style_header)
            ws.write(row, 1, asset_categ.name, style_header)
            
            row += 1
            ws.row(row).height = 700
            ws.write(row, 0, 'No', style_header)
            ws.write(row, 1, 'Asset Tag No', style_header)
            ws.write(row, 2, 'Asset Description', style_header)
            ws.write(row, 3, 'Location', style_header)
            ws.write(row, 4, 'Document Reference', style_header)
            ws.write(row, 5, 'Requisition Date', style_header)
            ws.write(row, 6, 'Requisition Value', style_header)
            ws.write(row, 7, 'Salvage Value', style_header)
            ws.write(row, 8, 'Depreciation Method', style_header)
            ws.write(row, 9, 'Number of Usage', style_header)
            ws.write(row, 10, 'B/F Accumulated Depreciation', style_header)
            ws.write(row, 11, 'Depreciation', style_header)
            ws.write(row, 12, 'Accumulated Depreciation', style_header)
            ws.write(row, 13, 'Net Book Value', style_header)
            
            row += 1
            total_req_val = 0.0
            total_sal_val = 0.0
            total_bf_accum_depr = 0.0
            total_next_depr = 0.0
            total_accum_depr = 0.0
            total_net_book = 0.0
            
            for asset in asset_obj.browse(cr, uid, asset_ids):
                bf_accum_depr = 0.0
                next_amount_depr = 0.0 
                accum_depr_val = 0.0
                net_book_val = 0.0
                
                method = ''
                if asset.method == 'linear':
                    method = 'Linear'
                elif asset.method == 'degressive':
                    method = 'Degressive'
                
#                 location = ''
#                 
#                 if asset.move_id and asset.move_id.location_dest_id:
#                     location = asset.move_id.location_dest_id.name
                    
                ws.row(row).height = 500
                ws.write(row, 0, count, style_content_left)
                ws.write(row, 1, asset.code or '', style_content_left)
                ws.write(row, 2, asset.product_desc or '', style_content_left)
                ws.write(row, 3, asset.asset_location or '', style_content_left)
                ws.write(row, 4, asset.picking_id.name or '', style_content_left)
                row_date = datetime.strptime(asset.purchase_date, '%Y-%m-%d').strftime('%m/%d/%Y') or ''
                ws.write(row, 5, row_date, style_content_left)
                ws.write(row, 6, asset.purchase_value or 0.0, style_content_right)
                ws.write(row, 7, asset.salvage_value or 0.0, style_content_right)
                ws.write(row, 8, method or '', style_content_left)
                ws.write(row, 9, asset.method_number or '', style_content_left)
                
                if from_date and to_date:
                    period_id = period_obj.find(cr, uid, dt=from_date)
                    bf_line_ids = asset_depreciation_line_obj.search(cr, uid, [('asset_id', '=', asset.id), ('effective_period_id', '=', period_id[0])])
                    if bf_line_ids:
                        asset_bf_line = asset_depreciation_line_obj.browse(cr, uid, bf_line_ids[0])
                        bf_accum_depr = asset_bf_line.depreciated_value
                else:
                    bf_line_ids = asset_depreciation_line_obj.search(cr, uid, [('asset_id', '=', asset.id), ('move_check', '=', True)], order='effective_date desc', limit=1)
                    if bf_line_ids:
                        asset_bf_line = asset_depreciation_line_obj.browse(cr, uid, bf_line_ids[0])
                        bf_accum_depr = asset_bf_line.depreciated_value
                
                
                #To find current depreciation value: Need to search depreciation line on depreciation board for respected "Amount already depreciated".
                # Here we will match "Amount already depreciated" (bf_accum_depr) in depreciation line and matched depreciation line's current depreciation will be taken.
                if from_date and to_date:
                    period_id = period_obj.find(cr, uid, dt=from_date)
                    bf_line_ids = asset_depreciation_line_obj.search(cr, uid, [('asset_id', '=', asset.id), ('effective_date', '>=', from_date),('effective_date', '<=', to_date), ('move_check', '=', True)])
                    if bf_line_ids:
                        for asset_bf_line in asset_depreciation_line_obj.browse(cr, uid, bf_line_ids):
                            next_amount_depr += asset_bf_line.amount
                else:
                    period_id = period_obj.find(cr, uid, dt=from_date)
                    bf_line_ids = asset_depreciation_line_obj.search(cr, uid, [('asset_id', '=', asset.id), ('move_check', '=', True)])
                    if bf_line_ids:
                        for asset_bf_line in asset_depreciation_line_obj.browse(cr, uid, bf_line_ids):
                            next_amount_depr += asset_bf_line.amount
                
                ws.write(row, 10, bf_accum_depr, style_content_right)
                
                ws.write(row, 11, next_amount_depr, style_content_right)
                
                accum_depr_val = (bf_accum_depr + next_amount_depr)
                ws.write(row, 12, accum_depr_val, style_content_right)
                net_book_val = (asset.purchase_value - accum_depr_val)
                ws.write(row, 13, net_book_val, style_content_right)
                
                total_req_val += asset.purchase_value
                total_sal_val += asset.salvage_value
                total_bf_accum_depr += bf_accum_depr
                total_next_depr += next_amount_depr
                total_accum_depr += accum_depr_val
                total_net_book += net_book_val
                
                row += 1
                count += 1
                
            ws.row(row).height = 500
            ws.write(row, 0, '', style_header_right)
            ws.write(row, 1, '', style_header_right)
            ws.write(row, 2, 'Total', style_header_right)
            ws.write(row, 3, '', style_header_right)
            ws.write(row, 4, '', style_header_right)
            ws.write(row, 5, '', style_header_right)
            ws.write(row, 6, total_req_val, style_header_right)
            ws.write(row, 7, total_sal_val, style_header_right)
            ws.write(row, 8, '', style_header_right)
            ws.write(row, 9, '', style_header_right)
            ws.write(row, 10, total_bf_accum_depr, style_header_right)
            ws.write(row, 11, total_next_depr, style_header_right)
            ws.write(row, 12, total_accum_depr, style_header_right)
            ws.write(row, 13, total_net_book, style_header_right)
            
            row += 3
            
        f = cStringIO.StringIO()
        wb.save(f)
        out = base64.encodestring(f.getvalue())
        return {
            'name':'Assets Register Reports',
            'res_model':'xls.report.wizard',
            'type':'ir.actions.act_window',
            'view_type':'form',
            'view_mode':'form',
            'target':'new',
            'nodestroy': True,
            'context': {'data':out, 'name':'Asset Register Report.xls'}
        }
        
    def check_report(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = self.read(cr, uid, ids)[0]
        datas = {
            'ids': context.get('active_ids', []),
            'model': 'account.asset.asset',
            'form': data
        }
        if data['excel_report']:
            aa = self.print_report_excel(cr, uid, ids, context=context)
            return aa
        else:
            return {
                'type': 'ir.actions.report.xml',
                'report_name': 'asset.categories',
                'datas': datas,
            }

fixed_asset_register_report()

class xls_report_wizrd(osv.osv_memory):
    _name = 'xls.report.wizard'
    _columns = {
        'name': fields.char('Filename', size=128),
        'data': fields.binary('Data'),
    }

    def default_get(self, cr, uid, fields, context=None):
        res = {}
        if not context:
            return res
        res = super(xls_report_wizrd, self).default_get(cr, uid, fields, context=context)
        if context.get('name'):
            res.update({'name': context['name'], 'data': context['data']})
        return res

xls_report_wizrd()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
