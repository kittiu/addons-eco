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

from operator import itemgetter
import time

from openerp.osv import fields, osv

class product_product(osv.osv):
    
    _inherit = 'product.product'

    _columns = {
        'property_expense_input_vat_tax': fields.property(
            'account.tax',
            type='many2one',
            relation='account.tax',
            string="Expense Input VAT Tax",
            view_load=True,
            domain="[('type_tax_use', '=', 'purchase')]",
            help="This Tax and its Account Code will be used in HR Expense Line, when VAT is identified.",
            required=True,
            readonly=True),
        'property_expense_personal_wht_tax': fields.property(
            'account.tax',
            type='many2one',
            relation='account.tax',
            string="Expense Personal WHT Tax",
            view_load=True,
            domain="[('type_tax_use', '=', 'purchase')]",
            help="This Tax and its Account Code will be used in HR Expense Line, when Supplier Type is Personal and WHT is identified.",
            required=True,
            readonly=True),
        'property_expense_company_wht_tax': fields.property(
            'account.tax',
            type='many2one',
            relation='account.tax',
            string="Expense Company WHT Tax",
            view_load=True,
            domain="[('type_tax_use', '=', 'purchase')]",
            help="This Tax and its Account Code will be used in HR Expense Line, when Supplier Type is Company and WHT is identified.",
            required=True,
            readonly=True),                       
    }

product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
