# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Ecosoft Co., Ltd. (http://ecosoft.co.th).
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

{
    'name' : "Product Price List based on Last Partner's Invoice",
    'author' : 'Ecosoft',
    'summary': 'Add new option in Price List Version to calculate price based on last invoice',
    'description': """
Add new option in Price List Version to calculate price based on last invoice

Note: Have not tested with multi-currency yet.

* Additional, second base field, this is optional for computation price list ,when price list in base equal to 0.0 , it will be new calculate price list with base2. 
* * Ecosof-addons/product_pricelist_last_invoice module
* * * New base2 and base2_pricelist_id Name field
* * * New constraints
* * * 1. _check_duplicate_base,Checking base not equal to base2
* * * 2. _check_base2_recursion, Checking base2 Pricelist has looping in Other Pricelist
* * * New Method
* * * 1._common_price_get_multi, Copy from price_get_multi and param:basefieldname for choosing field to calculate price list 
* * * 2. base_price_get_multi, Using "base" field computation a price list
* * * 3. base2_price_get_multi, Using "base2" field computation a price list
* * * Override price_get_multi method from product.pricelist module(replace method ,it not call super class)
* * * Modification price_get_multi_lastinvoice method,add param:basefieldname for choosing field to calculate price list
* * * Remove price_get method

""",
    'category': 'Purchase Management',
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['product'],
    'demo' : [],
    'data' : [
              'pricelist_view.xml',
    ],
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
