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


class purchase_requisition_line(osv.osv):

    _inherit = "purchase.requisition.line"
    _columns = {
        'product_uom_category_id': fields.integer("Product UOM Category ID"),
    }

    def onchange_product_id(self, cr, uid, ids, product_id, product_uom_id, context=None):
        res = super(purchase_requisition_line, self).onchange_product_id(cr, uid, ids, product_id, product_uom_id, context=context)
        product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
        if product.id:
            res['value'].update({'product_uom_category_id': product.uom_id.category_id.id})
        return res

purchase_requisition_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
