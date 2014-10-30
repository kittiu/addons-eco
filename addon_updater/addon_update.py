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
import time
from openerp.osv import osv, fields
from openerp.tools.translate import _
import os
import zipfile
from os.path import join as opj
from bzrlib.branch import Branch
import bzrlib.directory_service
import filecmp
import shutil
import logging
from openerp import pooler
import subprocess

_logger = logging.getLogger(__name__)


class addon_update(osv.osv):

    _name = "addon.update"
    _description = 'Addon Update Worksheet'
    _columns = {
        'name': fields.char('Name', size=64, required=True, readonly=True),
        'config_id': fields.many2one('addon.config', 'Addon Project', required=True, readonly=True, states={'draft': [('readonly', False)], 'check': [('readonly', False)]}),
        'update_lines': fields.one2many('addon.update.line', 'update_id', 'Update Lines', ondelete='cascade', readonly=True, states={'draft': [('readonly', False)], 'check': [('readonly', False)]}),
        'revision': fields.integer('Revision', readonly=True),
        'check_time': fields.datetime('Last Check', readonly=True),
        'state': fields.selection([('draft', 'Draft'),
                                   ('check', 'Checked'),
                                   ('ready', 'Ready'),
                                   ('done', 'Updated'),
                                   ('revert', 'Reverted'),
                                   ('cancel', 'Cancelled')], 'Status', required=True, readonly=True,
                help='* The \'Draft\' status is set when the work sheet in draft status. \
                    \n* The \'Checked\' status is set when project folder has been download and check for updated modules. \
                    \n* The \'Ready\' status is set when server has been restarted, and module are ready to upgrade. \
                    \n* The \'Updated\' status is set when things goes well, all selected module has been updated. \
                    \n* The \'Reverted\' status is set when things goes wrong, module will be set back to previous version. \
                    \n* The \'Cancelled\' status is set when a user cancel the work sheet.'),
        'note': fields.text('Notes'),
    }
    _defaults = {
        'state': 'draft',
        'name': '/'
    }
    _order = 'id desc'

    def create(self, cr, uid, vals, context=None):
        if vals.get('name', '/') == '/':
            vals['name'] = self.pool.get('ir.sequence').get(cr, uid, 'addon.update.sheet') or '/'
        config = self.pool.get('addon.config').browse(cr, uid, vals['config_id'])
        try:
            revisison, rev_id = Branch.open(config.root_path).last_revision_info()
            vals.update({'revision': revisison})
        except Exception, e:
            _logger.exception(str(e))
        return super(addon_update, self).create(cr, uid, vals, context=context)

    def _add_to_update_list(self, cr, uid, update_id, module_name, result, context=None):
        if context == None:
            context = {}
        if module_name == 'addon_updater':
            return False
        module_obj = self.pool.get('ir.module.module')
        update_line_obj = self.pool.get('addon.update.line')
        # From mod_name, find the module_id. But if not exist, change type = 'new'
        module_id = module_obj.search(cr, uid, [('name', '=', module_name)])
        if not module_id:
            line_dict = {
                'name': module_name,
                'update_id': update_id,
                'select': False,
                'module_id': False,
                'type': 'new',
                'state': 'new'
            }
        else:
            module = module_obj.browse(cr, uid, module_id[0], context=context)
            line_dict = {
                'update_id': update_id,
                'name': module.name,
                'select': False,
                'module_id': module.id,
                'type': result['type'],
                'changed_files': ', '.join(str(x) for x in result['changed_files']),
                'added_files': ', '.join(str(x) for x in result['added_files']),
                'removed_files': ', '.join(str(x) for x in result['removed_files']),
                'state': module.state,
            }
        return update_line_obj.create(cr, uid, line_dict, context=context)

    def _update_from_bzr(self, cr, uid, addon_id, context=None):
        addon_obj = self.pool.get('addon.config')
        addon_config = addon_obj.browse(cr, uid, addon_id, context)
        if addon_config:
            if addon_config.bzr_source:
                if not os.path.exists(addon_config.root_path):
                    # this helps us determine the full address of the remote branch
                    branchname = bzrlib.directory_service.directories.dereference(addon_config.bzr_source)
                    # let's now connect to the remote branch
                    remote_branch = Branch.open(branchname)
                    # download the branch
                    remote_branch.bzrdir.sprout(addon_config.root_path).open_branch()
                else:
                    b1 = Branch.open(addon_config.root_path)
                    b2 = Branch.open(addon_config.bzr_source)
                    b1.pull(b2)
                    subprocess.call(["bzr", "up", addon_config.root_path])
                    #b1.update()
        b1 = Branch.open(addon_config.root_path)
        revno, rev_id = b1.last_revision_info()
        return revno

    def _get_modules(self, cr, uid, path):
        """Returns the list of module names
        """
        def listdir(dir):
            def clean(name):
                name = os.path.basename(name)
                if name[-4:] == '.zip':
                    name = name[:-4]
                return name

            def is_really_module(name):
                manifest_name = opj(dir, name, '__openerp__.py')
                zipfile_name = opj(dir, name)
                return os.path.isfile(manifest_name) or zipfile.is_zipfile(zipfile_name)
            return map(clean, filter(is_really_module, os.listdir(dir)))

        plist = []
        plist.extend(listdir(path))
        return list(set(plist))

    def _compute_diff_files(self, dcmp, changed_files=[], added_files=[], removed_files=[], exclude=['pyc', 'jasper', '~1~', '~2~']):
        changed_files += filter(lambda a: a.split('.')[-1] not in exclude, dcmp.diff_files)
        added_files += filter(lambda a: a.split('.')[-1] not in exclude, dcmp.left_only)
        removed_files += filter(lambda a: a.split('.')[-1] not in exclude, dcmp.right_only)
        for sub_dcmp in dcmp.subdirs.values():
            self._compute_diff_files(sub_dcmp, changed_files, added_files,
                                   removed_files, exclude=exclude)

    def _compare_version(self, cr, uid, addon_config, module_name, context=None):
        if context == None:
            context = {}
        result = {'type': False,
                  'changed_files': [],
                  'added_files': [],
                  'removed_files': []
                  }
        sourcedir = os.path.join(addon_config.root_path, module_name)
        destdir = os.path.join(addon_config.production_path, module_name)
        if not os.path.isdir(sourcedir):
            return result
        if not os.path.isdir(destdir):
            result.update({'type': 'new'})
            return result
        # Compare folder
        changed_files, added_files, removed_files = [], [], []
        self._compute_diff_files(filecmp.dircmp(sourcedir, destdir), changed_files, added_files, removed_files)
        if changed_files + added_files + removed_files:
            result.update({'type': 'update',
                          'changed_files': changed_files,
                          'added_files': added_files,
                          'removed_files': removed_files})
        return result

    def action_cancel(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state': 'cancel'}, context=context)

    def action_check(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        # Delete lines first
        update_line_obj = self.pool.get('addon.update.line')
        line_ids = update_line_obj.search(cr, uid, [('update_id', 'in', ids)], context=context)
        update_line_obj.unlink(cr, uid, line_ids, context=context)
        # Update local branch
        for update in self.browse(cr, uid, ids):
            config = update.config_id
            # Delete backup directory, it will be created in action_sent
            if os.path.isdir(config.backup_path):
                shutil.rmtree(config.backup_path)
            try:
                revision = self._update_from_bzr(cr, uid, config.id, context)
            except Exception, e:
                raise osv.except_osv(_('Error Bazaar!'), str(e))
            # Compare each addon, if mismatch, add to list
            mod_names = self._get_modules(cr, uid, config.root_path)
            for mod_name in mod_names:
                result = self._compare_version(cr, uid, config, mod_name, context=context)  # Return type, list of diff files
                if result['type'] in ['new', 'update']:
                    self._add_to_update_list(cr, uid, update.id, mod_name, result, context=context)

            self.write(cr, uid, [update.id], {'state': 'check',
                                              'revision': revision,
                                              'check_time': time.strftime("%Y-%m-%d %H:%M:%S")}, context=context)
        return True

    def action_sent(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        for update in self.browse(cr, uid, ids):
            config = update.config_id
            # Create backup directory if not exists
            if not os.path.isdir(config.backup_path):
                os.mkdir(config.backup_path)
            # Get upgrade list and move folders
            install_list = []
            upgrade_list = []
            for update_line in update.update_lines:
                if update_line.select == True:
                    if update_line.type == 'new':
                        install_list.append(update_line.name)
                    if update_line.type == 'update':
                        upgrade_list.append(update_line.name)
                    sourcedir = os.path.join(config.root_path, update_line.name)
                    backupdir = os.path.join(config.backup_path, update_line.name)
                    destdir = os.path.join(config.production_path, update_line.name)
                    # Backup first
                    if os.path.isdir(destdir):
                        shutil.move(destdir, backupdir)
                    # Copy from local to production
                    shutil.copytree(sourcedir, destdir)

            if not install_list + upgrade_list:
                raise osv.except_osv(_('Warning!'), _('You have not select any addons to install/upgrade!'))

            self.write(cr, uid, [update.id], {'state': 'ready'}, context=context)

            # Update module list
            module_obj = self.pool.get('ir.module.module')
            module_obj.update_list(cr, uid,)

            # Update ir_module_module state
            to_install_ids = module_obj.search(cr, uid, [('name', 'in', install_list)])
            to_upgrade_ids = module_obj.search(cr, uid, [('name', 'in', upgrade_list)])
            module_obj.write(cr, uid, to_install_ids, {'state': 'to install'})
            module_obj.write(cr, uid, to_upgrade_ids, {'state': 'to upgrade'})

        return True

    def upgrade_module(self, cr, uid, ids, context=None):
        ir_module = self.pool.get('ir.module.module')

        # install/upgrade: double-check preconditions
        module_ids = ir_module.search(cr, uid, [('state', 'in', ['to upgrade', 'to install'])])
        if module_ids:
            cr.execute("""SELECT d.name FROM ir_module_module m
                                        JOIN ir_module_module_dependency d ON (m.id = d.module_id)
                                        LEFT JOIN ir_module_module m2 ON (d.name = m2.name)
                          WHERE m.id in %s and (m2.state IS NULL or m2.state IN %s)""",
                      (tuple(module_ids), ('uninstalled',)))
            unmet_packages = [x[0] for x in cr.fetchall()]
            if unmet_packages:
                raise osv.except_osv(_('Unmet Dependency!'),
                                     _('Following modules are not installed or unknown: %s') % ('\n\n' + '\n'.join(unmet_packages)))

            ir_module.download(cr, uid, module_ids, context=context)
            cr.commit()  # save before re-creating cursor below

        # Change state, if not specified, set to done.
        self.write(cr, uid, ids, {'state': context.get('to_state', False) or 'done'}, context=context)

        pooler.restart_pool(cr.dbname, update_module=True)
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
            'params': {'wait': True},
        }

    def action_revert(self, cr, uid, ids, context=None):
        if context == None:
            context = {}
        for update in self.browse(cr, uid, ids):
            config = update.config_id
            # If not backup path, raise error message
            if not os.path.isdir(config.backup_path):
                raise osv.except_osv(_('No backup!'),
                                     _('Backup folder %s does not exists. Revert fail!') % (config.backup_path,))
            # Get upgrade list and move folders
            install_list = []
            upgrade_list = []
            for update_line in update.update_lines:
                if update_line.select == True:
                    if update_line.type == 'new':
                        install_list.append(update_line.name)
                    if update_line.type == 'update':
                        upgrade_list.append(update_line.name)
                    backupdir = os.path.join(config.backup_path, update_line.name)
                    destdir = os.path.join(config.production_path, update_line.name)
                    # Copy from back from backup to production
                    if os.path.isdir(destdir):
                        shutil.rmtree(destdir)
                    if os.path.isdir(backupdir):
                        shutil.copytree(backupdir, destdir)
            self.write(cr, uid, [update.id], {'state': 'revert'}, context=context)

            # Update ir_module_module state
            module_obj = self.pool.get('ir.module.module')
            to_install_ids = module_obj.search(cr, uid, [('name', 'in', install_list)])
            to_upgrade_ids = module_obj.search(cr, uid, [('name', 'in', upgrade_list)])
            module_obj.write(cr, uid, to_install_ids, {'state': 'uninstalled'})  # to remove
            module_obj.unlink(cr, uid, to_install_ids)  # remove it.
            module_obj.write(cr, uid, to_upgrade_ids, {'state': 'to upgrade'})

        context.update({'to_state': 'revert'})
        self.upgrade_module(cr, uid, ids, context=context)
        return True

addon_update()


class addon_update_line(osv.osv):

    _name = "addon.update.line"
    _description = 'Addon Update Lines'
    _columns = {
        'update_id': fields.many2one('addon.update', 'Addon Update', required=True),
        'select': fields.boolean('Select', required=False),
        'module_id': fields.many2one('ir.module.module', 'Module', readonly=True, required=False),
        'name': fields.char('Technical Name', size=64, readonly=True, required=False),
        'type': fields.selection([
            ('new', 'New'),  # New state for package not available on production yet.
            ('update', 'Updated'),
        ], string='Type', readonly=True),
        'changed_files': fields.text('Changed Files', readonly=True),
        'added_files': fields.text('Added Files', readonly=True),
        'removed_files': fields.text('Removed Files', readonly=True),
        'state': fields.selection([
            ('new', 'New'),  # New state for package not available on production yet.
            ('uninstallable', 'Not Installable'),
            ('uninstalled', 'Not Installed'),
            ('installed', 'Installed'),
            ('to upgrade', 'To be upgraded'),
            ('to remove', 'To be removed'),
            ('to install', 'To be installed')
        ], string='Status', readonly=True, select=True),
    }
    _defaults = {
        'select': False,
    }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
