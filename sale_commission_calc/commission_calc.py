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
from datetime import datetime
from dateutil.relativedelta import relativedelta
import time
from openerp.osv import fields, osv
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

# Define the due date available for any commission rule
LAST_PAY_DATE_RULE = [('invoice_duedate', 'Invoice Due Date (default)'),
                      ('invoice_date_plus_cust_payterm', 'Invoice Date + Customer Payment Term')]

COMMISSION_LINE_STATE = [('draft', 'Not Ready'),
                          ('valid', 'Ready'),
                          ('invalid', 'Invalid'),
                          ('done', 'Done'),
                          ('skip', 'Skipped')]


class sale_team(osv.osv):

    _name = "sale.team"
    _description = "Sales Team"
    _columns = {
        'name': fields.char('Name', size=64, required=True),
        'commission_rule_id': fields.many2one('commission.rule', 'Commission Rule', required=False),
        'users': fields.many2many('res.users', 'sale_team_users_rel', 'tid', 'uid', 'Users'),
        'implied_ids': fields.many2many('sale.team', 'sale_team_implied_rel', 'tid', 'hid',
            string='Inherits', help='Users of this group automatically inherit those groups'),
        'require_paid': fields.boolean('Require Paid Invoice', help='Require invoice to be paid in full amount.'),
        'require_posted': fields.boolean('Require Payment Detail Posted', help='Require that all payment detail related to payments to invoice has been posted.'),
        'allow_overdue': fields.boolean('Allow overdue payment', help='Allow paying commission with overdue payment.'),
        'last_pay_date_rule': fields.selection(LAST_PAY_DATE_RULE, 'Last Pay Date Rule'),
        'buffer_days': fields.integer('Buffer Days', help="Additional days after last payment date to be eligible for commission.")
    }
    _defaults = {
        'require_paid': False,
        'require_posted': False,
        'allow_overdue': False,
        'buffer_days': 0,
    }
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The name of the team must be unique !')
    ]

sale_team()


