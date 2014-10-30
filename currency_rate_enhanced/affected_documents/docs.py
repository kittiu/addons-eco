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

# This file will contain all create account_move method of every document.


class account_invoice(osv.osv):

    _inherit = "account.invoice"

    def action_move_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if ids:
            invoice = self.browse(cr, uid, ids[0], context=context)
            if invoice.type in ('out_invoice', 'out_refund'):
                context.update({'pricelist_type': 'sale'})
            elif invoice.type in ('in_invoice', 'in_refund'):
                context.update({'pricelist_type': 'purchase'})
        return super(account_invoice, self).action_move_create(cr, uid, ids, context=context)

account_invoice()


class account_voucher(osv.osv):

    _inherit = "account.voucher"

    def action_move_line_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        if ids:
            voucher = self.browse(cr, uid, ids[0], context=context)
            if voucher.type in ('sale', 'receipt'):
                context.update({'pricelist_type': 'sale'})
            elif voucher.type in ('purchase', 'payment'):
                context.update({'pricelist_type': 'purchase'})
        return super(account_voucher, self).action_move_line_create(cr, uid, ids, context=context)

account_voucher()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
