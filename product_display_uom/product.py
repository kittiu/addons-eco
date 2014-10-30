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


class product_product(osv.osv):

    _inherit = 'product.product'

    _columns = {
        'display_uom': fields.many2one('product.uom', 'Display UoM', required=False, help="Additional UoM to be used when displaying reports"),
    }

    def get_product_available(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        res = super(product_product, self).get_product_available(cr, uid, ids, context=context)
        uom_obj = self.pool.get('product.uom')
        if context.get('display_uom', False):
            product_ids = res.keys()
            for product in self.browse(cr, uid, product_ids, context=context):  # 'id': 'display_uom'
                res[product.id] = product.display_uom and uom_obj._compute_qty_obj(cr, uid, product.uom_id, res[product.id], product.display_uom, context=context) or 0.0
        return res

#     def init(self, cr):
#         # This is a helper to guess "old" Relations between pickings and invoices
#         cr.execute('update product_product p set display_uom = 14 \
#                     where product_tmpl_id in (select id from product_template where uom_id =12)')

product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
