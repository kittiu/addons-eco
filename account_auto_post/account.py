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
from openerp.osv import osv

_logger = logging.getLogger(__name__)


class account_move(osv.osv):

    _inherit = 'account.move'

    def process_account_post(self, cr, uid, journal_ids=None, exclude_journal_ids=None, context=None):
        if context is None:
            context = {}
        if not journal_ids and not exclude_journal_ids:
            filters = [('state', '=', 'draft')]
        else:
            filters = [('state', '=', 'draft')]
            if journal_ids:
                filters.append(('journal_id', 'in', journal_ids))
            if exclude_journal_ids:
                filters.append(('journal_id', 'not in', exclude_journal_ids))            
        ids_move = self.search(cr, uid, filters, context=context)
        try:
            if ids_move:
                self.button_validate(cr, uid, ids_move, context=context)
        except Exception:
            _logger.exception("Failed processing account posting")

account_move()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
