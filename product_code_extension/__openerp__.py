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
    'name' : 'Product Code Extension',
    'version' : '1.0',
    'author' : 'Ecosoft',
    'summary': 'Dynamic Product Code based on referenced information',
    'description': """

Based on available information, product code (default_code) will be dynamically generated from,

<product_code>/<partner_code>/<product_sub_code>

If that information is not available, will be replaced with 0.

Sample of Dynamic Product Code
* 081/MV6001/01, 081/MV6001/02
* 000/MV6001/00

    """,
    'category': 'Sales',
    'sequence': 6,
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['product'],
    'demo' : [],
    'data' : [
        'product_view.xml',
        'res_partner_view.xml',
    ],
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
