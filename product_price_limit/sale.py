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
from openerp.tools.translate import _


class sale_order(osv.osv):
    
    _inherit = 'sale.order'
    
    def check_price_limit(self, cr, uid, ids, context=None):
        context = context or {}
        
        # If not have authority, check price limit.
        if not self.pool.get('ir.model.access').check_groups(cr, uid, "product_price_limit.group_approve_over_price_limit"):
            sale_obj = self.pool.get('sale.order')
            orders = sale_obj.browse(cr, uid, ids)
            
            for order in orders:
                pricelist = order.pricelist_id.id
                partner_id = order.partner_id.id
                date_order = order.date_order
                
                for line in order.order_line:
                    product = line.product_id.id
                    qty = line.product_uom_qty
                    uom = line.product_uom.id
                    price = line.price_unit
                    price_limit = self.pool.get('product.pricelist').price_limit_get(cr, uid, [pricelist],
                                product, qty or 1.0, partner_id, {
                                    'uom': uom,
                                    'date': date_order,
                                    })[pricelist]
                    if price < price_limit:
                        raise osv.except_osv(_('Need authorized person to confirm this order!'), _('The product "%s" price is too low!' % line.product_id.name))

        return True

sale_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
