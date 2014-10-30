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
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


# class account_invoice(osv.osv):
#
#     _inherit = 'account.invoice'
#
#     def check_tax_lines(self, cr, uid, inv, compute_taxes, ait_obj):
#         super(account_invoice, self).check_tax_lines(cr, uid, inv, compute_taxes, ait_obj)
#         total = 0.0
#         for tax in inv.tax_line:
#             total += (tax.base_adjusted + tax.amount_adjusted)
#         if total != inv.amount_total:
#             raise osv.except_osv(_('Warning!'), _('You adjustment:\nBase + Tax <> Total Amount'))
#
# account_invoice()


class account_invoice_tax(osv.osv):

    _inherit = 'account.invoice.tax'

    def _get_info_amount(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            if record.base_adjusted == False and record.amount_adjusted == False:
                res[record.id] = {
                    'base_adjusted': record.base,
                    'amount_adjusted': record.amount,
                }
            else:
                res[record.id] = {
                    'base_adjusted': record.base_adjusted,
                    'amount_adjusted': record.amount_adjusted,
                }
        return res

    def _save_info_amount(self, cr, uid, id, field_name, field_value, arg, context=None):
        cr.execute('update account_invoice_tax set ' + field_name + '=%s where id=%s', (field_value, id))
        return True

    _columns = {
        'base_adjusted': fields.function(_get_info_amount, fnct_inv=_save_info_amount, string='Base', digits_compute=dp.get_precision('Account'), store=True, multi='taxinfo'),
        'amount_adjusted': fields.function(_get_info_amount, fnct_inv=_save_info_amount, string='Amount', digits_compute=dp.get_precision('Account'), store=True, multi='taxinfo'),
    }

account_invoice_tax()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
