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
from lxml import etree

from openerp.osv import fields, osv
import openerp.addons.decimal_precision as dp

class purchase_order(osv.osv):

    _inherit = "purchase.order"
    
    def _get_line_qty(self, cr, uid, line, context=None):
        if line.product_uos:
            return line.product_uos_qty or 0.0
        return line.product_qty

    def _get_line_uom(self, cr, uid, line, context=None):
        if line.product_uos:
            return line.product_uos.id
        return line.product_uom.id
    
    def _prepare_inv_line(self, cr, uid, account_id, order_line, context=None):

        res = super(purchase_order,self)._prepare_inv_line(cr, uid, account_id, order_line, context)
 
        uosqty = self._get_line_qty(cr, uid, order_line, context=context)
        uos_id = self._get_line_uom(cr, uid, order_line, context=context)
        pu = 0.0
        if uosqty:
            pu = round(order_line.price_unit * order_line.product_qty / uosqty,
                    self.pool.get('decimal.precision').precision_get(cr, uid, 'Product Price'))

        res.update({'price_unit': pu, 
                    'quantity': uosqty,           
                    'uos_id': uos_id})

        return res
        
    def _prepare_order_line_move(self, cr, uid, order, order_line, picking_id, context=None):
        
        res = super(purchase_order,self)._prepare_order_line_move(cr, uid, order, order_line, picking_id, context)
        # If UOS, show UOS
        res.update({'product_uos_qty': (order_line.product_uos and order_line.product_uos_qty) or order_line.product_qty,
                    'product_uos': (order_line.product_uos and order_line.product_uos.id) or order_line.product_uom.id})
        return res
        
purchase_order()

class purchase_order_line(osv.osv):
    
    _inherit = "purchase.order.line"
    _columns = {
        'is_uos_product': fields.boolean("Product has UOS?"),
        'product_uos_qty': fields.float('Quantity (UoS)' ,digits_compute= dp.get_precision('Product UoS')),
        'product_uos': fields.many2one('product.uom', 'Product UoS'),
        'price_uos_unit': fields.float('Unit Price (UoS)', required=False, digits_compute=dp.get_precision('Product Price')),
    }
    
    def onchange_product_id(self, cr, uid, ids, pricelist_id, product_id, qty, uom, 
            partner_id, date_order=False, fiscal_position_id=False, date_planned=False,
            name='', price_unit=False, qty_uos=0, uos=False, context=None): 
        
        # Call super class method
        result = super(purchase_order_line,self).onchange_product_id(cr, uid, ids, pricelist_id, product_id, qty, uom,
            partner_id, date_order, fiscal_position_id, date_planned, name, price_unit, context)
                
        if not product_id:
            return result
        
        # Based on sale.product_id_change, additional logic goes here,
        i_result = {}
        i_domain = {}
        i_warning = {}
        if result.get('value'):
            i_result = result['value']
        if result.get('domain'):
            i_domain = result['domain']
        if result.get('warning'):
            i_warning = result['warning']
            
        product_uom_obj = self.pool.get('product.uom')
        product_obj = self.pool.get('product.product')
        product_obj = product_obj.browse(cr, uid, product_id, context=context)
        result = {}
        domain = {}
        warning = {}
        
        # Reset uom, if not in the same category.
        uom2 = False
        if uom:
            uom2 = product_uom_obj.browse(cr, uid, uom)
            if product_obj.uom_id.category_id.id != uom2.category_id.id:
                uom = False
        
        if (not uom) and (not uos):
            result['product_uom'] = product_obj.uom_id.id
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
                uos_category_id = product_obj.uos_id.category_id.id
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                uos_category_id = False
            domain = {'product_uom':
                        [('category_id', '=', product_obj.uom_id.category_id.id)],
                        'product_uos':
                        [('category_id', '=', uos_category_id)]}
        elif uos and not uom: # only happens if uom is False
            result['product_uom'] = product_obj.uom_id and product_obj.uom_id.id
            result['product_uom_qty'] = qty_uos / (product_obj.uos_coeff > 0 and product_obj.uos_coeff or 1)
        elif uom: # whether uos is set or not
            default_uom = product_obj.uom_id and product_obj.uom_id.id
            # KTU Start
            #result['product_uom'] = default_uom
            if not product_obj.uos_id:
                result['product_uom'] = uom
            else: # If UOS always force to default_uom
                result['product_uom'] = default_uom
                uom = default_uom
            # KTU End
            if product_obj.uos_id:
                result['product_uos'] = product_obj.uos_id.id
                result['product_uos_qty'] = qty * product_obj.uos_coeff
            else:
                result['product_uos'] = False
                result['product_uos_qty'] = qty
                
        # Start KTU: Reset the price_unit one more time, in case that UOS is available (as uom will always set back to default)
        result['is_uos_product'] = False
        if product_obj.uos_id:
            result['is_uos_product'] = True
            product_pricelist = self.pool.get('product.pricelist')
            if pricelist_id:
                price = product_pricelist.price_get(cr, uid, [pricelist_id],
                        product_obj.id, qty or 1.0, partner_id or False, {'uom': uom, 'date': date_order})[pricelist_id]
            else:
                price = product_obj.standard_price        
            result['price_unit'] = price
        # End KTU
        
        i_result.update(result)           
        i_domain.update(domain)
        i_warning.update(warning)
        
        return {'value': i_result, 'domain': i_domain, 'warning': i_warning}

    def onchange_product_uos(self, cr, uid, ids, product_id, is_uos_product=False, qty=0, uom=False, qty_uos=0, uos=False, context=None):
        
        # Return when, no product
        if product_id:
            # Case 1: product is not UOS
            if not is_uos_product:
                return {'value': {'product_uos_qty': qty, 'product_uos': False}}
            else:            
                if uos == uom:
                    return {'value': {'product_uos_qty': qty}}
                else:
                    product = self.pool.get('product.product').browse(cr, uid, product_id, context=context)
                    uom = product.uom_id.id
                    uos = product.uos_id.id
                    qty = qty_uos / (product.uos_coeff > 0 and product.uos_coeff or 1)
                    # Problem with recursive conversion if qty is adjusted.
                    #return {'value': {'product_qty': qty, 'product_uom': uom}}
                    return {'value': {'product_uom': uom}}
        return {}
    
    def onchange_price_uos_unit(self, cr, uid, ids, price_uos_unit, product_uos_qty, product_qty, context=None):
        if price_uos_unit and product_qty:
            price_unit = 0.0
            price_unit = float(price_uos_unit) * (float(product_uos_qty) / float(product_qty))
            return {'value': {'price_unit': price_unit}}
        return {}
    
    def copy_data(self, cr, uid, id, default=None, context=None):
        if not default:
            default = {}
        default.update({'price_uos_unit': 0.0})
        return super(purchase_order_line, self).copy_data(cr, uid, id, default, context)    
    
purchase_order_line()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
