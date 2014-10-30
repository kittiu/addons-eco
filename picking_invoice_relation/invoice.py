# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2011 Tiny SPRL (<http://tiny.be>).
#    Copyright (C) 2011 Camptocamp (<http://www.camptocamp.com>).
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
import types

class account_invoice(osv.osv):
    _inherit = "account.invoice"

    # FIXME -this is not used, because info is in account_invoice.name
    def _client_order_refs(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        for inv in self.browse(cr, uid, ids, context):
            client_ref = '' 
            for ref in inv.sale_order_ids:
                if ref.client_order_ref:
                    if client_ref:
                        client_ref +='; '
                    client_ref += ref.client_order_ref
            result[inv.id] = client_ref
        return result

    _columns = {
        'picking_ids': fields.many2many('stock.picking', 'picking_invoice_rel', 'invoice_id', 'picking_id', 'Pickings' ),
        'sale_order_ids': fields.many2many('sale.order', 'sale_order_invoice_rel', 'invoice_id', 'order_id', 'Sale Orders', readonly=True, help="This is the list of sale orders linked to this invoice. "),
        'purchase_order_ids': fields.many2many('purchase.order', 'purchase_invoice_rel', 'invoice_id', 'purchase_id', 'Purchase Orders', readonly=True, help="This is the list of purchase orders linked to this invoice. "),
        'client_order_refs' : fields.function(_client_order_refs, method=True, string="Client Sale Orders Ref", type='char'),
        'invoice_id_ref': fields.many2one('account.invoice', 'Invoice Ref', readonly=True),
        'invoice_refund_refs': fields.one2many('account.invoice', 'invoice_id_ref', string="Refunded Invoice", readonly=True),
    }
    
    def copy(self, cr, uid, id, default=None, context=None):
        default = default or {}
        default.update({
            'invoice_id_ref': False,
            'picking_ids':[],
            'sale_order_ids':[],
            })
        return super(account_invoice, self).copy(cr, uid, id, default, context)

    def write(self, cr, uid, ids, vals, context=None):
        res = super(account_invoice, self).write(cr, uid, ids, vals, context=context)
        # On create invoice, if picking associate with it has reference to another picking,
        # get the invoice associate with that picking.
        if not isinstance(ids, types.ListType): # Ensure it is a list before proceeding.
            ids = [ids]        
        for invoice_id in ids:
            invoice = self.browse(cr, uid, invoice_id)
            if not invoice.invoice_id_ref:
                if invoice.picking_ids and invoice.picking_ids[0]:
                    if invoice.picking_ids[0].picking_id_ref:
                        if invoice.picking_ids[0].picking_id_ref.invoice_ids and invoice.picking_ids[0].picking_id_ref.invoice_ids[0]:
                            invoice_id_ref = invoice.picking_ids[0].picking_id_ref.invoice_ids[0].id
                            # Update reference
                            self.write(cr, uid, [invoice_id], {'invoice_id_ref': invoice_id_ref}) 
                            # Update reference back to the original
                            self.write(cr, uid, [invoice_id_ref], {'invoice_id_ref': invoice_id}) 
        return res
    
    def _prepare_refund(self, cr, uid, invoice, date=None, period_id=None, description=None, journal_id=None, context=None):
        res = super(account_invoice, self)._prepare_refund(cr, uid, invoice, date=date, period_id=period_id, description=description, journal_id=journal_id, context=context)
        res['invoice_id_ref'] = invoice.id
        return res
    
    def refund(self, cr, uid, ids, date=None, period_id=None, description=None, journal_id=None, context=None):
        new_ids = super(account_invoice, self).refund(cr, uid, ids, date=date, period_id=period_id, description=description, journal_id=journal_id, context=context)
        for new_invoice in self.browse(cr, uid, new_ids, context=context):
            if new_invoice.invoice_id_ref:
                self.write(cr, uid, [new_invoice.invoice_id_ref.id], {'invoice_id_ref': new_invoice.id})
        return new_ids        

account_invoice()

