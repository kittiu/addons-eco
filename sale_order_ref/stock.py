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

from openerp.osv import osv, fields


class stock_picking_in(osv.osv):

    _inherit = 'stock.picking.in'
    _columns = {
        'ref_order_id': fields.many2one('sale.order', 'Ref Sales Order', domain="[('state','not in',('draft','sent','cancel'))]", ondelete='set null', select=True),
    }

stock_picking_in()


class stock_picking(osv.osv):

    _inherit = 'stock.picking'
    _columns = {
        'ref_order_id': fields.many2one('sale.order', 'Ref Sales Order', domain="[('state','not in',('draft','sent','cancel'))]", ondelete='set null', select=True),
    }

    def create(self, cr, uid, vals, context=None):
        res = super(stock_picking, self).create(cr, uid, vals, context=context)
        if vals.get('purchase_id', False):
            self.pool.get('purchase.order').update_ref_incoming_shipment(cr, uid, [vals.get('purchase_id', False)], context)
        return res

stock_picking()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
