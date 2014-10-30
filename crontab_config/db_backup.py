#!/usr/bin/python

import os
import sys
import glob
import base64
import subprocess
import xmlrpclib
import time
import getopt

def main(argv):
    iDBUser = ''
    oDBName = ''
    BacKDir = ''
    
    #init variable           
    date_backup = time.strftime('%Y%m%d_%H%M%S')
    
    #Logging
    command = "#Start:OE-->Backup DB at %s" % (date_backup)    
    print command
    
    #Check parameter
    try:
        opts, args = getopt.getopt(argv,"hu:d:p:",["uDBUser=","dDBName=","pBacKDir"])
    except getopt.GetoptError:
        print "Invalid command db_backup.sh -u <DBUser> -d <DBName> -p <BacKDir>"    
        #subprocess.call([command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'db_backup.py -u <DBUser> -d <DBName> -p <BacKDir>'
            sys.exit()
        elif opt in ("-u", "--iDBUser"):
            iDBUser = arg
        elif opt in ("-d", "--oDBName"):
                oDBName = arg
        elif opt in ("-p", "--pBacKDir"):
            BacKDir = arg
        else:
            print "Invalid command db_backup.sh -u <DBUser> -d <DBName> -p <BacKDir>"
            #subprocess.call([command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            sys.exit(2) 
    
    #Backup Database
    command = "pg_dump -U %s -f '%s/%s_dbbackup-%s.dmp' %s" %  (iDBUser, BacKDir, oDBName, date_backup ,oDBName)
    print command
    subprocess.call([command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    
    #Write file name to file for next restore database
    command = "echo '%s/%s_dbbackup-%s.dmp' > %s/oe_db_last_bkup.txt" % (BacKDir, oDBName, date_backup, BacKDir)
    print command
    subprocess.call([command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    
    #Logging
    command = "#End:OE-->Backup DB at %s" % (date_backup)	
    print command
    
if __name__ == "__main__":
    main(sys.argv[1:])


