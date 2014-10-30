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
    'name': 'Bzr Module Updater',
    'version': '1.0',
    'author': 'Ecosoft',
    'summary': 'Upgrade the updated modules from Launchpad',
    'description': """
Bazaar Module Updater
=====================

The reason for this add on is to better maintain the project that we are working on. Once the new/updated addon is available, administrator should know exactly what they are.

How user use this module will be different from normal upgrade procedure. We will use a work sheet in each time of upgrade. This will help keeping the history of upgrade along the way.

This will work for extra addon project, not core addon (web, addons, server) 

This module has 2 windows
-------------------------

Menu: Addon Updater located in Setting > Module

* Addon Projects -- is a master data for addon project configuration, i.e., path, launchpad url.
* Addon Update Sheet -- is where each update will be execute. User will check what is changed in each project then select which module to upgrade.

Working Steps
--------------

Given we have an addon project registered launchpad, i.e., mycustom-addons. And that we have this in our addon path as we start OpenERP.

1) Register this project in "Addon Projects", i.e.,
---------------------------------------------------

* Addon Project:    mycustom-addons
* Launchpad URL:    https://launchpad.net/mycompany-openerp/mycustom-addons
* Local Path:    /tmp/mycustom-addons
* Temp Backup Path:    /tmp/mycustom-addons_backup
* Production Path:    /opt/openerp_production/mycustom-addons
    
2) Do the upgrade with Addon Update Sheet
-----------------------------------------

Following is the step of execution,

1. Create new Addon Update Sheet
2. Select prjoect to work on and save it. If the local folder already have the project pulled last time, it will show current revision.
3. Click [Check Updated Modules], this step will access launchpad and if new project, it will do the braching. Otherwise, it will just pull and update branch. Note that, this step can take very long time depend on size of addon project.
4. Status will change from Draft to Checked, if there are updated or new addons, it will be listed in the table. At this step, everything occur in local folder not yet touch on projection folder.
5. Select addons to upgrade then click [Send to Production]. All the selected addons will be send to production folder, with the backup in backup folder. OpenERP server will be restarted to recompile the code. Now it will be Ready.
6. Once Ready, the Upgrade must be executed, otherwise, the code and the data in OpenERP may not be insynce and cause serious problem.
7. If anything went wrong or decide not to upgrade, click [Revert] to set things back to previous working system.

    """,
    'category': 'Tools',
    'website': 'http://www.ecosoft.co.th',
    'images': [],
    'depends': ['base'],
    'demo': [],
    'data': [
             'addon_config_view.xml',
             'addon_update_view.xml',
             'addon_update_sequence.xml',
    ],
    'test': [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
