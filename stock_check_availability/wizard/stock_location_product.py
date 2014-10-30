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
        'location_id': fields.many2one('stock.location', string='Location'),
    }
    _defaults = {
        'type': 'inventory'
    }

    def action_open_window(self, cr, uid, ids, context=None):
        def get_product_id(product_ids, lines, product_field):
            field_name = product_field.pop()
            if product_field:
                if not isinstance(lines, list):
                    lines = [lines]
                for line in lines:
                    return get_product_id(product_ids, (eval('line.' + field_name)), product_field)
            else:
                for line in lines:
                    product_ids.append((eval('line.' + field_name + '.id')))

        res = super(stock_location_product, self).action_open_window(cr, uid, ids, context=context)
        product_field_lv = context.get('product_field', False)
        model_name = context.get('active_model', False)
        active_ids = context.get('active_ids', False)
        product_ids = []
        for active_id in active_ids:
            if  product_field_lv and model_name and active_id:
                product_fields = list(product_field_lv)
                product_fields.reverse()
                obj = self.pool.get(model_name)
                lines = obj.browse(cr, uid, [active_id], context)
                get_product_id(product_ids, lines, product_fields)

        display_conditions = self.read(cr, uid, ids, ['location_id'], context=context)
        if display_conditions:
            ctx = res.get('context', {})
            #add filter by location
            if  display_conditions[0]['location_id']:
                ctx.update({'location': display_conditions[0]['location_id'][0]})
            res.update({'context': ctx})

        if product_ids:
            domain = res.get('domain', {})
            res['domain'] += [tuple(['id', 'in', product_ids])]
            res.update({'domain': domain})

        return res

stock_location_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
