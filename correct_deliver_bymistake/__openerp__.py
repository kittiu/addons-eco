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
    'name' : 'Correct Delivery By Mistake',
    'version' : '1.0',
    'author' : 'Ecosoft',
    'summary': 'Allow user to correct the problematic delivery.',
    'description': """
    
OpenERP do not allow user to directly cancel DO in status Delivered. In case of mistake keyed in, if user want to
cancel it, he/she have to start from cancel invoice, make the return, and re-deliver it again.

This addons helps doing the same thing in one click. This enhancement will add a new button in Delivery Order screen called,
"Correct Mistake Delivery" for the DO marked as Delivered. By clicking this button, generally the system will,

# Create incoming shipment (to even out with the DO) and Confirm it.
# Create a new Delivery Order to replace the mistake document and set to draft.

User will be able to come back re-deliver it.

    """,
    'category': 'Warehouse Management',
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : ['stock'],
    'demo' : [],
    'data' : ['stock_view.xml',
              'wizard/correct_delivery_bymistake_view.xml'],
    'test' : [],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
