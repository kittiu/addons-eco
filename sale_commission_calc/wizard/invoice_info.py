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


class invoice_info(osv.osv_memory):

    """Invoice Info"""

    _name = "invoice.info"
    _description = "Invoice Info"

    def _get_invoice_id(self, cr, uid, context=None):
        line_obj = self.pool.get('commission.worksheet.line').browse(cr, uid, context['active_id'])
        return line_obj.invoice_id and line_obj.invoice_id.id or False

    _columns = {
        'invoice_id': fields.many2one('account.invoice', 'Invoice Number', readonly=True),
        'invoice_info_line': fields.one2many('invoice.info.line', 'invoice_info_id', 'Invoice Info Lines', readonly=True)
    }

    _defaults = {
        'invoice_id': _get_invoice_id
    }

    def onchange_invoice_id(self, cr, uid, ids, invoice_id, context=None):
        invoice = self.pool.get('account.invoice').browse(cr, uid, invoice_id)
        invoice_info_line = []
        for line in invoice.invoice_line:
            invoice_info_line.append([0, 0, {
                'product_id': line.product_id and line.product_id.id or False,
                'name': line.name,
                'quantity': line.quantity,
                'uos_id': line.uos_id and line.uos_id.id or False,
                'price_unit': line.price_unit,
                'price_subtotal': line.price_subtotal
                }])
        return {'value': {
            'invoice_info_line': invoice_info_line,
        }}

invoice_info()


class invoice_info_line(osv.osv_memory):

    """Invoice Info Lines"""

    _name = "invoice.info.line"
    _description = "Invoice Info Lines"

    _columns = {
        'invoice_info_id': fields.many2one('invoice.info', 'Invoice Info'),
        'product_id': fields.many2one('product.product', 'Product'),
        'name': fields.char('Description'),
        'quantity': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        'uos_id': fields.many2one('product.uom', 'UoM'),
        'price_unit': fields.float('Unit Price', digits_compute=dp.get_precision('Account')),
        'price_subtotal': fields.float('Subtotal', digits_compute=dp.get_precision('Account')),
    }

invoice_info_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
