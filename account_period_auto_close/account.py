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
import logging
from openerp.osv import osv, fields
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class account_period(osv.osv):

    _inherit = 'account.period'

    def process_account_period_close(self, cr, uid, days=0, context=None):
        if context is None:
            context = {}        
        today = fields.date.context_today(self, cr, uid, context=context)
        date_today = datetime.strptime(today, '%Y-%m-%d')
        date = (date_today - relativedelta(days=days)).strftime('%Y-%m-%d')    
        period_ids = self.search(cr, uid, [('date_stop', '<', date)], context=context)
        mode = 'done'
        try:
            for id in period_ids:
                account_move_ids = self.pool.get('account.move').search(cr, uid, [('period_id', '=', id), ('state', '=', "draft")], context=context)
                if account_move_ids:
                    _logger.exception("Failed processing period close. Make sure all journal are posted")    
                cr.execute('update account_journal_period set state=%s where period_id=%s', (mode, id))
                cr.execute('update account_period set state=%s where id=%s', (mode, id))
        except Exception:
            _logger.exception("Failed processing account posting")

account_period()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
