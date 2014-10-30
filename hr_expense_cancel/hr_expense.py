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
from openerp import netsvc

class hr_expense_expense(osv.osv):
    
    _inherit = 'hr.expense.expense'
    
    def _compute_lines(self, cr, uid, ids, name, args, context=None):
        result = {}
        for expense in self.browse(cr, uid, ids, context=context):
            src = []
            lines = []
            if expense.account_move_id:
                for m in expense.account_move_id.line_id:
                    temp_lines = []
                    if m.reconcile_id:
                        temp_lines = map(lambda x: x.id, m.reconcile_id.line_id)
                    elif m.reconcile_partial_id:
                        temp_lines = map(lambda x: x.id, m.reconcile_partial_id.line_partial_ids)
                    lines += [x for x in temp_lines if x not in lines]
                    src.append(m.id)

            lines = filter(lambda x: x not in src, lines)
            result[expense.id] = lines
        return result
    
    _columns = {
        'payment_ids': fields.function(_compute_lines, relation='account.move.line', type="many2many", string='Payments'),
    }
    
    def expense_canceled(self, cr, uid, ids, context=None):     
        if context is None:
            context = {}
        account_move_obj = self.pool.get('account.move')
        expenses = self.read(cr, uid, ids, ['account_move_id', 'payment_ids'])
        move_ids = [] # ones that we will need to remove
        for expense in expenses:
            if expense['account_move_id']:
                move_ids.append(expense['account_move_id'][0])
            if expense['payment_ids']:
                account_move_line_obj = self.pool.get('account.move.line')
                pay_ids = account_move_line_obj.browse(cr, uid, expense['payment_ids'])
                for move_line in pay_ids:
                    if move_line.reconcile_partial_id and move_line.reconcile_partial_id.line_partial_ids:
                        raise osv.except_osv(_('Error!'), _('You cannot cancel an expense which is partially paid. You need to unreconcile related payment entries first.'))

        # First, detach the move ids
        self.write(cr, uid, ids, {'move_id':False})
        if move_ids:
            # second, invalidate the move(s)
            account_move_obj.button_cancel(cr, uid, move_ids, context=context)
            # delete the move this invoice was pointing to
            # Note that the corresponding move_lines and move_reconciles
            # will be automatically deleted too
            account_move_obj.unlink(cr, uid, move_ids, context=context)

        # Call super method.
        res = super(hr_expense_expense, self).expense_canceled(cr, uid, ids, context=context)
        return res
    
hr_expense_expense()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
