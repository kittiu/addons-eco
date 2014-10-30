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


class product_product(osv.osv):
    
    _inherit = "product.product"
    _columns = {
        'uos_coeff': fields.float('Unit of Measure -> UOS Coeff', digits_compute= dp.get_precision('Product UoS Coeff'),
            help='Coefficient to convert default Unit of Measure to Unit of Sale\n'
            ' uos = uom * coeff'),
    }
    
    def onchange_uom(self, cursor, user, ids, uom_id, uom_po_id):
        if uom_id:
            return {'value': {'uom_po_id': uom_id}}
        return {}
    
    def onchange_po_uom(self, cursor, user, ids, uom_id, uom_po_id):
        if uom_id:
            return {'value': {'uom_id': uom_po_id}}
        return {}
    
product_product()



class product_template(osv.osv):
    
    _inherit = "product.template"
    
    def _check_uom(self, cursor, user, ids, context=None):
        # No more validation as onchange_uom() will help changing the PO UOM.
        return True
    
    _constraints = [
        (_check_uom, 'Error: The default Unit of Measure and the purchase Unit of Measure must be in the same category.', ['uom_id']),
    ]
    
product_template()  


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
