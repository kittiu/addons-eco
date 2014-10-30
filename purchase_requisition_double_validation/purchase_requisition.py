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

class purchase_requisition(osv.osv):

    _inherit = "purchase.requisition"
    
    _columns = {
        'name': fields.char('Requisition Reference', size=32, required=False, readonly=True),
        'state': fields.selection([('draft','New'),
                                   ('in_purchase','Sent to Purchase'), # Additional Step
                                   ('in_progress','Sent to Suppliers'),('cancel','Cancelled'),('done','Purchase Done')],
            'Status', track_visibility='onchange', required=True)
    }
    
    _defaults = {
        'name': lambda obj, cr, uid, context: '/',
    }    
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('name','/')=='/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.requisition') or '/'
        return super(purchase_requisition, self).create(cr, uid, vals, context=context)
        
    def tender_in_purchase(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'state':'in_purchase'} ,context=context)   
      
purchase_requisition()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
