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

NO_DELETION_MSG = _('Can not delete document with assigned number %s!')

# Following documents included
#* sale.order (name)
#* purchase.order (name)
#* account.invoice (number)
#* account.voucher (number)
#* account.billing (number)
#* stock.picking (name)
#* stock.picking.out (name)
#* stock.picking.in (name)
#* payment.register (number)

class sale_order(osv.osv):
       
    _inherit = 'sale.order'
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for doc in self.browse(cr, uid, ids, context=context):
            if doc.name:
                raise osv.except_osv(_('Error!'), NO_DELETION_MSG%(doc.name,))
        return super(sale_order, self).unlink(cr, uid, ids, context=context)
      
sale_order()

class purchase_order(osv.osv):
       
    _inherit = 'purchase.order'
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for doc in self.browse(cr, uid, ids, context=context):
            if doc.name:
                raise osv.except_osv(_('Error!'), NO_DELETION_MSG%(doc.name,))
        return super(purchase_order, self).unlink(cr, uid, ids, context=context)
      
purchase_order()

class account_invoice(osv.osv):
       
    _inherit = 'account.invoice'
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for doc in self.browse(cr, uid, ids, context=context):
            if doc.number:
                raise osv.except_osv(_('Error!'), NO_DELETION_MSG%(doc.number,))
        return super(account_invoice, self).unlink(cr, uid, ids, context=context)
      
account_invoice()

class account_voucher(osv.osv):
       
    _inherit = 'account.voucher'
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for doc in self.browse(cr, uid, ids, context=context):
            if doc.number:
                raise osv.except_osv(_('Error!'), NO_DELETION_MSG%(doc.number,))
        return super(account_voucher, self).unlink(cr, uid, ids, context=context)
      
account_voucher()


class account_billing(osv.osv):
       
    _inherit = 'account.billing'
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for doc in self.browse(cr, uid, ids, context=context):
            if doc.number:
                raise osv.except_osv(_('Error!'), NO_DELETION_MSG%(doc.number,))
        return super(account_billing, self).unlink(cr, uid, ids, context=context)
      
account_billing()


class stock_picking(osv.osv):
       
    _inherit = 'stock.picking'
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for doc in self.browse(cr, uid, ids, context=context):
            if doc.name:
                raise osv.except_osv(_('Error!'), NO_DELETION_MSG%(doc.name,))
        return super(stock_picking, self).unlink(cr, uid, ids, context=context)
      
stock_picking()

class stock_picking_out(osv.osv):
       
    _inherit = 'stock.picking.out'
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for doc in self.browse(cr, uid, ids, context=context):
            if doc.name:
                raise osv.except_osv(_('Error!'), NO_DELETION_MSG%(doc.name,))
        return super(stock_picking_out, self).unlink(cr, uid, ids, context=context)
      
stock_picking_out()

class stock_picking_in(osv.osv):
       
    _inherit = 'stock.picking.in'
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for doc in self.browse(cr, uid, ids, context=context):
            if doc.name:
                raise osv.except_osv(_('Error!'), NO_DELETION_MSG%(doc.name,))
        return super(stock_picking_in, self).unlink(cr, uid, ids, context=context)
      
stock_picking_in()

class payment_register(osv.osv):
       
    _inherit = 'payment.register'
    
    def unlink(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        for doc in self.browse(cr, uid, ids, context=context):
            if doc.number:
                raise osv.except_osv(_('Error!'), NO_DELETION_MSG%(doc.number,))
        return super(payment_register, self).unlink(cr, uid, ids, context=context)
      
payment_register()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
