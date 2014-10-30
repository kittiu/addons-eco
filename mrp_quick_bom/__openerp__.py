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
    'name' : 'Quick BOM and MO',
    'version' : '1.0',
    'author' : 'Ecosoft',
    'summary': 'Allows quick creation of BOM and MO from selected products',
    'description': """

This module allows quick creation of BOM and MO from selected products.
* From Product page, user selects multiple products, new menu action "Create Product/BOM" will appears, 
* After new Product/BOM is created, user will be redirected to BOM page.
* In BOM page, user will modify quantities of components, and click button "Create MO"
* From Product page, add new Create Product/BOM button. This will create BOM based on Order Lines.

    """,
    'category': 'MRP',
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['mrp'],
    'demo' : [],
    'data' : [
              'wizard/product_make_bom_view.xml',
              'sale_view.xml'
    ],
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
