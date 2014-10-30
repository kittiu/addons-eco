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


class account_voucher(osv.osv):

    def _is_taxinv(self, cr, uid, ids, fieldnames, args, context=None):
        result = dict.fromkeys(ids, False)
        for record in self.browse(cr, uid, ids, context=context):
            # If account_voucher_tax table has non wht tax
            if len(record.voucher_taxinv):
                result[record.id] = True
        return result

    _inherit = 'account.voucher'

    _columns = {
        'is_taxinv': fields.function(_is_taxinv, type='boolean', string='Has Suspended Tax Invoice'),
        'voucher_taxinv': fields.one2many('account.voucher.taxinv', 'voucher_id', 'Voucher VAT Info'),
        'is_taxinv_publish': fields.boolean('Tax Invoice Published', help="If published, this information will be shown in Tax Report for the specified period"),
        'taxinv_period_id': fields.many2one('account.period', 'Tax Invoice Period', readonly=True),
        'is_basevat_invalid': fields.boolean('Base/Vat Invalid', help="Base amount or amount not equal to its accounting entry"),
    }

    def to_publish(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        is_basevat_invalid = False
        for voucher in self.browse(cr, uid, ids, context=context):
            # Check for base / tax amount
            if voucher.type == 'payment':
                avtax_obj = self.pool.get('account.voucher.tax')
                ctx.update({'is_taxinv': True})
                base_amount = tax_amount = base_amount2 = tax_amount2 = 0.0
                for tax in avtax_obj.compute(cr, uid, voucher.id, context=ctx).values():
                    base_amount += tax['base']
                    tax_amount += tax['amount']
                for taxinv in voucher.voucher_taxinv:
                    base_amount2 += taxinv.base_amount
                    tax_amount2 += taxinv.tax_amount
                if base_amount != base_amount2 or tax_amount != tax_amount2:
                    is_basevat_invalid = True
            # Period Check
            if not voucher.taxinv_period_id:
                raise osv.except_osv(_('Warning!'), _('Tax Invoice Period is not specified!'))
        return self.write(cr, uid, ids, {'is_taxinv_publish': True, 'is_basevat_invalid': is_basevat_invalid})

    def to_unpublish(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'is_taxinv_publish': False})

    def button_reset_taxinv(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        ctx = context.copy()
        avtax_obj = self.pool.get('account.voucher.tax')
        avtin_obj = self.pool.get('account.voucher.taxinv')
        for id in ids:
            voucher = self.browse(cr, uid, id, context=ctx)
            if voucher.type == 'payment':
                self.write(cr, uid, [id], {'taxinv_period_id': voucher.period_id and voucher.period_id.id or False})
                cr.execute("DELETE FROM account_voucher_taxinv WHERE voucher_id=%s ", (id,))
                ctx.update({'is_taxinv': True})
                for tax in avtax_obj.compute(cr, uid, id, context=ctx).values():
                    tax.update({'date': voucher.date})
                    avtin_obj.create(cr, uid, tax)
        return True

    def proforma_voucher(self, cr, uid, ids, context=None):
        super(account_voucher, self).proforma_voucher(cr, uid, ids, context=context)
        self.button_reset_taxinv(cr, uid, ids, context=context)
        return True

#     # For backward compatibility
#     def init(self, cr):
#         # Check where there are any existing records in account_voucher_taxinv
#         cr.execute("select count(*) from account_voucher_taxinv")
#         res = cr.fetchone()
#         if not res[0]:
#             cr.execute("select id from account_voucher where state in ('proforma', 'posted')")
#             voucher_ids = [x['id'] for x in cr.dictfetchall()]
#             self.button_reset_taxinv(cr, 1, voucher_ids)

account_voucher()


class account_voucher_taxinv(osv.osv):

    _name = 'account.voucher.taxinv'
    _description = 'Supplier Payment Tax Invoice'
    _columns = {
        'voucher_id': fields.many2one('account.voucher', 'Ref Voucher'),
        #  'invoice_id': fields.many2one('account.invoice', 'Supplier Invoice'),
        'account_id': fields.many2one('account.account', 'Account'),
        'date': fields.date('Date', help='This date will be used as Tax Invoice Date in VAT Report'),
        'number': fields.char('Number', size=64, help='Number Tax Invoice'),
        #  'partner_id': fields.many2one('res.partner', 'Supplier', size=128, readonly=True, help='Name of Organization to pay Tax'),
        'base_amount': fields.float('Base', digits_compute=dp.get_precision('Account')),
        'tax_id': fields.many2one('account.tax', 'Tax', domain=[('is_suspend_tax', '=', True), ('type_tax_use', '=', 'purchase')], required=True, readonly=False),
        'tax_amount': fields.float('VAT', digits_compute=dp.get_precision('Account')),
    }

#     def compute(self, cr, uid, voucher_id, context=None):
#         voucher = self.pool.get('account.voucher').browse(cr, uid, voucher_id, context=context)
#         advance_and_discount = {}
#         for voucher_line in voucher.line_ids:
#             invoice = voucher_line.move_line_id.invoice
#             if invoice:
#                 adv_disc_param = self.pool.get('account.voucher.line').get_adv_disc_param(cr, uid, invoice)
#                 # Add to dict
#                 advance_and_discount.update({invoice.id: adv_disc_param})
#         tax_grouped = self.pool.get('account.voucher.tax').compute_ex(cr, uid, voucher_id, advance_and_discount, context=context)
#         return tax_grouped

account_voucher_taxinv()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
