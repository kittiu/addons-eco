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


class purchase_order_line(osv.osv):

    _inherit = 'purchase.order.line'
    _columns = {
        'discount_amount': fields.float('Discount Amount', digits_compute=dp.get_precision('Discount')),
        'discount': fields.float('Discount (%)', digits=(16, 12)),
    }

    def onchange_discount_amount(self, cr, uid, ids, discount_amount, price_unit, context=None):
        val = {'discount': 0.0}
        if price_unit:
            discount = float(discount_amount) / float(price_unit) * 100
            val['discount'] = discount
        return {'value': val}

purchase_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
