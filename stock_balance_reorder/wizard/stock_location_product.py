# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
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
from openerp import netsvc
from openerp.osv import fields, osv

class stock_location_product(osv.osv_memory):
    _inherit = "stock.location.product"
    _columns = {
        'is_inout': fields.boolean('Show In/Out Quantity', required=False), 
        'is_safety': fields.boolean('Show Safety/Reorder Quantity', required=False),
        'is_show_negative': fields.boolean('Show Only Negative Reorder', required=False), 
    }
    _defaults = {
        'is_inout': True,
        'is_safety': False,     
        'is_show_negative': False,        
    }
    
    def action_open_window(self, cr, uid, ids, context=None):
        res = super(stock_location_product, self).action_open_window(cr, uid, ids,  context=context)
        # Additional fields to context
        display_conditions = self.read(cr, uid, ids, ['is_inout','is_safety','is_show_negative'], context=context)
        if display_conditions:
            ctx = res.get('context', {})
            ctx.update({'is_inout': display_conditions[0]['is_inout']})
            ctx.update({'is_safety': display_conditions[0]['is_safety']})
            ctx.update({'is_show_negative': display_conditions[0]['is_show_negative']})
            res.update({'context': ctx})
            
        if not res.get('domain', False): 
            res['domain'] = []
            
        if display_conditions[0]['is_safety']:        
            location_obj = self.pool.get('product.product')
            location_ids = location_obj._get_location(cr, uid, ids, context=res['context'])
            # Data filter only "Reorder Point Rule"     
            res['domain'] += [tuple(['orderpoint_ids','<>',False])] + [tuple(['orderpoint_ids.location_id','in',location_ids])]
            if display_conditions[0]['is_show_negative']:
                res['domain'] += [tuple(['qty_reorder','<',0])]

        return res

stock_location_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
