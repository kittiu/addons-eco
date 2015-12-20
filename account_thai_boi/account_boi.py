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
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv
from openerp import tools
from datetime import datetime


class account_boi(osv.osv):

    _name = "account.boi"
    _description = "BOI Certificate"

    def _search_is_active(self, cr, uid, obj, name, args, domain=None, context=None):
        if not len(args):
            return []
        today = fields.date.context_today(self,cr,uid,context=context)
        for arg in args:
            if arg[1] == '=':
                if arg[2]:  # Active = True
                    cr.execute("select id from account_boi where %s between date_start and date_end", (today,))
                else:
                    cr.execute("select id from account_boi where %s not between date_start and date_end", (today,))
                ids = map(lambda x: x[0], cr.fetchall())
            else:
                return []
        return [('id', 'in', [id for id in ids])]

    def _is_active(self, cr, uid, ids, field_names, arg=None, context=None):
        res =  dict.fromkeys(ids, False)
        today = datetime.strptime(fields.date.context_today(self,cr,uid,context=context), '%Y-%m-%d')
        for boi in self.browse(cr, uid, ids):
            date_start = datetime.strptime(boi.date_start, '%Y-%m-%d')
            date_end = datetime.strptime(boi.date_end, '%Y-%m-%d')
            if date_start <= today <= date_end:
                res[boi.id] = True
        return res  
      
    _columns = {
        'name': fields.char('BOI Cert.', size=64, required=True),
        'active': fields.function(_is_active, string='Active', type='boolean', fnct_search=_search_is_active,
                                  help="This active flag will be automatically reset based on date"),
        'analytic_account_id': fields.many2one('account.analytic.account', 'Analytic Account', domain=[('type','=','boi')], required=True, help="Analytic Account of type BOI"),
        'fiscal_position': fields.many2one('account.fiscal.position', 'Fiscal Position'),
        'date_start': fields.date('Permit Start Date'),
        'date_end': fields.date('Permit End Date'),
        'location_ids': fields.one2many('stock.location', 'boi_id', 'Locations', readonly=False, help="Specify location for this BOI"),
        'boi_items': fields.one2many('account.boi.item', 'boi_id', 'BOI Products', domain=[('is_fg','=',False)], readonly=False),
        'boi_items_fg': fields.one2many('account.boi.item', 'boi_id', 'BOI Products', domain=[('is_fg','=',True)], readonly=False),
        'boi_product_line': fields.one2many('account.boi.product', 'boi_id', 'BOI Products', domain=[('is_fg','=',False)], readonly=False),
        'boi_product_line_fg': fields.one2many('account.boi.product', 'boi_id', 'BOI Products', domain=[('is_fg','=',True)], readonly=False),
        'boi_product_borrow_detail': fields.one2many('account.boi.product.borrow.detail', 'boi_id', 'Borrow Details', readonly=True)
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
    
    def _invoiced_qty(self, cr, uid, ids, name, arg, context=None):
        res = dict.fromkeys(ids, 0.0)
        cr.execute("""
             SELECT sub.id,
                sub.product_qty as quantity,
                sub.uom_name
               FROM (SELECT boi.boi_item_id as id,
                            CASE
                                WHEN u.uom_type::text <> 'reference'::text THEN ( SELECT product_uom.name
                                   FROM product_uom
                                  WHERE product_uom.uom_type::text = 'reference'::text AND product_uom.active AND product_uom.category_id = u.category_id
                                 LIMIT 1)
                                ELSE u.name
                            END AS uom_name,
                        sum(ail.quantity / u.factor) AS product_qty
                       FROM account_invoice_line ail
                         JOIN account_invoice ai ON ai.id = ail.invoice_id
                     JOIN (SELECT ab.id boi_id, abp.boi_item_id, abp.product_id
                        FROM account_boi_product abp
                        JOIN account_boi ab ON ab.id = abp.boi_id) boi
                    ON boi.boi_id = ai.boi_id AND ail.product_id = boi.product_id
                         LEFT JOIN product_product pr ON pr.id = ail.product_id
                         LEFT JOIN product_uom u ON u.id = ail.uos_id
                         WHERE ai.type in ('in_invoice', 'in_refund')
                      GROUP BY boi.boi_item_id, u.uom_type, u.category_id, u.name) sub
                WHERE sub.id in %s;
        """, (tuple(ids),))
        for x in cr.fetchall():
            res[x[0]] = x[1]
        return res
    
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', required=True, ondelete='cascade', select=True, ),
        'name': fields.char('Name', size=128, required=True),
        'quota_qty': fields.float('Quota Qty', required=True, help="??? Should quota be specified by BOI Item ???"),
        'quota_uom': fields.many2one('product.uom', 'UoM'),
        'invoiced_qty': fields.function(_invoiced_qty, string='Invoiced Quantity', type='float', help="Quantity of this BOI Item that suppliers has invoiced (Supplier Invoice)"),
        'is_fg': fields.boolean('Finished Goods')
        #'invoiced_qty': fields.float('xxxx')
        #'used_qty': fields.function('Used Quantity', type='float', help="Quantity of this BOI Item that has been used in manufacturing (moved to production area)"),
    }
    _defaults = {
        'is_fg': lambda self,cr,uid,c: c.get('is_fg', False),
    }
