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
    'name' : 'HR Expense VAT Info',
    'version' : '1.0',
    'author' : 'Ecosoft',
    'summary': 'Additional VAT info',
    'description': """
    
This module extend HR Expense, allowing user to add more VAT detail to each Invoice Line.

This is useful when we pay VAT through other supplier, e.g., Expense to an employee, but VAT paid to customs department.
    
    """,
    'category': 'Human Resources',
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['hr_expense', 'web_m2x_options'],
    'demo' : [],
    'data' : ['wizard/expense_vatinfo_view.xml',
              'hr_expense_view.xml',
              'account_view.xml'
    ],
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
