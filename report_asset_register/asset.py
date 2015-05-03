# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from openerp.osv import fields,osv
from openerp.tools.translate import _

class account_asset_asset(osv.osv):
    _inherit = 'account.asset.asset'
    _columns = {
        'product_desc': fields.char('Product Description'),
        'asset_location': fields.char('Asset Location', required=False),
    }
    
    def create(self, cr, uid, vals, context=None):
        stock_move_obj = self.pool.get('stock.move')
        if vals.get('move_id', False) and not vals.get('product_desc'):
            move = stock_move_obj.browse(cr, uid, vals['move_id'], context=context)
            vals['product_desc'] = move.name
        return super(account_asset_asset, self).create(cr, uid, vals, context=context)
    
account_asset_asset()

class account_asset_depreciation_line(osv.osv):
    _inherit = 'account.asset.depreciation.line'
    _columns = {
        'effective_date': fields.related('move_id', 'date', type='date', string='Effective Date', store=True),
        'effective_period_id': fields.related('move_id', 'period_id', type='many2one', relation='account.period', string='Effective Period', store=True), 
    }

account_asset_depreciation_line()
