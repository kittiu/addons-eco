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
from datetime import datetime

from openerp.report import report_sxw
from openerp import pooler

class asset_categories_report(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(asset_categories_report, self).__init__(cr, uid, name, context=context)
        self.result = {}
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'sublines': self.sublines,
            'requisition_value_total': self.requisition_value_total,
            'bf_depr_value_total': self.bf_depr_value_total,
            'current_depr_value_total': self.current_depr_value_total,
            'accumlated_value_total': self.accumlated_value_total,
            'netbook_value_total': self.netbook_value_total,
            'get_start_period': self.get_start_period,
            'get_end_period': self.get_end_period,
            'get_start_date':self._get_start_date,
            'get_end_date':self._get_end_date,
            'get_filter': self._get_filter,
            'get_fiscalyear': self._get_fiscalyear,
        })
        
    def _get_fiscalyear(self, data):
        if data.get('form', False) and data['form'].get('fiscalyear_id', False):
            return pooler.get_pool(self.cr.dbname).get('account.fiscalyear').browse(self.cr, self.uid, data['form']['fiscalyear_id'][0]).name
        return ''

    def _get_filter(self, data):
        if data.get('form', False) and data['form'].get('filter', False):
            if data['form']['filter'] == 'filter_date':
                return self._translate('Date')
            elif data['form']['filter'] == 'filter_period':
                return self._translate('Periods')
        return self._translate('No Filters')

    def _get_start_date(self, data):
        if data.get('form', False) and data['form'].get('date_from', False):
            return data['form']['date_from']
        return ''
    
    def _get_end_date(self, data):
        if data.get('form', False) and data['form'].get('date_to', False):
            return data['form']['date_to']
        return ''

    def get_start_period(self, data):
        if data.get('form', False) and data['form'].get('period_from', False):
            return pooler.get_pool(self.cr.dbname).get('account.period').browse(self.cr,self.uid,data['form']['period_from'][0]).name
        return ''

    def get_end_period(self, data):
        if data.get('form', False) and data['form'].get('period_to', False):
            return pooler.get_pool(self.cr.dbname).get('account.period').browse(self.cr, self.uid, data['form']['period_to'][0]).name
        return ''
    
    def lines(self, data):
        asset_obj = self.pool.get('account.asset.asset')
        asset_categ_obj = self.pool.get('account.asset.category')
        period_obj = self.pool.get('account.period')
        year_obj = self.pool.get('account.fiscalyear')
        company_obj = self.pool.get('res.company')
        asset_depreciation_line_obj = self.pool.get('account.asset.depreciation.line')
        
        from_date = False
        to_date = False
        
        if data['form']['filter'] == 'filter_period':
            from_period_id = data['form']['period_from'][0]
            to_period_id = data['form']['period_to'][0]
            
            if from_period_id and to_period_id:
                from_date = period_obj.browse(self.cr, self.uid, from_period_id).date_start
                to_date = period_obj.browse(self.cr, self.uid, to_period_id).date_stop
                
            elif from_period_id and to_period_id:
                from_date = period_obj.browse(self.cr, self.uid, from_period_id).date_start
                to_date = period_obj.browse(self.cr, self.uid, from_period_id).date_stop
        elif data['form']['filter'] == 'filter_date':
            from_date = data['form']['date_from']
            to_date = data['form']['date_to']
        else:
