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
    'name' : 'Allow Fiscal Year Sequence for all document',
    'version' : '1.0',
    'author' : 'Ecosoft',
    'summary': '',
    'description': """
    
OpenERP only allow resetting of Sequence only for document with Journal, i.e., Invoices, Voucher.

This module make sure that, if context['fiscalyear_id'] is not passed (normally for non-Journal doc like Sales Order),
use today to get the Fiscal Year.

Once Fiscal Year is available, then sequence can be retrieved as setup in Sequence's Fiscal Year tab.

Note:

* This will have problem, i.e., if user use back date or forward date, system will not know.
* To resolve it, one must ensure that context['fiscalyear_id'] is passed programmatically.

    """,
    'category': 'Accounting',
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['account'],
    'demo' : [],
    'data' : [
    ],
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
