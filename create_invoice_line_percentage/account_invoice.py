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


class account_invoice(osv.osv):

    _inherit = "account.invoice"

    def _is_last_invoice(self, cr, uid, ids, type_inv, context=None):
        module_name = (type_inv == 'in_invoice' and 'purchase.order' or 'sale.order')
        order_field_name = (type_inv == 'in_invoice' and 'purchase_order_ids' or 'sale_order_ids')

        inv_ids = self.search(cr, uid, [('type', '=', type_inv),
                                        ('id', 'in', ids), ('state', '!=', 'cancel'),
                                        ('amount_deposit', '=', 0.00), ('amount_advance', '=', 0.00)], context=context)
        if inv_ids:
            order_obj = self.pool.get(module_name)
            #Get Purchase Order has create invoice by line percent
            orders = order_obj.search(cr, uid, [('invoice_ids', 'in', inv_ids), ('invoiced_rate', '!=', False)], context=context)
            found_ids = self.search(cr, uid, [('type', '=', type_inv),
                                        ('state', '!=', 'cancel'),
                                        (order_field_name, 'in', orders),
                                        '|', ('amount_deposit', '>', 0.00), ('amount_advance', '>', 0.00)], context=context)
            if found_ids:
                raise osv.except_osv(
                            _('Advance/Deposit!'),
                            _('Unable to cancel this invoice.!\n First cancel the last invoice'))

        return True

    def action_cancel(self, cr, uid, ids, context=None):
        self._is_last_invoice(cr, uid, ids, 'out_invoice', context)
        self._is_last_invoice(cr, uid, ids, 'in_invoice', context)
        super(account_invoice, self).action_cancel(cr, uid, ids, context)
        return True

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
