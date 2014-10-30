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

from openerp.osv import osv, fields
from openerp import tools
import os


class addon_config(osv.osv):

    _name = "addon.config"
    _description = 'Addon Project Config'

    def _get_addons_path(self):
        return tools.config['addons_path'].split(',')

    def _get_addon_name(self, cursor, user_id, context=None):
        addons_path = self._get_addons_path()
        res = []
        for path in addons_path:
            addon_name = os.path.basename(path)
            if addon_name not in ('addons'):
                res.append((addon_name, addon_name))
        return res

    _columns = {
        'name': fields.selection(_get_addon_name, 'Addon Project', required=True,),
        'note': fields.text('Description'),
        'root_path': fields.char('Local Path', required=True, help="Define local path where you want to keep addons project folder"),
        'backup_path': fields.char('Temp Backup Path', required=False, help="Define folder where backup addons will be stores (temporary)"),
        'bzr_source': fields.char('Launchpad URL', required=True),
        'production_path': fields.char('Production Path', required=True, help="Production Path where the new updated addons will be copied to"),
    }
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'No duplication of addon project allowed!'),
    ]

    def onchange_addon(self, cr, uid, ids, addon, context=None):
        res = {}
        addons = []
        addons_path = self._get_addons_path()
        for path in addons_path:
            addons.append((os.path.basename(path), path))
        sel_path = next((v[1] for i, v in enumerate(addons) if v[0] == addon), None)
        res.update({'value': {'production_path': sel_path,
                                'root_path': '/tmp/' + addon,
                                'backup_path': '/tmp/' + addon + '_backup'}})
        return res

    def onchange_rootpath(self, cr, uid, ids, rootpath, context=None):
        return {'value': {'backup_path': rootpath + '_backup'}}

addon_config()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
