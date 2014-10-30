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
import re
from openerp import netsvc
from openerp.osv import fields, osv

class product_product(osv.osv):

    _inherit = "product.product"
    
    def name_search(self, cr, user, name='', args=None, operator='ilike', context=None, limit=100):
        if not args:
            args = []
        if name:
            # Do not merge the 2 next lines into one single search, SQL search performance would be abysmal
            # on a database with thousands of matching products, due to the huge merge+unique needed for the
            # OR operator (and given the fact that the 'name' lookup results come from the ir.translation table
            # Performing a quick memory merge of ids in Python will give much better performance
            ids = set()
            ids.update(self.search(cr, user, args + [('default_code',operator,name)], limit=limit, context=context))
            if not limit or len(ids) < limit:
                words = name.split(' ')
                xargs = []
                for word in words:
                    if len(word.replace(' ','')) > 0:
                        xargs += [('name',operator,word.replace(' ',''))]
                ids = set()
                ids.update(self.search(cr, user, args + xargs, limit=(limit and (limit-len(ids)) or False) , context=context))
            ids = list(ids)
            # Default Code
            code_ids = self.search(cr, user, [('default_code',operator,name+'%')]+ args, limit=limit, context=context)
            ids = list(set(ids + code_ids))
            if not ids:
                ids = self.search(cr, user, [('ean13','=',name)]+ args, limit=limit, context=context)
            if not ids:
                ptrn = re.compile('(\[(.*?)\])')
                res = ptrn.search(name)
                if res:
                    ids = self.search(cr, user, [('default_code','=', res.group(2))] + args, limit=limit, context=context)
        else:
            ids = self.search(cr, user, args, limit=limit, context=context)
        result = self.name_get(cr, user, ids, context=context)
        return result
product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
