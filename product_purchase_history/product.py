# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2011 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011 Camptocamp (<http://www.camptocamp.com>).
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
import types

class product_product(osv.osv):
    
    def _get_supplier_invoice_lines(self, cr, uid, ids, field_names, arg=None, context=None):
        result = {}
        if not ids: return result
        for id in ids:
            result.setdefault(id, [])
        cr.execute('''SELECT avl.product_id, avl.id FROM account_invoice_line AS avl \
                     JOIN account_invoice AS ai on (avl.invoice_id = ai.id) \
                    WHERE avl.product_id in %s \
                    AND ai.state in ('open','paid') \
                    AND ai.type = 'in_invoice' \
                    ORDER BY ai.date_invoice desc''',(tuple(ids),))
        res = cr.fetchall()
        for r in res:
            result[r[0]].append(r[1])
        return result    
    
    _inherit = 'product.product'

    _columns = {
        'invoice_line_ids': fields.function(_get_supplier_invoice_lines, method=True, type='one2many', relation='account.invoice.line', string='Purchase History'),
    }
    
product_product()

