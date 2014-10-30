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
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv


class hr_expense_expense(osv.osv):

    def _is_vatinfo_tax(self, cr, uid, ids, fieldnames, args, context=None):
        result = dict.fromkeys(ids, 0)
        for record in self.browse(cr, uid, ids, context=context):
            # If any line has vatinfo_tax_amount
            for line in record.expense_vatinfo:
                if line.vatinfo_tax_amount:
                    result[record.id] = True
                    break
                else:
                    result[record.id] = False
        return result

    def _get_expense(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('hr.expense.line').browse(cr, uid, ids, context=context):
            result[line.expense_id.id] = True
        return result.keys()

    _inherit = 'hr.expense.expense'

    _columns = {
        'number': fields.char('Expense Number', size=128, required=False, readonly=True),
        'vatinfo_move_id': fields.many2one('account.move', 'Journal Entry (VAT Info)', readonly=True, select=1, ondelete='restrict', help="Link to the automatically generated Journal Items for Vat Info."),
        'vatinfo_move_date': fields.related('vatinfo_move_id', 'date', type="date", string="Journal Date (VAT Info)", readonly=True, states={'draft': [('readonly', False)]}, store=True),
        'expense_vatinfo': fields.one2many('hr.expense.line', 'expense_id', 'Expense Lines', readonly=False),
        'is_vatinfo_tax': fields.function(_is_vatinfo_tax, type='boolean', string='Is VAT Info Tax',
                    store={
                           'hr.expense.expense': (lambda self, cr, uid, ids, c={}: ids, None, 10),
                           'hr.expense.line': (_get_expense, ['vatinfo_tax_amount'], 10)
                           }),
    }

    def create(self, cr, uid, vals, context=None):
        vals['number'] = self.pool.get('ir.sequence').get(cr, uid, 'hr.expense.invoice') or '/'
        return super(hr_expense_expense, self).create(cr, uid, vals, context=context)

    def expense_confirm(self, cr, uid, ids, context=None):
        res = super(hr_expense_expense, self).expense_confirm(cr, uid, ids, context=context)
        for expense in self.browse(cr, uid, ids):
            if not expense.number:
                number = self.pool.get('ir.sequence').get(cr, uid, 'hr.expense.invoice') or '/'
                self.write(cr, uid, expense.id, {'number': number})
        return res

    def line_get_convert(self, cr, uid, x, part, date, context=None):
        res = super(hr_expense_expense, self).line_get_convert(cr, uid, x, part, date, context=context)
        res.update({'vatinfo_supplier_name': x.get('vatinfo_supplier_name', False)})
        return res

    def account_move_get(self, cr, uid, expense_id, context=None):
        """
        If journal_id is not forced, use the default as forced journal.
        This is to be used for Post Vat Info action.
        """
        res = super(hr_expense_expense, self).account_move_get(cr, uid, expense_id, context=context)
        self.write(cr, uid, expense_id, {'journal_id': res.get('journal_id', False)})
        return res

    def post_vatinfo(self, cr, uid, ids, context=None):
        period_obj = self.pool.get('account.period')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        if context is None:
            context = {}
        for expense in self.browse(cr, uid, ids, context=context):
            if not expense.journal_id.sequence_id:
                raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this expense.'))
            if not expense.line_ids:
                raise osv.except_osv(_('No Expense Lines!'), _('Please create some expense lines.'))
            if expense.vatinfo_move_id:
                continue

            ctx = context.copy()
            # one move line per expense line
            iml = self.pool.get('hr.expense.line').vatinfo_move_line_get(cr, uid, expense.id, context=ctx)

            date = time.strftime('%Y-%m-%d')
            part = self.pool.get("res.partner")._find_accounting_partner(expense.employee_id.address_home_id)
            line = map(lambda x: (0, 0, self.line_get_convert(cr, uid, x, part, date, context=ctx)), iml)

            journal_id = expense.journal_id.id
            journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
            if journal.centralisation:
                raise osv.except_osv(_('User Error!'),
                        _('You cannot create an expense on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

            line = self.finalize_expense_move_lines(cr, uid, expense, line)

            move = {
                'name': expense.number + '-A',
                'ref': expense.name,
                'line_id': line,
                'journal_id': journal_id,
                'date': date,
                'narration': expense.note,
                'company_id': expense.company_id.id,
            }
            ctx.update(company_id=expense.company_id.id,
                       account_period_prefer_normal=True)
            period_ids = period_obj.find(cr, uid, date, context=ctx)
            period_id = period_ids and period_ids[0] or False
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id

            move_id = move_obj.create(cr, uid, move, context=ctx)
            new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
            # make the invoice point to that move
            self.write(cr, uid, [expense.id], {'vatinfo_move_id': move_id, 'period_id': period_id, 'move_name': new_move_name}, context=ctx)
            move_obj.post(cr, uid, [move_id], context=ctx)
        return True

    def finalize_expense_move_lines(self, cr, uid, expense_browse, move_lines):
        """finalize_expense_move_lines(cr, uid, expense, move_lines) -> move_lines
        Hook method to be overridden in additional modules to verify and possibly alter the
        move lines to be created by an expense, for special cases.
        :param expense_browse: browsable record of the expense that is generating the move lines
        :param move_lines: list of dictionaries with the account.move.lines (as for create())
        :return: the (possibly updated) final move_lines to create for this expense
        """
        return move_lines

    def unpost_vatinfo(self, cr, uid, ids, context=None):
        move_obj = self.pool.get('account.move')
        if context is None:
            context = {}
        for expense in self.browse(cr, uid, ids, context=context):
            move_id = expense.vatinfo_move_id.id
            move_obj.button_cancel(cr, uid, [move_id])
            self.write(cr, uid, [expense.id], {'vatinfo_move_id': False})
            move_obj.unlink(cr, uid, [move_id])
        #self._log_event(cr, uid, ids)
        return True

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({'vatinfo_move_id': False})
        return super(hr_expense_expense, self).copy(cr, uid, id, default, context=context)

hr_expense_expense()


class hr_expense_line(osv.osv):

    _inherit = 'hr.expense.line'

    _columns = {
        'vatinfo_date': fields.date('Date', required=False, help='This date will be used as Tax Invoice Date in VAT Report'),
        'vatinfo_number': fields.char('Number', required=False, size=64, help='Number Tax Invoice'),
        'vatinfo_supplier_name': fields.char('Supplier', required=False, size=128, help='Name of Organization to pay Tax'),
        'vatinfo_tin': fields.char('Tax ID', required=False, size=64),
        'vatinfo_branch': fields.char('Branch No.', required=False, size=64),
        'vatinfo_base_amount': fields.float('Base', required=False, digits_compute=dp.get_precision('Account')),
        'vatinfo_tax_id': fields.many2one('account.tax', 'Tax', required=False, ),
        'vatinfo_tax_amount': fields.float('VAT', required=False, digits_compute=dp.get_precision('Account')),
    }

    def onchange_vat(self, cr, uid, ids, vatinfo_tax_id, vatinfo_tax_amount, context=None):
        res = {}
        if vatinfo_tax_id and vatinfo_tax_amount:
            vatinfo_tax = self.pool.get('account.tax').browse(cr, uid, vatinfo_tax_id)
            tax_percent = vatinfo_tax.amount or 0.0
            if tax_percent > 0.0:
                res['vatinfo_base_amount'] = vatinfo_tax_amount / tax_percent
        return {'value': res}

    def action_add_vatinfo(self, cr, uid, ids, data, context=None):
        for vatinfo in self.browse(cr, uid, ids, context=context):
            if vatinfo.expense_id.vatinfo_move_id:
                raise osv.except_osv(_('Error!'),
                    _('VAT Info can be changed only when it is not posted. \n' +
                      'To change, Unpost VAT Info first.'))

            self.write(cr, uid, vatinfo.id, {'vatinfo_date': data.vatinfo_date,
                                                 'vatinfo_number': data.vatinfo_number,
                                                 'vatinfo_supplier_name': data.vatinfo_supplier_name,
                                                 'vatinfo_tin': data.vatinfo_tin,
                                                 'vatinfo_branch': data.vatinfo_branch,
                                                 'vatinfo_base_amount': data.vatinfo_base_amount,
                                                 'vatinfo_tax_id': data.vatinfo_tax_id.id,
                                                 'vatinfo_tax_amount': data.vatinfo_tax_amount})
        return True

    def vatinfo_move_line_get(self, cr, uid, expense_id, context=None):
        if context is None:
            context = {}
        res = []
        expense = self.pool.get('hr.expense.expense').browse(cr, uid, expense_id, context=context)
        for line in expense.line_ids:
            # No additional vat info, continue
            if not line.vatinfo_tax_amount or line.vatinfo_tax_amount == 0:
                continue
            sign = 1
            account_id = line.vatinfo_tax_id.account_collected_id.id
            # Account Post, deduct from the Expense Line.
            if line.product_id and not line.product_id.property_account_expense:
                raise osv.except_osv(_('Error!'), _('Expense Account for this product %s is not defined!') % (line.product_id.name, ))
            res.append({
                'type': 'src',
                'name': line.name.split('\n')[0][:64],
                'price_unit': -sign * line.vatinfo_tax_amount,
                'quantity': 1.0,
                'price': -sign * line.vatinfo_tax_amount,
                'account_id': line.product_id and line.product_id.property_account_expense.id or False,
                'product_id': line.product_id and line.product_id.id or False,
                'uos_id': False,
                'account_analytic_id': False,
                'taxes': False,
            })
            # Account Post, Tax
            res.append({
                'type': 'tax',
                'name': line.vatinfo_tax_id.name,
                'price_unit': sign * line.vatinfo_tax_amount,
                'quantity': 1,
                'price': sign * line.vatinfo_tax_amount,
                'account_id': account_id,
                'product_id': False,
                'uos_id': False,
                'account_analytic_id': False,
                'taxes': False,
                'vatinfo_supplier_name': line.vatinfo_supplier_name,
            })
        return res

hr_expense_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
