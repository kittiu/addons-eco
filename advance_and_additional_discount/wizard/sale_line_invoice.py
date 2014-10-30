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

from openerp.osv import osv


class sale_order_line_make_invoice(osv.osv_memory):
    _inherit = "sale.order.line.make.invoice"

    def open_invoices(self, cr, uid, ids, invoice_ids, context=None):
        res = super(sale_order_line_make_invoice, self).open_invoices(cr, uid, ids, invoice_ids, context=context)
        invoice_obj = self.pool.get('account.invoice')
        if not isinstance(invoice_ids, list):
            invoice_ids = [invoice_ids]
        for invoice_id in invoice_ids:
            invoice = invoice_obj.browse(cr, uid, invoice_id)
            order = invoice.sale_order_ids[0]
            if order and order.retention_percentage > 0.0:
                invoice_obj.write(cr, uid, [invoice_id], {'is_retention': True})
        self.pool.get('account.invoice').button_compute(cr, uid, invoice_ids, context=context)
        return res

sale_order_line_make_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
