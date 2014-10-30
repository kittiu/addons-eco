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

class stock_picking(osv.osv):
    
    _inherit = 'stock.picking'
    
    def action_invoice_create(self, cr, uid, ids, journal_id=False,
                              group=False, type='out_invoice', context=None):
        res = super(stock_picking, self).action_invoice_create(cr, uid, ids, journal_id,
                                                               group, type, context=context)
        # Getting partner_invoice_id from DO's Order
        if type in ['out_invoice','out_refund']:
            picking_obj = self.pool.get('stock.picking.out')
            order_obj = self.pool.get('sale.order')
            inv_obj = self.pool.get('account.invoice')
            for picking_id in res:
                invoice_id = res.get(picking_id)
                picking = picking_obj.browse(cr, uid, picking_id)
                order_ids = order_obj.search(cr, uid, [('name','=',picking.origin)])
                if order_ids:
                    order = order_obj.browse(cr, uid, order_ids[0])
                    if order and order.partner_invoice_id:
                        inv_obj.write(cr, uid, [invoice_id], {'partner_invoice_id': order.partner_invoice_id.id}, context=context)
        return res

stock_picking()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
