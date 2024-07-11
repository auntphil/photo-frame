import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageFile
from pillow_heif import register_heif_opener
import psycopg2
import sys
from io import BytesIO
from dotenv import load_dotenv
import datetime

# Set up error handling and enable CORS
from flask import Flask, send_file

register_heif_opener()
ImageFile.LOAD_TRUNCATED_IMAGES = True

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable caching

load_dotenv()

if 'DB_HOSTNAME' not in os.environ:
    print('No Hostname')
    exit()


# Define your database connection parameters
host = os.environ['DB_HOSTNAME']
port = int(os.environ['DB_PORT'])
user = os.environ['DB_USERNAME']
password = os.environ['DB_PASSWORD']
database = os.environ['DB_DATABASE_NAME']

#Attempt DB Connection
try:
    # Connect to the Postgres database
    conn = psycopg2.connect(
        user=user,
        password=password,
        host=host,
        port=port,
        database=database
    )
    cursor = conn.cursor()
    print("Database Connected")
    conn.close()
except Exception as e:
    print(f"Error: {str(e)}")
    print(host)
    exit()

if "AM_I_IN_A_DOCKER_CONTAINER" in os.environ:
    container = True
else:
    container = False

if "LOGGING" in os.environ:
    logging = int(os.environ['LOGGING'])
else: 
    logging = 3

if "FRAME_PATH" in os.environ:
    photoPath = os.environ['FRAME_PATH']

if "FRAME_WIDTH" in os.environ:
    frameWidth = int(os.environ['FRAME_WIDTH'])
else:
    frameWidth = 1366
    
if "FRAME_HEIGHT" in os.environ:
    frameHeight = int(os.environ['FRAME_HEIGHT'])
else:
    frameHeight = 768

def saveViewed(id):
    if container:
        file = open("/config/viewed.log","a")
    else:
        file = open("viewed.log","a")
    file.write(f"{id}\n")
    file.close()

def readViewed():
    try:
        if container:
            file = open("/config/viewed.log")
        else:
            file = open("viewed.log")
        viewed = file.read().splitlines()
        file.close()
    except Exception as e:
        logger(3, f"readViewed: {e}")
        viewed = []
    return viewed



def logger(level, message):
    #Get Date
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S.%f')
    message = f"{formatted_time} - {message}\n"
    #Debug
    if logging == 7:
        if container:
            log = open("/logs/debug.log","a")
        else:
            log = open("debug.log","a")
        log.write(message)
    #Warning
    if logging >= level and level == 4:
        if container:
            log = open("/logs/warning.log","a")
        else:
            log = open("warning.log","a")
        log.write(message)
    #Error
    if logging >= level and level == 3:
        if container:
            log = open("/logs/error.log","a")
        else:
            log = open("error.log","a")
        log.write(message)
        log.close()

# Function to correct image orientation
def autorotate(image):
    try:
        exif = image._getexif()
        if exif is not None:
            orientation = exif.get(0x0112)
            if orientation is not None:
                if orientation == 3:
                    image = image.rotate(180, expand=True)
                elif orientation == 6:
                    image = image.rotate(270, expand=True)
                elif orientation == 8:
                    image = image.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass
    return image

# Define the route for image generation
@app.route('/generate_image', methods=['GET'])
def generate_image():
    global whereStatement, frameHeight, frameWidth, photoPath
    try:
        # Connect to the Postgres database
        conn = psycopg2.connect(
            user=user,
            password=password,
            host=host,
            port=port,
            database=database
        )
        cursor = conn.cursor()
        firstAttempt = True
        viewed = readViewed()

        while True:
            #Generate a searchable string for Database query
            viewedStr = "'" + "', '".join(viewed) + "'"
            # Execute the SQL query to retrieve a random image path and year
            cursor.execute(f"SELECT exif.\"assetId\", DATE_PART('month', exif.\"dateTimeOriginal\"::DATE), DATE_PART('year', exif.\"dateTimeOriginal\"::DATE), assets.\"originalPath\", assets.\"type\" FROM exif JOIN assets ON assets.\"id\" = exif.\"assetId\" WHERE DATE_PART('month', exif.\"dateTimeOriginal\"::DATE) = DATE_PART('month', current_date::DATE) AND assets.\"type\" = 'IMAGE'  AND assets.\"isArchived\" = FALSE AND assets.\"deletedAt\" IS NULL AND assets.\"id\"::text NOT IN ({viewedStr})  ORDER BY RANDOM() LIMIT 1")
            row = cursor.fetchone()


            if row:
                #Write found asset to log
                logger(7, f"DEBUG: Found assetId {row[0]}")

                id = row[0]
                year = int(row[2])
                path = row[3].replace("upload/","")

                # Open the image and correct orientation
                foreground = autorotate(Image.open(photoPath+path))
                background = autorotate(Image.open(photoPath+path))

                # Get image size
                width, height = background.size

                # Calculate frame and image ratios
                image_ratio = width / height

                # Background Blur
                resize_width = frameWidth * 1.3
                resize_height = (resize_width / image_ratio) * 1.3

                #Finding Top Left Corner
                if resize_width != frameWidth:
                    tl_x = int((resize_width - frameWidth) / 2)
                else:
                    tl_x = 0

                if resize_height != frameHeight:
                    tl_y = int((resize_height - frameHeight) / 2)
                else:
                    tl_y = 0

                #background = background.resize((int(width * 0.15), int(height * 0.15)))
                background = background.filter(ImageFilter.GaussianBlur(25))
                background = background.resize((int(resize_width), int(resize_height)))
                background = background.crop((tl_x, tl_y, tl_x + frameWidth, tl_y + frameHeight))

                # Foreground Image
                if width > height:
                    resize_height = frameHeight
                    resize_width = int(frameHeight * image_ratio)
                else:
                    resize_height = frameHeight
                    resize_width = int(frameHeight * image_ratio)

                foreground = foreground.resize((resize_width, resize_height))

                # Combine Images
                if resize_width != frameWidth:
                    tl_x = int((frameWidth - resize_width) / 2)
                else:
                    tl_x = 0

                draw = ImageDraw.Draw(foreground)
                font = ImageFont.truetype("PermanentMarker-Regular.ttf", 35)
                draw.text((25, resize_height - 60), str(year), fill="black", font=font, stroke_width = 2, stroke_fill=(255,255,255))

                Image.Image.paste(background, foreground, (tl_x, 0))
        
                #Mark Image as Shown
                viewed.append(id)
                saveViewed(id)

                # Create a BytesIO object to store the image
                img_io = BytesIO()

                # Save the composite image to the BytesIO object
                background.save(img_io, format="JPEG")
                img_io.seek(0)

                #Resetting tracker
                firstAttempt = True

                # Return the image as a response
                return send_file(img_io, mimetype='image/jpeg')
            else:
                if firstAttempt:
                    logger(7,"Clearing Viewed List")

                    #Clear list
                    viewed.clear()

                    #Removed Viewed Log
                    if container:
                        os.remove("/config/viewed.log")
                    else:
                        os.remove("viewed.log")

                    firstAttempt = False
                else:
                    logger(4, "WARNING: No Image Found")
                    return "No image found", 404
        
    except Exception as e:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        line_number = exception_traceback.tb_lineno

        logger(3, f"ERROR on line {str(line_number)}: {str(e)}")

        return str(e), 500       

    finally:
        conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
