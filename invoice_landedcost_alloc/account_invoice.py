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
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv
from openerp.tools.translate import _


class account_invoice(osv.osv):

    def _is_landedcost_alloc(self, cr, uid, ids, fieldnames, args, context=None):
        result = dict.fromkeys(ids, 0)
        for record in self.browse(cr, uid, ids, context=context):
            # If any line has vatinfo_tax_amount
            for line in record.landedcost_alloc_ids:
                if line.landedcost_amount_alloc:
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
        'landedcost_alloc_move_id': fields.many2one('account.move', 'Journal Entry (Landed Cost)', readonly=True, select=1, ondelete='restrict', help="Link to the automatically generated Journal Items for Landed Cost Allocation."),
        'landedcost_alloc_move_date': fields.related('landedcost_alloc_move_id', 'date', type="date", string="Journal Date (Landed Cost)", readonly=True),
        'force_landedcost_alloc_date': fields.date('Force Date'),
        'landedcost_alloc_ids': fields.one2many('account.invoice.landedcost.alloc', 'invoice_id', 'Landed Cost Lines'),
        'is_landedcost_alloc': fields.function(_is_landedcost_alloc, type='boolean', string='Landed Cost Allocated',
                    store={
                           'account.invoice': (lambda self, cr, uid, ids, c={}: ids, None, 10),
                           'account.invoice.line': (_get_invoice, ['landedcost_amount_alloc'], 10)
                           }),
    }

    def post_landedcost(self, cr, uid, ids, context=None):
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
            if inv.landedcost_alloc_move_id:
                continue

            ctx = context.copy()
            ctx.update({'lang': inv.partner_id.lang})
            # one move line per invoice line
            iml = self.pool.get('account.invoice.landedcost.alloc').landedcost_move_line_get(cr, uid, inv.id, context=ctx)

            date = inv.force_landedcost_alloc_date or time.strftime('%Y-%m-%d')
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
                'name': inv.number + '-LC',
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
            self.write(cr, uid, [inv.id], {'landedcost_alloc_move_id': move_id, 'period_id': period_id, 'move_name': new_move_name}, context=ctx)
            # Pass invoice in context in method post: used if you want to get the same
            # account move reference when creating the same invoice after a cancelled one:
            move_obj.post(cr, uid, [move_id], context=ctx)
        self._log_event(cr, uid, ids)
        return True

    def unpost_landedcost(self, cr, uid, ids, context=None):
        move_obj = self.pool.get('account.move')
        if context is None:
            context = {}
        for inv in self.browse(cr, uid, ids, context=context):
            move_id = inv.landedcost_alloc_move_id.id
            move_obj.button_cancel(cr, uid, [move_id])
            self.write(cr, uid, [inv.id], {'landedcost_alloc_move_id': False})
            move_obj.unlink(cr, uid, [move_id])
        self._log_event(cr, uid, ids)
        return True

    def copy(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
        default.update({'landedcost_alloc_move_id': False})
        return super(account_invoice, self).copy(cr, uid, id, default, context=context)

    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None, description=None, journal_id=None, context=None):
        invoice_data = super(account_invoice, self)._prepare_refund(cr, uid, invoice, date=date, period_id=period_id, description=description, journal_id=journal_id, context=context)
        landedcost_alloc_line = self._refund_cleanup_lines(cr, uid, invoice.landedcost_alloc_ids, context=context)
        invoice_data.update({'landedcost_alloc_ids': landedcost_alloc_line})
        return invoice_data

account_invoice()


class account_invoice_landedcost_alloc(osv.osv):

    _name = 'account.invoice.landedcost.alloc'
    _description = 'Invoice Landed Cost Allocation'

    _columns = {
        'invoice_id': fields.many2one('account.invoice', 'Invoice', ondelete="cascade"),
        'supplier_invoice_id': fields.many2one('account.invoice', 'Supplier Invoice', domain="[('type', '=', 'in_invoice'), ('id', '!=', parent.id), ('state', 'not in', ['draft', 'cancel'])]", ondelete="restrict", required=True, help="Supplier Invoice, in which this invoice is paying for its landed cost"),
        'landedcost_account_id': fields.many2one('account.account', 'Landed Cost Account', required=True, domain=[('type', '!=', 'view')]),
        'landedcost_amount_alloc': fields.float('Allocation', required=True, digits_compute=dp.get_precision('Account')),
    }

    def onchange_supplier_invoice_id(self, cr, uid, ids, invoice_id, supplier_invoice_id, context=None):
        res = {'value': {'landedcost_account_id': False}}
        invoice_obj = self.pool.get('account.invoice')
        if invoice_id:
            invoice = invoice_obj.browse(cr, uid, invoice_id, context=context)
            # Only if all Account of this invoice lines is the same, use this account code, otherwise, user will manually select
            account_ids = list(set([x.account_id.id for x in invoice.invoice_line]))  # Get unique value
            if len(account_ids) == 1:
                res['value']['landedcost_account_id'] = account_ids[0]
        return res

    def landedcost_move_line_get(self, cr, uid, invoice_id, context=None):

        if context is None:
            context = {}
            
        cur_obj = self.pool.get('res.currency')
        ctx = context.copy()

        res = []
        inv = self.pool.get('account.invoice').browse(cr, uid, invoice_id, context=context)
        
        company_currency = self.pool['res.company'].browse(cr, uid, inv.company_id.id).currency_id.id
        ctx.update({'date': inv.date_invoice})
        ctx.update({'pricelist_type': 'purchase'})
        diff_currency_p = inv.currency_id.id <> company_currency

        for line in inv.landedcost_alloc_ids:
            # No amount allocation, continue
            if not line.landedcost_amount_alloc or line.landedcost_amount_alloc == 0:
                continue

            if inv.currency_id.id != company_currency:
                amount_company_currency = cur_obj.compute(cr, uid, inv.currency_id.id, company_currency, line.landedcost_amount_alloc, context=ctx)
            else:
                amount_company_currency = line.landedcost_amount_alloc

            sign = 1
            account_id = line.landedcost_account_id.id
            if inv.type in ('out_invoice', 'in_invoice'):
                sign = -1
            else:
                sign = 1

            # Dr
            res.append({
                'type': 'src',
                'name': line.supplier_invoice_id.internal_number,
                'price_unit': -sign * amount_company_currency,
                'quantity': 1.0,
                'price': -sign * amount_company_currency,
                'account_id': account_id,
                'product_id': False,
                'uos_id': False,
                'account_analytic_id': False,
                'taxes': False,
                'amount_currency': diff_currency_p \
                        and line.landedcost_amount_alloc or False,
                'currency_id': diff_currency_p \
                        and inv.currency_id.id or False,
            })

            # Account Post, Tax
            res.append({
                'type': 'dest',
                'name': line.invoice_id.internal_number,
                'price_unit': sign * amount_company_currency,
                'quantity': 1,
                'price': sign * amount_company_currency,
                'account_id': account_id,
                'product_id': False,
                'uos_id': False,
                'account_analytic_id': False,
                'taxes': False,
                'amount_currency': diff_currency_p \
                        and line.landedcost_amount_alloc or False,
                'currency_id': diff_currency_p \
                        and inv.currency_id.id or False,
            })

        return res

account_invoice_landedcost_alloc()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
