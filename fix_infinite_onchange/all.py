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

class stock_move(osv.osv):
    
    _inherit = "stock.move"

    def onchange_quantity(self, cr, uid, ids, product_id, product_qty,
                          product_uom, product_uos):
        res = super(stock_move, self).onchange_quantity(cr, uid, ids, product_id, product_qty, product_uom, product_uos)
        if product_uos and product_uom and (product_uom != product_uos):
            result = res.get('value', {})
            if result.get('product_uos_qty', False):
                prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
                result.update({'product_uos_qty': round(result['product_uos_qty'], prec)})
        return res

    def onchange_uos_quantity(self, cr, uid, ids, product_id, product_uos_qty,
                          product_uos, product_uom):
        res = super(stock_move, self).onchange_uos_quantity(cr, uid, ids, product_id, product_uos_qty, product_uos, product_uom)
        if product_uos and product_uom and (product_uom != product_uos):
            result = res.get('value', {})
            if result.get('product_qty', False):
                prec = self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Unit of Measure')
                result.update({'product_qty': round(result['product_qty'], prec)})
        return res

stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
