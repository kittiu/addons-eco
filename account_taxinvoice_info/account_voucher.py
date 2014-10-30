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


class account_voucher(osv.osv):

    _inherit = 'account.voucher'

    def _is_tax_adjustable(self, cr, uid, ids, name, args, context=None):
        # Tax is adjustable when they are non-withholding, non-suspended tax
        voucher = self.browse(cr, uid, ids[0], context=context)
        res = {voucher.id: False}
        for tax_line in voucher.tax_line:
            if not self._is_purchase_suspend_account(cr, uid, tax_line.account_id) \
                    and not self._is_wht_account(cr, uid, tax_line.account_id):
                res[voucher.id] = True
                break
        return res

    def _is_period_diff(self, cr, uid, ids, name, args, context=None):
        # Tax is adjustable when they are non-withholding, non-suspended tax
        voucher = self.browse(cr, uid, ids[0], context=context)
        res = {voucher.id: False}
        if voucher.period_id and voucher.rpt_period_id:  # Both has period assigned
            if voucher.period_id != voucher.rpt_period_id:
                res[voucher.id] = True
        return res

    _columns = {
        'is_tax_adjustable': fields.function(_is_tax_adjustable, string='Is Tax Adjustable?', type='boolean',),
        'adjust_taxinvoice_info': fields.boolean('Adjust Tax Invoice for VAT Report'),
        'taxinvoice_info_line': fields.one2many('account.voucher.taxinfo.line', 'voucher_id', 'Tax Invoice Info Lines', readonly=False),
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

    def _is_wht_account(self, cr, uid, account, context=None):
        # Check whether this account_id is being used in Withholding Tax
        cr.execute('select distinct account_collected_id from account_tax where is_wht=True and account_collected_id is not null')
        wht_accounts = map(lambda x: x[0], cr.fetchall())
        if account.id in wht_accounts:
            return True
        else:
            return False

    def onchange_adjust_taxinvoice_info(self, cr, uid, ids, adjust_taxinvoice_info, context=None):
        if not ids:
            return True
        res = {'value': {'rpt_period_id': False, 'taxinvoice_info_line': False}}
        taxinvoice_info = []
        if adjust_taxinvoice_info:
            voucher = self.browse(cr, uid, ids[0], context=context)
            for tax_line in voucher.tax_line:
                if not self._is_purchase_suspend_account(cr, uid, tax_line.account_id) \
                    and not self._is_wht_account(cr, uid, tax_line.account_id):
                    taxinvoice_info.append({'invoice_id': voucher.id,
                                            'taxinvoice_date': voucher.date,
                                            'taxinvoice_number': False,
                                            'taxinvoice_partner_id': voucher.partner_id.id,
                                            'taxinvoice_tin': voucher.partner_id.vat,
                                            'taxinvoice_branch': voucher.partner_id.branch,
                                            'taxinvoice_base': tax_line.base,
                                            'taxinvoice_amount': tax_line.amount})
            res['value']['rpt_period_id'] = voucher.period_id.id
            res['value']['taxinvoice_info_line'] = taxinvoice_info
        else:
            # Remove preiod and tax info table
            res_ids = self.pool.get('account.voucher.taxinfo.line').search(cr, uid, [('voucher_id', '=', ids[0])], context=context)
            self.pool.get('account.voucher.taxinfo.line').unlink(cr, uid, res_ids, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        # If rpt_period_id is updated when period has been closed, do not allow.
        res = super(account_voucher, self).write(cr, uid, ids, vals, context=context)
        for voucher in self.browse(cr, uid, ids, context=context):
            if voucher.rpt_period_id:
                period = self.pool.get('account.period').browse(cr, uid, voucher.rpt_period_id.id)
                if period.state == 'done':
                    raise osv.except_osv(_('Error!'), _("""The Tax Invoice Report Period %s has been closed.
                                                            If you insist to use it, please reopen the period first.""") % (period.name))
        return res

    def _create_adjust_taxinvoice_info(self, cr, uid, ids, context=None):
        taxinfo_obj = self.pool.get('account.voucher.taxinfo.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            # Remove preiod and tax info table
            res_ids = taxinfo_obj.search(cr, uid, [('voucher_id', '=', voucher.id)], context=context)
            taxinfo_obj.unlink(cr, uid, res_ids, context=context)
            self.write(cr, uid, [voucher.id], {'rpt_period_id': False,
                                               'adjust_taxinvoice_info': False})
            if voucher.is_tax_adjustable:
                for tax_line in voucher.tax_line:
                    if not self._is_purchase_suspend_account(cr, uid, tax_line.account_id) \
                            and not self._is_wht_account(cr, uid, tax_line.account_id):
                        taxinvoice_info = {'voucher_id': voucher.id,
                                            'taxinvoice_date': voucher.date,
                                            'taxinvoice_number': False,
                                            'taxinvoice_partner_id': voucher.partner_id.id,
                                            'taxinvoice_tin': voucher.partner_id.vat,
                                            'taxinvoice_branch': voucher.partner_id.branch,
                                            'taxinvoice_base': tax_line.base,
                                            'taxinvoice_amount': tax_line.amount}
                        taxinfo_obj.create(cr, uid, taxinvoice_info, context=context)
                self.write(cr, uid, [voucher.id], {'rpt_period_id': voucher.period_id.id,
                                                   'adjust_taxinvoice_info': True})
        return True

    def action_move_line_create(self, cr, uid, ids, context=None):
        res = super(account_voucher, self).action_move_line_create(cr, uid, ids, context=context)
        # After create move line (or posted), call onchange
        self._create_adjust_taxinvoice_info(cr, uid, ids, context=context)
        return res

    def action_cancel_draft(self, cr, uid, ids, context=None):
        res = super(account_voucher, self).action_cancel_draft(cr, uid, ids, context=context)
        taxinfo_obj = self.pool.get('account.voucher.taxinfo.line')
        for voucher in self.browse(cr, uid, ids, context=context):
            # Remove preiod and tax info table
            res_ids = taxinfo_obj.search(cr, uid, [('voucher_id', '=', voucher.id)], context=context)
            taxinfo_obj.unlink(cr, uid, res_ids, context=context)
            self.write(cr, uid, [voucher.id], {'rpt_period_id': False,
                                               'adjust_taxinvoice_info': False})
        return res

account_voucher()


class account_voucher_taxinfo_line(osv.osv):

    _name = 'account.voucher.taxinfo.line'
    _description = "Tax Invoice Info Line"
    _columns = {
        'voucher_id': fields.many2one('account.voucher', 'Payment', required=True),
        'taxinvoice_date': fields.date('Date', help='Tax Invoice Date', required=True),
        'taxinvoice_number': fields.char('Number', size=64, help='Number Tax Invoice', required=False),
        'taxinvoice_partner_id': fields.many2one('res.partner', 'Supplier', required=True),
        'taxinvoice_tin': fields.char('Tax ID', required=False, size=64),
        'taxinvoice_branch': fields.char('Branch', required=False, size=64),
        'taxinvoice_base': fields.float('Base', digits_compute=dp.get_precision('Account'), required=True),
        'taxinvoice_amount': fields.float('Amount', digits_compute=dp.get_precision('Account'), required=True),
    }

account_voucher_taxinfo_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
