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


class account_invoice(osv.osv):

    def _is_vatinfo_tax(self, cr, uid, ids, fieldnames, args, context=None):
        result = dict.fromkeys(ids, 0)
        for record in self.browse(cr, uid, ids, context=context):
            # If any line has vatinfo_tax_amount
            for line in record.invoice_vatinfo:
                if line.vatinfo_tax_amount:
                    result[record.id] = True
                    break
                else:
                    result[record.id] = False
        return result

    def _get_invoice(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('account.invoice.line').browse(cr, uid, ids, context=context):
            result[line.invoice_id.id] = True
        return result.keys()

    _inherit = 'account.invoice'

    _columns = {
        'vatinfo_move_id': fields.many2one('account.move', 'Journal Entry (VAT Info)', readonly=True, select=1, ondelete='restrict', help="Link to the automatically generated Journal Items for Vat Info."),
        'vatinfo_move_date': fields.related('vatinfo_move_id', 'date', type="date", string="Journal Date (VAT Info)", readonly=True),
        'invoice_vatinfo': fields.one2many('account.invoice.line', 'invoice_id', 'Invoice Lines', readonly=True, states={'draft': [('readonly', False)]}),
        'is_vatinfo_tax': fields.function(_is_vatinfo_tax, type='boolean', string='Is VAT Info Tax',
                    store={
                           'account.invoice': (lambda self, cr, uid, ids, c={}: ids, None, 10),
                           'account.invoice.line': (_get_invoice, ['vatinfo_tax_amount'], 10)
                           }),
    }

    def line_get_convert(self, cr, uid, x, part, date, context=None):
        res = super(account_invoice, self).line_get_convert(cr, uid, x, part, date, context=context)
        res.update({'vatinfo_supplier_name': x.get('vatinfo_supplier_name', False)})
        return res

    def post_vatinfo(self, cr, uid, ids, context=None):
        period_obj = self.pool.get('account.period')
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        if context is None:
            context = {}
        for inv in self.browse(cr, uid, ids, context=context):
            if not inv.journal_id.sequence_id:
                raise osv.except_osv(_('Error!'), _('Please define sequence on the journal related to this invoice.'))
            if not inv.invoice_line:
                raise osv.except_osv(_('No Invoice Lines!'), _('Please create some invoice lines.'))
            if inv.vatinfo_move_id:
                continue

            ctx = context.copy()
            ctx.update({'lang': inv.partner_id.lang})
            # one move line per invoice line
            iml = self.pool.get('account.invoice.line').vatinfo_move_line_get(cr, uid, inv.id, context=ctx)

            date = time.strftime('%Y-%m-%d')
            part = self.pool.get("res.partner")._find_accounting_partner(inv.partner_id)
            line = map(lambda x: (0, 0, self.line_get_convert(cr, uid, x, part.id, date, context=ctx)), iml)
            line = self.group_lines(cr, uid, iml, line, inv)

            journal_id = inv.journal_id.id
            journal = journal_obj.browse(cr, uid, journal_id, context=ctx)
            if journal.centralisation:
                raise osv.except_osv(_('User Error!'),
                        _('You cannot create an invoice on a centralized journal. Uncheck the centralized counterpart box in the related journal from the configuration menu.'))

            line = self.finalize_invoice_move_lines(cr, uid, inv, line)

            move = {
                'name': inv.number + '-VAT',
                'ref': inv.name,
                'line_id': line,
                'journal_id': journal_id,
                'date': date,
                'narration': inv.comment,
                'company_id': inv.company_id.id,
            }
            ctx.update(company_id=inv.company_id.id,
                       account_period_prefer_normal=True)
            period_ids = period_obj.find(cr, uid, date, context=ctx)
            period_id = period_ids and period_ids[0] or False
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id

            ctx.update(invoice=inv)
            move_id = move_obj.create(cr, uid, move, context=ctx)
            new_move_name = move_obj.browse(cr, uid, move_id, context=ctx).name
            # make the invoice point to that move
            self.write(cr, uid, [inv.id], {'vatinfo_move_id': move_id, 'period_id': period_id, 'move_name': new_move_name}, context=ctx)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move_obj.post(cr, uid, [move_id], context=ctx)
        self._log_event(cr, uid, ids)
        return True

    def unpost_vatinfo(self, cr, uid, ids, context=None):
        move_obj = self.pool.get('account.move')
        if context is None:
            context = {}
        for inv in self.browse(cr, uid, ids, context=context):
            move_id = inv.vatinfo_move_id.id
            move_obj.button_cancel(cr, uid, [move_id])
            self.write(cr, uid, [inv.id], {'vatinfo_move_id': False})
            move_obj.unlink(cr, uid, [move_id])
        self._log_event(cr, uid, ids)
        return True

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({'vatinfo_move_id': False})
        return super(account_invoice, self).copy(cr, uid, id, default, context=context)

account_invoice()


class account_invoice_line(osv.osv):

    _inherit = 'account.invoice.line'
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
            if vatinfo.invoice_id.vatinfo_move_id:
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

    def vatinfo_move_line_get(self, cr, uid, invoice_id, context=None):

        if context is None:
            context = {}

        res = []
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)

        for line in inv.invoice_line:
            # No additional vat info, continue
            if not line.vatinfo_tax_amount or line.vatinfo_tax_amount == 0:
                continue

            sign = 1
            account_id = 0
            if inv.type in ('out_invoice', 'in_invoice'):
                sign = 1
                account_id = line.vatinfo_tax_id.account_collected_id.id
            else:
                sign = -1
                account_id = line.vatinfo_tax_id.account_paid_id.id

            # Account Post, deduct from the Invoice Line.
            res.append({
                'type': 'src',
                'name': line.name.split('\n')[0][:64],
                'price_unit': -sign * line.vatinfo_tax_amount,
                'quantity': 1.0,
                'price': -sign * line.vatinfo_tax_amount,
                'account_id': line.account_id.id,
                'product_id': line.product_id.id,
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

account_invoice_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
