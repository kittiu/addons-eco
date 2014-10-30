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
    'name': 'Post Account Rounding',
    'version': '1.0',
    'author': 'Assign unbalanced amount to rounding account',
    'summary': '',
    'description': """

In some very rare case, posting of invoices be not balance. 
As last alternative, We put this unbalanced amount into rounding account on account posting.

Note: This module is considered finished. But I do not have chance to test it, as not enough case.

    """,
    'category': 'Accounting & Finance',
    'sequence': 100,
    'website': 'http://www.ecosoft.co.th',
    'images': [],
    'depends': ['account', 'account_anglo_saxon'],
    'demo': [],
    'data': ['res_config_view.xml'
    ],
    'test': [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