account_boi_item()

class account_boi_product(osv.osv):
    
    _name = "account.boi.product"
    _description = "BOI Products Avail & Borrows"
    _rec_name = "product_id"
    
    def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
        """ Finds the incoming and outgoing quantity of product.
        @return: Dictionary of values
        """
        if not field_names:
            field_names = []
        if context is None:
            context = {}
        res = {}
        product_ids = []
        boi_product = {}
        boi = self.browse(cr, uid, ids[0]).boi_id
        locations = boi.location_ids
        for id in ids:
            res[id] = {}.fromkeys(field_names, 0.0)
            obj = self.browse(cr, uid, id)
            product_id = obj.product_id.id
            product_ids.append(product_id)
            boi_product.update({id: product_id})
        for f in field_names:
            c = context.copy()
            if f == 'qty_available':
                c.update({ 'states': ('done',), 'what': ('in', 'out') })
#             if f == 'virtual_available':
#                 c.update({ 'states': ('confirmed','waiting','assigned','done'), 'what': ('in', 'out') })
#             if f == 'incoming_qty':
#                 c.update({ 'states': ('confirmed','waiting','assigned'), 'what': ('in',) })
#             if f == 'outgoing_qty':
#                 c.update({ 'states': ('confirmed','waiting','assigned'), 'what': ('out',) })
            for location in locations:
                c.update({'location': location.id})
                stock = self.pool.get('product.product').get_product_available(cr, uid, product_ids, context=c)
                for id in ids:
                    res[id][f] += stock.get(boi_product[id], 0.0)
        return res

    def _product_used(self, cr, uid, ids, field_names=None, arg=False, context=None):
        if context is None:
            context = {}

        boi_products = {}
        for p in self.read(cr, uid, ids, ['id', 'product_id'], context=None):
            boi_products.update({p['product_id'][0]: p['id']})
        product_obj = self.pool.get('product.product')
        product_ids = boi_products.keys()
            
        res = {}
        for id in ids:
            fields = {}
            for f in field_names:
                fields[f] = 0
            res[id] = fields   

        boi = self.browse(cr, uid, ids[0]).boi_id

        # this will be a dictionary of the product UoM by product id
        product2uom = {}
        uom_ids = []
        for product in product_obj.read(cr, uid, product_ids, ['uom_id'], context=context):
            product2uom[product['id']] = product['uom_id'][0]
            uom_ids.append(product['uom_id'][0])
        # this will be a dictionary of the UoM resources we need for conversion purposes, by UoM id
        uoms_o = {}
        for uom in self.pool.get('product.uom').browse(cr, uid, uom_ids, context=context):
            uoms_o[uom.id] = uom

        for f in field_names:

            this_loc_ids = [l.id for l in boi.location_ids]
            if f == 'qty_borrowed':
                domain =  [('boi_id','=',False), ('usage','=','internal'), ('chained_location_type','!=','customer')]
            if f == 'qty_consumed':
                domain =  [('boi_id','=',False), ('usage','=','production')]
            other_loc_ids = self.pool.get('stock.location').search(cr, uid, domain)
            states = ['done']
            where = [tuple(this_loc_ids),tuple(other_loc_ids),tuple(product_ids),tuple(states)]

            # In
            cr.execute(
                """select sum(product_qty), product_id, product_uom
                    from stock_move
                    where location_dest_id IN %s
                    and (location_id IN %s
                        or location_id IN (select id from stock_location where boi_id is not null 
                                            and boi_id not in (select boi_id from stock_location where id = stock_move.location_dest_id))
                        )
                    and product_id  IN %s
                    and state in %s
                    group by product_id, product_uom""",tuple(where))
            results = cr.fetchall()
            # Out
            cr.execute(
                """select sum(product_qty), product_id, product_uom
                    from stock_move
                    where location_id IN %s
                    and (location_dest_id IN %s
                        or location_dest_id IN (select id from stock_location where boi_id is not null 
                                            and boi_id not in (select boi_id from stock_location where id = stock_move.location_id))
                        )
                    and product_id  IN %s
                    and state in %s
                    group by product_id, product_uom""",tuple(where))
            results2 = cr.fetchall()
                
            # Get the missing UoM resources
            uom_obj = self.pool.get('product.uom')
            uoms = map(lambda x: x[2], results) + map(lambda x: x[2], results2)
            if context.get('uom', False):
                uoms += [context['uom']]
            uoms = filter(lambda x: x not in uoms_o.keys(), uoms)
            if uoms:
                uoms = uom_obj.browse(cr, uid, list(set(uoms)), context=context)
                for o in uoms:
                    uoms_o[o.id] = o
                    
            #TOCHECK: before change uom of product, stock move line are in old uom.
            context.update({'raise-exception': False})
            # Count the incoming quantities
            for amount, prod_id, prod_uom in results:
                amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
                         uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
                res[boi_products[prod_id]][f] -= amount
            # Count the outgoing quantities
            for amount, prod_id, prod_uom in results2:
                amount = uom_obj._compute_qty_obj(cr, uid, uoms_o[prod_uom], amount,
                        uoms_o[context.get('uom', False) or product2uom[prod_id]], context=context)
                res[boi_products[prod_id]][f] += amount
            
        return res
    
    
    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', required=True, ondelete='cascade', select=True, ),
        'boi_item_id': fields.many2one('account.boi.item', 'BOI Item', ondelete='restrict', domain="[('boi_id','=',boi_id)]", required=True),
        'product_id': fields.many2one('product.product', 'Product', domain="['|', ('sale_ok','=',is_fg), ('purchase_ok','!=',is_fg)]", required=True),
        'qty_available': fields.function(_product_available,
                type='float',  digits_compute=dp.get_precision('Product Unit of Measure'), multi='qty',
                string='Available Qty'),
        'qty_borrowed': fields.function(_product_used, 
                type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
                string='Borrowed Qty', multi="qty_used"),
        'qty_consumed': fields.function(_product_used, 
                type='float',  digits_compute=dp.get_precision('Product Unit of Measure'),
                string='Consumed Qty', multi="qty_used"),
        'is_fg': fields.boolean('Finished Goods')        #'qty_borrowed': fields.float('XXX')
    }
    _defaults = {
        'boi_id': lambda self,cr,uid,c: c.get('boi_id', False),
        'is_fg': lambda self,cr,uid,c: c.get('is_fg', False),
    }
    
    def action_view_borrowed_move(self, cr, uid, ids, context=None):
        return self.action_view_used_move(cr, uid, ids, usage='internal', context=context)
    
    def action_view_consumed_move(self, cr, uid, ids, context=None):
        return self.action_view_used_move(cr, uid, ids, usage='production', context=context)

    def action_view_used_move(self, cr, uid, ids, usage='internal', context=None):
        
        mod_obj = self.pool.get('ir.model.data')
        act_obj = self.pool.get('ir.actions.act_window')
        result = mod_obj.get_object_reference(cr, uid, 'stock', 'act_product_stock_move_open')
        id = result and result[1] or False
        result = act_obj.read(cr, uid, [id], context=context)[0]
        
        boi_product = self.browse(cr, uid, ids[0])
        
        # Borrowed Items are,
        # 1) From these locations, 2) To Internal, non-BOI, non-Output
        other_loc_ids = self.pool.get('stock.location').search(cr, uid, [('boi_id','=',False), ('usage','=',usage), ('chained_location_type','!=','customer')])
        this_loc_ids = [l.id for l in boi_product.boi_id.location_ids]
        states = ['done']
        where = [tuple(this_loc_ids),tuple(other_loc_ids), tuple(this_loc_ids),tuple(other_loc_ids), tuple([boi_product.product_id.id]), tuple(states)]
        cr.execute(
            """select id
                from stock_move
                where (   (location_dest_id IN %s
                            and (location_id IN %s
                                or location_id IN (select id from stock_location where boi_id is not null 
                                                    and boi_id not in (select boi_id from stock_location where id = stock_move.location_dest_id))
                                ))
                or
                            (location_id IN %s
                            and (location_dest_id IN %s
                                or location_dest_id IN (select id from stock_location where boi_id is not null 
                                                    and boi_id not in (select boi_id from stock_location where id = stock_move.location_id))
                                ))   )
                and product_id  IN %s
                and state in %s""",tuple(where))
        res = cr.fetchall()
        
        
        result['domain'] = [('id','in', [x for x in res])]
