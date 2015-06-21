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

from openerp.osv import fields, osv
from openerp.tools.translate import _
import time

class account_invoice(osv.osv):
       
    _inherit = 'account.invoice'
    
    def switch_dr_cr(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        account_move = self.pool.get('account.move')
        invoices = self.read(cr, uid, ids, ['move_id'])
        for i in invoices:
            if i['move_id']:
                moves = account_move.browse(cr, uid, i['move_id'][0])
                for line in moves.line_id:
                    cr.execute('UPDATE account_move_line SET credit=%s, debit=%s ' \
                                'WHERE id=%s ',
                                (line.debit, line.credit, line.id))
                    
    def reconcile_voided_documents(self, cr, uid, doc_name, context=None):
        account_move_line_obj = self.pool.get('account.move.line')
        period_obj = self.pool.get('account.period')
        period_id = False
        journal_id= False
        account_id = False

        if context is None:
            context = {}

        date = time.strftime('%Y-%m-%d')
        ids = period_obj.find(cr, uid, dt=date, context=context)
        if ids:
            period_id = ids[0]
            
        # Getting move_line_ids of the voided documents.
        cr.execute('select aml.id from account_move_line aml \
                        join account_account aa on aa.id = aml.account_id \
                        where aa.reconcile = true and aml.reconcile_id is null \
                        and aml.move_id in (select id from account_move where name like %s)',(doc_name+'%',))
        move_line_ids = map(lambda x: x[0], cr.fetchall())
        account_move_line_obj.reconcile(cr, uid, move_line_ids, 'manual', account_id,
                                        period_id, journal_id, context=context)
        return True

    # kittiu: Overwriting account.account_invoice.action_cancel()
    def action_cancel(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        invoices = self.read(cr, uid, ids, ['move_id', 'payment_ids', 'id', 'internal_number', 'origin'])
        move_ids = [] # ones that we will need to remove
        for i in invoices:
            if i['move_id']:
                move_ids.append(i['move_id'][0])
            if i['payment_ids']:
                account_move_line_obj = self.pool.get('account.move.line')
                pay_ids = account_move_line_obj.browse(cr, uid, i['payment_ids'])
                for move_line in pay_ids:
                    if move_line.reconcile_partial_id and move_line.reconcile_partial_id.line_partial_ids:
                        raise osv.except_osv(_('Error!'), _('You cannot cancel an invoice which is partially paid. You need to unreconcile related payment entries first.'))

        # First, set the invoices as cancelled but NOT detach the move_id
        self.write(cr, uid, ids, {'state':'cancel'})
        
        # Second, 
        # - Create counter document _VOID, by copy the existing one.
        # - Validate it to create journal entry, but switch credit <-> debit.
        # - Set _VOID document state to cancel.
        new_ids = []
        for i in invoices: # For each cancel invoice with internal_number
            if i['internal_number']:
                new_id = self.copy(cr, uid, i['id'], context=context)
                self.write(cr, uid, [new_id], {'internal_number':i['internal_number'] + '_VOID'})
                new_ids.append(new_id)
                
        # Validate by replicatong workflow step act_open
        if len(new_ids) > 0:
            self.action_date_assign(cr, uid, new_ids)
            self.action_move_create(cr, uid, new_ids)    
            self.action_number(cr, uid, new_ids)    
            self.invoice_validate(cr, uid, new_ids)
            # Marked as cancelled
            self.switch_dr_cr(cr, uid, new_ids)
            self.write(cr, uid, new_ids, {'state':'cancel'})
            
        # Full reconciled the voided documents
        for i in invoices:
            if i['internal_number']:
                self.reconcile_voided_documents(cr, uid, i['internal_number'])
            
        self._log_event(cr, uid, ids, -1.0, 'Cancel Invoice')
        self._log_event(cr, uid, new_ids, -1.0, 'Counter Cancel Invoice')
        
        # For invoice from DO, reset invoice_state to 2binvoiced
        picking_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        for i in invoices:
            picking_ids = picking_obj.search(cr, uid, [('name', '=', i['origin'])])
            if picking_ids:
                move_ids = move_obj.search(cr, uid, [('picking_id', 'in', picking_ids)])
                picking_obj.write(cr, uid, picking_ids, {'invoice_state': '2binvoiced'})
                move_obj.write(cr, uid, move_ids, {'invoice_state': '2binvoiced'})
        
        return True
    
    
    # go from canceled state to draft state
    # kittiu: case merged invoice, ensure that they are recreated again.
    # But for NSTDA, we do not allow set to draft at all.
#     def action_cancel_draft(self, cr, uid, ids, *args):
#         
#         picking_obj = self.pool.get('stock.picking')
#         invoice_ids = []
#         # If the canceled invoice was merged and created from DOs, unlink this and re-create them.
#         for invoice in self.browse(cr, uid, ids):
#             context = {}
#             context['date_inv'] = invoice.date_invoice
#             context['inv_type'] = 'out_invoice'
#             do_numbers = invoice.origin and invoice.origin.replace(' ','').replace(':',',').split(',')
#             # In case with DO reference,
#             if do_numbers and len(do_numbers) > 0:
#                 do_ids = picking_obj.search(cr, uid, [('name','in', do_numbers)])
#                 picking_obj.write(cr, uid, do_ids, {'invoice_state':'2binvoiced'})
#                 res = picking_obj.action_invoice_create(cr, uid, do_ids, 
#                                                       journal_id = invoice.journal_id.id, 
#                                                       group = False, 
#                                                       type = context['inv_type'],
#                                                       context=context)
#                 # Successful creating new invoices, drop existing invoices
#                 if len(res) > 0:
#                     invoice_ids += res.values()
#             # No DO reference, just copy new invoice.
#             else:
#                 new_id = self.copy(cr, uid, invoice.id, context=context)
#                 invoice_ids = [new_id] 
#                 
#         if len(invoice_ids) > 0:
#             data_pool = self.pool.get('ir.model.data')
#             action_model = False
#             action = {}
#             action_model,action_id = data_pool.get_object_reference(cr, uid, 'account', "action_invoice_tree1")
#             if action_model:
#                 action_pool = self.pool.get(action_model)
#                 action = action_pool.read(cr, uid, action_id, context=context)
#                 action['domain'] = "[('id','in', ["+','.join(map(str,invoice_ids))+"])]"
#             return action
#                     
#         return True
    
account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
