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
# TODO
# - Only create Payment Register, if Type = Receipt

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class account_voucher(osv.osv):

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for account_voucher in self.browse(cr, uid, ids, context=context):
            res[account_voucher.id] = {
                'amount_total': 0.0,
            }
            val = 0.0
            for line in account_voucher.payment_details:
                val += line.amount
            res[account_voucher.id]['amount_total'] = val
        return res

    def _get_account_voucher(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.voucher.pay.detail').browse(cr, uid, ids, context=context):
            result[line.voucher_id.id] = True
        return result.keys()

    def _get_journal(self, cr, uid, context=None):
        # Ignore the more complex account_voucher._get_journal() and simply return Bank in tansit journal.
        type = context.get('type', False)
        if type and type == 'receipt':
            res = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'payment_register', 'bank_intransit_journal')
            return res and res[1] or False
        else:
            res = self._make_journal_search(cr, uid, 'bank', context=context)
            return res and res[0] or False
        return False

    _inherit = 'account.voucher'
    #_rec_name = 'number'
    _columns = {
        'journal_id': fields.many2one('account.journal', 'Journal', required=True, readonly=False),
        'payment_details': fields.one2many('account.voucher.pay.detail', 'voucher_id', 'Payment Details'),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                'account.voucher.pay.detail': (_get_account_voucher, None, 10),
            },
            multi='sums', help="The total amount."),
        'is_paydetail_created': fields.boolean('Payment Details Created', readonly=True)
    }
    _defaults = {
        'journal_id': _get_journal,
    }

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if context is None:
            context = {}
        return [(r['id'], r['number'] or '') for r in self.read(cr, uid, ids, ['number'], context, load='_classic_write')]

    def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if context is None:
            context = {}
        ids = []
        if name:
            ids = self.search(cr, user, [('number', operator, name)] + args, limit=limit, context=context)
        if not ids:
            ids = self.search(cr, user, [('name', operator, name)] + args, limit=limit, context=context)
        return self.name_get(cr, user, ids, context)

    def create_payment_register(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        # Validate Payment and Payment Detail Amount
        this = self.browse(cr, uid, ids[0], context=context)
        if this.type == 'receipt':
            if (this.amount_total or 0.0) != (this.amount or 0.0):
                raise osv.except_osv(_('Unable to save!'), _('Total Amount in Payment Details must equal to Paid Amount'))
        payment_register_pool = self.pool.get('payment.register')
        for voucher in self.browse(cr, uid, ids, context=context):
            if voucher.type != 'receipt':  # Only on receipt case.
                continue
            # For each of the Payment Detail, create a new payment detail.
            period_pool = self.pool.get('account.period')
            ctx = context.copy()
            ctx.update({'company_id': voucher.company_id.id})
            for payment_detail in voucher.payment_details:
                pids = period_pool.find(cr, uid, payment_detail.date_due, context=ctx)
                res = {'voucher_id': voucher.id,
                        'pay_detail_id': payment_detail.id,
                        'name': payment_detail.name,
                        'type': payment_detail.type,
                        'check_no': payment_detail.check_no,
                        'date_due': payment_detail.date_due,
                        'original_pay_currency_id': voucher.currency_id and voucher.currency_id.id or voucher.company_id.currency_id.id,
                        'original_pay_amount': payment_detail.amount,
                        'amount': payment_detail.amount,
                        'date': payment_detail.date_due,
                        'period_id': pids and pids[0] or False,
                }
                payment_register_pool.create(cr, uid, res, context)
            self.write(cr, uid, [voucher.id], {'is_paydetail_created': True})
        return True

    def cancel_voucher(self, cr, uid, ids, context=None):
        # If this voucher has related payment register, make sure all of them are cancelled first.
        payment_register_pool = self.pool.get('payment.register')
        for voucher in self.browse(cr, uid, ids, context=context):
            register_ids = payment_register_pool.search(cr, uid, [('voucher_id', '=', voucher.id), ('state', '<>', 'cancel')], limit=1)
            if register_ids:  # if at least 1 record not cancelled, raise error
                raise osv.except_osv(_('Error!'), _('You can not cancel this Payment.\nYou need to cancel all Payment Details associate with this payment first.'))
            #register_ids = payment_register_pool.search(cr, uid, [('voucher_id', '=', voucher.id)])
            if register_ids == []:  # All register has been deleted.
                self.write(cr, uid, [voucher.id], {'is_paydetail_created': False})
        # Normal call
        res = super(account_voucher, self).cancel_voucher(cr, uid, ids, context=context)
        return res

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        if context is None:
            context = {}
        default = default.copy()
        default['is_paydetail_created'] = False
        return super(account_voucher, self).copy(cr, uid, id, default, context=context)

account_voucher()


class account_voucher_pay_detail(osv.osv):

    _name = "account.voucher.pay.detail"
    _description = "Payment Details"

    _columns = {
        'name': fields.char('Bank/Branch', size=128, required=False),
        'voucher_id': fields.many2one('account.voucher', 'Voucher Reference', ondelete='cascade', select=True),
        'type': fields.selection([
            ('check', 'Check'),
            ('cash', 'Cash'),
            ('transfer', 'Transfer'),
            ], 'Type', required=True, select=True, change_default=True),
        'check_no': fields.char('Check No.', size=64),
        'date_due': fields.date('Check Date'),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account')),
        #'date_payin': fields.date('Pay-in Date'),
    }

account_voucher_pay_detail()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
