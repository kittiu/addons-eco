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


class stock_picking(osv.osv):
    
    _inherit = "stock.picking"

    def do_partial(self, cr, uid, ids, partial_datas, context=None):
        # pass pricelist_type variable based on pick.type, this will be passed to the currency.compute()
        pick_types = list(set([x.type for x in self.browse(cr, uid, ids)]))
        if len(pick_types) > 1:
            raise osv.except_osv(_('Error'), _('Mixed Picking In/Out not allowed!'))
        if len(pick_types) == 1:
            if pick_types[0] == 'in':
                context.update({'pricelist_type': 'purchase'})
                cr.pricelist_type = 'sale'  # Actually this is not a proper way of passing value, but no choice.
            elif pick_types[0] == 'out':
                context.update({'pricelist_type': 'sale'})
            #cr.pricelist_type = 'purchase'
        return super(stock_picking, self).do_partial(cr, uid, ids, partial_datas, context=context)
        
stock_picking()


class res_currency(osv.osv):
    
    _inherit = "res.currency"

    def compute(self, cr, uid, from_currency_id, to_currency_id, from_amount,
                round=True, currency_rate_type_from=False, currency_rate_type_to=False, context=None):
        if not context:
            context = {}
        if hasattr(cr, 'pricelist_type') and cr.pricelist_type:  # because problem with stock.do_partial(), which not pass context, we pass it this here.
            context.update({'pricelist_type': cr.pricelist_type})
        return super(res_currency, self).compute(cr, uid, from_currency_id, to_currency_id, from_amount,
                round=round, currency_rate_type_from=currency_rate_type_from, currency_rate_type_to=currency_rate_type_to, context=context)
        
res_currency()




        
        
        
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
