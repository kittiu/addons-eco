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
from openerp.osv import  osv
from openerp.tools.translate import _
    

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    
    def multi_invoice_to_receipt(self, cr, uid, ids, context=None):
        self.proforma_voucher(cr, uid, ids, context)
        return {'type': 'ir.actions.act_window_close'}
        
    
    #Overriding 
    def recompute_voucher_lines(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        res = super(account_voucher, self).recompute_voucher_lines(cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context)
        
        if not context.get('active_ids',False):
            return res

        data_inv = self.pool.get('account.invoice').read(cr, uid, context['active_ids'], ['state','number'], context=context)        
        number_invs = [data['number'] for data in data_inv]
        
        
        rec_count= len(res['value']['line_cr_ids'])
        i=0
        #Compare Selected invoice(s) with invoice(s) in system if invoice are difference will delete invoice in system
        while i<rec_count:
            record = res['value']['line_cr_ids'][i]
            if record['name'] not in number_invs:
                del res['value']['line_cr_ids'][i]
                rec_count= len(res['value']['line_cr_ids'])
            else:                   
                i+=1            
        
        rec_count= len(res['value']['line_dr_ids'])
        i=0
        #Compare Selected invoice(s) with invoice(s) in system if invoice are difference will delete invoice in system
        while i<rec_count:
            record = res['value']['line_dr_ids'][i]
            if record['name'] not in number_invs:
                del res['value']['line_dr_ids'][i]
                rec_count= len(res['value']['line_dr_ids'])
            else:                   
                i+=1            
                
        return res
    
#     #Overriding 
#     def default_get(self,cr, uid, fields, context=None):
#         
#         res = super(account_voucher, self).default_get(cr, uid, fields, context)   
#          
#         if not context.get('create_payment',False): #It's not have selected invoice(s)
#             return res
#          
#         data_inv = self.pool.get('account.invoice').read(cr, uid, context['active_ids'], ['state','partner_id','amount_total'], context=context)  
#         
#         #Sum total paid in selected invoice(s)
#         res['amount'] = sum(data['amount_total'] for data in data_inv)
#              
#         #Distinct customer
#         data_inv=set([data['partner_id'] for data in data_inv])
#         
#         lv = list(data_inv) 
#         if len(lv)<>1:#Customer are difference
#             return res
# #         
# #         res['type']='receipt'
# #         res['partner_id'] = lv[0][0]
#         return res
    
             
account_voucher()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
