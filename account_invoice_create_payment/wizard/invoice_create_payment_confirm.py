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
from openerp.osv import  osv,fields
from openerp.tools.translate import _
class invoice_create_payment_confirm(osv.osv_memory):   
    _name = 'invoice.create.payment.confirm' 
    _description = 'Create draft payment' 
    _columns = { 
                'date_due': fields.date('Due Date'),
                'group_flag': fields.boolean("Grouping")
                } 
    _default={'group_flag':False}
    
    def _invalid_invoice(self, cr, uid, ids, context=None):
        if not context:
            context ={}
             
        if not context.get('create_payment',False):#It's not have selected invoice(s)
            return False
         
        #  1.Validate  status are open 
        data_inv = self.pool.get('account.invoice').read(cr, uid, context['active_ids'], ['state','partner_id','amount_total'], context=context)   
        for record in data_inv:
            if record['state'] not in ('open'):
#                 return self.pool.get('warning').error(cr, uid, title='Create Payment', message="The status in selected invoice(s) must be open only",context=context)
                raise osv.except_osv(_('Warning!'), _("The status in selected invoice(s) must be open only"))
# 
#         # 2.Validate selected invoice(s) are customer difference
#         data_inv=set([data['partner_id'] for data in data_inv])
#         lv = list(data_inv)
#         if len(lv)<>1:#Customer are difference
# #             return self.pool.get('warning').error(cr, uid, title='Create Payment', message="Selected invoice(s) cannot be customer difference",context=context)
#             raise osv.except_osv(_('Warning!'), _("Selected invoice(s) cannot be customer difference"))
#         
        return False
    def _partner_list(self, cr, uid, ids, context=None):
        data_inv = self.pool.get('account.invoice').read(cr, uid, context['active_ids'], ['partner_id'], context=context)
        data_inv=set([data['partner_id'][0] for data in data_inv])
        lv = list(data_inv)
        return lv
    
    def _lists_fields_voucher(self,cr, uid, ids, context=None):
        return ['comment', 'message_follower_ids', 'line_cr_ids', 'is_multi_currency', 'reference', 'line_dr_ids', 
                 'number', 'company_id', 'currency_id', 'narration', 'message_ids', 'payment_rate_currency_id', 
                 'paid_amount_in_company_currency', 'partner_id', 'writeoff_acc_id', 'tax_line', 'move_ids', 'state', 
                 'pre_line', 'type', 'payment_option', 'account_id', 'currency_help_label', 'is_paydetail_created', 
                 'period_id', 'billing_id', 'date', 'audit', 'payment_rate', 'name', 'writeoff_amount', 'analytic_id', 
                 'journal_id', 'amount', 'amount_total', 'payment_details']
    
    def _pre_create_voucher(self, cr, uid, ids, partner_id,inv_ids,due_date, context=None):
        obj_voucher = self.pool.get('account.voucher')
        obj_invoice = self.pool.get('account.invoice') 
        part_obj = self.pool.get("res.partner")
        
        lfields = self._lists_fields_voucher(cr, uid, ids, context)
        data_voucher =  obj_voucher.default_get(cr, uid, lfields, context )
        data_voucher['partner_id']=partner_id
         
        data_voucher['amount']=0.0
        data_voucher['date'] = due_date
       
        
        inv_ids = obj_invoice.search(cr, uid, [('id','in',inv_ids),('partner_id','=',partner_id)],)
        data_inv = obj_invoice.read(cr, uid, inv_ids, ['type'], context=context)    
