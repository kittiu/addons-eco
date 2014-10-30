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
import types
from openerp import netsvc
from openerp.osv import fields, osv
from openerp.tools.translate import _

class stock_picking(osv.osv):

    _inherit = "stock.picking"

    _columns = {
        'create_uid':  fields.many2one('res.users', 'Creator', readonly=True),
        'product_categ_id': fields.many2one('product.category', 'Product Category'),
    }
    
    def write(self, cr, uid, ids, vals, context=None):
        if not isinstance(ids, types.ListType): # Ensure it is a list before proceeding.
            ids = [ids]        
        for id in ids:
            if vals.get('location_id', False):
                cr.execute('update stock_move set location_id = %s where picking_id = %s', (vals.get('location_id'), id))
            if vals.get('location_dest_id', False):
                cr.execute('update stock_move set location_dest_id = %s where picking_id = %s', (vals.get('location_dest_id'), id))
        return  super(stock_picking, self).write(cr, uid, ids, vals, context=context)

stock_picking()


class stock_move(osv.osv):

    _inherit = "stock.move"

    def _default_location_destination(self, cr, uid, context=None):
        if context is None: 
            context = {}
        if context.get('location_dest_id', False):
            location_dest_id = context.get('location_dest_id')
            return location_dest_id
        return super(stock_move, self)._default_location_destination(cr, uid, context=context)

    def _default_location_source(self, cr, uid, context=None):
        if context is None: 
            context = {}
        if context.get('location_id', False):
            location_id = context.get('location_id')
            return location_id
        return super(stock_move, self)._default_location_source(cr, uid, context=context)

    _defaults = {
        'location_id': _default_location_source,
        'location_dest_id': _default_location_destination,
    }
    
    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        if context == None:
            context = {}
        res = super(stock_move,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        if context.get('product_categ_id', False):
            if res['fields'].get('product_id', False):
                res['fields']['product_id']['domain'] = [('categ_id','child_of',context.get('product_categ_id', False))]
        return res 
        
    def onchange_move_type(self, cr, uid, ids, type, context=None):
        if context.get('simplified_move', False):
            return True
        return super(stock_move, self).onchange_move_type(cr, uid, ids, type, context=context)

stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
