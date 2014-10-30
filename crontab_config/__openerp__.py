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
    'name' : 'Schedule Backup and Restore Database',
    'version' : '1.0',
    'author' : 'Ecosoft',
    'summary': 'Manage schedule of OS',
    'description': """
    
Schedule Backup and Restore Database (Crontab Configuration)
============================================================
This module will be work internally as command line interface (for Linux only) through linux crontab to backup and restore database.

1. Backup database <DB>

2. Restore as database <DB>_TEST

3. Update image (i.e., with test logo) to <DB>_TEST

Just install this module, and it should work. Setup schedule time as you need it.
Note: Itself, can also be used as scheduler instead of normal scheduler in OpenERP (you will see this backup and restore as one example).

Features
========
* Add, Modify, Delete schedule
* Direct process through command line interface

Setup Procedure
===============
Menu -> Setting/Technical/Scheduler/Crontab Configuration

Fields:

1. Crontab Name - name of crontab

2. Description - more information

3. Scheduling - crontab scheduling

    3.1 Minute: 0-59
    
    3.2 Hour: 0-23
    
    3.3 Day: 1-31
    
    3.4 Month: 1-12
    
    3.5 Weekday: 0-6, where 0 = Sunday
    
4. Execute Directory - OpenERP's root path to be used for log file, Temp File, DB Backup File and etc (depends on type of program) 

5. Command - command to run the program in command line interface pattern, require full path.

6. Active - when True, will create crontab scheduler in OS. When False will delete it.

7. Status

    7.1 Draft
    
    7.2 Confirmed
    
    7.3 Cancelled
    
8. Attach File - Additional files, to be used in process (optional)

Note: crontab scheduler will be created only when State = Confirmed and Active = True

Technical Detail
================

Backup Database Script:

    Use script, db_backup.py (written in Python)
    
        db_backup.py -u <DBUser> -d <DBName> -p <BacKDir>
        
    Example:
    
        '/home/buasri/workspace/ecosoft_official_addons/ecosoft-addons/crontab_config/db_backup.py' -u openerp -d TT -p '/home/buasri/workspace/openerp_tt'>>'/home/buasri/workspace/openerp_tt/crontab_oe.log'
    
    Process:
    
    1. Create backup database as <dbname>_dbbackup-YYYY-MM-DD hh:mm:ss.dmp
    
    2. Create file oe_db_last_bkup.txt to be used for restoration
    
    
Restore Database Process:
    
    Use script, db_restore.py (written in Python)
    
        db_restore.py -u <DBUser> -d <DBName> -p <BacKDir> 
        
    -i id of crontab in OpenERP, from table crontab_config
    -c id of Company in OpenERP, from table res_company
    
    Example:
    
        '/home/buasri/workspace/ecosoft_official_addons/ecosoft-addons/crontab_config/db_restore.py' -u openerp -d TT_TEST -p '/home/buasri/workspace/openerp_tt'>>'/home/buasri/workspace/openerp_tt/crontab_oe.log'
    
    Process
    
    1. Disconnect database to be restored
    
    2. Delete database
    
    3. Create new database
    
    4. Restore it.
    
    5. Read attached logo file
    
    6. Resize logo file
    
    7. Update logo file

    """,
    'category': 'Tools',
    'sequence': 7,
    'website' : 'http://www.ecosoft.co.th',
    'images' : [],
    'depends' : [],
    'demo' : [],
    'data' : [
        'crontab_config_view.xml',
        'crontab_config_data.xml',
    ],
    'test' : [
    ],
    'auto_install': False,
    'application': True,
    'installable': True,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
