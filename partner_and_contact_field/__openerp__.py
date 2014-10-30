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

{
    'name' : "Partner and Attention field in SO/PO",
    'author' : 'Kitti U.',
    'summary': '',
    'description': """
Features
========
* Supplier/Customer field to show only Partner marked as Company
* New Contact field to show contact on selected Supplier/Contact
""",
    'category': 'Sales Management',
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['web_m2x_options', 'purchase', 'sale'],
    'demo' : [],
    'data' : [
        'purchase_view.xml',
        'sale_view.xml',
    ],
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
