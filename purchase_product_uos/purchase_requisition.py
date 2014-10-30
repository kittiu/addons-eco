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

import time
from lxml import etree

from openerp.osv import fields, osv

class purchase_requisition(osv.osv):

    _inherit = "purchase.requisition"
    
    def make_purchase_order(self, cr, uid, ids, partner_id, context=None):
        res = super(purchase_requisition, self).make_purchase_order(cr, uid, ids, partner_id, context=context)
        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')
        for id in ids:
            order = purchase_obj.browse(cr, uid, res[id])
            pricelist_id = order.pricelist_id.id
            date_order = order.date_order
            fiscal_position_id = order.fiscal_position.id
            for line in order.order_line:
                product_id = line.product_id.id
                qty = line.product_qty
                uom = line.product_uom.id
                date_planned = line.date_planned
                name = line.name
                # Get UOS if exists
                result = purchase_line_obj.onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom, 
                partner_id, date_order, fiscal_position_id, date_planned,
                name, price_unit=False, qty_uos=0, uos=False, context=context)
                # Update UOS
                product_uos_qty = result['value'].get('product_uos_qty', False)
                product_uos = result['value'].get('product_uos', False)
                if product_uos_qty or product_uos:
                    purchase_line_obj.write(cr, uid, [line.id], {'product_uos_qty': product_uos_qty, 'product_uos': product_uos})

        return res
        
purchase_requisition()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