#         result['domain'] = [('product_id','in',[boi_product.product_id.id]), 
#                             '|', '&', ('location_id','in',this_loc_ids), ('location_dest_id','in',other_loc_ids),
#                                  '&', ('location_dest_id','in',this_loc_ids), ('location_id','in',other_loc_ids)]
        result['context'] = {}
        return result
    
account_boi_product()


class account_boi_product_borrow_detail(osv.osv):
    _name = "account.boi.product.borrow.detail"
    _description = "Product Borrow Detail"
    _auto = False
    _rec_name = 'product_id'

    _columns = {
        'boi_id': fields.many2one('account.boi', 'BOI Cert.', readonly=True),
        'boi_location_id': fields.many2one('stock.location', 'BOI Location', readonly=True),
        'borrow_location_id': fields.many2one('stock.location', 'Borrower Location', readonly=True),
        'product_id': fields.many2one('product.product', 'Product', readonly=True),
        'quantity':fields.float('Quantity', readonly=True),
        'uom_name': fields.char('UoM', readonly=True),
    }
    _order = 'quantity desc'

    def init(self, cr):
        # self._table = account_invoice_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            select row_number() over (order by quantity desc) id, * from
            (select b.boi_id, b.boi_location_id, b.borrow_location_id, b.product_id, sum(b.qty) quantity, b.uom_name from
            (
                select sl.boi_id, a.boi_location_id, a.borrow_location_id, a.product_id,
                a.qty/u.factor qty,
                CASE
                     WHEN u.uom_type::text <> 'reference'::text
                    THEN ( SELECT product_uom.name
                           FROM product_uom
                           WHERE product_uom.uom_type::text = 'reference'::text
                        AND product_uom.active
                        AND product_uom.category_id = u.category_id LIMIT 1)
                    ELSE u.name
                    END AS uom_name
                from
                (
                    -- Borrow BOI Location
                    (select sum(product_qty) qty, location_id boi_location_id, location_dest_id borrow_location_id, product_id, product_uom
                    from stock_move where state = 'done'
                    and location_id in (select id from stock_location where boi_id is not null)
                    and location_dest_id in (select id from stock_location where boi_id is null and usage='internal' and chained_location_type != 'customer')
                    group by location_id, location_dest_id, product_id, product_uom)
                    union
                    -- Back to BOI Location
                    (select -sum(product_qty) qty, location_dest_id boi_location_id, location_id borrow_location_id, product_id, product_uom
                    from stock_move where state = 'done'
                    and location_dest_id in (select id from stock_location where boi_id is not null)
                    and location_id in (select id from stock_location where boi_id is null and usage='internal' and chained_location_type != 'customer')
                    group by location_id, location_dest_id, product_id, product_uom)
                ) a
                LEFT JOIN product_uom u ON u.id = a.product_uom
                LEFT JOIN stock_location sl on sl.id = a.boi_location_id
            ) b
            group by b.boi_id, b.boi_location_id, b.borrow_location_id, b.product_id, b.uom_name) c           
        )"""% (self._table,))

account_boi_product_borrow_detail()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
