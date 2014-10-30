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
    'name': "Sales Commission Calculations Extension",
    'author': 'Ecosoft',
    'summary': '',
    'description': """

This module extend the sale_commission_calc with following features,

Additional Deduction on total commission
----------------------------------------

This feature give extra deduction to the commission when commission is being created.
On Create Commission Invoice wizard, user can add extra deduction amount (< commission amount).
The deduction amount will be placed in Commission Invoice as Additional Discount (%)

Comply with Additional Discount (%)
-----------------------------------

Making sure that when do Commission Calculation, the commission will be deducted by the factor of additional discount.


Note:
-----

This module depend on advance_and_additonal_discount, which is a very big module to be added. Make sure it is really necessary to use this addon.
""",
    'category': 'Sales',
    'sequence': 20,
    'website': 'http://www.ecosoft.co.th',
    'images': [],
    'depends': ['sale_commission_calc', 'advance_and_additional_discount'],
    'demo': [
    ],
    'data': [
          'wizard/create_commission_invoice_view.xml',
          'commission_calc_view.xml',
    ],
    'test': [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
