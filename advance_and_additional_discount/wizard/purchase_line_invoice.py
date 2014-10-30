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

import ast
from openerp.osv import osv


class purchase_line_invoice(osv.osv_memory):

    _inherit = 'purchase.order.line_invoice'

    def makeInvoices(self, cr, uid, ids, context=None):
        invoice_obj = self.pool.get('account.invoice')
        purchase_obj = self.pool.get('purchase.order')
        purchase_line_obj = self.pool.get('purchase.order.line')
        res = super(purchase_line_invoice, self).makeInvoices(cr, uid, ids, context=context)
        # retrieve invoice_ids from domain, and compute it.
        domain = ast.literal_eval(res.get('domain'))
        invoice_ids = domain[0][2]
        # get purchase order
        if context.get('active_model', False) == 'purchase.order':
            purchase = purchase_obj.browse(cr, uid, context.get('active_id', False))
            invoice_obj.write(cr, uid, invoice_ids, {'add_disc': purchase.add_disc or 0.0}, context)
        else:  # try getting it from purchase_line
            purchase_line = purchase_line_obj.browse(cr, uid, context.get('active_ids')[0])
            invoice_obj.write(cr, uid, invoice_ids, {'add_disc': purchase_line.order_id.add_disc or 0.0}, context)
        invoice_obj.button_compute(cr, uid, invoice_ids, context=context)
        invoice_obj.button_reset_taxes(cr, uid, invoice_ids, context)
        return res

purchase_line_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
