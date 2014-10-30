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

import time
from openerp import netsvc
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class payment_register(osv.osv):

    def _get_reference(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('reference', False)

    def _get_narration(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('narration', False)

    def _make_journal_search(self, cr, uid, ttype, context=None):
        journal_pool = self.pool.get('account.journal')
        return journal_pool.search(cr, uid, [('type', '=', ttype)], limit=1)

    def _get_exchange_rate_currency(self, cr, uid, context=None):
        """
        Return the default value for field original_pay_currency_id: the currency of the journal
        if there is one, otherwise the currency of the user's company
        """
        if context is None:
            context = {}
        journal_pool = self.pool.get('account.journal')
        journal_id = context.get('journal_id', False)
        if journal_id:
            journal = journal_pool.browse(cr, uid, journal_id, context=context)
            if journal.currency:
                return journal.currency.id
        #no journal given in the context, use company currency as default
        return self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id

    def _paid_amount_in_company_currency(self, cr, uid, ids, name, args, context=None):
        if not ids:
            return {}
        res = {}
        rate = 1.0
        for register in self.browse(cr, uid, ids, context=context):
            if register.currency_id:
                if register.company_id.currency_id.id == register.original_pay_currency_id.id:
                    rate = 1 / register.exchange_rate
                else:
                    ctx = context.copy()
                    ctx.update({'date': register.date})
                    voucher_rate = self.browse(cr, uid, register.id, context=ctx).currency_id.rate
                    company_currency_rate = register.company_id.currency_id.rate
                    rate = voucher_rate * company_currency_rate
            res[register.id] = register.amount / rate
        return res

    _name = 'payment.register'
    _description = 'Payment Register'
    _inherit = ['mail.thread']
    _order = "date desc, id desc"
    _rec_name = 'number'
    _columns = {
        # Document
        'number': fields.char('Number', size=32, readonly=True,),
        # Header Information from Payment document
        'voucher_id': fields.many2one('account.voucher', 'Customer Payment', readonly=True, states={'draft': [('readonly', False)]}),
        'partner_id': fields.related('voucher_id', 'partner_id', type='many2one', relation='res.partner', string='Partner', store=True, readonly=True),
        'date_payment': fields.related('voucher_id', 'date', type='date', relation='account.voucher', string='Payment Date', store=True, readonly=True),
        'journal_transit_id': fields.related('voucher_id', 'journal_id', type='many2one', relation='account.journal', string='Payment in Transit', store=True, readonly=True),
        'account_transit_id': fields.related('voucher_id', 'account_id', type='many2one', relation='account.account', string='Account in Transit', store=True, readonly=True),
        'original_pay_currency_id': fields.many2one('res.currency', 'Original Payment Currency', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'amount_pay_total': fields.related('voucher_id', 'amount', type='float', relation='account.voucher', string='Payment Total', store=True, readonly=True),
        'original_pay_amount': fields.float('Original Pay Amount', digits_compute=dp.get_precision('Account'), required=True, readonly=True, states={'draft': [('readonly', False)]}),
        # Company Information
        'company_id': fields.related('voucher_id', 'company_id', type='many2one', relation='res.company', string='Company', store=True, readonly=True),
        'company_currency_id': fields.related('company_id', 'currency_id', type='many2one', relation='res.currency', string='Company Currency', store=True, readonly=True),
        'paid_amount_in_company_currency': fields.function(_paid_amount_in_company_currency, string='Paid Amount in Company Currency', type='float', readonly=True),
        'memo': fields.char('Memo', size=256, readonly=True, states={'draft': [('readonly', False)]}),
        'reference': fields.char('Ref #', size=64, readonly=True, states={'draft': [('readonly', False)]}, help="Transaction reference number."),
        # Multi Currency from Original Currency to Target Currency
        'is_multi_currency': fields.boolean('Multi Currency Voucher', help='Fields with internal purpose only that depicts if the voucher is a multi currency one or not'),
        'exchange_rate': fields.float('Exchange Rate', digits=(12, 6), required=True, readonly=True, states={'draft': [('readonly', False)]},),
        'exchange_rate_payin': fields.float('Exchange Rate Payin', digits=(12, 6), required=True, readonly=True, states={'draft': [('readonly', False)]},),
        # Payment Detail
        'pay_detail_id': fields.many2one('account.voucher.pay.detail', 'Payment Detail Ref', ondelete='restrict', select=True),
        'name': fields.char('Bank/Branch', size=128, readonly=True, states={'draft': [('readonly', False)]}),
        'type': fields.selection([
            ('check', 'Check'),
            ('cash', 'Cash'),
            ('transfer', 'Transfer'),
            ], 'Type', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'check_no': fields.char('Check No.', size=64, readonly=True, states={'draft': [('readonly', False)]}),
        'date_due': fields.date('Date Due', readonly=True, states={'draft': [('readonly', False)]}),
        'amount': fields.float('Amount', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft': [('readonly', False)]}),
        # Payment Register
        'date': fields.date('Pay-in Date', readonly=True, select=True, states={'draft': [('readonly', False)]}, help="Effective date for accounting entries"),
        'period_id': fields.many2one('account.period', 'Period', readonly=True, states={'draft': [('readonly', False)]}),
        'journal_id': fields.many2one('account.journal', 'Target Bank', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'account_id': fields.many2one('account.account', 'Account', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'currency_id': fields.many2one('res.currency', 'Currency', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'amount_payin': fields.float('Pay-in Amount', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft': [('readonly', False)]}),
        # Miscellenous
        'narration': fields.text('Notes', readonly=False),
        'state': fields.selection(
            [('draft', 'Draft'),
             ('cancel', 'Cancelled'),
             ('posted', 'Posted'),
             ('bounce_check', 'Bounced Check'),
            ], 'Status', readonly=True, size=32,
            help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed payment register. \
                        \n* The \'Posted\' status is used when user create payment register,a Register number is generated and accounting entries are created in account \
                        \n* The \'Cancelled\' status is used when user cancel payment register.'),
        'move_id': fields.many2one('account.move', 'Account Entry'),
        'move_ids': fields.related('move_id', 'line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
        # Diff
        #'writeoff_amount': fields.function(_get_writeoff_amount, string='Difference Amount', type='float', readonly=True, help="Computed as the difference between the amount stated in the voucher and the sum of allocation on the voucher lines."),
        'writeoff_amount': fields.float('Diff Amount', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft': [('readonly', False)]}, help="Computed as the difference between the amount stated in the Payment Detail and the Payment Register."),
        'writeoff_amount_local': fields.float('Diff Amount (local)', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft': [('readonly', False)]}, help="Computed as the difference between the amount stated in the Payment Detail and the Payment Register."),
        'gainloss_amount': fields.float('Gain / Loss', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft': [('readonly', False)]}),
        'payment_option': fields.selection([('with_writeoff', 'Reconcile Payment Balance')], 'Payment Difference', required=True, readonly=True, states={'draft': [('readonly', False)]}, help="This field helps you to choose what you want to do with the eventual difference between the paid amount and the sum of allocated amounts. You can either choose to keep open this difference on the partner's account, or reconcile it with the payment(s)"),
        'writeoff_acc_id': fields.many2one('account.account', 'Counterpart Account', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'comment': fields.char('Counterpart Comment', size=64, required=False, readonly=False),
        'new_register_id': fields.many2one('payment.register', 'New Payment Detail', readonly=True, help='This new Payment Register is created to replace the one with bounced check.'),
    }
    _defaults = {
        'reference': _get_reference,
        'narration': _get_narration,
        'state': 'draft',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self, cr, uid, c: self.pool.get('res.company')._company_default_get(cr, uid, 'payment.register', context=c),
        'payment_option': 'with_writeoff',
        'comment': _('Write-Off'),
        'exchange_rate': 1.0,
        'exchange_rate_payin': 1.0,
        'original_pay_currency_id': _get_exchange_rate_currency,
    }

    def create(self, cr, uid, vals, context=None):
        register = super(payment_register, self).create(cr, uid, vals, context=context)
        self.create_send_note(cr, uid, [register], context=context)
        return register

    def unlink(self, cr, uid, ids, context=None):
        for t in self.read(cr, uid, ids, ['state'], context=context):
            if t['state'] not in ('draft', 'cancel'):
                raise osv.except_osv(_('Invalid Action!'), _('Cannot delete voucher(s) which are already opened or paid.'))
        return super(payment_register, self).unlink(cr, uid, ids, context=context)

    def copy(self, cr, uid, id, default=None, context=None):
        if context is None:
            context = {}
        if context.get('bounce_check', False):
            if default is None:
                default = {}
            default.update({
                'state': 'draft',
                'number': False,
                'move_id': False,
                'line_cr_ids': False,
                'line_dr_ids': False,
            })
            if 'date' not in default:
                default['date'] = time.strftime('%Y-%m-%d')
            return super(payment_register, self).copy(cr, uid, id, default, context)
        else:
            raise osv.except_osv(_('Error!'), _('Duplication of Payment Detail not allowed. If this payment detail is cancelled, and you want to renew, use "Set to Draft" instead.'))

    def create_send_note(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            message = "Payment Register <b>created</b>."
            self.message_post(cr, uid, [obj.id], body=message, subtype="payment_register.mt_register", context=context)

    def post_send_note(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            message = "Payment Register '%s' is <b>posted</b>." % obj.move_id.name
            self.message_post(cr, uid, [obj.id], body=message, subtype="payment_register.mt_register", context=context)

    def validate_register(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            if not obj.journal_id.id or not obj.date:
                raise osv.except_osv(_('Warning!'), _('Pay-in Date and Target Bank is not selected.'))
        self.action_move_line_create(cr, uid, ids, context=context)
        return True

    def register_move_line_create(self, cr, uid, register_id, move_id, company_currency, current_currency, context=None):
        if context is None:
            context = {}
        move_line_obj = self.pool.get('account.move.line')
        register_brw = self.pool.get('payment.register').browse(cr, uid, register_id, context)
        ctx = context.copy()
        ctx.update({'date': register_brw.date})
        amount = self._convert_amount(cr, uid, register_brw.amount_payin, register_brw.id, context=ctx)
        move_line = {
            'journal_id': register_brw.journal_id.id,
            'period_id': register_brw.period_id.id,
            'name': register_brw.name or '/',
            'account_id': register_brw.account_id.id,
            'move_id': move_id,
            'partner_id': register_brw.partner_id.id,
            'currency_id': company_currency != current_currency and current_currency or False,
            #'analytic_account_id': register_brw.account_analytic_id and register_brw.account_analytic_id.id or False,
            'amount_currency': company_currency != current_currency and register_brw.amount_payin or 0.0,
            'quantity': 1,
            'credit': amount < 0 and -amount or 0.0,
            'debit': amount > 0 and amount or 0.0,
            'date': register_brw.date
        }
        move_line_id = move_line_obj.create(cr, uid, move_line)
        return move_line_id

    def writeoff_move_line_create(self, cr, uid, register, move_id, company_currency, current_currency, context=None):
        if context is None:
            context = {}
        if not register.writeoff_amount_local:
            return False
        amount = register.writeoff_amount_local
        move_line = {
            'journal_id': register.journal_id.id,
            'period_id': register.period_id.id,
            'name': register.name or '/',
            'account_id': register.writeoff_acc_id.id,
            'move_id': move_id,
            'partner_id': register.partner_id.id,
            'currency_id': company_currency != current_currency and current_currency or False,
            #'analytic_account_id': register_brw.account_analytic_id and register_brw.account_analytic_id.id or False,
            'amount_currency': company_currency != current_currency and register.writeoff_amount or 0.0,
            'quantity': 1,
            'credit': amount < 0 and -amount or 0.0,
            'debit': amount > 0 and amount or 0.0,
            'date': register.date
        }
        move_line_id = self.pool.get('account.move.line').create(cr, uid, move_line)
        return move_line_id

    def gainloss_move_line_create(self, cr, uid, register, move_id, context=None):
        if context is None:
            context = {}
        company = register.company_id
        ctx = context.copy()
        ctx.update({'date': register.date})
        amount_payin_company_currency = self._convert_amount(cr, uid, register.amount_payin, register.id, context=ctx)
        # make the rounding as defined in company currency.
        currency_obj = self.pool.get('res.currency')
        amount_payin_company_currency = currency_obj.round(cr, uid, company.currency_id, amount_payin_company_currency)
        paid_amount_in_company_currency = currency_obj.round(cr, uid, company.currency_id, register.paid_amount_in_company_currency)
        writeoff_amount_local = currency_obj.round(cr, uid, company.currency_id, register.writeoff_amount_local)
        # amount to post
        amount = amount_payin_company_currency - paid_amount_in_company_currency + writeoff_amount_local
        if abs(amount) < 10 ** -4:            
            return False
        if not company.income_currency_exchange_account_id or not company.expense_currency_exchange_account_id:
            raise osv.except_osv(_('Accounting Error !'),
                _('Gain/Loss Exchange Rate Account is not setup properly! Please see Settings > Configuration > Accounting.'))            
        move_line = {
            'journal_id': register.journal_id.id,
            'period_id': register.period_id.id,
            'name': register.name or '/',
            'account_id': amount > 0 and company.income_currency_exchange_account_id.id or company.expense_currency_exchange_account_id.id,
            'move_id': move_id,
            'partner_id': register.partner_id.id,
            'currency_id': False,
            #'analytic_account_id': register_brw.account_analytic_id and register_brw.account_analytic_id.id or False,
            'amount_currency': 0.0,
            'quantity': 1,
            'credit': amount > 0 and amount or 0.0,
            'debit': amount < 0 and -amount or 0.0,
            'date': register.date
        }
        move_line_id = self.pool.get('account.move.line').create(cr, uid, move_line)
        # Assign amount to gainloss_amount field
        self.write(cr, uid, [register.id], {'gainloss_amount': amount})
        return move_line_id

    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Confirm the register given in ids and create the journal entries for each of them
        '''
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        for register in self.browse(cr, uid, ids, context=context):
            if register.move_id:
                continue
            company_currency = self._get_company_currency(cr, uid, register.id, context)
            current_currency = self._get_current_currency(cr, uid, register.id, context)
            # we select the context to use accordingly if it's a multicurrency case or not
            context = self._sel_context(cr, uid, register.id, context)
            # But for the operations made by _convert_amount, we always need to give the date in the context
            ctx = context.copy()
            ctx.update({'date': register.date})
            # Create the account move record.
            move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, register.id, context=context), context=context)
            # Get the name of the account_move just created
            name = move_pool.browse(cr, uid, move_id, context=context).name
            # Create the first line of the register
            move_line_pool.create(cr, uid, self.first_move_line_get(cr, uid, register.id, move_id, company_currency, current_currency, context), context)
            # Create one move line per register line where amount is not 0.0
            self.register_move_line_create(cr, uid, register.id, move_id, company_currency, current_currency, context)
            # Create the writeoff/gainloss line if needed
            self.writeoff_move_line_create(cr, uid, register, move_id, company_currency, current_currency, context)
            self.gainloss_move_line_create(cr, uid, register, move_id, context)
            # We post the register.
            self.write(cr, uid, [register.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            self.post_send_note(cr, uid, [register.id], context=context)
            if register.journal_id.entry_posted:
                move_pool.post(cr, uid, [move_id], context={})
        return True

    def onchange_journal_date(self, cr, uid, ids, journal_id, original_pay_amount, original_pay_currency_id, company_id, amount, amount_payin, date, context=None):
        if context is None:
            context = {}
        if not ids or not journal_id:
            return False
        voucher = self.browse(cr, uid, ids[0])
        # Set Account and Currency
        currency_obj = self.pool.get('res.currency')
        journal_pool = self.pool.get('account.journal')
        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        account_id = journal.default_debit_account_id.id or journal.default_credit_account_id.id
        currency = journal.currency or journal.company_id.currency_id
        original_pay_currency = currency_obj.browse(cr, uid, original_pay_currency_id)
        vals = {'value': {}}
        vals['value'].update({'account_id': account_id})
        vals['value'].update({'currency_id': currency.id})
        # Compute Payment Rate
        ctx = context.copy()
        ctx.update({'date': voucher.date_payment})
        exchange_rate = currency_obj._get_conversion_rate(cr, uid, currency, original_pay_currency, context=ctx)
        ctx.update({'date': date})
        exchange_rate_payin = currency_obj._get_conversion_rate(cr, uid, currency, original_pay_currency, context=ctx)
        vals['value'].update({'exchange_rate': exchange_rate})
        vals['value'].update({'exchange_rate_payin': exchange_rate_payin})
        # Compute period
        period_pool = self.pool.get('account.period')
        ctx.update({'company_id': company_id})
        pids = period_pool.find(cr, uid, date, context=ctx)
        if pids:
            vals['value'].update({'period_id': pids[0]})
        # Compute Amount
        res = self.onchange_rate(cr, uid, ids, exchange_rate, exchange_rate_payin, amount, amount_payin, original_pay_amount, context=context)
        for key in res.keys():
            vals[key].update(res[key])
        return vals

    def onchange_date(self, cr, uid, ids, journal_id, original_pay_amount, original_pay_currency_id, company_id, amount, amount_payin, date, context=None):
        if context is None:
            context = {}
        res = {'value': {}}
        #set the period of the register
        period_pool = self.pool.get('account.period')
        ctx = context.copy()
        ctx.update({'company_id': company_id})
        pids = period_pool.find(cr, uid, date, context=ctx)
        if pids:
            res['value'].update({'period_id': pids[0]})
        return res

    def onchange_rate(self, cr, uid, ids, exchange_rate, exchange_rate_payin, amount, amount_payin, original_pay_amount, context=None):
        res = {'value': {}}
        amount = exchange_rate and float(original_pay_amount) / float(exchange_rate) or float(amount)
        amount_payin = exchange_rate_payin and float(original_pay_amount) / float(exchange_rate_payin) or float(amount_payin)
        res['value'].update({'amount': amount,
                            'amount_payin': amount_payin,
                            })
        return res

    def onchange_amount(self, cr, uid, ids, field, amount, amount_payin, writeoff_amount, exchange_rate_payin, context=None):
        res = {'value': {}}
        if field in ('amount', 'amount_payin'):
            diff = (amount or 0.0) - (amount_payin or 0.0)
            res['value']['writeoff_amount'] = round(diff, 2)
            res['value']['writeoff_amount_local'] = round(diff * exchange_rate_payin, 2)
        elif field == 'writeoff_amount':
            payin = (amount or 0.0) - (writeoff_amount or 0.0)
            res['value']['amount_payin'] = round(payin, 2)
            res['value']['writeoff_amount_local'] = round(writeoff_amount * exchange_rate_payin, 2)
        return res

    def _unpost_register(self, cr, uid, ids, context=None):
        reconcile_pool = self.pool.get('account.move.reconcile')
        move_pool = self.pool.get('account.move')
        for register in self.browse(cr, uid, ids, context=context):
            recs = []
            for line in register.move_ids:
                if line.reconcile_id:
                    recs += [line.reconcile_id.id]
                if line.reconcile_partial_id:
                    recs += [line.reconcile_partial_id.id]

            reconcile_pool.unlink(cr, uid, recs)

            if register.move_id:
                move_pool.button_cancel(cr, uid, [register.move_id.id])
                move_pool.unlink(cr, uid, [register.move_id.id])
        return True

    def cancel_register(self, cr, uid, ids, context=None):
        self._unpost_register(cr, uid, ids, context=context)
        message = "Payment Register <b>cancelled</b>."
        self.message_post(cr, uid, ids, body=message, subtype="payment_register.mt_register", context=context)
        res = {
            'state': 'cancel',
            'move_id': False,
        }
        self.write(cr, uid, ids, res)
        return True

    # Case bounce check, same as cancel, but status to 'bounce_check' then create new one with reference to the old.
    def bounce_check(self, cr, uid, ids, context=None):
        assert len(ids) == 1, 'This option should only be used for a single id at a time.'
        self._unpost_register(cr, uid, ids, context=context)
        message = "Payment Register <b>bounced check</b>."
        self.message_post(cr, uid, ids, body=message, subtype="payment_register.mt_register", context=context)
        ctx = context.copy()
        ctx.update({'bounce_check': True})
        # Create a new document
        new_register_id = self.copy(cr, uid, ids[0], {'date': False, 'journal_id': False, 'amount_payin': False}, context=ctx)
        res = {
            'state': 'bounce_check',
            'move_id': False,
            'new_register_id': new_register_id,
        }
        self.write(cr, uid, ids, res)
        return True

    def cancel_to_draft(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for register_id in ids:
            message = "Payment Register <b>set to draft</b>."
            self.message_post(cr, uid, [register_id], body=message, subtype="payment_register.mt_register", context=context)
            wf_service.trg_delete(uid, 'payment.register', register_id, cr)
            wf_service.trg_create(uid, 'payment.register', register_id, cr)
        self.write(cr, uid, ids, {'state': 'draft'})
        return True

    def _get_company_currency(self, cr, uid, register_id, context=None):
        return self.pool.get('payment.register').browse(cr, uid, register_id, context).journal_id.company_id.currency_id.id

    def _get_current_currency(self, cr, uid, register_id, context=None):
        register = self.pool.get('payment.register').browse(cr, uid, register_id, context)
        return register.currency_id.id or self._get_company_currency(cr, uid, register.id, context)

    def _sel_context(self, cr, uid, register_id, context=None):
        company_currency = self._get_company_currency(cr, uid, register_id, context)
        current_currency = self._get_current_currency(cr, uid, register_id, context)
        if current_currency != company_currency:
            context_multi_currency = context.copy()
            register_brw = self.pool.get('payment.register').browse(cr, uid, register_id, context)
            context_multi_currency.update({'date': register_brw.date})
            return context_multi_currency
        return context

    def _convert_amount(self, cr, uid, amount, register_id, context=None):
        currency_obj = self.pool.get('res.currency')
        register = self.browse(cr, uid, register_id, context=context)
        res = amount
        if register.currency_id.id == register.company_id.currency_id.id:
            # the rate specified on the voucher is for the company currency
            res = currency_obj.round(cr, uid, register.company_id.currency_id, (amount * register.exchange_rate))
        else:
            # the rate specified on the voucher is not relevant, we use all the rates in the system
            res = currency_obj.compute(cr, uid, register.currency_id.id, register.company_id.currency_id.id, amount, context=context)
        return res

    def first_move_line_get(self, cr, uid, register_id, move_id, company_currency, current_currency, context=None):

        register_brw = self.pool.get('payment.register').browse(cr, uid, register_id, context)
        debit = credit = 0.0
        # TODO: is there any other alternative then the voucher type ??
        # ANSWER: We can have payment and receipt "In Advance".
        # TODO: Make this logic available.
        # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
        credit = register_brw.paid_amount_in_company_currency
        if debit < 0:
            credit = -debit
            debit = 0.0
        if credit < 0:
            debit = -credit
            credit = 0.0
        sign = debit - credit < 0 and -1 or 1
        #set the first line of the voucher
        move_line = {
                'name': register_brw.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': register_brw.account_transit_id.id,
                'move_id': move_id,
                'journal_id': register_brw.journal_transit_id.id,
                'period_id': register_brw.period_id.id,
                'partner_id': register_brw.partner_id.id,
                'currency_id': company_currency != current_currency and current_currency or False,
                'amount_currency': company_currency != current_currency and sign * register_brw.amount or 0.0,
                'date': register_brw.date,
                'date_maturity': register_brw.date_due
            }
        return move_line

    def account_move_get(self, cr, uid, register_id, context=None):
        '''
        This method prepare the creation of the account move related to the given register.
        :param register_id: Id of voucher for which we are creating account_move.
        :return: mapping between fieldname and value of account move to create
        :rtype: dict
        '''
        seq_obj = self.pool.get('ir.sequence')
        register_brw = self.pool.get('payment.register').browse(cr, uid, register_id, context)
        if register_brw.number:
            name = register_brw.number
        elif register_brw.journal_id.sequence_id:
            if not register_brw.journal_id.sequence_id.active:
                raise osv.except_osv(_('Configuration Error !'),
                    _('Please activate the sequence of selected journal !'))
            name = seq_obj.next_by_id(cr, uid, register_brw.journal_id.sequence_id.id, context=context)
        else:
            raise osv.except_osv(_('Error!'),
                        _('Please define a sequence on the journal.'))
        if not register_brw.reference:
            ref = name.replace('/', '')
        else:
            ref = register_brw.reference

        move = {
            'name': name,
            'journal_id': register_brw.journal_id.id,
            'narration': register_brw.narration,
            'date': register_brw.date,
            'ref': ref,
            'period_id': register_brw.period_id and register_brw.period_id.id or False
        }
        return move

payment_register()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
