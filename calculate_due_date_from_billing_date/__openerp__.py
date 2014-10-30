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
    'name' : 'Calculate Invoice Due Date from Billing Date',
    'version' : '1.0',
    'author' : 'Ecosoft',
    'summary': 'For Supplier Invoice',
    'description': """

This module includes:

* Supplier Invoice -- Billing Date
* Due date will be calculated based on billing date.

""",
    'category': 'Accounting & Finance',
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['account'],
    'demo' : [],
    'data' : [
        'account_invoice_view.xml',
    ],
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
