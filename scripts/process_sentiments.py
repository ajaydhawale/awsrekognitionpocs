#!/usr/bin/python
import sys
import cgi, os, os.path
import cgitb; cgitb.enable()
import ConfigParser
import Image
import boto3
from datetime import datetime
from os import environ
from ast import literal_eval

Config = ConfigParser.ConfigParser()
Config.read("/var/www/html/config.ini")

IMAGES_SUBDIR = '/images/'
UPLOADED_IMAGES_SUBDIR = '/uploaded/'
THUMBNAILS_SUBDIR = '/thumbnails/'

SENTIMENTS_DIR = Config.get('Defaults', 'SENTIMENTS_DIRECTORY')
IMAGES_DIR = SENTIMENTS_DIR + IMAGES_SUBDIR

if not os.path.exists(SENTIMENTS_DIR):
    os.makedirs(SENTIMENTS_DIR)

if not os.path.exists(IMAGES_DIR):
    os.makedirs(IMAGES_DIR)

if not os.path.exists(IMAGES_DIR + UPLOADED_IMAGES_SUBDIR):
    os.makedirs(IMAGES_DIR + UPLOADED_IMAGES_SUBDIR)

if not os.path.exists(IMAGES_DIR + THUMBNAILS_SUBDIR):
    os.makedirs(IMAGES_DIR + THUMBNAILS_SUBDIR)

THUMBNAIL_SIZE = literal_eval(Config.get('Defaults', 'THUMBNAIL_SIZE'))
HOST = Config.get('Defaults', 'HOST')

os.environ['AWS_SHARED_CREDENTIALS_FILE'] = Config.get('Defaults', 'AWS_SHARED_CREDENTIALS_FILE')
os.environ['AWS_SHARED_CONFIG_FILE'] = Config.get('Defaults', 'AWS_SHARED_CONFIG_FILE')

timestamp = (datetime.utcnow()-datetime.fromtimestamp(0)).total_seconds()
autorefreshmesg = 'The page shall autorefresh in 10 seconds'

print """Content-Type: text/html\n\n
         <html><head><meta http-equiv=\"refresh\" content=\"10; URL=http://%s/sentiments.html\">
         <body>""" %(HOST)

form = cgi.FieldStorage()

# Get filename here.
fileitem = form['filename']

# Test if the file was uploaded
if fileitem.filename:
    # Strip leading path from file name to avoid directory traversal attacks
    fname = os.path.basename(fileitem.filename)
    # The file is actually saved by adding prefix <timestamp>_
    afname = str(timestamp) + "_" + fname
    # Full path of the image
    imgfile = IMAGES_DIR + UPLOADED_IMAGES_SUBDIR + afname
    open(imgfile, 'wb').write(fileitem.file.read())

    # Thumbnail path
    tnfile = IMAGES_DIR + THUMBNAILS_SUBDIR + afname
    # Start getting thumbnail
    tn = Image.open(imgfile)
    # Only if incoming file is in supported format
    #if tn.format in ('JPEG', 'PNG'):
    if tn.format in ('JPEG'):
        if hasattr(tn, '_getexif'):
            orientation = 0x0112
            exif = tn._getexif()
            if exif is not None:
                orientation = exif[orientation]
                rotations = {
                    3: Image.ROTATE_180,
                    6: Image.ROTATE_270,
                    8: Image.ROTATE_90
                }
                if orientation in rotations:
                    tn = tn.transpose(rotations[orientation])

        tn.thumbnail(THUMBNAIL_SIZE, Image.ANTIALIAS)
        tn.save(tnfile)

        # Connect to AWS Rekognition to detect faces and get confidence score
        # If confidence score > 60.00 we say it's a happy sentiment else unhappy
        client = boto3.client('rekognition', region_name='us-east-1')

        happylist = open(IMAGES_DIR + "happy.list", "a+")
        unhappylist = open(IMAGES_DIR + "unhappy.list", "a+")

        #imagefile = THUMBNAILS_SUBDIR + name
        response = client.detect_faces(Image={'Bytes': open(tnfile, "rb").read()}, Attributes = ['ALL',])
        if len(response['FaceDetails']) > 0:
            for resp in response['FaceDetails'][0]['Emotions']:
                if resp['Type'] == "HAPPY":
                    if resp['Confidence'] > 60.00:
                        happylist.write(afname +"\n")
                    else:
                        unhappylist.write(afname + "\n")
            message = 'The file "' + fname + '" was uploaded successfully. ' + autorefreshmesg
        else:
            message = 'Could not detect any face in the uploaded file "' + fname + '". ' + autorefreshmesg
       
        happylist.close()
        unhappylist.close()
    else:
        message = 'Cannot process your file. Only JPEG format is supported. ' + autorefreshmesg
else:
    message = 'No file was uploaded. '+ autorefreshmesg
   

happynames = ""
unhappynames = ""

if os.path.exists(IMAGES_DIR + "happy.list"):
    happylist = open(IMAGES_DIR + "happy.list", "r")
    happynames = happylist.read().splitlines()
    happylist.close()

if os.path.exists(IMAGES_DIR + "unhappy.list"):
    unhappylist = open(IMAGES_DIR + "unhappy.list", "r")
    unhappynames = unhappylist.read().splitlines()
    unhappylist.close()

# Create sentiments page
sentimentspage = open(SENTIMENTS_DIR + "sentiments.html", "w")
sentimentspage.write("<html><head><meta http-equiv=\"refresh\" content=\"10; URL=http://%s/sentiments.html\"><body><BR><BR>" %(HOST))
sentimentspage.write("<h3>Happy Sentiments</h3>")
for hname in happynames :
    sentimentspage.write("<img src=http://%s/%s/%s>" %(HOST, IMAGES_SUBDIR + THUMBNAILS_SUBDIR, hname))
sentimentspage.write("<h3>Un Happy Sentiments</h3>")
for uhname in unhappynames :
    sentimentspage.write("<img src=http://%s/%s/%s>" %(HOST, IMAGES_SUBDIR + THUMBNAILS_SUBDIR, uhname))
sentimentspage.write("</body></html>")
sentimentspage.close()

# Print message and sentiments page as response. The page gets auto refreshed after 10 seconds
print "<p>%s</p><BR><BR>" %(message)
print "<h3>Happy Sentiments</h3>"
for hname in happynames :
    print "<img src=http://%s/%s/%s>" %(HOST, IMAGES_SUBDIR + THUMBNAILS_SUBDIR, hname)
print "<BR><BR>"
print "<h3>Un happy Sentiments</h3>"
for uhname in unhappynames :
    print "<img src=http://%s/%s/%s>" %(HOST, IMAGES_SUBDIR + THUMBNAILS_SUBDIR, uhname)
print "</body></html>"
