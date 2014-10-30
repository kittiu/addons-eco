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


class purchase_order(osv.osv):

    _inherit = "purchase.order"
    _columns = {
        'ref_order_id': fields.many2one('sale.order', 'Ref Sales Order', domain="[('state','not in',('draft','sent','cancel'))]", readonly=False),
    }

    def create(self, cr, uid, vals, context=None):
        order = super(purchase_order, self).create(cr, uid, vals, context=context)
        if vals.get('requisition_id', False):
            self.update_ref_purchase_order(cr, uid, [vals['requisition_id']], context)
        return order

    def update_ref_purchase_order(self, cr, uid, requisition_ids, context=None):
        res = {}
        pr_obj = self.pool.get('purchase.requisition')
        for pr in pr_obj.browse(cr, uid, requisition_ids, context=context):
            res = {
                'ref_order_id': pr.id and pr.ref_order_id.id or False,
            }
            pr_ids = self.search(cr, uid, [('requisition_id', 'in', requisition_ids)])
            self.write(cr, uid, pr_ids, res, context=context)
        return True

    def update_ref_incoming_shipment(self, cr, uid, purchase_ids, context=None):
        res = {}
        sk_obj = self.pool.get('stock.picking.in')
        stock_ids = sk_obj.search(cr, uid, [('purchase_id', 'in', purchase_ids)])
        for po_rec in self.browse(cr, uid, purchase_ids, context=context):
            res = {
                'ref_order_id': po_rec.ref_order_id and po_rec.ref_order_id.id or False,
            }
            stock_ids = sk_obj.search(cr, uid, [('purchase_id', '=', po_rec.id)])
            sk_obj.write(cr, uid, stock_ids, res, context=context)
        return True

purchase_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
