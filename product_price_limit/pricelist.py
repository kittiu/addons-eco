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
import openerp.addons.decimal_precision as dp

class product_pricelist_item(osv.osv):
    
    _inherit = 'product.pricelist.item'
    _columns = {
        'price_subtract_percent': fields.float('% Subtract', digits=(16,4), help='Specify the percentage to subtract from the calculated price.'),
        'price_subtract_amount': fields.float('Amount Subtract',
            digits_compute= dp.get_precision('Product Price'), help='Specify the fixed amount to subtract from the calculated price.'),
    }
    _defaults = {
        'price_subtract_percent': 0.0,
        'price_subtract_amount': 0.0,
    }
        
product_pricelist_item()

class product_pricelist(osv.osv):
    
    _inherit = 'product.pricelist'

    def price_limit_get(self, cr, uid, ids, prod_id, qty, partner=None, context=None):
        res_multi = self.price_get_multi(cr, uid, pricelist_ids=ids, products_by_qty_by_partner=[(prod_id, qty, partner)], context=context)
        res = res_multi[prod_id]
        # Base on computed price, calculate for price_limit
        price = res[ids[-1]]
        pricelist_item = self.pool.get('product.pricelist.item').browse(cr, uid, res_multi.get('item_id', ids[-1]))
        if pricelist_item.price_subtract_percent or pricelist_item.price_subtract_amount: # no price limit
            price_limit = price * (1 - pricelist_item.price_subtract_percent) - pricelist_item.price_subtract_amount
            res[ids[-1]] = price_limit
        else:
            res[ids[-1]] = 0.0
        # --
        res.update({'item_id': {ids[-1]: res_multi.get('item_id', ids[-1])}})
        return res
    
product_pricelist()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