#         data_voucher['amount']= sum(data['amount_total'] for data in data_inv)
        ttype=set([data['type'] for data in data_inv])
        
        lv = list(ttype) 
        if len(lv)<>1:#Customer are difference
            raise osv.except_osv(_('Warning!'), _("The selected invoice(s) type be difference"))
        if 'out_invoice' in lv:
            data_voucher['type']='receipt'
        else:
            data_voucher['type']='payment'
       
        #Get parent of partner    
        part = part_obj.browse(cr, uid, partner_id, context=context)
        partner_id = part_obj._find_accounting_partner(part).id    
        data_voucher['partner_id']=partner_id
        
        res = obj_voucher.onchange_partner_id(cr, uid, ids, partner_id, data_voucher['journal_id'], data_voucher['amount'], data_voucher['currency_id'], data_voucher['type'], data_voucher['date'], context)
        
        return data_voucher,res
        
    def _create_group_payment(self, cr, uid, ids, partner_id, inv_ids,due_date, context=None):
        obj_voucher = self.pool.get('account.voucher')       
        obj_voucher_line =self.pool.get('account.voucher.line')
        
        voucher_ids=[]
        #initial data before create voucher
        data_voucher,res = self._pre_create_voucher(cr, uid, ids, partner_id, inv_ids,due_date, context)
        
        #Create voucher from credit account_move_line      
        if len(res['value']['line_cr_ids'])>0:
            record =res['value']['line_cr_ids'][0]
            data_voucher['account_id']=res['value']['account_id']
            data_voucher['payment_rate_currency_id']=res['value']['payment_rate_currency_id']
            
            #Create voucher
            voucher_id = obj_voucher.create(cr, uid, data_voucher, context)
            
            #Create line voucher
            for record in res['value']['line_cr_ids']:
                tmp = record.copy()
                tmp.update({'voucher_id':voucher_id})
                obj_voucher_line.create(cr, uid, tmp, context)
                voucher_ids.append(voucher_id)         
                
        #Create voucher from debit account_move_line          
        if len(res['value']['line_dr_ids'])>0:
            record =res['value']['line_dr_ids'][0]
            data_voucher['account_id']=res['value']['account_id']
            data_voucher['payment_rate_currency_id']=res['value']['payment_rate_currency_id']
            #Create voucher
            voucher_id = obj_voucher.create(cr, uid, data_voucher, context)
            
            #Create line voucher
            for record in res['value']['line_dr_ids']:
                tmp = record.copy()
                tmp.update({'voucher_id':voucher_id})
                obj_voucher_line.create(cr, uid, tmp, context)
                voucher_ids.append(voucher_id)                 
                   
        return voucher_ids,data_voucher['type']
    
    def _create_single_payment(self, cr, uid, ids, partner_id,inv_ids,due_date, context=None):
        
        
        obj_voucher = self.pool.get('account.voucher')
        obj_voucher_line =self.pool.get('account.voucher.line')
     
        voucher_ids=[]
        
        #initial data before create voucher
        data_voucher,res = self._pre_create_voucher(cr, uid, ids, partner_id, inv_ids,due_date, context)
        
        #Create voucher from credit account_move_line
        if len(res['value']['line_cr_ids'])>0:                                    
            for record in res['value']['line_cr_ids']: 
                #Create voucher
                data_voucher['account_id']=res['value']['account_id']
                data_voucher['payment_rate_currency_id']=res['value']['payment_rate_currency_id']
                voucher_id = obj_voucher.create(cr, uid, data_voucher, context)
                
                #Create line voucher
                tmp = record.copy()
                tmp.update({'voucher_id':voucher_id})
                obj_voucher_line.create(cr, uid, tmp, context)
                voucher_ids.append(voucher_id)       
                     
        #Create voucher from debit account_move_line        
        if len(res['value']['line_dr_ids'])>0:                                    
            for record in res['value']['line_dr_ids']:
                data_voucher['account_id']=res['value']['account_id']
                data_voucher['payment_rate_currency_id']=res['value']['payment_rate_currency_id']
                #Create voucher
                voucher_id = obj_voucher.create(cr, uid, data_voucher, context)
                
                #Create line voucher
                tmp = record.copy()
                tmp.update({'voucher_id':voucher_id})
                obj_voucher_line.create(cr, uid, tmp, context)
                voucher_ids.append(voucher_id)
        return voucher_ids,data_voucher['type']
    
    
    def invoice_create_confirm(self, cr, uid, ids, context=None):
        """
        This wizard will create voucher the all the selected draft invoices
    """
        
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        
        valid = self._invalid_invoice(cr, uid, ids, context)
        voucher_ids=[]
        if (valid):
            return valid
        
        partner_ids = self._partner_list(cr, uid, ids, context)
        #for partner_id in partner_ids:
      
        data = self.read(cr, uid, ids, ['date_due','group_flag'], context)
        
        active_ids=context.get('active_ids',False)
        
        for record in data:
            for partner_id in partner_ids:#Create payment each partner
                due_date = record['date_due']
               
                if record['group_flag']:#Merge invoice by partner
                    voucher_id,ttype=self._create_group_payment(cr, uid, ids,partner_id, active_ids,due_date,context)
                    voucher_ids += voucher_id
                else:#s
                    voucher_id,ttype,=self._create_single_payment(cr, uid, ids,partner_id,active_ids,due_date,context)
                    voucher_ids += voucher_id
        
        if len(voucher_ids)<=0:#Error on create payment
            raise osv.except_osv(_('Warning!'), _("The selected invoice(s) not matching with system"))
        
        if ttype=='receipt':
            action_name = 'action_vendor_receipt'
        else:
            action_name ='action_vendor_payment'
        
        #Return is action view
        result = mod_obj.get_object_reference(cr, uid, 'account_voucher', action_name)
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        result['domain'] = "[('id','in', [" + ','.join(map(str, voucher_ids)) + "])]"
        result['context']={'create_payment':True,'active_ids':active_ids}
        return result
    
invoice_create_payment_confirm()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    