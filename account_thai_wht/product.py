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

from openerp.osv import fields, osv

# class product_product(osv.osv):
#     _inherit = "product.product"
# 
#     _columns = {
#         'use_suspend_account': fields.boolean('Use Suspend Tax Account', help='By default, product of type service will use suspend tax account. This can be overwritten for special case.'),
#     }
    
#     Lek think we do not need to link Suspend with Service. So just comment out, jut in case.
#     def onchange_type(self, cr, uid, ids, type, context=None):
#         res = {}
#         if type == 'service':
#             res['use_suspend_account'] = True
#         else:
#             res['use_suspend_account'] = False
#         return {'value': res}
    
# product_product()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