#             if data['form']['fiscalyear_id']:
#                 from_date = year_obj.browse(self.cr, self.uid, data['form']['fiscalyear_id'][0]).date_start
#                 to_date = year_obj.browse(self.cr, self.uid, data['form']['fiscalyear_id'][0]).date_stop
#             else:
                pass
        
        if data['form']['asset_categ_ids']:
            categories_ids = data['form']['asset_categ_ids']
        else:
            categories_ids = asset_categ_obj.search(self.cr, self.uid, [])

        if data['form']['company_id']:
            company_ids = [data['form']['company_id'][0]]
        else:
            company_ids = company_obj.search(self.cr, self.uid, [])

        for categ_id in categories_ids:
            res = []
            categ = asset_categ_obj.browse(self.cr, self.uid, categ_id)
            
            domain = []
            if from_date and to_date:
                #domain.append(('purchase_date', '>=', from_date))
                #domain.append(('purchase_date', '<=', to_date))
                pass
            domain.append(('category_id', '=', categ_id))
            domain.append(('company_id', 'in', company_ids))
            domain.append(('state', '=', 'open')) #Only running assets.
            
            asset_ids = asset_obj.search(self.cr, self.uid, domain)
            
            count = 1
            for asset in asset_obj.browse(self.cr, self.uid, asset_ids):
                bf_accum_depr = 0.0
                next_amount_depr = 0.0
                
                # Calculcatoin of: B/F Accumulated Depreciation 
                #  Report filter: If user select Period/Date from x to y,
                #- B/F Accumulated Depreciation (B) = Amount Already Depreciated of x.
                if from_date and to_date:
                    period_id = period_obj.find(self.cr, self.uid, dt=from_date)
                    bf_line_ids = asset_depreciation_line_obj.search(self.cr, self.uid, [('asset_id', '=', asset.id), ('effective_period_id', '=', period_id[0])])
                    if bf_line_ids:
                        asset_bf_line = asset_depreciation_line_obj.browse(self.cr, self.uid, bf_line_ids[0])
                        bf_accum_depr = asset_bf_line.depreciated_value
                else:
                    bf_line_ids = asset_depreciation_line_obj.search(self.cr, self.uid, [('asset_id', '=', asset.id), ('move_check', '=', True)], order='effective_date desc', limit=1)
                    if bf_line_ids:
                        asset_bf_line = asset_depreciation_line_obj.browse(self.cr, self.uid, bf_line_ids[0])
                        bf_accum_depr = asset_bf_line.depreciated_value
               
                #- Depreciation (C) = Sum of Depreciation for x to y.
                # Calculcatoin of: Depreciation 
                if from_date and to_date:
                    period_id = period_obj.find(self.cr, self.uid, dt=from_date)
                    bf_line_ids = asset_depreciation_line_obj.search(self.cr, self.uid, [('asset_id', '=', asset.id), ('effective_date', '>=', from_date),('effective_date', '<=', to_date), ('move_check', '=', True)])
                    if bf_line_ids:
                        for asset_bf_line in asset_depreciation_line_obj.browse(self.cr, self.uid, bf_line_ids):
                            next_amount_depr += asset_bf_line.amount
                else:
                    period_id = period_obj.find(self.cr, self.uid, dt=from_date)
                    bf_line_ids = asset_depreciation_line_obj.search(self.cr, self.uid, [('asset_id', '=', asset.id), ('move_check', '=', True)])
                    if bf_line_ids:
                        for asset_bf_line in asset_depreciation_line_obj.browse(self.cr, self.uid, bf_line_ids):
                            next_amount_depr += asset_bf_line.amount
                        
                method = ''
                if asset.method == 'linear':
                    method = 'Linear'
                elif asset.method == 'degressive':
                    method = 'Degressive'
                res.append({
                    'no': count,
                    'asset_tag_no': asset.code,
                    'asset_desc': asset.product_desc or '',
                    'location': asset.asset_location or '',
                    'doc_ref': asset.picking_id.name,
                    'requisition_date': datetime.strptime(asset.purchase_date, '%Y-%m-%d').strftime('%Y-%m-%d') or '',
                    'requisition_value': asset.purchase_value,
                    'salvage_value': asset.salvage_value,
                    'depr_method': method,
                    'no_usage': asset.method_number,
                    'bf_acc_depr': bf_accum_depr, #Amount already depreciated
                    'depr': next_amount_depr,#Current Depreciated or Depreciation column on report
                    'acc_depr': (bf_accum_depr + next_amount_depr), #Using formula-> Accumulated Depreciation /
                    'net_value': (asset.purchase_value - (bf_accum_depr + next_amount_depr)),#Using formula -> Net Book Value
                })
                count += 1
            self.result.update({categ.name: res})
        return self.result
    
    def sublines(self, sline):
        return self.result[sline]
    
    def requisition_value_total(self, sline):
        req_total = 0.0
        for line in self.result[sline]:
            req_total += line['requisition_value']
        return req_total
    
    def bf_depr_value_total(self, sline):
        current_req_total = 0.0
        for line in self.result[sline]:
            current_req_total += line['bf_acc_depr']
        return current_req_total

    def current_depr_value_total(self, sline):
        current_depr_total = 0.0
        for line in self.result[sline]:
            current_depr_total += line['depr']
        return current_depr_total
    
    def accumlated_value_total(self, sline):
        accumlated_value_total = 0.0
        for line in self.result[sline]:
            accumlated_value_total += line['acc_depr']
        return accumlated_value_total
    
    def netbook_value_total(self, sline):
        netbook_value_total = 0.0
        for line in self.result[sline]:
            netbook_value_total += line['net_value']
        return netbook_value_total

report_sxw.report_sxw('report.asset.categories', 'account.asset.asset', 'addons/report_asset_register/report/asset_categories_report.rml', parser=asset_categories_report , header='internal landscape')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
