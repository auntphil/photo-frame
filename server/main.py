import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageFile
import psycopg2
import sys
from io import BytesIO
from dotenv import load_dotenv

# Set up error handling and enable CORS
from flask import Flask, send_file

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
        attempt = 1

        while True:
            # Execute the SQL query to retrieve a random image path and year
            cursor.execute("SELECT exif.\"assetId\", DATE_PART('month', exif.\"dateTimeOriginal\"::DATE), DATE_PART('year', exif.\"dateTimeOriginal\"::DATE), assets.\"originalPath\", assets.\"type\" FROM exif JOIN assets ON assets.\"id\" = exif.\"assetId\" WHERE DATE_PART('month', exif.\"dateTimeOriginal\"::DATE) = DATE_PART('month', current_date::DATE) AND assets.\"type\" = 'IMAGE' ORDER BY RANDOM() LIMIT 1")
            row = cursor.fetchone()


            if row:
                #Write found asset to log
                if container:
                    f = open("/logs/db.log","a")
                else:
                    f = open("db.log","a")
                f.write(f"Found assetId: {row[4]} - {row[0]}\n")
                f.close()

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
                #TODO Mark Image as Shown

                # Create a BytesIO object to store the image
                img_io = BytesIO()

                # Save the composite image to the BytesIO object
                background.save(img_io, format="JPEG")
                img_io.seek(0)

                # Return the image as a response
                return send_file(img_io, mimetype='image/jpeg')
            else:
                if attempt == 1:
                    #TODO Set all shown Images to null
                    attempt+=1
                else:
                    return "No image found", 404
        
    except Exception as e:
        exception_type, exception_object, exception_traceback = sys.exc_info()
        line_number = exception_traceback.tb_lineno
        print(f"Error on line {str(line_number)}: {str(e)}")
        return str(e), 500       

    finally:
        conn.close()


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)