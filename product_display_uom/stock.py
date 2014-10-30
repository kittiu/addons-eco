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

    _inherit = 'stock.move'

    def _display_qty(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for id in ids:
            res[id] = {'display_qty': False, 'display_uom': False}
        if not ids:
            return res
        uom_obj = self.pool.get('product.uom')
        for move in self.browse(cr, uid, ids, context=context):
            if move.product_id.display_uom:
                res[move.id]['display_qty'] = uom_obj._compute_qty_obj(cr, uid, move.product_uom, move.product_qty, move.product_id.display_uom, context=context)
                res[move.id]['display_uom'] = move.product_id.display_uom.id
        return res

    _columns = {
        'display_qty': fields.function(_display_qty, type='float', string="Display Quantity", multi="display", store=True),
        'display_uom': fields.function(_display_qty, type='many2one', relation='product.uom', string="Display UoM", multi="display", store=True),
    }

stock_move()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
