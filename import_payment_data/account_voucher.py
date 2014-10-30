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

import base64
from openerp.osv import fields, osv
from openerp.tools.translate import _
from openerp import netsvc
import openerp.addons.decimal_precision as dp

class account_voucher(osv.osv):

    _inherit = 'account.voucher'
    _columns = {
        'import_file': fields.binary('Import File (*.csv)', readonly=True, states={'draft':[('readonly',False)]}),
        'import_amount': fields.float('Import Amount', digits_compute=dp.get_precision('Account'), readonly=True, states={'draft':[('readonly',False)]}),
        'mismatch': fields.integer('Import Mismatched', readonly=True, states={'draft':[('readonly',False)]}),
        'mismatch_list': fields.char('Mismatch List', readonly=True, states={'draft':[('readonly',False)]}),
    }
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('import_amount', False):
            vals.update({'amount': vals['import_amount']})
        if vals.get('mismatch', False):
            vals.update({'mismatch': vals['mismatch']})
        if vals.get('mismatch_list', False):
            vals.update({'mismatch_list': vals['mismatch_list']})
        return super(account_voucher, self).create(cr, uid, vals, context=context)
        
    def write(self, cr, uid, ids, vals, context=None):
        if vals.get('import_amount', False):
            vals.update({'amount': vals['import_amount']})   
        if vals.get('mismatch', False):
            vals.update({'mismatch': vals['mismatch']})
        if vals.get('mismatch_list', False):
            vals.update({'mismatch_list': vals['mismatch_list']})
        return super(account_voucher, self).write(cr, uid, ids, vals, context=context)
        
    def onchange_import_file(self, cr, uid, ids, import_file, rate, partner_id, journal_id, currency_id, ttype, date, payment_rate_currency_id, company_id, context=None):
        # Prepare Import FIle Data
        if not import_file:
            res = {'value': {'import_amount': False, 'mismatch': False, 'mismatch_list': False}}
            return res
        
        # Read file
        file_list = base64.decodestring(import_file).split('\n')
        payment_lines = {}
        amount = 0.0
        for line in file_list:
            if line != '':
                data = line.split(',')
                payment_lines.update({data[0]: float(data[1])})
                amount += float(data[1])  

        if context is None:
            context = {}
        ctx = context.copy()
        ctx.update({'date': date})
        #read the voucher rate with the right date in the context
        currency_id = currency_id or self.pool.get('res.company').browse(cr, uid, company_id, context=ctx).currency_id.id
        voucher_rate = self.pool.get('res.currency').read(cr, uid, currency_id, ['rate'], context=ctx)['rate']
        ctx.update({
            'voucher_special_currency': payment_rate_currency_id,
            'voucher_special_currency_rate': rate * voucher_rate})
        res = self.recompute_voucher_lines_csv(cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, payment_lines, context=ctx)
        vals = self.onchange_rate(cr, uid, ids, rate, amount, currency_id, payment_rate_currency_id, company_id, context=ctx)
        for key in vals.keys():
            res[key].update(vals[key])     
            
        vals = {'value': {'import_amount': amount}}
        for key in vals.keys():
            res[key].update(vals[key])        
        
        return res
        
    # The original recompute_voucher_lines() do not aware of withholding and csv import file.
    # Here we will re-adjust it. As such, the amount allocation will be reduced and carry to the next lines.
    def recompute_voucher_lines_csv(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, payment_lines, context=None):
        res = super(account_voucher, self).recompute_voucher_lines(cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=context)
        line_cr_ids = res['value']['line_cr_ids']
        line_dr_ids = res['value']['line_dr_ids']
        lines = line_cr_ids + line_dr_ids
# 
#         # This part simply calculate the advance_and_discount variable
#         move_line_obj = self.pool.get('account.move.line')
#         advance_and_discount = {}
#         for line in lines:
#             move_line = move_line_obj.browse(cr, uid, line['move_line_id'])
#             invoice = move_line.invoice
#             if invoice:
#                 adv_disc_param = self.pool.get('account.voucher.line').get_adv_disc_param(cr, uid, invoice)
#                 # Add to dict
#                 advance_and_discount.update({invoice.id: adv_disc_param})
#         # End
#         
        # Match payment_lines with lines's move_line_id
        move_line_obj = self.pool.get('account.move.line')
        payment_lines, mismatch, mismatch_list = self.matched_payment_lines(payment_lines, lines)
        for line in lines:
            amount, amount_wht = 0.0, 0.0 
            if line['move_line_id'] in payment_lines:
                # Amount to reconcile, always positive value -> make abs(..)
                amount_alloc = abs(payment_lines[line['move_line_id']]) or 0.0
                # ** Only if amount_alloc > 0, Calculate withholding amount **
                if amount_alloc:
                    adv_disc_param = {}
                    move_line = move_line_obj.browse(cr, uid, line['move_line_id'])
                    invoice = move_line.invoice
                    if invoice:
                        adv_disc_param = self.pool.get('account.voucher.line').get_adv_disc_param(cr, uid, invoice)
                        # Test to get full wht first
                        original_amount, original_wht_amt = self.pool.get('account.voucher.line')._get_amount_wht(cr, uid, partner_id, line['move_line_id'], line['amount_original'], line['amount_original'], adv_disc_param, context=context)
                        amount, amount_wht = self._get_amount_wht_ex(cr, uid, partner_id, line['move_line_id'], line['amount_original'], original_wht_amt, amount_alloc, adv_disc_param, context=context)
            # Adjust remaining
            line['amount'] = amount+amount_wht
            line['amount_wht'] = -amount_wht
            line['reconcile'] = line['amount'] == line['amount_unreconciled']
            
        vals = {'value': {'mismatch': mismatch, 'mismatch_list': mismatch_list}}
        for key in vals.keys():
            res[key].update(vals[key])
             
        return res
    
    def matched_payment_lines(self, payment_lines, move_lines):
        new_payment_lines = {}
        mismatch = 0
        mismatch_list = False
        for key in payment_lines.keys():
            matched = False
            for move_line in move_lines:
                if key == move_line['name'] or key == move_line['reference']:
                    new_payment_lines.update({move_line['move_line_id']: payment_lines[key]})
                    matched = True
                    break
            if not matched:
                if not mismatch_list:
                    mismatch_list = key
                else:
                    mismatch_list = ('%s,%s') % (mismatch_list, key)
                mismatch += 1
        return new_payment_lines, mismatch, mismatch_list

account_voucher()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
