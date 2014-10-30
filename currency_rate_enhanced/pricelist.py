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


class product_pricelist(osv.osv):

    _inherit = 'product.pricelist'

    def price_get(self, cr, uid, ids, prod_id, qty, partner=None, context=None):

        if context is None:
            context = {}
        # Assumption: all price list ids passed into this method should be either sales or purchase
        # Then we can pass the this flag in context, so that currency.compute() can use it to use selling or purchase rate
        # Otherwise, we raise the message, so we know there are other cases
        if not isinstance(ids, list):
            ids = [ids]
        results = self.read(cr, uid, list(set(ids)), ['type'], context=context)
        pricelist_types = list(set([x['type'] for x in results]))
        pricelist_type = 'sale'  # Default Transaction Type
        if len(pricelist_types) == 1:
            pricelist_type = pricelist_types[0]
        elif len(pricelist_types) > 1:
            raise osv.except_osv(_('Error!'), _('Mixed Sale/Purchase pricelist exception!'))
        context.update({'pricelist_type': pricelist_type})

        res = super(product_pricelist, self).price_get(cr, uid, ids, prod_id, qty, partner=partner, context=context)
        return res

product_pricelist()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
