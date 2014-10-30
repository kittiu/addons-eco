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
from lxml import etree

from openerp import netsvc
from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp
from openerp.tools.translate import _


class account_billing(osv.osv):

    def _get_type(self, cr, uid, context=None):
        if context is None:
            context = {}
        return context.get('type', False)

    def _get_period(self, cr, uid, context=None):
        if context is None: context = {}
        if context.get('period_id', False):
            return context.get('period_id')
        periods = self.pool.get('account.period').find(cr, uid)
        return periods and periods[0] or False

    def _make_journal_search(self, cr, uid, ttype, context=None):
        journal_pool = self.pool.get('account.journal')
        return journal_pool.search(cr, uid, [('type', '=', ttype)], limit=1)

    def _get_journal(self, cr, uid, context=None):
        if context is None: context = {}
        invoice_pool = self.pool.get('account.invoice')
        journal_pool = self.pool.get('account.journal')
        if context.get('invoice_id', False):
            currency_id = invoice_pool.browse(cr, uid, context['invoice_id'], context=context).currency_id.id
            journal_id = journal_pool.search(cr, uid, [('currency', '=', currency_id)], limit=1)
            return journal_id and journal_id[0] or False
        if context.get('journal_id', False):
            return context.get('journal_id')
        if not context.get('journal_id', False) and context.get('search_default_journal_id', False):
            return context.get('search_default_journal_id')

        ttype = 'bank'
        res = self._make_journal_search(cr, uid, ttype, context=context)
        return res and res[0] or False

    def _get_tax(self, cr, uid, context=None):
        if context is None: context = {}
        journal_pool = self.pool.get('account.journal')
        journal_id = context.get('journal_id', False)
        if not journal_id:
            ttype = context.get('type', 'bank')
            res = journal_pool.search(cr, uid, [('type', '=', ttype)], limit=1)
            if not res:
                return False
            journal_id = res[0]

        if not journal_id:
            return False
        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        account_id = journal.default_credit_account_id or journal.default_debit_account_id
        if account_id and account_id.tax_ids:
            tax_id = account_id.tax_ids[0].id
            return tax_id
        return False

    def _get_payment_rate_currency(self, cr, uid, context=None):
        """
        Return the default value for field payment_rate_currency_id: the currency of the journal
        if there is one, otherwise the currency of the user's company
        """
        if context is None: context = {}
        journal_pool = self.pool.get('account.journal')
        journal_id = context.get('journal_id', False)
        if journal_id:
            journal = journal_pool.browse(cr, uid, journal_id, context=context)
            if journal.currency:
                return journal.currency.id
        #no journal given in the context, use company currency as default
        return self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.currency_id.id

    def _get_currency(self, cr, uid, context=None):
        if context is None: context = {}
        journal_pool = self.pool.get('account.journal')
        journal_id = context.get('journal_id', False)
        if journal_id:
            journal = journal_pool.browse(cr, uid, journal_id, context=context)
            if journal.currency:
                return journal.currency.id
        return False

    def _get_partner(self, cr, uid, context=None):
        if context is None: context = {}
        return context.get('partner_id', False)

    def _get_reference(self, cr, uid, context=None):
        if context is None: context = {}
        return context.get('reference', False)

    def _get_narration(self, cr, uid, context=None):
        if context is None: context = {}
        return context.get('narration', False)

    def _get_amount(self, cr, uid, context=None):
        if context is None:
            context= {}
        return context.get('amount', 0.0)

    def name_get(self, cr, uid, ids, context=None):
        if not ids:
            return []
        if context is None: context = {}
        return [(r['id'], (r['number'] or 'N/A')) for r in self.read(cr, uid, ids, ['number'], context, load='_classic_write')]

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        mod_obj = self.pool.get('ir.model.data')
        if context is None: context = {}

        if view_type == 'form':
            if not view_id and context.get('invoice_type'):
                if context.get('invoice_type') in ('out_invoice', 'out_refund'):
                    result = mod_obj.get_object_reference(cr, uid, 'account_billing', 'view_vendor_receipt_form')
                else:
                    result = mod_obj.get_object_reference(cr, uid, 'account_billing', 'view_vendor_payment_form')
                result = result and result[1] or False
                view_id = result
            if not view_id and context.get('line_type'):
                if context.get('line_type') == 'customer':
                    result = mod_obj.get_object_reference(cr, uid, 'account_billing', 'view_vendor_receipt_form')
                else:
                    result = mod_obj.get_object_reference(cr, uid, 'account_billing', 'view_vendor_payment_form')
                result = result and result[1] or False
                view_id = result

        res = super(account_billing, self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])

        if context.get('type', 'sale') in ('purchase', 'payment'):
            nodes = doc.xpath("//field[@name='partner_id']")
            for node in nodes:
                node.set('domain', "[('supplier', '=', True)]")
        res['arch'] = etree.tostring(doc)
        return res

    def _compute_billing_amount(self, cr, uid, line_cr_ids, amount):
        credit = 0.0
        sign = 1
        for l in line_cr_ids:
            credit += l['amount']
        return -(amount - sign * (credit))

    def onchange_line_ids(self, cr, uid, ids, line_cr_ids, amount, billing_currency, context=None):
        context = context or {}
        if not line_cr_ids:
            return {'value':{}}
        line_osv = self.pool.get("account.billing.line")
        line_cr_ids = resolve_o2m_operations(cr, uid, line_osv, line_cr_ids, ['amount'], context)

        #compute the field is_multi_currency that is used to hide/display options linked to secondary currency on the billing
        is_multi_currency = False
        if billing_currency:
            # if the billing currency is not False, it means it is different than the company currency and we need to display the options
            is_multi_currency = True
        else:
            #loop on the billing lines to see if one of these has a secondary currency. If yes, we need to define the options
            for billing_line in line_cr_ids:
                company_currency = False
                company_currency = billing_line.get('move_line_id', False) and self.pool.get('account.move.line').browse(cr, uid, billing_line.get('move_line_id'), context=context).company_id.currency_id.id
                if billing_line.get('currency_id', company_currency) != company_currency:
                    is_multi_currency = True
                    break
        return {'value': {'billing_amount': self._compute_billing_amount(cr, uid, line_cr_ids, amount), 'is_multi_currency': is_multi_currency}}

    def _get_billing_amount(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        currency_obj = self.pool.get('res.currency')
        res = {}
        for billing in self.browse(cr, uid, ids, context=context):
            credit = 0.0
            sign = 1
            for l in billing.line_cr_ids:
                credit += l.amount
            currency = billing.currency_id or billing.company_id.currency_id
            res[billing.id] =  - currency_obj.round(cr, uid, currency, billing.amount - sign * (credit))
        return res

    def _paid_amount_in_company_currency(self, cr, uid, ids, name, args, context=None):
        if not ids: return {}
        res = {}
        rate = 1.0
        for billing in self.browse(cr, uid, ids, context=context):
            if billing.currency_id:
                if billing.company_id.currency_id.id == billing.payment_rate_currency_id.id:
                    rate =  1 / billing.payment_rate
                else:
                    ctx = context.copy()
                    ctx.update({'date': billing.date})
                    billing_rate = self.browse(cr, uid, billing.id, context=ctx).currency_id.rate
                    company_currency_rate = billing.company_id.currency_id.rate
                    rate = billing_rate * company_currency_rate
            res[billing.id] =  billing.amount / rate
        return res

    _name = 'account.billing'
    _description = 'Accounting Billing'
    _inherit = ['mail.thread']
    _order = "date desc, id desc"
    _columns = {
        'active': fields.boolean('Active', help=""),
#        'type':fields.selection([
#            ('receipt','Receipt'),
#        ],'Default Type', readonly=True, states={'draft':[('readonly',False)]}),
        'name':fields.char('Memo', size=256, readonly=True, states={'draft':[('readonly',False)]}),
        'date':fields.date('Date', readonly=True, select=True, states={'draft':[('readonly',False)]}, help="Effective date for accounting entries"),
        'journal_id':fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'account_id':fields.many2one('account.account', 'Account', required=False, readonly=True, states={'draft':[('readonly',False)]}),
        'line_ids':fields.one2many('account.billing.line','billing_id','Billing Lines', readonly=True, states={'draft':[('readonly',False)]}),
        'line_cr_ids':fields.one2many('account.billing.line','billing_id','Credits',
                                      context={'default_type':'cr'}, readonly=True, states={'draft':[('readonly',False)]}),
        'period_id': fields.many2one('account.period', 'Period', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'narration':fields.text('Notes', readonly=True, states={'draft':[('readonly',False)]}),
        'currency_id': fields.related('journal_id','currency', type='many2one', relation='res.currency', string='Currency', readonly=True),
        'company_id': fields.many2one('res.company', 'Company', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'state':fields.selection(
            [('draft','Draft'),
             ('cancel','Cancelled'),
             ('billed','Billed')
            ], 'Status', readonly=True, size=32,
            help=' * The \'Draft\' status is used when a user is encoding a new and unconfirmed billing. \
                        \n* The \'Billed\' status is used when user create billing,a billing number is generated \
                        \n* The \'Cancelled\' status is used when user cancel billing.'),
        'amount': fields.float('Total', digits_compute=dp.get_precision('Account'), required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'tax_amount':fields.float('Tax Amount', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft':[('readonly',False)]}),
        'reference': fields.char('Ref #', size=64, readonly=True, states={'draft':[('readonly',False)]}, help="Transaction reference number."),
        'number': fields.char('Number', size=32, readonly=True,),
        #ktu, 'move_id':fields.many2one('account.move', 'Account Entry'),
        #ktu, 'move_ids': fields.related('move_id','line_id', type='one2many', relation='account.move.line', string='Journal Items', readonly=True),
        'partner_id':fields.many2one('res.partner', 'Partner', change_default=1, readonly=True, states={'draft':[('readonly',False)]}),
        #ktu, 'audit': fields.related('move_id','to_check', type='boolean', help='Check this box if you are unsure of that journal entry and if you want to note it as \'to be reviewed\' by an accounting expert.', relation='account.move', string='To Review'),
        #ktu, 'paid': fields.function(_check_paid, string='Paid', type='boolean', help="The billing has been totally paid."),
#        'pay_now':fields.selection([
#            ('pay_now','Pay Directly'),
#            ('pay_later','Pay Later or Group Funds'),
#        ],'Payment', select=True, readonly=True, states={'draft':[('readonly',False)]}),
        'tax_id': fields.many2one('account.tax', 'Tax', readonly=True, states={'draft':[('readonly',False)]}, domain=[('price_include','=', False)], help="Only for tax excluded from price"),
        #'pre_line':fields.boolean('Previous Payments ?', required=False),
        'date_due': fields.date('Due Date', readonly=True, select=True, states={'draft':[('readonly',False)]}),
        'payment_option':fields.selection([
                                           ('without_writeoff', 'Keep Open'),
                                           ('with_writeoff', 'Reconcile Payment Balance'),
                                           ], 'Payment Difference', required=True, readonly=True, states={'draft': [('readonly', False)]}, help="This field helps you to choose what you want to do with the eventual difference between the paid amount and the sum of allocated amounts. You can either choose to keep open this difference on the partner's account, or reconcile it with the payment(s)"),
#        'writeoff_acc_id': fields.many2one('account.account', 'Counterpart Account', readonly=True, states={'draft': [('readonly', False)]}),
        'comment': fields.char('Counterpart Comment', size=64, required=True, readonly=True, states={'draft': [('readonly', False)]}),
#        'analytic_id': fields.many2one('account.analytic.account','Write-Off Analytic Account', readonly=True, states={'draft': [('readonly', False)]}),
        'billing_amount': fields.function(_get_billing_amount, string='Billing Amount', type='float', store=True, readonly=True, help="Computed as the difference between the amount stated in the billing and the sum of allocation on the billing lines."),
        'payment_rate_currency_id': fields.many2one('res.currency', 'Payment Rate Currency', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'payment_rate': fields.float('Exchange Rate', digits=(12,6), required=True, readonly=True, states={'draft': [('readonly', False)]},
            help='The specific rate that will be used, in this billing, between the selected currency (in \'Payment Rate Currency\' field)  and the billing currency.'),
        'paid_amount_in_company_currency': fields.function(_paid_amount_in_company_currency, string='Paid Amount in Company Currency', type='float', readonly=True),
        'is_multi_currency': fields.boolean('Multi Currency Billing', help='Fields with internal purpose only that depicts if the billing is a multi currency one or not'),
        'payment_id':fields.many2one('account.voucher', 'Payment Ref#', required=False, readonly=True),
    }
    _defaults = {
        'active': True,
        'period_id': _get_period,
        'partner_id': _get_partner,
        'journal_id':_get_journal,
        'currency_id': _get_currency,
        'reference': _get_reference,
        'narration':_get_narration,
        'amount': _get_amount,
        #'type':_get_type,
        'state': 'draft',
        #'pay_now': 'pay_now',
        'name': '',
        'date': lambda *a: time.strftime('%Y-%m-%d'),
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.billing',context=c),
        'tax_id': _get_tax,
        'payment_option': 'without_writeoff',
        'comment': _('Write-Off'),
        'payment_rate': 1.0,
        'payment_rate_currency_id': _get_payment_rate_currency,
    }

    def create(self, cr, uid, vals, context=None):
        billing =  super(account_billing, self).create(cr, uid, vals, context=context)
        self.create_send_note(cr, uid, [billing], context=context)
        return billing

    def compute_tax(self, cr, uid, ids, context=None):
        tax_pool = self.pool.get('account.tax')
        partner_pool = self.pool.get('res.partner')
        position_pool = self.pool.get('account.fiscal.position')
        billing_line_pool = self.pool.get('account.billing.line')
        billing_pool = self.pool.get('account.billing')
        if context is None: context = {}

        for billing in billing_pool.browse(cr, uid, ids, context=context):
            billing_amount = 0.0
            for line in billing.line_ids:
                billing_amount += line.untax_amount or line.amount
                line.amount = line.untax_amount or line.amount
                billing_line_pool.write(cr, uid, [line.id], {'amount':line.amount, 'untax_amount':line.untax_amount})

            if not billing.tax_id:
                self.write(cr, uid, [billing.id], {'amount':billing_amount, 'tax_amount':0.0})
                continue

            tax = [tax_pool.browse(cr, uid, billing.tax_id.id, context=context)]
            partner = partner_pool.browse(cr, uid, billing.partner_id.id, context=context) or False
            taxes = position_pool.map_tax(cr, uid, partner and partner.property_account_position or False, tax)
            tax = tax_pool.browse(cr, uid, taxes, context=context)

            total = billing_amount
            total_tax = 0.0

            if not tax[0].price_include:
                for line in billing.line_ids:
                    for tax_line in tax_pool.compute_all(cr, uid, tax, line.amount, 1).get('taxes', []):
                        total_tax += tax_line.get('amount', 0.0)
                total += total_tax
            else:
                for line in billing.line_ids:
                    line_total = 0.0
                    line_tax = 0.0

                    for tax_line in tax_pool.compute_all(cr, uid, tax, line.untax_amount or line.amount, 1).get('taxes', []):
                        line_tax += tax_line.get('amount', 0.0)
                        line_total += tax_line.get('price_unit')
                    total_tax += line_tax
                    untax_amount = line.untax_amount or line.amount
                    billing_line_pool.write(cr, uid, [line.id], {'amount':line_total, 'untax_amount':untax_amount})

            self.write(cr, uid, [billing.id], {'amount':total, 'tax_amount':total_tax})
        return True

    def onchange_price(self, cr, uid, ids, line_ids, tax_id, partner_id=False, context=None):
        context = context or {}
        tax_pool = self.pool.get('account.tax')
        partner_pool = self.pool.get('res.partner')
        position_pool = self.pool.get('account.fiscal.position')
        line_pool = self.pool.get('account.billing.line')
        res = {
            'tax_amount': False,
            'amount': False,
        }
        billing_total = 0.0

        line_ids = resolve_o2m_operations(cr, uid, line_pool, line_ids, ["amount"], context)

        total_tax = 0.0
        for line in line_ids:
            line_amount = 0.0
            line_amount = line.get('amount',0.0)

            if tax_id:
                tax = [tax_pool.browse(cr, uid, tax_id, context=context)]
                if partner_id:
                    partner = partner_pool.browse(cr, uid, partner_id, context=context) or False
                    taxes = position_pool.map_tax(cr, uid, partner and partner.property_account_position or False, tax)
                    tax = tax_pool.browse(cr, uid, taxes, context=context)

                if not tax[0].price_include:
                    for tax_line in tax_pool.compute_all(cr, uid, tax, line_amount, 1).get('taxes', []):
                        total_tax += tax_line.get('amount')

            billing_total += line_amount
        total = billing_total + total_tax

        res.update({
            'amount': total or billing_total,
            'tax_amount': total_tax
        })
        return {
            'value': res
        }

    def onchange_term_id(self, cr, uid, ids, term_id, amount):
        term_pool = self.pool.get('account.payment.term')
        terms = False
        due_date = False
        default = {'date_due':False}
        if term_id and amount:
            terms = term_pool.compute(cr, uid, term_id, amount)
        if terms:
            due_date = terms[-1][0]
            default.update({
                'date_due':due_date
            })
        return {'value':default}

#    def onchange_journal_billing(self, cr, uid, ids, line_ids=False, tax_id=False, price=0.0, partner_id=False, journal_id=False, ttype=False, company_id=False, context=None):
#        """price
#        Returns a dict that contains new values and context
#
#        @param partner_id: latest value from user input for field partner_id
#        @param args: other arguments
#        @param context: context arguments, like lang, time zone
#
#        @return: Returns a dict which contains new values, and context
#        """
#        default = {
#            'value':{},
#        }
#
#        if not partner_id or not journal_id:
#            return default
#
#        partner_pool = self.pool.get('res.partner')
#        journal_pool = self.pool.get('account.journal')
#
#        journal = journal_pool.browse(cr, uid, journal_id, context=context)
#        partner = partner_pool.browse(cr, uid, partner_id, context=context)
#        account_id = False
#        tr_type = False
#        if journal.type in ('sale','sale_refund'):
#            account_id = partner.property_account_receivable.id
#            tr_type = 'sale'
#        elif journal.type in ('purchase', 'purchase_refund','expense'):
#            account_id = partner.property_account_payable.id
#            tr_type = 'purchase'
#        else:
#            if not journal.default_credit_account_id or not journal.default_debit_account_id:
#                raise osv.except_osv(_('Error!'), _('Please define default credit/debit accounts on the journal "%s".') % (journal.name))
#            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
#            tr_type = 'receipt'
#
#        default['value']['account_id'] = account_id
#        default['value']['type'] = ttype or tr_type
#
#        vals = self.onchange_journal(cr, uid, ids, journal_id, line_ids, tax_id, partner_id, time.strftime('%Y-%m-%d'), price, ttype, company_id, context)
#        default['value'].update(vals.get('value'))
#
#        return default

    def onchange_rate(self, cr, uid, ids, rate, amount, currency_id, payment_rate_currency_id, company_id, context=None):
        res =  {'value': {'paid_amount_in_company_currency': amount}}
        company_currency = self.pool.get('res.company').browse(cr, uid, company_id, context=context).currency_id
        if rate and amount and currency_id:# and currency_id == payment_rate_currency_id:
            billing_rate = self.pool.get('res.currency').browse(cr, uid, currency_id, context).rate
            if company_currency.id == payment_rate_currency_id:
                company_rate = rate
            else:
                company_rate = self.pool.get('res.company').browse(cr, uid, company_id, context=context).currency_id.rate
            res['value']['paid_amount_in_company_currency'] = amount / billing_rate * company_rate
        return res

#    def onchange_amount(self, cr, uid, ids, amount, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None):
#        if context is None:
#            context = {}
#        res = self.recompute_billing_lines(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=context)
#        ctx = context.copy()
#        ctx.update({'date': date})
#        vals = self.onchange_rate(cr, uid, ids, rate, amount, currency_id, payment_rate_currency_id, company_id, context=ctx)
#        for key in vals.keys():
#            res[key].update(vals[key])
#        return res

    def recompute_payment_rate(self, cr, uid, ids, vals, currency_id, date, journal_id, amount, context=None):
        if context is None:
            context = {}
        #on change of the journal, we need to set also the default value for payment_rate and payment_rate_currency_id
        currency_obj = self.pool.get('res.currency')
        journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
        company_id = journal.company_id.id
        payment_rate = 1.0
        payment_rate_currency_id = currency_id
        ctx = context.copy()
        ctx.update({'date': date})
        o2m_to_loop = 'line_cr_ids'
        if o2m_to_loop and 'value' in vals and o2m_to_loop in vals['value']:
            for billing_line in vals['value'][o2m_to_loop]:
                if billing_line['currency_id'] != currency_id:
                    # we take as default value for the payment_rate_currency_id, the currency of the first invoice that
                    # is not in the billing currency
                    payment_rate_currency_id = billing_line['currency_id']
                    tmp = currency_obj.browse(cr, uid, payment_rate_currency_id, context=ctx).rate
                    billing_currency_id = currency_id or journal.company_id.currency_id.id
                    payment_rate = tmp / currency_obj.browse(cr, uid, billing_currency_id, context=ctx).rate
                    break
        res = self.onchange_rate(cr, uid, ids, payment_rate, amount, currency_id, payment_rate_currency_id, company_id, context=ctx)
        for key in res.keys():
            vals[key].update(res[key])
        vals['value'].update({'payment_rate': payment_rate})
        if payment_rate_currency_id:
            vals['value'].update({'payment_rate_currency_id': payment_rate_currency_id})
        return vals

    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, date, context=None):
        if context is None:
            context = {}
        # Additional Condition for Matching Billing Date
        context.update({'billing_date_condition': ['|',('date_maturity', '=', False),('date_maturity', '<=', date)]})
        if not journal_id:
            return {}
        res = self.recompute_billing_lines(cr, uid, ids, partner_id, journal_id, amount, currency_id, date, context=context)
        vals = self.recompute_payment_rate(cr, uid, ids, res, currency_id, date, journal_id, amount, context=context)
        for key in vals.keys():
            res[key].update(vals[key])

        return res

    def recompute_billing_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, date, context=None):
        """
        Returns a dict that contains new values and context

        @param partner_id: latest value from user input for field partner_id
        @param args: other arguments
        @param context: context arguments, like lang, time zone

        @return: Returns a dict which contains new values, and context
        """
        def _remove_noise_in_o2m():
            """if the line is partially reconciled, then we must pay attention to display it only once and
                in the good o2m.
                This function returns True if the line is considered as noise and should not be displayed
            """
            if line.reconcile_partial_id:
                sign = 1
                if currency_id == line.currency_id.id:
                    if line.amount_residual_currency * sign <= 0:
                        return True
                else:
                    if line.amount_residual * sign <= 0:
                        return True
            return False

        if context is None:
            context = {}
        billing_date_condition = context.get('billing_date_condition', [])
        context_multi_currency = context.copy()
        if date:
            context_multi_currency.update({'date': date})

        currency_pool = self.pool.get('res.currency')
        move_line_pool = self.pool.get('account.move.line')
        partner_pool = self.pool.get('res.partner')
        journal_pool = self.pool.get('account.journal')
        line_pool = self.pool.get('account.billing.line')

        #set default values
        default = {
            'value': {'line_cr_ids': [] },
        }

        #drop existing lines
        line_ids = ids and line_pool.search(cr, uid, [('billing_id', '=', ids[0])]) or False
        if line_ids:
            line_pool.unlink(cr, uid, line_ids)

        if not partner_id or not journal_id:
            return default

        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        partner = partner_pool.browse(cr, uid, partner_id, context=context)
        currency_id = currency_id or journal.company_id.currency_id.id
        account_id = False
        if journal.type in ('sale','sale_refund'):
            account_id = partner.property_account_receivable.id
        elif journal.type in ('purchase', 'purchase_refund','expense'):
            account_id = partner.property_account_payable.id
        else:
            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id

        default['value']['account_id'] = account_id

        if journal.type not in ('cash', 'bank'):
            return default

        total_credit = price or 0.0
        account_type = 'receivable'

        if not context.get('move_line_ids', False):
            ids = move_line_pool.search(cr, uid, 
                                        [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id), 
                                         ] + billing_date_condition, 
                                        context=context)
        else:
            ids = context['move_line_ids']
        invoice_id = context.get('invoice_id', False)
        company_currency = journal.company_id.currency_id.id
        move_line_found = False

        #order the lines by most old first
        ids.reverse()
        account_move_lines = move_line_pool.browse(cr, uid, ids, context=context)

        #compute the total debit/credit and look for a matching open amount or invoice
        for line in account_move_lines:
            if _remove_noise_in_o2m():
                continue

            if invoice_id:
                if line.invoice.id == invoice_id:
                    #if the invoice linked to the billing line is equal to the invoice_id in context
                    #then we assign the amount on that line, whatever the other billing lines
                    move_line_found = line.id
                    break
            elif currency_id == company_currency:
                #otherwise treatments is the same but with other field names
                if line.amount_residual == price:
                    #if the amount residual is equal the amount billing, we assign it to that billing
                    #line, whatever the other billing lines
                    move_line_found = line.id
                    break
                #otherwise we will split the billing amount on each line (by most old first)
                total_credit += line.credit or 0.0
            elif currency_id == line.currency_id.id:
                if line.amount_residual_currency == price:
                    move_line_found = line.id
                    break
                total_credit += line.credit and line.amount_currency or 0.0

        #billing line creation
        for line in account_move_lines:

            if _remove_noise_in_o2m():
                continue

            if line.currency_id and currency_id==line.currency_id.id:
                amount_original = abs(line.amount_currency)
                amount_unreconciled = abs(line.amount_residual_currency)
            else:
                amount_original = currency_pool.compute(cr, uid, company_currency, currency_id, line.credit or 0.0)
                amount_unreconciled = currency_pool.compute(cr, uid, company_currency, currency_id, abs(line.amount_residual))
            line_currency_id = line.currency_id and line.currency_id.id or company_currency
            rs = {
                'move_line_id':line.id,
                'type': line.credit and 'dr' or 'cr',
                'reference':line.invoice.reference,
                'account_id':line.account_id.id,
                'amount_original': amount_original,
                'amount': (move_line_found == line.id) and min(abs(price), amount_unreconciled) or amount_unreconciled,
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
                'currency_id': line_currency_id,
            }
            
            # Negate DR records
            if rs['type'] == 'dr':
                rs['amount_original'] = - rs['amount_original']
                rs['amount'] = - rs['amount']
                rs['amount_unreconciled'] = - rs['amount_unreconciled']

            if rs['amount_unreconciled'] == rs['amount']:
                rs['reconcile'] = True
            else:
                rs['reconcile'] = False

            default['value']['line_cr_ids'].append(rs)

#            if ttype == 'payment' and len(default['value']['line_cr_ids']) > 0:
#                default['value']['pre_line'] = 1
#            elif ttype == 'receipt' and len(default['value']['line_dr_ids']) > 0:
#                default['value']['pre_line'] = 1
            default['value']['billing_amount'] = self._compute_billing_amount(cr, uid, default['value']['line_cr_ids'], price)
        return default

    def onchange_payment_rate_currency(self, cr, uid, ids, currency_id, payment_rate, payment_rate_currency_id, date, amount, company_id, context=None):
        if context is None:
            context = {}
        res = {'value': {}}
        #set the default payment rate of the billing and compute the paid amount in company currency
        if currency_id and currency_id == payment_rate_currency_id:
            ctx = context.copy()
            ctx.update({'date': date})
            vals = self.onchange_rate(cr, uid, ids, payment_rate, amount, currency_id, payment_rate_currency_id, company_id, context=ctx)
            for key in vals.keys():
                res[key].update(vals[key])
        return res

    def onchange_date(self, cr, uid, ids, date, currency_id, payment_rate_currency_id, amount, company_id, context=None):
        """
        @param date: latest value from user input for field date
        @param args: other arguments
        @param context: context arguments, like lang, time zone
        @return: Returns a dict which contains new values, and context
        """
        if context is None:
            context ={}
        res = {'value': {}}
        #set the period of the billing
        period_pool = self.pool.get('account.period')
        currency_obj = self.pool.get('res.currency')
        ctx = context.copy()
        ctx.update({'company_id': company_id})
        pids = period_pool.find(cr, uid, date, context=ctx)
        if pids:
            res['value'].update({'period_id':pids[0]})
        if payment_rate_currency_id:
            ctx.update({'date': date})
            payment_rate = 1.0
            if payment_rate_currency_id != currency_id:
                tmp = currency_obj.browse(cr, uid, payment_rate_currency_id, context=ctx).rate
                billing_currency_id = currency_id or self.pool.get('res.company').browse(cr, uid, company_id, context=ctx).currency_id.id
                payment_rate = tmp / currency_obj.browse(cr, uid, billing_currency_id, context=ctx).rate
            vals = self.onchange_payment_rate_currency(cr, uid, ids, currency_id, payment_rate, payment_rate_currency_id, date, amount, company_id, context=context)
            vals['value'].update({'payment_rate': payment_rate})
            for key in vals.keys():
                res[key].update(vals[key])
        
        res2 = self.onchange_partner_id(cr, uid, ids, ctx['partner_id'], ctx['journal_id'], amount, currency_id, date, context)
        for key in res2.keys():
            res[key].update(res2[key])
        
        return res

    def onchange_journal(self, cr, uid, ids, journal_id, line_ids, tax_id, partner_id, date, amount, company_id, context=None):
        if not journal_id:
            return False
        journal_pool = self.pool.get('account.journal')
        journal = journal_pool.browse(cr, uid, journal_id, context=context)
        account_id = journal.default_credit_account_id or journal.default_debit_account_id
        tax_id = False
        if account_id and account_id.tax_ids:
            tax_id = account_id.tax_ids[0].id

        vals = {'value':{} }
        currency_id = False
        if journal.currency:
            currency_id = journal.currency.id
        vals['value'].update({'currency_id': currency_id})
        res = self.onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, date, context)
        for key in res.keys():
            vals[key].update(res[key])
        return vals

    def button_proforma_billing(self, cr, uid, ids, context=None):
        context = context or {}
        wf_service = netsvc.LocalService("workflow")
        for vid in ids:
            wf_service.trg_validate(uid, 'account.billing', vid, 'proforma_billing', cr)
        return {'type': 'ir.actions.act_window_close'}

    # KTU
    def validate_billing(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, { 'state': 'billed' })
        self.write(cr, uid, ids, { 'number': self.pool.get('ir.sequence').get(cr, uid, 'account.billing') })
        self.message_post(cr, uid, ids, body=_('Billing is billed.'), context=context)
        return True
    # KTU
    def action_cancel_draft(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        for billing_id in ids:
            wf_service.trg_create(uid, 'account.billing', billing_id, cr)
        self.write(cr, uid, ids, {'state':'draft'})
        self.message_post(cr, uid, ids, body=_('Billing is reset to draft'), context=context)
        return True
    # KTU
    def cancel_billing(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, { 'state': 'cancel' })
        self.message_post(cr, uid, ids, body=_('Billing is cancelled.'), context=context)
        return True

    # KTU
    def unlink(self, cr, uid, ids, context=None):
        for t in self.read(cr, uid, ids, ['state'], context=context):
            if t['state'] not in ('draft', 'cancel'):
                raise osv.except_osv(_('Invalid Action!'), _('Cannot delete billing(s) which are already billed.'))
        return super(account_billing, self).unlink(cr, uid, ids, context=context)

    def _sel_context(self, cr, uid, billing_id, context=None):
        """
        Select the context to use accordingly if it needs to be multicurrency or not.

        :param billing_id: Id of the actual billing
        :return: The returned context will be the same as given in parameter if the billing currency is the same
                 than the company currency, otherwise it's a copy of the parameter with an extra key 'date' containing
                 the date of the billing.
        :rtype: dict
        """
        company_currency = self._get_company_currency(cr, uid, billing_id, context)
        current_currency = self._get_current_currency(cr, uid, billing_id, context)
        if current_currency <> company_currency:
            context_multi_currency = context.copy()
            billing_brw = self.pool.get('account.billing').browse(cr, uid, billing_id, context)
            context_multi_currency.update({'date': billing_brw.date})
            return context_multi_currency
        return context
#
#    def first_move_line_get(self, cr, uid, billing_id, move_id, company_currency, current_currency, context=None):
#        '''
#        Return a dict to be use to create the first account move line of given billing.
#
#        :param billing_id: Id of billing what we are creating account_move.
#        :param move_id: Id of account move where this line will be added.
#        :param company_currency: id of currency of the company to which the billing belong
#        :param current_currency: id of currency of the billing
#        :return: mapping between fieldname and value of account move line to create
#        :rtype: dict
#        '''
#        billing_brw = self.pool.get('account.billing').browse(cr,uid,billing_id,context)
#        debit = credit = 0.0
#        # TODO: is there any other alternative then the billing type ??
#        # ANSWER: We can have payment and receipt "In Advance".
#        # TODO: Make this logic available.
#        # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
#        if billing_brw.type in ('purchase', 'payment'):
#            credit = billing_brw.paid_amount_in_company_currency
#        elif billing_brw.type in ('sale', 'receipt'):
#            debit = billing_brw.paid_amount_in_company_currency
#        if debit < 0: credit = -debit; debit = 0.0
#        if credit < 0: debit = -credit; credit = 0.0
#        sign = debit - credit < 0 and -1 or 1
#        #set the first line of the billing
#        move_line = {
#                'name': billing_brw.name or '/',
#                'debit': debit,
#                'credit': credit,
#                'account_id': billing_brw.account_id.id,
#                'move_id': move_id,
#                'journal_id': billing_brw.journal_id.id,
#                'period_id': billing_brw.period_id.id,
#                'partner_id': billing_brw.partner_id.id,
#                'currency_id': company_currency <> current_currency and  current_currency or False,
#                'amount_currency': company_currency <> current_currency and sign * billing_brw.amount or 0.0,
#                'date': billing_brw.date,
#                'date_maturity': billing_brw.date_due
#            }
#        return move_line
#
#    def account_move_get(self, cr, uid, billing_id, context=None):
#        '''
#        This method prepare the creation of the account move related to the given billing.
#
#        :param billing_id: Id of billing for which we are creating account_move.
#        :return: mapping between fieldname and value of account move to create
#        :rtype: dict
#        '''
#        seq_obj = self.pool.get('ir.sequence')
#        billing_brw = self.pool.get('account.billing').browse(cr,uid,billing_id,context)
#        if billing_brw.number:
#            name = billing_brw.number
#        elif billing_brw.journal_id.sequence_id:
#            if not billing_brw.journal_id.sequence_id.active:
#                raise osv.except_osv(_('Configuration Error !'),
#                    _('Please activate the sequence of selected journal !'))
#            name = seq_obj.next_by_id(cr, uid, billing_brw.journal_id.sequence_id.id, context=context)
#        else:
#            raise osv.except_osv(_('Error!'),
#                        _('Please define a sequence on the journal.'))
#        if not billing_brw.reference:
#            ref = name.replace('/','')
#        else:
#            ref = billing_brw.reference
#
#        move = {
#            'name': name,
#            'journal_id': billing_brw.journal_id.id,
#            'narration': billing_brw.narration,
#            'date': billing_brw.date,
#            'ref': ref,
#            'period_id': billing_brw.period_id and billing_brw.period_id.id or False
#        }
#        return move
#
#    def _get_exchange_lines(self, cr, uid, line, move_id, amount_residual, company_currency, current_currency, context=None):
#        '''
#        Prepare the two lines in company currency due to currency rate difference.
#
#        :param line: browse record of the billing.line for which we want to create currency rate difference accounting
#            entries
#        :param move_id: Account move wher the move lines will be.
#        :param amount_residual: Amount to be posted.
#        :param company_currency: id of currency of the company to which the billing belong
#        :param current_currency: id of currency of the billing
#        :return: the account move line and its counterpart to create, depicted as mapping between fieldname and value
#        :rtype: tuple of dict
#        '''
#        if amount_residual > 0:
#            account_id = line.billing_id.company_id.expense_currency_exchange_account_id
#            if not account_id:
#                raise osv.except_osv(_('Insufficient Configuration!'),_("You should configure the 'Loss Exchange Rate Account' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
#        else:
#            account_id = line.billing_id.company_id.income_currency_exchange_account_id
#            if not account_id:
#                raise osv.except_osv(_('Insufficient Configuration!'),_("You should configure the 'Gain Exchange Rate Account' in the accounting settings, to manage automatically the booking of accounting entries related to differences between exchange rates."))
#        # Even if the amount_currency is never filled, we need to pass the foreign currency because otherwise
#        # the receivable/payable account may have a secondary currency, which render this field mandatory
#        account_currency_id = company_currency <> current_currency and current_currency or False
#        move_line = {
#            'journal_id': line.billing_id.journal_id.id,
#            'period_id': line.billing_id.period_id.id,
#            'name': _('change')+': '+(line.name or '/'),
#            'account_id': line.account_id.id,
#            'move_id': move_id,
#            'partner_id': line.billing_id.partner_id.id,
#            'currency_id': account_currency_id,
#            'amount_currency': 0.0,
#            'quantity': 1,
#            'credit': amount_residual > 0 and amount_residual or 0.0,
#            'debit': amount_residual < 0 and -amount_residual or 0.0,
#            'date': line.billing_id.date,
#        }
#        move_line_counterpart = {
#            'journal_id': line.billing_id.journal_id.id,
#            'period_id': line.billing_id.period_id.id,
#            'name': _('change')+': '+(line.name or '/'),
#            'account_id': account_id.id,
#            'move_id': move_id,
#            'amount_currency': 0.0,
#            'partner_id': line.billing_id.partner_id.id,
#            'currency_id': account_currency_id,
#            'quantity': 1,
#            'debit': amount_residual > 0 and amount_residual or 0.0,
#            'credit': amount_residual < 0 and -amount_residual or 0.0,
#            'date': line.billing_id.date,
#        }
#        return (move_line, move_line_counterpart)

    def _convert_amount(self, cr, uid, amount, billing_id, context=None):
        '''
        This function convert the amount given in company currency. It takes either the rate in the billing (if the
        payment_rate_currency_id is relevant) either the rate encoded in the system.

        :param amount: float. The amount to convert
        :param billing: id of the billing on which we want the conversion
        :param context: to context to use for the conversion. It may contain the key 'date' set to the billing date
            field in order to select the good rate to use.
        :return: the amount in the currency of the billing's company
        :rtype: float
        '''
        currency_obj = self.pool.get('res.currency')
        billing = self.browse(cr, uid, billing_id, context=context)
        res = amount
        if billing.payment_rate_currency_id.id == billing.company_id.currency_id.id:
            # the rate specified on the billing is for the company currency
            res = currency_obj.round(cr, uid, billing.company_id.currency_id, (amount * billing.payment_rate))
        else:
            # the rate specified on the billing is not relevant, we use all the rates in the system
            res = currency_obj.compute(cr, uid, billing.currency_id.id, billing.company_id.currency_id.id, amount, context=context)
        return res
#
#    def billing_move_line_create(self, cr, uid, billing_id, line_total, move_id, company_currency, current_currency, context=None):
#        '''
#        Create one account move line, on the given account move, per billing line where amount is not 0.0.
#        It returns Tuple with tot_line what is total of difference between debit and credit and
#        a list of lists with ids to be reconciled with this format (total_deb_cred,list_of_lists).
#
#        :param billing_id: billing id what we are working with
#        :param line_total: Amount of the first line, which correspond to the amount we should totally split among all billing lines.
#        :param move_id: Account move wher those lines will be joined.
#        :param company_currency: id of currency of the company to which the billing belong
#        :param current_currency: id of currency of the billing
#        :return: Tuple build as (remaining amount not allocated on billing lines, list of account_move_line created in this method)
#        :rtype: tuple(float, list of int)
#        '''
#        if context is None:
#            context = {}
#        move_line_obj = self.pool.get('account.move.line')
#        currency_obj = self.pool.get('res.currency')
#        tax_obj = self.pool.get('account.tax')
#        tot_line = line_total
#        rec_lst_ids = []
#
#        billing_brw = self.pool.get('account.billing').browse(cr, uid, billing_id, context)
#        ctx = context.copy()
#        ctx.update({'date': billing_brw.date})
#        for line in billing_brw.line_ids:
#            #create one move line per billing line where amount is not 0.0
#            if not line.amount:
#                continue
#            # convert the amount set on the billing line into the currency of the billing's company
#            amount = self._convert_amount(cr, uid, line.untax_amount or line.amount, billing_brw.id, context=ctx)
#            # if the amount encoded in billing is equal to the amount unreconciled, we need to compute the
#            # currency rate difference
#            if line.amount == line.amount_unreconciled:
#                if not line.move_line_id.amount_residual:
#                    raise osv.except_osv(_('Wrong bank statement line'),_("You have to delete the bank statement line which the payment was reconciled to manually. Please check the payment of the partner %s by the amount of %s.")%(line.billing_id.partner_id.name, line.billing_id.amount))
#                sign = billing_brw.type in ('payment', 'purchase') and -1 or 1
#                currency_rate_difference = sign * (line.move_line_id.amount_residual - amount)
#            else:
#                currency_rate_difference = 0.0
#            move_line = {
#                'journal_id': billing_brw.journal_id.id,
#                'period_id': billing_brw.period_id.id,
#                'name': line.name or '/',
#                'account_id': line.account_id.id,
#                'move_id': move_id,
#                'partner_id': billing_brw.partner_id.id,
#                'currency_id': line.move_line_id and (company_currency <> line.move_line_id.currency_id.id and line.move_line_id.currency_id.id) or False,
#                'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
#                'quantity': 1,
#                'credit': 0.0,
#                'debit': 0.0,
#                'date': billing_brw.date
#            }
#            if amount < 0:
#                amount = -amount
#                if line.type == 'dr':
#                    line.type = 'cr'
#                else:
#                    line.type = 'dr'
#
#            if (line.type=='dr'):
#                tot_line += amount
#                move_line['debit'] = amount
#            else:
#                tot_line -= amount
#                move_line['credit'] = amount
#
#            if billing_brw.tax_id and billing_brw.type in ('sale', 'purchase'):
#                move_line.update({
#                    'account_tax_id': billing_brw.tax_id.id,
#                })
#
#            if move_line.get('account_tax_id', False):
#                tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
#                if not (tax_data.base_code_id and tax_data.tax_code_id):
#                    raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))
#
#            # compute the amount in foreign currency
#            foreign_currency_diff = 0.0
#            amount_currency = False
#            if line.move_line_id:
#                billing_currency = billing_brw.currency_id and billing_brw.currency_id.id or billing_brw.journal_id.company_id.currency_id.id
#                # We want to set it on the account move line as soon as the original line had a foreign currency
#                if line.move_line_id.currency_id and line.move_line_id.currency_id.id != company_currency:
#                    # we compute the amount in that foreign currency.
#                    if line.move_line_id.currency_id.id == current_currency:
#                        # if the billing and the billing line share the same currency, there is no computation to do
#                        sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
#                        amount_currency = sign * (line.amount)
#                    elif line.move_line_id.currency_id.id == billing_brw.payment_rate_currency_id.id:
#                        # if the rate is specified on the billing, we must use it
#                        billing_rate = currency_obj.browse(cr, uid, billing_currency, context=ctx).rate
#                        amount_currency = (move_line['debit'] - move_line['credit']) * billing_brw.payment_rate * billing_rate
#                    else:
#                        # otherwise we use the rates of the system (giving the billing date in the context)
#                        amount_currency = currency_obj.compute(cr, uid, company_currency, line.move_line_id.currency_id.id, move_line['debit']-move_line['credit'], context=ctx)
#                if line.amount == line.amount_unreconciled and line.move_line_id.currency_id.id == billing_currency:
#                    sign = billing_brw.type in ('payment', 'purchase') and -1 or 1
#                    foreign_currency_diff = sign * line.move_line_id.amount_residual_currency + amount_currency
#
#            move_line['amount_currency'] = amount_currency
#            billing_line = move_line_obj.create(cr, uid, move_line)
#            rec_ids = [billing_line, line.move_line_id.id]
#
#            if not currency_obj.is_zero(cr, uid, billing_brw.company_id.currency_id, currency_rate_difference):
#                # Change difference entry in company currency
#                exch_lines = self._get_exchange_lines(cr, uid, line, move_id, currency_rate_difference, company_currency, current_currency, context=context)
#                new_id = move_line_obj.create(cr, uid, exch_lines[0],context)
#                move_line_obj.create(cr, uid, exch_lines[1], context)
#                rec_ids.append(new_id)
#
#            if line.move_line_id and line.move_line_id.currency_id and not currency_obj.is_zero(cr, uid, line.move_line_id.currency_id, foreign_currency_diff):
#                # Change difference entry in billing currency
#                move_line_foreign_currency = {
#                    'journal_id': line.billing_id.journal_id.id,
#                    'period_id': line.billing_id.period_id.id,
#                    'name': _('change')+': '+(line.name or '/'),
#                    'account_id': line.account_id.id,
#                    'move_id': move_id,
#                    'partner_id': line.billing_id.partner_id.id,
#                    'currency_id': line.move_line_id.currency_id.id,
#                    'amount_currency': -1 * foreign_currency_diff,
#                    'quantity': 1,
#                    'credit': 0.0,
#                    'debit': 0.0,
#                    'date': line.billing_id.date,
#                }
#                new_id = move_line_obj.create(cr, uid, move_line_foreign_currency, context=context)
#                rec_ids.append(new_id)
#
#            if line.move_line_id.id:
#                rec_lst_ids.append(rec_ids)
#
#        return (tot_line, rec_lst_ids)
#
#    def writeoff_move_line_get(self, cr, uid, billing_id, line_total, move_id, name, company_currency, current_currency, context=None):
#        '''
#        Set a dict to be use to create the writeoff move line.
#
#        :param billing_id: Id of billing what we are creating account_move.
#        :param line_total: Amount remaining to be allocated on lines.
#        :param move_id: Id of account move where this line will be added.
#        :param name: Description of account move line.
#        :param company_currency: id of currency of the company to which the billing belong
#        :param current_currency: id of currency of the billing
#        :return: mapping between fieldname and value of account move line to create
#        :rtype: dict
#        '''
#        currency_obj = self.pool.get('res.currency')
#        move_line = {}
#
#        billing_brw = self.pool.get('account.billing').browse(cr,uid,billing_id,context)
#        current_currency_obj = billing_brw.currency_id or billing_brw.journal_id.company_id.currency_id
#
#        if not currency_obj.is_zero(cr, uid, current_currency_obj, line_total):
#            diff = line_total
#            account_id = False
#            write_off_name = ''
#            if billing_brw.payment_option == 'with_writeoff':
#                account_id = billing_brw.writeoff_acc_id.id
#                write_off_name = billing_brw.comment
#            elif billing_brw.type in ('sale', 'receipt'):
#                account_id = billing_brw.partner_id.property_account_receivable.id
#            else:
#                account_id = billing_brw.partner_id.property_account_payable.id
#            sign = billing_brw.type == 'payment' and -1 or 1
#            move_line = {
#                'name': write_off_name or name,
#                'account_id': account_id,
#                'move_id': move_id,
#                'partner_id': billing_brw.partner_id.id,
#                'date': billing_brw.date,
#                'credit': diff > 0 and diff or 0.0,
#                'debit': diff < 0 and -diff or 0.0,
#                'amount_currency': company_currency <> current_currency and (sign * -1 * billing_brw.billing_amount) or False,
#                'currency_id': company_currency <> current_currency and current_currency or False,
#                'analytic_account_id': billing_brw.analytic_id and billing_brw.analytic_id.id or False,
#            }
#
#        return move_line

    def _get_company_currency(self, cr, uid, billing_id, context=None):
        '''
        Get the currency of the actual company.

        :param billing_id: Id of the billing what i want to obtain company currency.
        :return: currency id of the company of the billing
        :rtype: int
        '''
        return self.pool.get('account.billing').browse(cr,uid,billing_id,context).journal_id.company_id.currency_id.id

    def _get_current_currency(self, cr, uid, billing_id, context=None):
        '''
        Get the currency of the billing.

        :param billing_id: Id of the billing what i want to obtain current currency.
        :return: currency id of the billing
        :rtype: int
        '''
        billing = self.pool.get('account.billing').browse(cr,uid,billing_id,context)
        return billing.currency_id.id or self._get_company_currency(cr,uid,billing.id,context)
#
#    def action_move_line_create(self, cr, uid, ids, context=None):
#        '''
#        Confirm the billings given in ids and create the journal entries for each of them
#        '''
#        if context is None:
#            context = {}
#        move_pool = self.pool.get('account.move')
#        move_line_pool = self.pool.get('account.move.line')
#        for billing in self.browse(cr, uid, ids, context=context):
#            if billing.move_id:
#                continue
#            company_currency = self._get_company_currency(cr, uid, billing.id, context)
#            current_currency = self._get_current_currency(cr, uid, billing.id, context)
#            # we select the context to use accordingly if it's a multicurrency case or not
#            context = self._sel_context(cr, uid, billing.id, context)
#            # But for the operations made by _convert_amount, we always need to give the date in the context
#            ctx = context.copy()
#            ctx.update({'date': billing.date})
#            # Create the account move record.
#            move_id = move_pool.create(cr, uid, self.account_move_get(cr, uid, billing.id, context=context), context=context)
#            # Get the name of the account_move just created
#            name = move_pool.browse(cr, uid, move_id, context=context).name
#            # Create the first line of the billing
#            move_line_id = move_line_pool.create(cr, uid, self.first_move_line_get(cr,uid,billing.id, move_id, company_currency, current_currency, context), context)
#            move_line_brw = move_line_pool.browse(cr, uid, move_line_id, context=context)
#            line_total = move_line_brw.debit - move_line_brw.credit
#            rec_list_ids = []
#            if billing.type == 'sale':
#                line_total = line_total - self._convert_amount(cr, uid, billing.tax_amount, billing.id, context=ctx)
#            elif billing.type == 'purchase':
#                line_total = line_total + self._convert_amount(cr, uid, billing.tax_amount, billing.id, context=ctx)
#            # Create one move line per billing line where amount is not 0.0
#            line_total, rec_list_ids = self.billing_move_line_create(cr, uid, billing.id, line_total, move_id, company_currency, current_currency, context)
#
#            # Create the writeoff line if needed
#            ml_writeoff = self.writeoff_move_line_get(cr, uid, billing.id, line_total, move_id, name, company_currency, current_currency, context)
#            if ml_writeoff:
#                move_line_pool.create(cr, uid, ml_writeoff, context)
#            # We post the billing.
#            self.write(cr, uid, [billing.id], {
#                'move_id': move_id,
#                'state': 'posted',
#                'number': name,
#            })
#            self.post_send_note(cr, uid, [billing.id], context=context)
#            if billing.journal_id.entry_posted:
#                move_pool.post(cr, uid, [move_id], context={})
#            # We automatically reconcile the account move lines.
#            reconcile = False
#            for rec_ids in rec_list_ids:
#                if len(rec_ids) >= 2:
#                    reconcile = move_line_pool.reconcile_partial(cr, uid, rec_ids, writeoff_acc_id=billing.writeoff_acc_id.id, writeoff_period_id=billing.period_id.id, writeoff_journal_id=billing.journal_id.id)
#            if reconcile:
#                self.reconcile_send_note(cr, uid, [billing.id], context=context)
#        return True

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({
            'state': 'draft',
            'number': False,
            'move_id': False,
            'line_cr_ids': False,
            'reference': False
        })
        if 'date' not in default:
            default['date'] = time.strftime('%Y-%m-%d')
        return super(account_billing, self).copy(cr, uid, id, default, context)

    # -----------------------------------------
    # OpenChatter notifications and need_action
    # -----------------------------------------
    _document_type = {
        'payment': 'Supplier Billing',
        'receipt': 'Customer Billing',
        False: 'Payment',
    }

    def create_send_note(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            message = "Billing Document <b>created</b>."
            self.message_post(cr, uid, [obj.id], body=message, subtype="account_billing.mt_billing", context=context)

    def post_send_note(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            message = "%s '%s' is <b>posted</b>." % (self._document_type[obj.type or False], obj.move_id.name)
            self.message_post(cr, uid, [obj.id], body=message, subtype="account_billing.mt_billing", context=context)

    def reconcile_send_note(self, cr, uid, ids, context=None):
        for obj in self.browse(cr, uid, ids, context=context):
            message = "%s <b>reconciled</b>." % self._document_type[obj.type or False]
            self.message_post(cr, uid, [obj.id], body=message, subtype="account_billing.mt_billing", context=context)

account_billing()

class account_billing_line(osv.osv):
    _name = 'account.billing.line'
    _description = 'Billing Lines'
    _order = "move_line_id"

    # If the payment is in the same currency than the invoice, we keep the same amount
    # Otherwise, we compute from company currency to payment currency
    def _compute_balance(self, cr, uid, ids, name, args, context=None):
        currency_pool = self.pool.get('res.currency')
        rs_data = {}
        for line in self.browse(cr, uid, ids, context=context):
            ctx = context.copy()
            ctx.update({'date': line.billing_id.date})
            res = {}
            company_currency = line.billing_id.journal_id.company_id.currency_id.id
            billing_currency = line.billing_id.currency_id and line.billing_id.currency_id.id or company_currency
            move_line = line.move_line_id or False

            if not move_line:
                res['amount_original'] = 0.0
                res['amount_unreconciled'] = 0.0
            elif move_line.currency_id and billing_currency==move_line.currency_id.id:
                res['amount_original'] = currency_pool.compute(cr, uid, move_line.currency_id.id, billing_currency, abs(move_line.amount_currency), context=ctx)
                res['amount_unreconciled'] = currency_pool.compute(cr, uid, move_line.currency_id and move_line.currency_id.id or company_currency, billing_currency, abs(move_line.amount_residual_currency), context=ctx)
            elif move_line and move_line.credit > 0:
                res['amount_original'] = currency_pool.compute(cr, uid, company_currency, billing_currency, move_line.credit, context=ctx)
                res['amount_unreconciled'] = currency_pool.compute(cr, uid, company_currency, billing_currency, abs(move_line.amount_residual), context=ctx)
            else:
                res['amount_original'] = currency_pool.compute(cr, uid, company_currency, billing_currency, move_line.debit, context=ctx)
                res['amount_unreconciled'] = currency_pool.compute(cr, uid, company_currency, billing_currency, abs(move_line.amount_residual), context=ctx)

            rs_data[line.id] = res
        return rs_data

    def _currency_id(self, cr, uid, ids, name, args, context=None):
        '''
        This function returns the currency id of a billing line. It's either the currency of the
        associated move line (if any) or the currency of the billing or the company currency.
        '''
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            move_line = line.move_line_id
            if move_line:
                res[line.id] = move_line.currency_id and move_line.currency_id.id or move_line.company_id.currency_id.id
            else:
                res[line.id] = line.billing_id.currency_id and line.billing_id.currency_id.id or line.billing_id.company_id.currency_id.id
        return res

    _columns = {
        'billing_id':fields.many2one('account.billing', 'billing', required=1, ondelete='cascade'),
        'name':fields.char('Description', size=256),
        'reference': fields.char('Invoice Reference', size=64, help="The partner reference of this invoice."),
        'account_id':fields.many2one('account.account','Account', readonly=True, required=True),
        'partner_id':fields.related('billing_id', 'partner_id', type='many2one', relation='res.partner', string='Partner'),
        'untax_amount':fields.float('Untax Amount'),
        'amount':fields.float('Amount', digits_compute=dp.get_precision('Account')),
        'reconcile': fields.boolean('Full Reconcile'),
        'type':fields.selection([('dr','Debit'),('cr','Credit')], 'Dr/Cr'),
        'account_analytic_id':  fields.many2one('account.analytic.account', 'Analytic Account'),
        'move_line_id': fields.many2one('account.move.line', 'Journal Item'),
        'date_original': fields.related('move_line_id','date', type='date', relation='account.move.line', string='Date', readonly=1),
        'date_due': fields.related('move_line_id','date_maturity', type='date', relation='account.move.line', string='Due Date', readonly=1),
        'amount_original': fields.function(_compute_balance, multi='dc', type='float', string='Original Amount', store=True, digits_compute=dp.get_precision('Account')),
        'amount_unreconciled': fields.function(_compute_balance, multi='dc', type='float', string='Open Balance', store=True, digits_compute=dp.get_precision('Account')),
        'company_id': fields.related('billing_id','company_id', relation='res.company', type='many2one', string='Company', store=True, readonly=True),
        'currency_id': fields.function(_currency_id, string='Currency', type='many2one', relation='res.currency', readonly=True),
    }
    _defaults = {
        'name': '',
    }

    def onchange_reconcile(self, cr, uid, ids, reconcile, amount, amount_unreconciled, context=None):
        vals = {'amount': 0.0}
        if reconcile:
            vals = {'amount': amount_unreconciled}
        return {'value': vals}
    
    def onchange_amount(self, cr, uid, ids, reconcile, amount, amount_unreconciled, context=None):
        vals = {}
        if amount==amount_unreconciled:
            vals = {'reconcile': True}
        else:
            vals = {'reconcile': False, 'amount':0.0}
        return {'value': vals}
    
#    def onchange_amount(self, cr, uid, ids, amount, amount_unreconciled, context=None):
#        vals = {}
#        if amount:
#            vals['reconcile'] = (amount == amount_unreconciled)
#        return {'value': vals}
#
#    def onchange_move_line_id(self, cr, user, ids, move_line_id, context=None):
#        """
#        Returns a dict that contains new values and context
#
#        @param move_line_id: latest value from user input for field move_line_id
#        @param args: other arguments
#        @param context: context arguments, like lang, time zone
#
#        @return: Returns a dict which contains new values, and context
#        """
#        res = {}
#        move_line_pool = self.pool.get('account.move.line')
#        if move_line_id:
#            move_line = move_line_pool.browse(cr, user, move_line_id, context=context)
#            if move_line.credit:
#                ttype = 'dr'
#            else:
#                ttype = 'cr'
#            res.update({
#                'account_id': move_line.account_id.id,
#                'type': ttype,
#                'currency_id': move_line.currency_id and move_line.currency_id.id or move_line.company_id.currency_id.id,
#            })
#        return {
#            'value':res,
#        }

    def default_get(self, cr, user, fields_list, context=None):

        if context is None:
            context = {}
        partner_id = context.get('partner_id', False)
        partner_pool = self.pool.get('res.partner')
        values = super(account_billing_line, self).default_get(cr, user, fields_list, context=context)
        if ('account_id' not in fields_list):
            return values
        
        if partner_id:
            partner = partner_pool.browse(cr, user, partner_id, context=context)
            account_id = partner.property_account_receivable.id

        values.update({
            'account_id':account_id,
        })
        return values
account_billing_line()

def resolve_o2m_operations(cr, uid, target_osv, operations, fields, context):
    results = []
    for operation in operations:
        result = None
        if not isinstance(operation, (list, tuple)):
            result = target_osv.read(cr, uid, operation, fields, context=context)
        elif operation[0] == 0:
            # may be necessary to check if all the fields are here and get the default values?
            result = operation[2]
        elif operation[0] == 1:
            result = target_osv.read(cr, uid, operation[1], fields, context=context)
            if not result: result = {}
            result.update(operation[2])
        elif operation[0] == 4:
            result = target_osv.read(cr, uid, operation[1], fields, context=context)
        if result != None:
            results.append(result)
    return results


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
