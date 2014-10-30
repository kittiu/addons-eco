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
import subprocess
import os
import tempfile

class crontab_config(osv.osv):
    _loging = os.path.realpath(tempfile.tempdir) + "/crontab_oe.log"
    _root = os.path.realpath(tempfile.tempdir)
        
    _name = "crontab.config"
    _columns = {
        'name': fields.char('Crontab Name', size=128, required=True,),
        'note': fields.text('Description'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('done','Confirmed'),
            ('cancel', 'Cancelled'),
            ], 'Status', readonly=True,
             select=True),
        'minute':fields.char('Minute', required=True),
        'hour':fields.char('Hour', required=True),
        'day':fields.char('Day of Month', required=True),
        'month':fields.char('Month', required=True),
        'week':fields.char('Day of Week', required=True),
        'command':fields.char('Command', required=True),
        'working_path':fields.char('Execute Directory'),
        'active':fields.boolean('Active'),
        'last_exec':fields.datetime('Last Manually Execute',readonly=True),
        'attfile': fields.binary('Attach File'),
        'system_flag':fields.boolean('System',readoly=True) 
        
    }
    
    _defaults = {
        'minute': '*',
        'hour': '*',
        'day': '*',
        'month': '*',
        'week': '*',
        'active':True,
        'state':"draft",
        'system_flag':False,
        'working_path':os.path.realpath(tempfile.tempdir),
        }
    
    def get_command(self,cr, user, ids, context=None):
        commands = dict.fromkeys(ids, {})
        cron_recs = self.read(cr, user, ids, ['id','name','command','working_path','active','minute','hour','day','month','week','state'], context=context)
        for cron_rec in cron_recs:
            commands[cron_rec['id']].update({'command':"echo '#Start:OE-->"+ (cron_rec.get('name',False) or "")+"';" + 
                                            (cron_rec.get('command',False) or ""),
                                            'name':(cron_rec.get('name',False) or ""),
                                            'active':(cron_rec.get('active',False)) and (cron_rec.get('state',False)=='done'),
                                            'schedule':(cron_rec.get('minute',False) or "") + " " + (cron_rec.get('hour',False) or "")  + " " +
                                                        (cron_rec.get('day',False) or "")  + " " + (cron_rec.get('month',False) or "")  + " " +
                                                        (cron_rec.get('week',False) or "") ,
                                            'working_path':cron_rec.get('working_path',False)
                                    })  
        return commands
    
    def write(self, cr, uid, ids, vals, context=None):           
        res = super(crontab_config, self).write(cr, uid, ids, vals, context=context)            
        self.generate_crontab(cr, uid, ids, context)
      
        return res
    
    def create(self, cr, uid, vals, context=None):
        if vals.get('working_path',False) :
            if len(vals.get('working_path',""))>0:
                working_path = vals.get('working_path',"")
                working_path_len = len(working_path)
                if not working_path.endswith("/",working_path_len,working_path_len):
                    vals['working_path']=vals.get('working_path',"")+"/"
        res_id = super(crontab_config, self).create(cr, uid, vals, context=context)
        
        self.generate_crontab(cr, uid, [res_id], context)
        
        return res_id 
    
    def generate_crontab(self,cr, user, ids, context=None):        
        
        #Get Command from database                        
        commands = self.get_command(cr, user, ids, context)
        
        for id in ids:
            
            working_path = commands[id].get('working_path',self._root)
            
            #Create temporary. 
            tmpfn1 = os.tempnam(working_path,'oe1')
            tmpfn2 = os.tempnam(working_path,'oe2')
            
            #Extract Crontab to temporary file
            #Note,make sure you have permission to access directory and directory exists.
            p = subprocess.call(["crontab -l > "+ tmpfn1], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        
            #Search with "#Start:OE-->" + name crontrab  and delete it.
            subprocess.call(["sed '/#Start:OE-->"+ (commands[id].get('name',False) or "") +"/d' "+  tmpfn1 +" > "+ tmpfn2], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            
            if  commands[id].get('active',False):#Active and state is done
                #Append new command into temporary file
                fo = open(tmpfn2, "a")
                fo.write( commands[id].get('schedule', "") + " " + commands[id].get('command', "")+ ">>" + working_path +"/crontab_oe.log\n");
                fo.close()
                
            #Generate the Crontab from file.
            p = subprocess.call(["crontab "+ tmpfn2], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        
            #Delete temporary file
            p = subprocess.call(["rm "+ tmpfn1], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            p = subprocess.call(["rm "+ tmpfn2], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
           
        return True
    
    def action_button_confirm(self,cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'done'}, context)
        return True
    
    def action_button_cancel(self,cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'cancel'}, context)
        return True
    
    def action_button_draft(self,cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft'}, context)
        return True
    
    def action_button_execute(self,cr, uid, ids, context=None):
        commands = self.get_command(cr, uid, ids, context)
         
        for id in ids:
            p = subprocess.call([commands[id].get('command',"")+ ">>" + commands[id].get('working_path',self._root) +"/crontab_oe.log\n"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            self.write(cr, uid, ids, {'last_exec':time.strftime('%Y-%m-%d %H:%M:%S')}, context)
 
        return True
    
    def setup_dbbackup(self, cr, uid, ids=None, context=None):
        _curr_path = os.path.dirname(__file__)
        #id = obj_data.get_object_reference(cr, uid, 'crontab_config','backup_database')[1]
        command = "'%s/db_backup.py' -u openerp -d %s -p '%s'" % (_curr_path, cr.dbname, self._root)
        values = {'command':command}
        
        self.write(cr, uid, ids, values, context=None)
    
    def setup_dbrestore(self, cr, uid, ids=None, context=None):
        
        _curr_path = os.path.dirname(__file__)
        
        strid = "%s"% ','.join(str(x) for x in ids)
        
        #id = obj_data.get_object_reference(cr, uid, 'crontab_config','backup_database')[1]
        command = "'%s/db_restore.py' -u openerp -d %s -p '%s' -i %s -c 1 " % (_curr_path, cr.dbname + "_TEST", self._root, strid)
        values = {'command':command}
        
        self.write(cr, uid, ids, values, context=None)
        
    def unlink(self, cr, uid, ids, context=None):        
        stat = self.read(cr, uid, ids, ['system_flag'], context=context)
        for t in stat:
            if t['system_flag']:
                raise osv.except_osv(_('Warning!'), _("This is system command, it can't delete."))          
            else:
                #Delete crontab
                self.write(cr, uid, ids, {'state':'cancel'}, context)
                #Delete 
                super(crontab_config, self).unlink(cr, uid, [t['id']], context=context)
        return True
    
crontab_config()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
