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
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv
from openerp.tools.translate import _


class account_invoice(osv.osv):

    _inherit = 'account.invoice'

    def _is_tax_adjustable(self, cr, uid, ids, name, args, context=None):
        # Tax is adjustable when they are non-withholding, non-suspended tax
        invoice = self.browse(cr, uid, ids[0], context=context)
        res = {invoice.id: False}
        for tax_line in invoice.tax_line:
            if not self._is_purchase_suspend_account(cr, uid, tax_line.account_id) \
                and not tax_line.is_wht:
                res[invoice.id] = True
                break
        return res

    def _is_period_diff(self, cr, uid, ids, name, args, context=None):
        # Tax is adjustable when they are non-withholding, non-suspended tax
        invoice = self.browse(cr, uid, ids[0], context=context)
        res = {invoice.id: False}
        if invoice.period_id and invoice.rpt_period_id:  # Both has period assigned
            if invoice.period_id != invoice.rpt_period_id:
                res[invoice.id] = True
        return res

    _columns = {
        'is_tax_adjustable': fields.function(_is_tax_adjustable, string='Is Tax Adjustable?', type='boolean',),
        'adjust_taxinvoice_info': fields.boolean('Adjust Tax Invoice for VAT Report'),
        'taxinvoice_info_line': fields.one2many('account.invoice.taxinfo.line', 'invoice_id', 'Tax Invoice Info Lines', readonly=False),
        'rpt_period_id': fields.many2one('account.period', 'Report Period', required=False),
        'is_period_diff': fields.function(_is_period_diff, string='Is Period Diff?', type='boolean',),
    }
    _defaults = {
        'adjust_taxinvoice_info': False
    }

    def _is_purchase_suspend_account(self, cr, uid, account, context=None):
        # Check whether this account_id is being used in Tax as Suspended Tax account
        cr.execute('select distinct account_suspend_collected_id from account_tax where account_suspend_collected_id is not null')
        suspend_tax_accounts = map(lambda x: x[0], cr.fetchall())
        cr.execute('select distinct account_collected_id from account_tax where account_collected_id is not null')
        tax_accounts = map(lambda x: x[0], cr.fetchall())
        if account.id in suspend_tax_accounts and account.id in tax_accounts:
            raise osv.except_osv(_('Error!'), _('%s is used as both Suspended and Non-Suspended Tax Account') % (account.name))
        if account.id in suspend_tax_accounts:
            return True
        else:
            return False

    def onchange_adjust_taxinvoice_info(self, cr, uid, ids, adjust_taxinvoice_info, context=None):
        res = {'value': {'rpt_period_id': False, 'taxinvoice_info_line': False}}
        taxinvoice_info = []
        if adjust_taxinvoice_info:
            invoice = self.browse(cr, uid, ids[0], context=context)
            for tax_line in invoice.tax_line:
                if not self._is_purchase_suspend_account(cr, uid, tax_line.account_id) \
                    and not tax_line.is_wht:
                    taxinvoice_info.append({'invoice_id': invoice.id,
                                            'taxinvoice_date': invoice.date_invoice,
                                            'taxinvoice_number': invoice.supplier_invoice_number,
                                            'taxinvoice_partner_id': invoice.partner_id.id,
                                            'taxinvoice_tin': invoice.partner_id.vat,
                                            'taxinvoice_branch': invoice.partner_id.branch,
                                            'taxinvoice_base': tax_line.base,
                                            'taxinvoice_amount': tax_line.amount})
            res['value']['rpt_period_id'] = invoice.period_id.id
            res['value']['taxinvoice_info_line'] = taxinvoice_info
        else:
            # Remove preiod and tax info table
            res_ids = self.pool.get('account.invoice.taxinfo.line').search(cr, uid, [('invoice_id', '=', ids[0])], context=context)
            self.pool.get('account.invoice.taxinfo.line').unlink(cr, uid, res_ids, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        # If rpt_period_id is updated when period has been closed, do not allow.
        res = super(account_invoice, self).write(cr, uid, ids, vals, context=context)
        for invoice in self.browse(cr, uid, ids, context=context):
            if invoice.rpt_period_id:
                period = self.pool.get('account.period').browse(cr, uid, invoice.rpt_period_id.id)
                if period.state == 'done':
                    raise osv.except_osv(_('Error!'), _("""The Tax Invoice Report Period %s has been closed.
                                                            If you insist to use it, please reopen the period first.""") % (period.name))
        return res

account_invoice()


class account_invoice_taxinfo_line(osv.osv):

    _name = 'account.invoice.taxinfo.line'
    _description = "Tax Invoice Info Line"
    _columns = {
        'invoice_id': fields.many2one('account.invoice', 'Invoice', required=True),
        'taxinvoice_date': fields.date('Date', help='Tax Invoice Date', required=True),
        'taxinvoice_number': fields.char('Number', size=64, help='Number Tax Invoice', required=True),
        'taxinvoice_partner_id': fields.many2one('res.partner', 'Supplier', required=True),
        'taxinvoice_tin': fields.char('Tax ID', required=False, size=64),
        'taxinvoice_branch': fields.char('Branch', required=False, size=64),
        'taxinvoice_base': fields.float('Base', digits_compute=dp.get_precision('Account'), required=True),
        'taxinvoice_amount': fields.float('Amount', digits_compute=dp.get_precision('Account'), required=True),
    }

account_invoice_taxinfo_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
