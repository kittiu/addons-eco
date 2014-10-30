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

from _common import rounding

from openerp.osv import fields, osv
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp

class product_pricelist_item(osv.osv):
   
    def _price_field_get(self, cr, uid, context=None):
        result = super(product_pricelist_item, self)._price_field_get(cr, uid, context=context)
        result.append((-10, _("Partner's last invoice price")))
        return result
    
    #Checking base2 Pricelist has looping with Other Pricelist
    def _check_base2_recursion(self, cr, uid, ids, context=None):
        for obj_list in self.browse(cr, uid, ids, context=context):
            if obj_list.base2 == -1:
                main_pricelist = obj_list.price_version_id.pricelist_id.id
                other_pricelist = obj_list.base2_pricelist_id.id
                if main_pricelist == other_pricelist:
                    return False
        return True
    
    #Checking base not equal to base2
    def _check_duplicate_base(self, cr, uid, ids, context=None):     
        price_items = self.browse(cr, uid, ids, context=context)   
        
        for price_item in price_items:
                
            if price_item.base== price_item.base2 and price_item.base!=-1 and price_item.base2!=-1:
                return False
            
            if price_item.base2_pricelist_id==price_item.base_pricelist_id and (price_item.base2==-1 and price_item.base==-1):
                return False
        return True
    
    _inherit = "product.pricelist.item"

    _columns = {
        'base': fields.selection(_price_field_get, 'First Based on', required=True, size=-1, help="Base price for computation."),
        'base2': fields.selection(_price_field_get, 'Second Based(optional)', size=-1, help="Second base price for computation."),
        'base2_pricelist_id': fields.many2one('product.pricelist', 'Other Pricelist'),
    }
    
    _constraints = [
        (_check_duplicate_base, 'Error: The First Base same as Second Based', ['base','base2','base_pricelist_id','base2_pricelist_id']),
        (_check_base2_recursion, 'Error! You cannot assign the Main Pricelist as Other Pricelist in PriceList Item!', ['base2_pricelist_id']),
    ]

product_pricelist_item()

class product_pricelist(osv.osv):
    
    _inherit = 'product.pricelist'
    #Copy from price_get_multi and param:basefieldname for choosing field to calculate price list 
    def _common_price_get_multi(self, cr, uid, pricelist_ids, products_by_qty_by_partner,basefieldname='base', context=None):
        """multi products 'price_get'.
           @param pricelist_ids:
           @param products_by_qty:
           @param partner:
           @param context: {
             'date': Date of the pricelist (%Y-%m-%d),}
           @return: a dict of dict with product_id as key and a dict 'price by pricelist' as value
        """
