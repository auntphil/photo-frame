#!/usr/bin/python
#postgres:///synofoto?host=/run/postgresql
from http.client import NETWORK_AUTHENTICATION_REQUIRED
import psycopg2, random, time, json, os, sys
from PIL import Image, ImageFilter, ExifTags

#Photo Interval in Seconds
f = open('settings.json')
settings = json.load(f)
pfid = str(sys.argv[1])

def changePhoto():
    try:
        if(os.path.exists(settings['photoframe_root']+pfid+'/next.jpg')):
            os.rename(settings['photoframe_root']+pfid+'/next.jpg',settings['photoframe_root']+pfid+'/current.jpg')

        conn = psycopg2.connect(
            database=settings["database"],
            user=settings["user"],
            password=settings["password"],
            host=settings["host"],
            port=settings["port"]
        )
    except Exception as e :
        print(e)
        exit()

    newPhoto = True

    while newPhoto:
        #Accessing database and retrieving all photos in a specific album
        cur = conn.cursor()
        cur.execute("select unit.filename, folder.name from unit inner join many_item_has_many_normal_album on many_item_has_many_normal_album.id_item = unit.id_item inner join folder on unit.id_folder = folder.id where many_item_has_many_normal_album.id_normal_album = " + settings['album'])
        rows = cur.fetchall()
        count = len(rows)

        #Getting random photo from album
        photoRow = rows[random.randint(0,count-1)]


        if not photoRow[0].endswith('mp4'):
            newPhoto = False



    #Creating path to photo
    path = "{}{}/{}".format(settings['photo_root'],photoRow[1],photoRow[0])

    try:
        #Open original Image
        background = Image.open(path)
        #background = Image.open("/volume1/homes/xandrew/Photos/2021/11 - November/2021-10-01 05.31.43.jpg")

        #Get Proper Rotation of Photo
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation]=='Orientation':
                break
        exif = background._getexif()
        if exif[orientation] == 3:
            background=background.rotate(180, expand=True)
        elif exif[orientation] == 6:
            background=background.rotate(270, expand=True)
        elif exif[orientation] == 8:
            background=background.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # cases: image don't have getexif
        pass

    #photo = Image.open(path)
    photo = background.copy()


    #Image Size
    background_width = int(sys.argv[2])
    background_height = int(sys.argv[3])
    background_ratio = background_height/background_width

    #Checking if Background is Portrait
    if background_width < background_height:
        #Get larger height and width for zoom blur
        temp_width=int(((background_height*0.2)+background_height)/background_ratio)
        temp_height=int((background_height*0.2)+background_height)

        #Resize image
        background = background.resize((temp_width,temp_height))



    #crop image 
    bk_width = int(sys.argv[2])
    bk_height = int(bk_width / 1.777)

    left=0
    top=(bk_height - bk_height )/2
    right=bk_width
    bottom=(bk_height + bk_height )/2
    background = background.crop((left, top, right, bottom))

    #Create blurred version of image
    background = background.filter(ImageFilter.GaussianBlur(radius=65))

    #Paste photo
    photo_width, photo_height = photo.size
    photo_ratio = photo_height/photo_width
    photo = photo.resize((int(bk_height/photo_ratio),bk_height))
    photo_width, photo_height = photo.size
    background.paste(photo, (int((bk_width - photo_width)/2),0))

    #If current does not exist, save photo as current and next.
    if(not os.path.exists(settings['photoframe_root'] + pfid +'/current.jpg')):
        background.save(settings['photoframe_root'] + pfid  + "/current.jpg")
        
    background.save(settings['photoframe_root'] + pfid + "/next.jpg")

    #Closing db connection
    conn.close()

def main():
    changePhoto()


if __name__ == "__main__":
    main()