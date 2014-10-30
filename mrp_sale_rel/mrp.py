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

from openerp.osv import fields, osv

class mrp_production(osv.osv):
    
    _inherit = 'mrp.production'
    
    def _get_ids_order_and_parent_from_origin(self, cr, origin, context=None):
        order_id = False
        parent_id = False
        if origin:
            origin = origin.split(':')
            order = origin[0]
            parent = len(origin) > 1 and origin[1] or ''
            if order and order != '':
                cr.execute('select id from sale_order where name=%s order by id desc', (order,))
                res = cr.fetchone()
                order_id = res and res[0] or False
            if parent and parent != '':
                cr.execute('select id from mrp_production where name=%s order by id desc', (parent,))
                res = cr.fetchone()
                parent_id = res and res[0] or False    
        return order_id, parent_id
        
    _columns = {
        'order_id': fields.many2one('sale.order', 'Sales Order', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'parent_id': fields.many2one('mrp.production', 'Parent', required=False, readonly=True, change_default=True),
    }

    def init(self, cr):
        # This is a helper to guess "old" Relations
        cr.execute('select id, origin from mrp_production where length(origin) > 0')
        origins = cr.dictfetchall()
        for origin in origins:
            production_id = origin['id']
            order_id, parent_id = self._get_ids_order_and_parent_from_origin(cr, origin['origin'])
            if order_id:
                cr.execute('update mrp_production set order_id = %s where id = %s', (order_id, production_id,))
            if parent_id:
                cr.execute('update mrp_production set parent_id = %s where id = %s', (parent_id, production_id,))

    def create(self, cr, uid, vals, context=None):
        origin = vals.get('origin', False)
        order_id = vals.get('order_id', False)
        if origin: # If origin has SO# or MO#,
            order_id, parent_id = self._get_ids_order_and_parent_from_origin(cr, origin)
            vals.update({'order_id': order_id, 'parent_id': parent_id})
        elif order_id: # No origin, if order_id is specified, update it back to origin.
            so_number = self.pool.get('sale.order').browse(cr, uid, order_id).name
            vals.update({'origin': so_number})
        res = super(mrp_production, self).create(cr, uid, vals, context=context)
        return res

mrp_production()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
