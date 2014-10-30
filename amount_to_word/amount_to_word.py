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

from openerp import netsvc
from openerp.osv import fields, osv
from openerp.tools.amount_to_text_en import amount_to_text


def _amount_total_text(self, cursor, user, ids, name, arg, context=None):
    res = {}
    for order in self.browse(cursor, user, ids, context=context):
        a = ''
        b = ''
        if order.currency_id.name == 'THB':
            a = 'Baht'
            b = 'Satang'
        if order.currency_id.name == 'USD':
            a = 'Dollar'
            b = 'Cent'
        if order.currency_id.name == 'EUR':
            a = 'Euro'
            b = 'Cent'
        res[order.id] = amount_to_text(order.amount_total, 'en', a).replace('Cents', b).replace('Cent', b)
    return res


class account_invoice(osv.osv):
    _inherit = 'account.invoice'
    _columns = {
        'amount_total_text': fields.function(_amount_total_text, string='Amount Total (Text)', type='char'),
    }
account_invoice()


class sale_order(osv.osv):
    _inherit = "sale.order"
    _columns = {
        'amount_total_text': fields.function(_amount_total_text, string='Amount Total (Text)', type='char'),
    }
sale_order()


class purchase_order(osv.osv):
    _inherit = "purchase.order"
    _columns = {
        'amount_total_text': fields.function(_amount_total_text, string='Amount Total (Text)', type='char'),
    }
purchase_order()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
