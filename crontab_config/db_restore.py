#!/usr/bin/python

import os
import sys
import glob
import base64
import subprocess
import time
import getopt
import psycopg2
import io
import StringIO

from PIL import Image
from PIL import ImageOps
from random import random
import base64

#Check parameter
def main(argv):
    iDBUser = ''
    oDBName = ''
    BacKDir = ''
    company_id = False
    id =False
    #init variable           
    date_backup = time.strftime('%Y%m%d_%H%M%S')
    
    #Logging
    command = "#Start:OE-->Restore DB at' %s" % (date_backup)    
    print command
    
    #Check parameter
    try:
        opts, args = getopt.getopt(argv,"hu:d:p:i:c:",["uDBUser=","dDBName=","pBacKDir","iID","cCompany",])
    except getopt.GetoptError:
        print "Invalid command db_restore.sh -u <DBUser> -d <DBName> -p <BacKDir> -i <iID> -c <cCompany>"
        #subprocess.call([command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'db_restore.py -u <DBUser> -d <DBName> -p <BacKDir> -i<iID> -c <cCompany>'
            sys.exit()
        elif opt in ("-u", "--iDBUser"):
            iDBUser = arg
        elif opt in ("-d", "--oDBName"):
                oDBName = arg
        elif opt in ("-p", "--pBacKDir"):
            BacKDir = arg
        
        elif opt in ("-i", "--iID"):
            id = arg
        
        elif opt in ("-c", "--cCompany"):
            company_id = arg
            
        else:
            print "Invalid command db_restore.sh -u <DBUser> -d <DBName> -p <BacKDir> -i<iID> -c <cCompany>" 
            #subprocess.call([command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            sys.exit(2) 
    
    if not os.path.exists(("%s/oe_db_last_bkup.txt" % (BacKDir))):
        print "The Database haven't backup"
    else:
        command = "var=$(cat %s/oe_db_last_bkup.txt);echo $var;" % (BacKDir)
        fileName = None
        process = subprocess.Popen([command], shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        process.poll()
        if process:
            fileName = process.communicate()[0]
            fileName = fileName.replace('\n','')
            
        if fileName and os.path.exists(fileName):
            
            
            #Restart PostgesSQL (new version use pid, do both)
            # < 9.2
            command = "psql -U postgres -d postgres --pset=format=unaligned -c \"SELECT pg_terminate_backend(procpid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '%s';\"" % (oDBName)
            print command
            subprocess.call([command],shell=True)
            process.wait()            
            # > 9.2
            command = "psql -U postgres -d postgres --pset=format=unaligned -c \"SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = '%s';\"" % (oDBName)
            print command
            subprocess.call([command],shell=True)
            process.wait()
            
            #Drop Database
            command = "dropdb -U %s %s" % (iDBUser,oDBName)
            print command
            subprocess.call([command], shell=True)
            process.wait()
            
            #Create Database
            command = "createdb -U %s %s " % (iDBUser,oDBName)
            print command
            subprocess.call([command],shell=True)
            
            #Backup Database
            command = "psql -U %s -d %s -f '%s' > %s/oe_db_restore.log " % (iDBUser,oDBName,fileName,BacKDir)
            print command
            process = subprocess.Popen([command],shell=True)
            process.wait()
            
            #Logging
            command = "Change the logo of company"
            print command
            change_company_logo(iDBUser, oDBName, BacKDir, id, company_id)
        else:
            print "Database dump file not found"
            
    #Logging
    command = "#End:OE-->Restore DB at' %s" % (date_backup)    
    print command
    
     
def change_company_logo(iDBUser, oDBName, BacKDir, id, company_id):
    con = None
    try:    
        con = psycopg2.connect(database=oDBName, user=iDBUser)      
        cur = con.cursor()
        
        cur.execute("SELECT (attfile) FROM crontab_config WHERE id in (%s);" % (id))
        data = cur.fetchone()
        if not (data and data[0]):
            print 'The logo file not found,Please import logo file before backup database!!!!!'
            return
        
        open('%s/tmp_logo' %(BacKDir), 'wb').write(base64.decodestring(data[0]))
        data = readImage('%s/tmp_logo' %(BacKDir))
        #data = readImage('%s/tt-addons/tt_config/logo_test.jpg' % (BacKDir))
        
        
        encoded_data = base64.b64encode(data) 
        
        size = (None, None)
        image =  image_resize_image(encoded_data)
        
        size = (128, 128)
        image_medium =  image_resize_image(encoded_data)
        
        size = (64, 64)
        image_small =  image_resize_image(encoded_data)
        
        size = (180, None)
        logo_web = image_resize_image(encoded_data, size)
        
        cur.execute("UPDATE res_partner SET image=%s,image_medium=%s,image_small=%s WHERE id=%s", (image,image_medium,image_small,company_id))    
        cur.execute("UPDATE res_company SET logo_web=%s WHERE id=%s", (logo_web,company_id))    
        
        con.commit()
    except psycopg2.DatabaseError, e:
        if con:
            con.rollback()
            
        print 'Error %s' % e   
         
    finally:
        if con:
            con.close()   
            
def readImage(imgfile):

    try:
        fin = open(imgfile, "rb")
        img = fin.read()
        return img
        
    except IOError, e:
        print "Error %d: %s" % (e.args[0],e.args[1])
        return False

    finally:        
        if fin:
            fin.close()

def image_resize_image(base64_source, size=(1024, 1024), encoding='base64', filetype='PNG', avoid_if_small=False):
    """ Function to resize an image. The image will be resized to the given
        size, while keeping the aspect ratios, and holes in the image will be
        filled with transparent background. The image will not be stretched if
        smaller than the expected size.
        Steps of the resizing:
        - Compute width and height if not specified.
        - if avoid_if_small: if both image sizes are smaller than the requested
          sizes, the original image is returned. This is used to avoid adding
          transparent content around images that we do not want to alter but
          just resize if too big. This is used for example when storing images
          in the 'image' field: we keep the original image, resized to a maximal
          size, without adding transparent content around it if smaller.
        - create a thumbnail of the source image through using the thumbnail
          function. Aspect ratios are preserved when using it. Note that if the
          source image is smaller than the expected size, it will not be
          extended, but filled to match the size.
        - create a transparent background that will hold the final image.
        - paste the thumbnail on the transparent background and center it.

        :param base64_source: base64-encoded version of the source
            image; if False, returns False
        :param size: 2-tuple(width, height). A None value for any of width or
            height mean an automatically computed value based respectivelly
            on height or width of the source image.
        :param encoding: the output encoding
        :param filetype: the output filetype
        :param avoid_if_small: do not resize if image height and width
            are smaller than the expected size.
    """
    if not base64_source:
        return False
    if size == (None, None):
        return base64_source
    image_stream = io.BytesIO(base64_source.decode(encoding))
    image = Image.open(image_stream)

    asked_width, asked_height = size
    if asked_width is None:
        asked_width = int(image.size[0] * (float(asked_height) / image.size[1]))
    if asked_height is None:
        asked_height = int(image.size[1] * (float(asked_width) / image.size[0]))
    size = asked_width, asked_height

    # check image size: do not create a thumbnail if avoiding smaller images
    if avoid_if_small and image.size[0] <= size[0] and image.size[1] <= size[1]:
        return base64_source

    if image.size <> size:
        # If you need faster thumbnails you may use use Image.NEAREST
        image = ImageOps.fit(image, size, Image.ANTIALIAS)
    if image.mode not in ["1", "L", "P", "RGB", "RGBA"]:
        image = image.convert("RGB")

    background_stream = StringIO.StringIO()
    image.save(background_stream, filetype)
    return background_stream.getvalue().encode(encoding)
              
if __name__ == "__main__":
    main(sys.argv[1:])