#         basefieldname='base'
        def _create_parent_category_list(id, lst):
            if not id:
                return []
            parent = product_category_tree.get(id)
            if parent:
                lst.append(parent)
                return _create_parent_category_list(parent, lst)
            else:
                return lst
        # _create_parent_category_list

        if context is None:
            context = {}

        date = time.strftime('%Y-%m-%d')
        if 'date' in context:
            date = context['date']

        currency_obj = self.pool.get('res.currency')
        product_obj = self.pool.get('product.product')
        product_category_obj = self.pool.get('product.category')
        product_uom_obj = self.pool.get('product.uom')
        supplierinfo_obj = self.pool.get('product.supplierinfo')
        price_type_obj = self.pool.get('product.price.type')

        # product.pricelist.version:
        if not pricelist_ids:
            pricelist_ids = self.pool.get('product.pricelist').search(cr, uid, [], context=context)

        pricelist_version_ids = self.pool.get('product.pricelist.version').search(cr, uid, [
                                                        ('pricelist_id', 'in', pricelist_ids),
                                                        '|',
                                                        ('date_start', '=', False),
                                                        ('date_start', '<=', date),
                                                        '|',
                                                        ('date_end', '=', False),
                                                        ('date_end', '>=', date),
                                                    ])
        if len(pricelist_ids) != len(pricelist_version_ids):
            raise osv.except_osv(_('Warning!'), _("At least one pricelist has no active version !\nPlease create or activate one."))

        # product.product:
        product_ids = [i[0] for i in products_by_qty_by_partner]
        #products = dict([(item['id'], item) for item in product_obj.read(cr, uid, product_ids, ['categ_id', 'product_tmpl_id', 'uos_id', 'uom_id'])])
        products = product_obj.browse(cr, uid, product_ids, context=context)
        products_dict = dict([(item.id, item) for item in products])

        # product.category:
        product_category_ids = product_category_obj.search(cr, uid, [])
        product_categories = product_category_obj.read(cr, uid, product_category_ids, ['parent_id'])
        product_category_tree = dict([(item['id'], item['parent_id'][0]) for item in product_categories if item['parent_id']])

        results = {}
        base_pricelist_id =basefieldname+'_pricelist_id'
        
        for product_id, qty, partner in products_by_qty_by_partner:
            for pricelist_id in pricelist_ids:
                price = False

                tmpl_id = products_dict[product_id].product_tmpl_id and products_dict[product_id].product_tmpl_id.id or False

                categ_id = products_dict[product_id].categ_id and products_dict[product_id].categ_id.id or False
                categ_ids = _create_parent_category_list(categ_id, [categ_id])
                if categ_ids:
                    categ_where = '(categ_id IN (' + ','.join(map(str, categ_ids)) + '))'
                else:
                    categ_where = '(categ_id IS NULL)'

                if partner:
                    partner_where = basefieldname + ' <> -2 OR %s IN (SELECT name FROM product_supplierinfo WHERE product_id = %s) '
                    partner_args = (partner, tmpl_id)
                else:
                    partner_where = basefieldname+' <> -2 '
                    partner_args = ()

                cr.execute(
                    'SELECT i.*, pl.currency_id '
                    'FROM product_pricelist_item AS i, '
                        'product_pricelist_version AS v, product_pricelist AS pl '
                    'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = %s) '
                        'AND (product_id IS NULL OR product_id = %s) '
                        'AND (' + categ_where + ' OR (categ_id IS NULL)) '
                        'AND (' + partner_where + ') '
                        'AND price_version_id = %s '
                        'AND (min_quantity IS NULL OR min_quantity <= %s) '
                        'AND i.price_version_id = v.id AND v.pricelist_id = pl.id '
                    'ORDER BY sequence',
                    (tmpl_id, product_id) + partner_args + (pricelist_version_ids[0], qty))
                res1 = cr.dictfetchall()
                uom_price_already_computed = False
                for res in res1:
                    if res:
                        if res[basefieldname] == -1:
                            if not res[base_pricelist_id]:
                                price = 0.0
                            else:
                                price_tmp = self.price_get(cr, uid,
                                        [res[base_pricelist_id]], product_id,
                                        qty, context=context)[res[base_pricelist_id]]
                                ptype_src = self.browse(cr, uid, res[base_pricelist_id]).currency_id.id
                                uom_price_already_computed = True
                                price = currency_obj.compute(cr, uid, ptype_src, res['currency_id'], price_tmp, round=False)
                        elif res[basefieldname] == -2:
                            # this section could be improved by moving the queries outside the loop:
                            where = []
                            if partner:
                                where = [('name', '=', partner) ]
                            sinfo = supplierinfo_obj.search(cr, uid,
                                    [('product_id', '=', tmpl_id)] + where)
                            price = 0.0
                            if sinfo:
                                qty_in_product_uom = qty
                                product_default_uom = product_obj.read(cr, uid, [product_id], ['uom_id'])[0]['uom_id'][0]
                                supplier = supplierinfo_obj.browse(cr, uid, sinfo, context=context)[0]
                                seller_uom = supplier.product_uom and supplier.product_uom.id or False
                                if seller_uom and product_default_uom and product_default_uom != seller_uom:
                                    uom_price_already_computed = True
                                    qty_in_product_uom = product_uom_obj._compute_qty(cr, uid, product_default_uom, qty, to_uom_id=seller_uom)
                                cr.execute('SELECT * ' \
                                        'FROM pricelist_partnerinfo ' \
                                        'WHERE suppinfo_id IN %s' \
                                            'AND min_quantity <= %s ' \
                                        'ORDER BY min_quantity DESC LIMIT 1', (tuple(sinfo),qty_in_product_uom,))
                                res2 = cr.dictfetchone()
                                if res2:
                                    price = res2['price']
                        else:
                            price_type = price_type_obj.browse(cr, uid, int(res[basefieldname]))
                            uom_price_already_computed = True
                            price = currency_obj.compute(cr, uid,
                                    price_type.currency_id.id, res['currency_id'],
                                    product_obj.price_get(cr, uid, [product_id],
                                    price_type.field, context=context)[product_id], round=False, context=context)

                        if price is not False:
                            price_limit = price
                            price = price * (1.0+(res['price_discount'] or 0.0))
                            price = rounding(price, res['price_round']) #TOFIX: rounding with tools.float_rouding
                            price += (res['price_surcharge'] or 0.0)
                            if res['price_min_margin']:
                                price = max(price, price_limit+res['price_min_margin'])
                            if res['price_max_margin']:
                                price = min(price, price_limit+res['price_max_margin'])
                            break

                    else:
                        # False means no valid line found ! But we may not raise an
                        # exception here because it breaks the search
                        price = False

                if price:
                    results['item_id'] = res['id']
                    if 'uom' in context and not uom_price_already_computed:
                        product = products_dict[product_id]
                        uom = product.uos_id or product.uom_id
                        price = product_uom_obj._compute_price(cr, uid, uom.id, price, context['uom'])

                if results.get(product_id):
                    results[product_id][pricelist_id] = price
                else:
                    results[product_id] = {pricelist_id: price}

        return results
    
    #Calculate price list use base field
    def base_price_get_multi(self, cr, uid, pricelist_ids, products_by_qty_by_partner, context=None):        
        res = self._common_price_get_multi(cr, uid, pricelist_ids, products_by_qty_by_partner, basefieldname='base', context=context)
        return res
    
    #Calculate price list use base2 field
    def base2_price_get_multi(self, cr, uid, pricelist_ids, products_by_qty_by_partner, context=None):
        res = self._common_price_get_multi(cr, uid, pricelist_ids, products_by_qty_by_partner, basefieldname='base2', context=context)
        return res
    
    #Override price_get_multi method from product.pricelist module,it make sure all dependency are apply.
    def price_get_multi(self, cr, uid, pricelist_ids, products_by_qty_by_partner, context=None):        
        
        res = self.price_get_multi_lastinvoice(cr, uid, pricelist_ids, products_by_qty_by_partner,basefieldname="base",context=context)
        if not res:
            res = super(product_pricelist, self).price_get_multi(cr, uid, pricelist_ids, products_by_qty_by_partner=products_by_qty_by_partner, context=context)
            
        for products in products_by_qty_by_partner:
            for pricelist_id in pricelist_ids:
                if res[products[0]][pricelist_id]<=0.0:
                    res_multi = self.price_get_multi_lastinvoice(cr, uid, [pricelist_id], [products],basefieldname="base2",context=context)
                    if not res_multi:
                        res_multi = self.base2_price_get_multi(cr, uid, pricelist_ids = [pricelist_id], products_by_qty_by_partner = [products], context=context)          
                        res[products[0]][pricelist_id]=res_multi[products[0]][pricelist_id]
        return res
    
    #Calculate for the new type of price list - Partner last invoice price
    def price_get_multi_lastinvoice(self, cr, uid, pricelist_ids, products_by_qty_by_partner, basefieldname="base",context=None):
        """multi products 'price_get'.
           @param pricelist_ids:
           @param products_by_qty:
           @param partner:
           @param basefieldname: 
           @param context: {
             'date': Date of the pricelist (%Y-%m-%d),}
           @return: a dict of dict with product_id as key and a dict 'price by pricelist' as value
        """
        #basefieldname='base'
        def _create_parent_category_list(id, lst):
            if not id:
                return []
            parent = product_category_tree.get(id)
            if parent:
                lst.append(parent)
                return _create_parent_category_list(parent, lst)
            else:
                return lst
        # _create_parent_category_list

        if context is None:
            context = {}

        date = time.strftime('%Y-%m-%d')
        if 'date' in context:
            date = context['date']

        currency_obj = self.pool.get('res.currency')
        product_obj = self.pool.get('product.product')
        product_category_obj = self.pool.get('product.category')
        product_uom_obj = self.pool.get('product.uom')
        supplierinfo_obj = self.pool.get('product.supplierinfo')
        price_type_obj = self.pool.get('product.price.type')

        # product.pricelist.version:
        if not pricelist_ids:
            pricelist_ids = self.pool.get('product.pricelist').search(cr, uid, [], context=context)

        pricelist_version_ids = self.pool.get('product.pricelist.version').search(cr, uid, [
                                                        ('pricelist_id', 'in', pricelist_ids),
                                                        '|',
                                                        ('date_start', '=', False),
                                                        ('date_start', '<=', date),
                                                        '|',
                                                        ('date_end', '=', False),
                                                        ('date_end', '>=', date),
                                                    ])
        if len(pricelist_ids) != len(pricelist_version_ids):
            raise osv.except_osv(_('Warning!'), _("At least one pricelist has no active version !\nPlease create or activate one."))

        # product.product:
        product_ids = [i[0] for i in products_by_qty_by_partner]
        #products = dict([(item['id'], item) for item in product_obj.read(cr, uid, product_ids, ['categ_id', 'product_tmpl_id', 'uos_id', 'uom_id'])])
        products = product_obj.browse(cr, uid, product_ids, context=context)
        products_dict = dict([(item.id, item) for item in products])

        # product.category:
        product_category_ids = product_category_obj.search(cr, uid, [])
        product_categories = product_category_obj.read(cr, uid, product_category_ids, ['parent_id'])
        product_category_tree = dict([(item['id'], item['parent_id'][0]) for item in product_categories if item['parent_id']])

        results = {}
        for product_id, qty, partner in products_by_qty_by_partner:
            for pricelist_id in pricelist_ids:
                price = False

                tmpl_id = product_id and products_dict[product_id].product_tmpl_id and products_dict[product_id].product_tmpl_id.id or False

                categ_id = product_id and products_dict[product_id].categ_id and products_dict[product_id].categ_id.id or False
                categ_ids = _create_parent_category_list(categ_id, [categ_id])
                if categ_ids:
                    categ_where = '(categ_id IN (' + ','.join(map(str, categ_ids)) + '))'
                else:
                    categ_where = '(categ_id IS NULL)'

                if partner:
                    partner_where = basefieldname+' <> -2 OR %s IN (SELECT name FROM product_supplierinfo WHERE product_id = %s) '
                    partner_args = (partner, tmpl_id)
                else:
                    partner_where = basefieldname+' <> -2 '
                    partner_args = ()

                cr.execute(
                    'SELECT i.*, pl.currency_id '
                    'FROM product_pricelist_item AS i, '
                        'product_pricelist_version AS v, product_pricelist AS pl '
                    'WHERE (product_tmpl_id IS NULL OR product_tmpl_id = %s) '
                        'AND (product_id IS NULL OR product_id = %s) '
                        'AND (' + categ_where + ' OR (categ_id IS NULL)) '
                        'AND (' + partner_where + ') '
                        'AND price_version_id = %s '
                        'AND (min_quantity IS NULL OR min_quantity <= %s) '
                        'AND i.price_version_id = v.id AND v.pricelist_id = pl.id '
                    'ORDER BY sequence',
                    (tmpl_id, product_id) + partner_args + (pricelist_version_ids[0], qty))
                res1 = cr.dictfetchall()
                uom_price_already_computed = False
                for res in res1:
                    if res:
                        if res[basefieldname] == -10: # Partner's last invoice price
                            price = 0.0
                            product_default_uom = product_obj.read(cr, uid, [product_id], ['uom_id'])[0]['uom_id'][0]
                            cr.execute("select i.partner_id, il.product_id, il.price_unit, il.uos_id \
                                        from account_invoice i \
                                        inner join account_invoice_line il on il.invoice_id = i.id \
                                        inner join product_uom uom on uom.id = il.uos_id \
                                        where state not in ('draft','cancel') \
                                        and il.product_id = %s \
                                        and i.partner_id = %s \
                                        order by i.write_date desc limit 1", (product_id,partner or -1,))
                                                     
                            res2 = cr.dictfetchone()
                            if res2:
                                line_uom = res2['uos_id']
                                if line_uom and product_default_uom and product_default_uom != line_uom:
                                    uom_price_already_computed = True
                                    price = product_uom_obj._compute_price(cr, uid, line_uom, res2['price_unit'], product_default_uom)
                                else:                           
                                    price = res2['price_unit']
                        else:
                            return False

                        if price is not False:
                            price_limit = price
                            price = price * (1.0+(res['price_discount'] or 0.0))
                            price = rounding(price, res['price_round']) #TOFIX: rounding with tools.float_rouding
                            price += (res['price_surcharge'] or 0.0)
                            if res['price_min_margin']:
                                price = max(price, price_limit+res['price_min_margin'])
                            if res['price_max_margin']:
                                price = min(price, price_limit+res['price_max_margin'])
                            break

                    else:
                        # False means no valid line found ! But we may not raise an
                        # exception here because it breaks the search
                        price = False

                if price:
                    results['item_id'] = res['id']
                    if 'uom' in context and not uom_price_already_computed:
                        product = products_dict[product_id]
                        uom = product.uos_id or product.uom_id
                        price = product_uom_obj._compute_price(cr, uid, uom.id, price, context['uom'])

                if results.get(product_id):
                    results[product_id][pricelist_id] = price
                else:
                    results[product_id] = {pricelist_id: price}

        return results
product_pricelist()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