class commission_worksheet(osv.osv):

    _name = 'commission.worksheet'
    _description = 'Commission Worksheet'

    def _get_other_info(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for sheet in self.browse(cr, uid, ids, context):
            object = sheet.salesperson_id or sheet.sale_team_id or False
            if object:
                res[sheet.id] = {
                    'commission_rule_id': object.commission_rule_id and object.commission_rule_id.id or False,
                    'last_pay_date_rule': object.last_pay_date_rule,
                    'require_paid': object.require_paid,
                    'require_posted': object.require_posted,
                    'allow_overdue': object.allow_overdue,
                    'buffer_days': object.buffer_days
                }
        return res

    def _get_period(self, cr, uid, context=None):
        if context is None:
            context = {}
        if context.get('period_id', False):
            return context.get('period_id')
        ctx = dict(context, account_period_prefer_normal=True)
        periods = self.pool.get('account.period').find(cr, uid, context=ctx)
        return periods and periods[0] or False

    def _calculate_commission(self, cr, uid, rule, worksheet, invoices, context=None):
        if rule.type == 'percent_fixed':
            return self._calculate_percent_fixed(cr, uid, rule, worksheet, invoices, context=context)
        if rule.type == 'percent_product_category':
            return self._calculate_percent_product_category(cr, uid, rule, worksheet, invoices, context=context)
        if rule.type == 'percent_product':
            return self._calculate_percent_product(cr, uid, rule, worksheet, invoices, context=context)
        if rule.type == 'percent_product_step':
            return self._calculate_percent_product_step(cr, uid, rule, worksheet, invoices, context=context)
        if rule.type == 'percent_amount':
            return self._calculate_percent_amount(cr, uid, rule, worksheet, invoices, context=context)
        # No matched rule return False as signal.
        return False

    def _prepare_worksheet_line(self, worksheet, invoice, base_amt, commission_amt, context=None):
        # Invoice or Refund
        sign = invoice.type == 'out_refund' and -1 or 1
        res = {
            'worksheet_id': worksheet.id,
            'invoice_id': invoice.id,
            'date_invoice': invoice.date_invoice,
            'invoice_amt': base_amt * sign,
            'commission_amt': commission_amt * sign,
        }
        return res

    def _get_base_amount(self, invoice):
        # Generic case
        base_amt = invoice.amount_untaxed
        return base_amt
    # --- This sections provide logics for each rules ---

    def _calculate_percent_fixed(self, cr, uid, rule, worksheet, invoices, context=None):
        if context is None:
            context = {}
        context.update({'last_loop': False})
        commission_rate = rule.fix_percent / 100
        worksheet_line_obj = self.pool.get('commission.worksheet.line')
        length, i = len(invoices), 0
        for invoice in invoices:
            i += 1  # Mark last loop and updat context (to be passed to _amount_all
            if i == length:
                context.update({'last_loop': True})
            base_amt = self._get_base_amount(invoice)
            # For each order, find its match rule line
            commission_amt = 0.0
            if commission_rate:
                commission_amt = base_amt * commission_rate
            res = self._prepare_worksheet_line(worksheet, invoice, base_amt, commission_amt, context=context)
            worksheet_line_obj.create(cr, uid, res, context=context)
        return True

    def _calculate_percent_product_category(self, cr, uid, rule, worksheet, invoices, context=None):
        if context is None:
            context = {}
        context.update({'last_loop': False})
        commission_rate = 0.0
        worksheet_line_obj = self.pool.get('commission.worksheet.line')
        length, i = len(invoices), 0
        for invoice in invoices:
            i += 1  # Mark last loop and updat context (to be passed to _amount_all
            if i == length:
                context.update({'last_loop': True})
            base_amt = self._get_base_amount(invoice)
            # For each product line
            commission_amt = 0.0
            for line in invoice.invoice_line:
                percent_commission = line.product_id.categ_id.percent_commission
                commission_rate = percent_commission and percent_commission / 100 or 0.0
                if commission_rate:
                    commission_amt += line.price_subtotal * commission_rate
            res = self._prepare_worksheet_line(worksheet, invoice, base_amt, commission_amt, context=context)
            worksheet_line_obj.create(cr, uid, res, context=context)
        return True

    def _calculate_percent_product(self, cr, uid, rule, worksheet, invoices, context=None):
        if context is None:
            context = {}
        context.update({'last_loop': False})
        commission_rate = 0.0
        worksheet_line_obj = self.pool.get('commission.worksheet.line')
        length, i = len(invoices), 0
        for invoice in invoices:
            i += 1  # Mark last loop and updat context (to be passed to _amount_all
            if i == length:
                context.update({'last_loop': True})
            base_amt = self._get_base_amount(invoice)
            # For each product line
            commission_amt = 0.0
            for line in invoice.invoice_line:
                # Make sure the product price each the limit_price, before assign commission
                percent_commission = (line.price_unit >= line.product_id.limit_price) and line.product_id.percent_commission or 0.0
                commission_rate = percent_commission and percent_commission / 100 or 0.0
                if commission_rate:
                    commission_amt += line.price_subtotal * commission_rate
            res = self._prepare_worksheet_line(worksheet, invoice, base_amt, commission_amt, context=context)
            worksheet_line_obj.create(cr, uid, res, context=context)
        return True

    def _calculate_percent_product_step(self, cr, uid, rule, worksheet, invoices, context=None):
        if context is None:
            context = {}
        context.update({'last_loop': False})
        commission_rate = 0.0
        worksheet_line_obj = self.pool.get('commission.worksheet.line')
        product_uom_obj = self.pool.get('product.uom')
        length, i = len(invoices), 0
        for invoice in invoices:
            i += 1  # Mark last loop and updat context (to be passed to _amount_all
            if i == length:
                context.update({'last_loop': True})
            base_amt = self._get_base_amount(invoice)
            # For each product line
            commission_amt = 0.0
            for line in invoice.invoice_line:
                percent_commission = 0.0
                # Getting steps commission
                product = line.product_id
                if not product:
                    continue
                default_uom = product.uom_id and product.uom_id.id
                q = product_uom_obj._compute_qty(cr, uid, line.uos_id.id, 1, default_uom)
                uom_price_unit = line.price_unit / (q or 1.0)
                if product.rate_step_ids:
                    rate_steps = [(x.amount_over, x.percent_commission) for x in product.rate_step_ids]
                    rate_steps = sorted(rate_steps, reverse=True)
                    for rate_step in rate_steps:
                        if uom_price_unit >= rate_step[0]:
                            percent_commission = rate_step[1]
                            break
                        else:
                            continue
                # --
                commission_rate = percent_commission and percent_commission / 100 or 0.0
                if commission_rate:
                    commission_amt += line.price_subtotal * commission_rate
            res = self._prepare_worksheet_line(worksheet, invoice, base_amt, commission_amt, context=context)
            worksheet_line_obj.create(cr, uid, res, context=context)
        return True

    def _calculate_percent_amount(self, cr, uid, rule, worksheet, invoices, context=None):
        if context is None:
            context = {}
        context.update({'last_loop': False})
        worksheet_line_obj = self.pool.get('commission.worksheet.line')
        length, i = len(invoices), 0
        for invoice in invoices:
            i += 1  # Mark last loop and updat context (to be passed to _amount_all
            if i == length:
                context.update({'last_loop': True})
            base_amt = self._get_base_amount(invoice)
            # For each order, find its match rule line
            commission_amt = 0.0
            ranges = rule.rule_rates
            for range in ranges:
                commission_rate = range.percent_commission / 100
                if base_amt <= range.amount_upto:
                    commission_amt = base_amt * commission_rate
                    break
            res = self._prepare_worksheet_line(worksheet, invoice, commission_amt, context=context)
            worksheet_line_obj.create(cr, uid, res, context=context)
        return True

    # --- END ---

    def _get_product_commission(self, cr, uid):
        ir_model_data = self.pool.get('ir.model.data')
        product = ir_model_data.get_object(cr, uid, 'sale_commission_calc', 'product_product_commission')
        return product.id

    def _get_worksheet(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('commission.worksheet.line').browse(cr, uid, ids, context=context):
            result[line.worksheet_id.id] = True
        return result.keys()

    def _amount_all(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        if context is None:
            context = {}
        # If called from calculation method, only do when last_loop = true. But if not, i.e., from update worksheet line, always do it.
        if ('last_loop' not in context) or context.get('last_loop', False):
            for worksheet in self.browse(cr, uid, ids, context=context):
                res[worksheet.id] = {
                    'amount_draft': 0.0,
                    'amount_valid': 0.0,
                    'amount_invalid': 0.0,
                    'amount_done': 0.0,
                    'amount_skip': 0.0,
                    'amount_total': 0.0,
                }
                total = 0.0
                # Update line status first.
                line_ids = [line.id for line in worksheet.worksheet_lines]
                self.pool.get('commission.worksheet.line').update_commission_line_status(cr, uid, line_ids, context=context)
                # Start calculation.
                for line in worksheet.worksheet_lines:
                    if line.commission_state == 'draft':
                        res[worksheet.id]['amount_draft'] += line.amount_subtotal
                    if line.commission_state == 'valid':
                        res[worksheet.id]['amount_valid'] += line.amount_subtotal
                    if line.commission_state == 'invalid':
                        res[worksheet.id]['amount_invalid'] += line.amount_subtotal
                    if line.commission_state == 'done':
                        res[worksheet.id]['amount_done'] += line.amount_subtotal
                    if line.commission_state == 'skip':
                        res[worksheet.id]['amount_skip'] += line.amount_subtotal
                    total += line.amount_subtotal
                res[worksheet.id]['amount_total'] = total
        return res

    _columns = {
        'name': fields.char('Name', size=64, required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'sale_team_id': fields.many2one('sale.team', 'Team', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'salesperson_id': fields.many2one('res.users', 'Salesperson', required=False, readonly=True, states={'draft': [('readonly', False)]}),
        'period_id': fields.many2one('account.period', 'Period', required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'worksheet_lines': fields.one2many('commission.worksheet.line', 'worksheet_id', 'Calculation Lines', ondelete='cascade', readonly=False),
        'state': fields.selection([('draft', 'Draft'),
                                   ('confirmed', 'Confirmed'),
                                   ('done', 'Done'),
                                   ('cancel', 'Cancelled')], 'Status', required=True, readonly=True,
                help='* The \'Draft\' status is set when the work sheet in draft status. \
                    \n* The \'Confirmed\' status is set when the work sheet is confirmed by related parties. \
                    \n* The \'Done\' status is set when the work sheet is ready to pay for commission. This state can not be undone. \
                    \n* The \'Cancelled\' status is set when a user cancel the work sheet.'),
        'invoice_ids': fields.one2many('account.invoice', 'worksheet_id', 'Invoices', readonly=True),
        'amount_draft': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Not Ready', multi='sums',
            store={
                #'commission.worksheet': (lambda self, cr, uid, ids, c={}: ids, ['worksheet_lines'], 10),
                'commission.worksheet.line': (_get_worksheet, ['done', 'force', 'adjust_amt', 'commission_state'], 10),
            },),
        'amount_valid': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Ready', multi='sums',
            store={
                #'commission.worksheet': (lambda self, cr, uid, ids, c={}: ids, ['worksheet_lines'], 10),
                'commission.worksheet.line': (_get_worksheet, ['done', 'force', 'adjust_amt', 'commission_state'], 10),
            },),
        'amount_invalid': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Invalid', multi='sums',
            store={
                #'commission.worksheet': (lambda self, cr, uid, ids, c={}: ids, ['worksheet_lines'], 10),
                'commission.worksheet.line': (_get_worksheet, ['done', 'force', 'adjust_amt', 'commission_state'], 10),
            },),
        'amount_done': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Done', multi='sums',
            store={
                #'commission.worksheet': (lambda self, cr, uid, ids, c={}: ids, ['worksheet_lines'], 10),
                'commission.worksheet.line': (_get_worksheet, ['done', 'force', 'adjust_amt', 'commission_state'], 10),
            },),
        'amount_skip': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Skipped', multi='sums',
            store={
                #'commission.worksheet': (lambda self, cr, uid, ids, c={}: ids, ['worksheet_lines'], 10),
                'commission.worksheet.line': (_get_worksheet, ['done', 'force', 'adjust_amt', 'commission_state'], 10),
            },),
        'amount_total': fields.function(_amount_all, digits_compute=dp.get_precision('Account'), string='Total Amount', multi='sums',
            store={
                #'commission.worksheet': (lambda self, cr, uid, ids, c={}: ids, ['worksheet_lines'], 20),
                'commission.worksheet.line': (_get_worksheet, ['done', 'force', 'adjust_amt', 'commission_state'], 20),
            },),
        # Other Info
        'commission_rule_id': fields.function(_get_other_info, type='many2one', relation='commission.rule', string='Applied Commission',
            store=False, multi='other_info'),
        'last_pay_date_rule': fields.function(_get_other_info, type='selection', selection=LAST_PAY_DATE_RULE, string='Last Pay Date Rule',
            store=False, multi='other_info'),
        'require_paid': fields.function(_get_other_info, type='boolean', string='Require Paid Invoice',
            store=False, multi='other_info'),
        'require_posted': fields.function(_get_other_info, type='boolean', string='Require Payment Detail Posted',
            store=False, multi='other_info'),
        'allow_overdue': fields.function(_get_other_info, type='boolean', string='Allow Overdue Payment',
            store=False, multi='other_info'),
        'buffer_days': fields.function(_get_other_info, type='integer', relation='commission.rule', string='Buffer Days',
            store=False, multi='other_info'),
    }
    _defaults = {
        'state': 'draft',
        'period_id': _get_period,
        'name': '/'
    }
    _sql_constraints = [
        ('unique_sale_team_period', 'unique(sale_team_id, period_id)', 'Duplicate Sale Team / Period'),
        ('unique_salesperson_period', 'unique(salesperson_id, period_id)', 'Duplicate Salesperson / Period')
    ]
    _order = 'id desc'

    def create(self, cr, uid, vals, context=None):
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'commission.worksheet') or '/'
        return super(commission_worksheet, self).create(cr, uid, vals, context=context)

    def action_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'draft'})
        return True

    def action_confirm(self, cr, uid, ids, context=None):
        # Only if today has passed the period, allow to confirm
        period_obj = self.pool.get('account.period')
        for worksheet in self.browse(cr, uid, ids):
            period = period_obj.browse(cr, uid, worksheet.period_id.id)
            if time.strftime('%Y-%m-%d') <= period.date_stop:
                raise osv.except_osv(_('Warning!'), _("You cannot confirm this worksheet. Period not yet over!"))
            # self.action_calculate(cr, uid, ids, context=context)
        # Confirm all worksheet
        self.write(cr, uid, ids, {'state': 'confirmed'})
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        # Only allow cancel if no commission has been paid yet.
        worksheet_line_obj = self.pool.get('commission.worksheet.line')
        for worksheet in self.browse(cr, uid, ids):
            line_ids = worksheet_line_obj.search(cr, uid, [('worksheet_id', '=', worksheet.id), ('done', '=', True)])
            if line_ids:
                raise osv.except_osv(_('Warning!'), _("Worksheet(s) has issued commission(s) and can not be cancelled!"))
        self.write(cr, uid, ids, {'state': 'cancel'})
        return True

    def action_done(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'done'})
        return True

    def _get_matched_invoices_by_period(self, cr, uid, salesperson_id, sale_team_id, period, context=None):
        res_id = salesperson_id or sale_team_id
        condition = salesperson_id and 't.salesperson_id = %s' or 't.sale_team_id = %s'
        cr.execute("select ai.id from account_invoice ai \
                            join account_invoice_team t on ai.id = t.invoice_id \
                            where ai.state in ('open','paid') \
                            and ai.type in ('out_invoice','out_refund') \
                            and date_invoice >= %s and date_invoice <= %s \
                            and " + condition + " order by ai.id", \
                            (period.date_start, period.date_stop, res_id))
        invoice_ids = map(lambda x: x[0], cr.fetchall())
        return invoice_ids

    def action_calculate(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        period_obj = self.pool.get('account.period')
        worksheet_line_obj = self.pool.get('commission.worksheet.line')
        invoice_obj = self.pool.get('account.invoice')
        # For each work sheet, reset the calculation
        for worksheet in self.browse(cr, uid, ids):
            salesperson_id = worksheet.salesperson_id and worksheet.salesperson_id.id or False
            sale_team_id = worksheet.sale_team_id and worksheet.sale_team_id.id or False
            period = period_obj.browse(cr, uid, worksheet.period_id.id)
            if not (salesperson_id or sale_team_id) or not period:
                continue
            rule = (worksheet.salesperson_id and worksheet.salesperson_id.commission_rule_id) \
                    or (worksheet.sale_team_id and worksheet.sale_team_id.commission_rule_id)
            if not rule:
                raise osv.except_osv(_('Error!'), _('No commission rule specified for this salesperson/team!'))
            # Delete old lines
            line_ids = worksheet_line_obj.search(cr, uid, [('worksheet_id', '=', worksheet.id)])
            worksheet_line_obj.unlink(cr, uid, line_ids)
            # Search for matched Completed Invoice for this work sheet (either salesperson or sales team)
            invoice_ids = self._get_matched_invoices_by_period(cr, uid, salesperson_id, sale_team_id, period, context=context)
            invoices = invoice_obj.browse(cr, uid, invoice_ids)
            self._calculate_commission(cr, uid, rule, worksheet, invoices, context=context)
            # Update satus
#             line_ids = [line.id for line in worksheet.worksheet_lines]
#             self.pool.get('commission.worksheet.line').update_commission_line_status(cr, uid, line_ids, context=context)
        return True

#     def update_line_status(self, cr, uid, ids, context=None):
#         for worksheet in self.browse(cr, uid, ids):
#             line_ids = [line.id for line in worksheet.worksheet_lines]
#             self.pool.get('commission.worksheet.line').update_commission_line_status(cr, uid, line_ids, context=context)
#         return True

    def final_update_invoice(self, cr, uid, inv_rec, context=None):
        # Prepare for hook
        return inv_rec

    def final_update_invoice_line(self, cr, uid, inv_rec_line, context=None):
        # Prepare for hook
        return inv_rec_line

    def action_create_invoice(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        context.update({'type': 'in_invoice'})
        worksheet_line_obj = self.pool.get('commission.worksheet.line')
        inv_obj = self.pool.get('account.invoice')
        invline_obj = self.pool.get('account.invoice.line')
        invoice_ids = []
        worksheets = self.browse(cr, uid, ids, context=context)
        product_id = self._get_product_commission(cr, uid)
        for worksheet in  worksheets:
            users = []
            if worksheet.salesperson_id:
                users = [worksheet.salesperson_id]
            elif worksheet.sale_team_id:
                users = worksheet.sale_team_id.users
            else:
                continue

            line_ids = worksheet_line_obj.search(cr, uid, [('worksheet_id', '=', worksheet.id),
                                                           ('commission_state', '=', 'valid')])
            if not line_ids:
                raise osv.except_osv(_('Warning!'), _("No Commission Invoice(s) can be created for Worksheet %s" % (worksheet.name)))

            #Create invoice for each sale person in team
            for user in users:
                #initial value of invoice
                inv_rec = inv_obj.default_get(cr, uid,
                                              ['type', 'state', 'journal_id', 'currency_id', 'company_id', 'reference_type', 'check_total',
                                               'internal_number', 'user_id', 'sent'], context=context)
                inv_rec.update(inv_obj.onchange_partner_id(cr, uid, [], 'in_invoice', user.partner_id.id, company_id=inv_rec['company_id'])['value'])
                inv_rec.update({'origin': worksheet.name,
                                'worksheet_id': worksheet.id,
                                'type': 'in_invoice',
                                'partner_id': user.partner_id.id,
                                'date_invoice': time.strftime('%Y-%m-%d'),
                                'comment': context.get('comment', False)})
                inv_rec = self.final_update_invoice(cr, uid, inv_rec, context=context)
                invoice_id = inv_obj.create(cr, uid, inv_rec, context=context)
                invoice_ids.append(invoice_id)
                wlines = worksheet_line_obj.browse(cr, uid, line_ids, context=context)
                for wline in wlines:
#                   #initial value of invoice lines
                    inv_line_rec = (invline_obj.product_id_change(cr, uid, [], product_id, False, 1, name=False, type='in_invoice',
                                    partner_id=user.partner_id.id, fposition_id=False,
                                    price_unit=0, currency_id=inv_rec['currency_id'],
                                    context=None, company_id=inv_rec['company_id'])['value'])
                    inv_line_rec.update({
                                         'name': _('Period: ') + worksheet.period_id.name + \
                                                _(', Invoice: ') + wline.invoice_id.number,
                                         'origin': worksheet.name,
                                         'invoice_id': invoice_id,
                                         'product_id': product_id,
                                         'partner_id': user.partner_id.id,
                                         'company_id': inv_rec['company_id'],
                                         'currency_id': inv_rec['currency_id'],
                                         'price_unit': wline.amount_subtotal,
                                         'price_subtotal': wline.amount_subtotal,
                                         })
                    invline_obj.create(cr, uid, inv_line_rec, context=context)
                    #Update worksheet line was paid commission
                    worksheet_line_obj.write(cr, uid, [wline.id], {'done': True, 'commission_state': 'done'}, context)
            if worksheet_line_obj.search_count(cr, uid, [('worksheet_id', '=', worksheet.id), ('commission_state', 'in', ('draft', 'valid'))]) <= 0:
                #All worksheet lines has been paid will update state of worksheet is done.
                self.write(cr, uid, [worksheet.id], {'state': 'done'})
        #Show new Invoice
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'account', 'action_invoice_tree2')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['domain'] = "[('id','in', [" + ','.join(map(str, invoice_ids)) + "])]"
        result['name'] = 'Commission invoice(s)'
        return result

commission_worksheet()


class commission_worksheet_line(osv.osv):

    _name = "commission.worksheet.line"
    _description = "Commission Worksheet Lines"

    def _get_date_maturity(self, cr, uid, invoice, date_start):
        payment_term_id = invoice.partner_id.property_payment_term and invoice.partner_id.property_payment_term.id or False
        if payment_term_id:
            pterm_list = self.pool.get('account.payment.term').compute(cr, uid, payment_term_id, value=1, date_ref=date_start)
            if pterm_list:
                pterm_list = [l[0] for l in pterm_list]
                pterm_list.sort()
                date_maturity = pterm_list[-1]
                return date_maturity
        return False

    def _calculate_last_pay_date(self, cr, uid, rule, invoice, context=None):
        if rule == 'invoice_duedate':
            return invoice.date_due
        elif rule == 'invoice_date_plus_cust_payterm':
            date_start = invoice.date_invoice
            return self._get_date_maturity(cr, uid, invoice, date_start) or invoice.date_due
        else:
            return None

    def _get_commission_params(self, cr, uid, ids, context=None):
        res = {
            'require_paid': False,
            'require_posted': False,
            'allow_overdue': False,
            'last_pay_date_rule': False,
            'buffer_days': 0,
        }
        if ids:
            worksheet = self.browse(cr, uid, ids[0], context=context).worksheet_id
            i = worksheet.salesperson_id or worksheet.sale_team_id
            if i:
                res['require_paid'] = i.require_paid
                res['require_posted'] = i.require_posted
                res['allow_overdue'] = i.allow_overdue
                res['last_pay_date_rule'] = i.last_pay_date_rule
                res['buffer_days'] = i.buffer_days
        return res

    def _get_invoice_related_payment_amt(self, cr, uid, invoice, context=None):
        """
        This method will get amount of all payment related to this invoice. Note that, the amount will also cover other invoices
        """
        ids = [x.id for x in invoice.payment_ids]
        if not ids:
            return 0.0
        cr.execute("select sum(av.amount) from account_voucher av \
                        where av.id in ( \
                            select mv.id from account_move_line ml \
                            inner join account_move m on m.id = ml.move_id \
                            inner join account_voucher mv on mv.move_id = m.id \
                            where ml.id in %s \
                        ) \
                        and state = 'posted'", (tuple(ids),))
        sum_payments = ids and cr.fetchone()[0] or 0.0
        return sum_payments

    def _get_invoice_related_payment_detail_amt(self, cr, uid, invoice, context=None):
        """
        This method will get amount of all payment details related to this invoice. Note that, the amount will also cover other invoices
        """
        ids = [x.id for x in invoice.payment_ids]
        if not ids:
            return 0.0
        cr.execute("select sum(pd.amount) from payment_register pd \
                        inner join account_voucher av on av.id = pd.voucher_id \
                        where av.id in ( \
                            select mv.id from account_move_line ml \
                            inner join account_move m on m.id = ml.move_id \
                            inner join account_voucher mv on mv.move_id = m.id \
                            where ml.id in %s \
                        ) \
                        and pd.state = 'posted'", (tuple(ids),))
        sum_registers = ids and cr.fetchone()[0] or 0.0
        return sum_registers

    def _is_pay_posted(self, cr, uid, invoice, context=None):
        payment_amt = self._get_invoice_related_payment_amt(cr, uid, invoice) or 0.0
        paid_amt = self._get_invoice_related_payment_detail_amt(cr, uid, invoice) or 0.0
        # Payment is posted if total in posted payment_details >= total pay about in payments
        if paid_amt >= payment_amt:
            return True
        return False

    def _check_commission_line_status(self, cr, uid, line, params, context=None):
        res = {}
        # Params
        require_paid = params['require_paid']
        require_posted = params['require_posted']
        allow_overdue = params['allow_overdue']
        last_pay_date_rule = params['last_pay_date_rule']
        buffer_days = params['buffer_days']
        # Checks
        invoice = line.invoice_id
        # Calculate each field,
        # 1) paid_date
        paid_date = (invoice.state == 'paid' and invoice.payment_ids and invoice.payment_ids[-1].date or None)
        # 2) last_pay_date
        last_pay_date = self._calculate_last_pay_date(cr, uid, last_pay_date_rule, invoice, context=context)
        # Add buffer
        last_pay_date = (datetime.strptime(last_pay_date, '%Y-%m-%d') + relativedelta(days=buffer_days or 0)).strftime('%Y-%m-%d')
        # 3) posted payment?
        # 3.1) invoie's payment and paid amount
        posted = invoice.state == 'paid' and self._is_pay_posted(cr, uid, invoice) or False
        # 4) is overdue
        # If allow commission overdue, this will never be overdue. Else, check paid_date against last pay date
        overdue = not allow_overdue and \
                    last_pay_date and \
                    paid_date and \
                    (datetime.strptime(paid_date, '%Y-%m-%d') > datetime.strptime(last_pay_date, '%Y-%m-%d')) or \
                    False
        # 5) commission_state
        state = 'draft'
        if line.done:  # Done, always done and do nothing.
            state = 'done'
        elif line.invoice_state == 'cancel':  # Cancelled invoice, always invalid
            state = 'invalid'
        elif line.force == 'skip':  # Skip, always skip.
            state = 'skip'
        elif line.force == 'allow':  # Allow, always valid.
            state = 'valid'
        elif line.invoice_state == 'open':  # Allow unpaid, always valid.
            if not require_paid:
                state = 'valid'
        elif line.invoice_state == 'paid':
            if posted:
                if not overdue:
                    state = 'valid'  # Paid + posted + Not Overdue
                else:
                    if allow_overdue:
                        state = 'valid'  # Paid + posted + Overdue, but allow over due
                    else:
                        state = 'invalid'  # otherwise invalid
            else:
                if not require_posted:
                    if not overdue:
                        state = 'valid'  # Paid + posted + Not Overdue
                    else:
                        if allow_overdue:
                            state = 'valid'  # Paid + posted + Overdue, but allow over due
                        else:
                            state = 'invalid'  # otherwise invalid
                else:
                    state = 'draft'  # Paid + Not posted
        # Updates
        res = {
            'paid_date': paid_date,
            'last_pay_date': last_pay_date,
            'posted': posted,
            'overdue': overdue,
            'commission_state': state
        }
        return res

    def update_commission_line_status(self, cr, uid, ids, context=None):
        res = {}
        # Prepare parameter from worksheet
        params = self._get_commission_params(cr, uid, ids, context=context)
        # For each worksheet line,
        for line in self.browse(cr, uid, ids, context=context):
            res = self._check_commission_line_status(cr, uid, line, params, context=context)
            cr.execute('update commission_worksheet_line set \
                            paid_date = %s, \
                            last_pay_date = %s, \
                            posted = %s, \
                            overdue = %s, \
                            commission_state = %s \
                            where id = %s',
                                    (res['paid_date'],
                                     res['last_pay_date'],
                                     res['posted'],
                                     res['overdue'],
                                     res['commission_state'],
                                     line.id))
        return True

    def _amount_subtotal(self, cr, uid, ids, name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context=context):
            res[line.id] = line.commission_amt + line.adjust_amt
        return res

    _columns = {
        'worksheet_id': fields.many2one('commission.worksheet', 'Commission Worksheet', ondelete='cascade'),
        'invoice_id': fields.many2one('account.invoice', 'Invoice', readonly=True),
        'partner_id': fields.related('invoice_id', 'partner_id', type="many2one", relation="res.partner", string="Customer", readonly=True),
        'date_invoice': fields.date('Invoice Date', readonly=True),
        'invoice_amt': fields.float('Amount', readonly=True),
        'commission_amt': fields.float('Commission', readonly=True),
        'adjust_amt': fields.float('Adjust', readonly=True, states={'confirmed': [('readonly', False)]}, help="Adjustment can be both positive or negative"),
        'amount_subtotal': fields.function(_amount_subtotal, digits_compute=dp.get_precision('Account'), string='Total',
            store={
                   'commission.worksheet.line': (lambda self, cr, uid, ids, c={}: ids, ['commission_amt', 'adjust_amt'], 5),
            }),
        'invoice_state': fields.related('invoice_id', 'state', type='selection', readonly=True, string="Status",
                                        selection=[('open', 'Open'),
                                                    ('paid', 'Paid'),
                                                    ('cancel', 'Cancelled')]),
        'paid_date': fields.date('Paid Date', readonly=True, help="The date of payment that make this invoice marked as paid"),
        'last_pay_date': fields.date('Due Date', readonly=True, help="Last payment date that will make commission valid. This date is calculated by the due date condition"),
        'overdue': fields.boolean('Overdue', readonly=True, help="For the paid invoice, is it over due?"),
        'commission_state': fields.selection(COMMISSION_LINE_STATE, 'State', readonly=True),
        'posted': fields.boolean('Posted', readonly=True, help="This flag show whether all payment has been posted as Payment Details"),
        'done': fields.boolean('Done', readonly=True, help="This flag show whether the commission has been issued."),
        'force': fields.selection([('skip', 'Skip'), ('allow', 'Allow')], 'Force', readonly=True, states={'confirmed': [('readonly', False)]},),
        'note': fields.text('Note', help="Reason for forcing", readonly=True, states={'confirmed': [('readonly', False)]},),
        'state': fields.related('worksheet_id', 'state', type='selection', selection=[('draft', 'Draft'),
                                   ('confirmed', 'Confirmed'),
                                   ('done', 'Done'),
                                   ('cancel', 'Cancelled')], string='Worksheet State')
    }
    _defaults = {
        'done': False,
    }
    _order = 'id'

    def unlink(self, cr, uid, ids, context=None):
        line_ids = self.search(cr, uid, [('id', 'in', ids), ('done', '=', True)], context=context)
        if line_ids and len(line_ids) > 0:
            wlines = self.browse(cr, uid, line_ids)
            invoice_numbers = [wline.invoice_id.number for wline in wlines]
            raise osv.except_osv(_('Error!'), _("You can't delete this Commission Worksheet, \
                                                because commission has been issued for Invoice No. %s" % (",".join(invoice_numbers))))
        else:
            return super(commission_worksheet_line, self).unlink(cr, uid, ids, context=context)

#     def write(self, cr, uid, ids, vals, context=None):
#         res = super(commission_worksheet_line, self).write(cr, uid, ids, vals, context=context)
#         self.update_commission_line_status(cr, uid, ids, context=context)
#         return res

commission_worksheet_line()


class res_users(osv.osv):

    _inherit = "res.users"
    _columns = {
        'commission_rule_id': fields.many2one('commission.rule', 'Applied Commission', required=False, readonly=False),
        'require_paid': fields.boolean('Require Paid Invoice', help='Require invoice to be paid in full amount.'),
        'require_posted': fields.boolean('Require Payment Detail Posted', help='Require that all payment detail related to payments to invoice has been posted.'),
        'allow_overdue': fields.boolean('Allow Overdue Payment', help='Allow paying commission with overdue payment.'),
        'last_pay_date_rule': fields.selection(LAST_PAY_DATE_RULE, 'Last Pay Date Rule'),
        'buffer_days': fields.integer('Buffer Days')
    }
    _defaults = {
        'require_paid': False,
        'require_posted': False,
        'allow_overdue': False,
        'buffer_days': 0,
    }

res_users()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
