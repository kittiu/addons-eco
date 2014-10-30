# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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


class account_invoice(osv.osv):

    _inherit = 'account.invoice'
    _columns = {
        'ref_sale_order_id': fields.many2one('sale.order', 'Ref Sales Order', readonly=True, states={'draft': [('readonly', False)]}),
    }

    def write(self, cr, uid, ids, vals, context=None):
        # if has ref_sale_order_id, write it here.
        res = super(account_invoice, self).write(cr, uid, ids, vals, context=context)
        if not isinstance(ids, list):
            ids = [ids]
        for invoice in self.browse(cr, uid, ids, context=context):
            purchase = invoice.purchase_order_ids and invoice.purchase_order_ids[0] or False
            if purchase and purchase.ref_sale_order_id:
                cr.execute('update account_invoice set ref_sale_order_id=%s where id=%s and ref_sale_order_id is null', (purchase.ref_sale_order_id.id, invoice.id))
        return res

    def action_move_create(self, cr, uid, ids, context=None):
        res = super(account_invoice, self).action_move_create(cr, uid, ids, context=context)
        # Update all account move line for this account_move
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.move_id and invoice.ref_sale_order_id:
                cr.execute('update account_move_line set ref_sale_order_id = %s where move_id = %s', (invoice.ref_sale_order_id.id, invoice.move_id.id))
        return res

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
