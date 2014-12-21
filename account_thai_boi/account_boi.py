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

class account_boi(osv.osv):

    _name = "account.boi"
    _description = "BOI Certificate"
    _columns = {
        'name': fields.char('BOI Cert.', size=64, required=True),
        'active': fields.boolean('Active'),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', domain=[('type','=','boi')], required=True, help="Analytic Account of type BOI"),
        'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position'),
        'date_start': fields.date('Permit Start Date'),
        'date_end': fields.date('Permit End Date'),
        'warehouse_ids': fields.one2many('stock.warehouse', 'boi_id', 'Warehouses', readonly=True, help="In Warehouse window, you can specify warehouse for this BOI"),
        'boi_items': fields.one2many('account.boi.item', 'boi_id', 'BOI Products', readonly=False),
        'boi_product_line': fields.one2many('account.boi.product', 'boi_id', 'BOI Products', readonly=False),
    }
    _defaults = {
        'active': True,
    }
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'BOI Certificate Name must be unique!'),
    ]

account_boi()

class account_boi_item(osv.osv):

    _name = "account.boi.item"
    _description = "BOI Items & Quotas"
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', required=True, ondelete='cascade', select=True, ),
        'name': fields.char('Name', size=128, required=True),
        'quota_qty': fields.float('Quota Qty', required=True, help="??? Should quota be specified by BOI Item ???"),
        'quota_uom': fields.many2one('product.uom', 'UoM'),
        'invoiced_qty': fields.float('Invoiced Qty', required=True, help="Quantity of this BOI Item what has been invoiced"),
    }

account_boi_item()

class account_boi_product(osv.osv):
    
    _name = "account.boi.product"
    _description = "BOI Products Avail & Borrows"
    _rec_name = "product_id"
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', required=True, ondelete='cascade', select=True, ),
        'boi_item_id': fields.many2one('account.boi.item', 'BOI Item', ondelete='restrict', domain="[('boi_id','=',boi_id)]", required=True),
        'product_id': fields.many2one('product.product', 'Product', domain=[('purchase_ok','=',True)], required=True),
        'avail_qty': fields.float('Available Qty'),
        'borrowed_qty': fields.float('Borrowed Qty'),
    }
    _defaults = {
        'boi_id': lambda s, cr, uid, c: c.get('boi_id', False)
    }

account_boi_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
