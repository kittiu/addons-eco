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
    'name' : 'Double Validation on Purchase Requisition',
    'version' : '0.1',
    'category': 'Purchase Management',
    'images' : [],
    'depends' : ['purchase_requisition'],
    'author' : 'Ecosoft',
    'description': """
Double-validation for purchase requisition.
==========================================

The objective of this module is to allow splitting of process between requester and approving manager.
This module adding new state "Send to Purchase", in which state, only manager can - Send to supplier, Create Quotation, Purchase Done
For PR Groups,
* User: Can only click Sent to Purchase
* Manager: Can do everything with the Purchase Requisition
    """,
    'website': 'http://www.ecosoft.co.th',
    'data': [
        'purchase_requisition_view.xml',
    ],
    'test': [
    ],
    'demo': [],
    'installable': True,
    'auto_install': False
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
