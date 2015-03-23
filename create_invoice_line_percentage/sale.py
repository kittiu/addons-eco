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
import inspect

class sale_order_line(osv.osv):
    
    _inherit = 'sale.order.line'
    
    # A complete overwrite method of sale_order_line
    def _fnct_line_invoiced(self, cr, uid, ids, field_name, args, context=None):
        res = dict.fromkeys(ids, False)
        uom_obj = self.pool.get('product.uom')
        for this in self.browse(cr, uid, ids, context=context):
            # kittiu, if product line, we need to calculate carefully
            if this.product_id and not this.product_uos: # TODO: uos case is not covered yet.
                args, v, k, d = inspect.getargspec(uom_obj._compute_qty)
                if 'round' in args:
                    oline_qty = uom_obj._compute_qty(cr, uid, this.product_uom.id, this.product_uom_qty, this.product_id.uom_id.id, round=False)
                else:
                    oline_qty = uom_obj._compute_qty(cr, uid, this.product_uom.id, this.product_uom_qty, this.product_id.uom_id.id)
                iline_qty = 0.0
                for iline in this.invoice_lines:
                    if iline.invoice_id.state != 'cancel':
                        if not this.product_uos: # Normal Case
                            if 'round' in args:
                                iline_qty += uom_obj._compute_qty(cr, uid, iline.uos_id.id, iline.quantity, iline.product_id.uom_id.id, round=False)
                            else:
                                iline_qty += uom_obj._compute_qty(cr, uid, iline.uos_id.id, iline.quantity, iline.product_id.uom_id.id)
                        else: # UOS case.
                            iline_qty += iline.quantity / (iline.product_id.uos_id and iline.product_id.uos_coeff or 1)                        
                # Test quantity
                res[this.id] = iline_qty >= oline_qty
            else:
                res[this.id] = this.invoice_lines and \
                all(iline.invoice_id.state != 'cancel' for iline in this.invoice_lines) 
        return res
    
    # A complete overwrite method. We need it here because it is called from a function field.
    def _order_lines_from_invoice(self, cr, uid, ids, context=None):
        # direct access to the m2m table is the less convoluted way to achieve this (and is ok ACL-wise)
        cr.execute("""SELECT DISTINCT sol.id FROM sale_order_invoice_rel rel JOIN
                                                  sale_order_line sol ON (sol.order_id = rel.order_id)
                                    WHERE rel.invoice_id = ANY(%s)""", (list(ids),))
        return [i[0] for i in cr.fetchall()]        
    
    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False, context=None):
        res = super(sale_order_line, self)._prepare_order_line_invoice_line(cr, uid, line, account_id=account_id, context=context)
        line_percent = context.get('line_percent', False)
        if line_percent:
            res.update({'quantity': (res.get('quantity') or 0.0) * (line_percent / 100)})
        return res
    
    _columns = {
        'invoiced': fields.function(_fnct_line_invoiced, string='Invoiced', type='boolean',
            store={
                'account.invoice': (_order_lines_from_invoice, ['state'], 10),
                'sale.order.line': (lambda self,cr,uid,ids,ctx=None: ids, ['invoice_lines'], 10)}),
    }
    
sale_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
