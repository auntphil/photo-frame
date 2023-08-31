import os, sys
import sqlite3, json, time
from datetime import datetime
from PIL import Image
import secrets

# Opening JSON file
if os.path.isfile("settings.json"):
    with open('settings.json', 'r') as openfile:
        settings = json.load(openfile)
else:
    settings = {}
if len(sys.argv) > 1:
    scan_type = sys.argv[1]
else:
    scan_type = "normal"

# Replace these with your actual paths
max_size = 200  # Set your desired max size here

def create_thumbnail(source_path, max_size):
    image = Image.open(source_path)
    width, height = image.size

    aspect_ratio = width / height

    if width <= max_size and height <= max_size:
        thumbnail_width = width
        thumbnail_height = height
    elif aspect_ratio > 1:
        thumbnail_width = max_size
        thumbnail_height = max_size / aspect_ratio
    else:
        thumbnail_width = max_size * aspect_ratio
        thumbnail_height = max_size

    random_name = secrets.token_hex(8)  # Generate a random alphanumeric name
    random_name = random_name+str(time.time()).replace('.','')
    thumbnail_path = os.path.join(settings["thumbnail_dir"], random_name + '.jpg')

    thumbnail_image = image.resize((int(thumbnail_width), int(thumbnail_height)), Image.Resampling.LANCZOS)
    thumbnail_image.save(thumbnail_path, 'JPEG', quality=90)

    return random_name  # Return the generated name

def initialize_database():
    conn = sqlite3.connect(settings["db_path"])
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS pictures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT,
                    path TEXT,
                    make TEXT,
                    model TEXT,
                    date_taken TEXT,
                    year TEXT,
                    month TEXT,
                    thumbnail_path TEXT)''')
    
    cursor.execute('''CREATE TABLE IF NOT EXISTS albums (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    pictures_id TEXT,
                    shown TEXT)''')

    conn.commit()
    conn.close()

def is_image_in_database(filename):
    conn = sqlite3.connect(settings["db_path"])
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM pictures WHERE filename = ?", (filename,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def scan_folder(folder_path):
    initialize_database()

    conn = sqlite3.connect(settings["db_path"])
    cursor = conn.cursor()

    for root, dirs, files in os.walk(folder_path):
        if not any(os.path.isdir(os.path.join(root, dir)) for dir in dirs):
            modified_time = os.path.getmtime(root)
            current_time = datetime.now().timestamp()
            twenty_four_hours_ago = current_time - (24 * 60 * 60)

            if modified_time < twenty_four_hours_ago and scan_type != 'all' :
                print(f"Skipping folder '{root}' due to old modification time.")
                continue

        for file in files:
            file_path = os.path.join(root, file)
            extension = os.path.splitext(file)[1].lower()
            image_extensions = ['.jpg', '.jpeg', '.png']

            if extension in image_extensions and not is_image_in_database(file):
                try:
                    exif_data = Image.open(file_path)._getexif()

                    if exif_data is not None:
                        make = exif_data.get(271, '') if 271 in exif_data else ''
                        model = exif_data.get(272, '') if 272 in exif_data else ''
                        date_taken = exif_data.get(36867, None) if 36867 in exif_data else None
                    else:
                        make = ''
                        model = ''
                        year = None
                        month = None
                        date_taken = None


                    if date_taken:
                        date_taken = datetime.strptime(date_taken, "%Y:%m:%d %H:%M:%S").strftime('%Y-%m-%d %H:%M:%S')
                        year = date_taken[:4]
                        month = date_taken[5:7]

                    cursor.execute("INSERT INTO pictures (filename, path, make, model, date_taken, year, month) "
                                   "VALUES (?, ?, ?, ?, ?, ?, ?)",
                                   (file, file_path, make, model, date_taken, year, month))

                    conn.commit()

                    random_name = create_thumbnail(file_path, max_size)

                    cursor.execute("UPDATE pictures SET thumbnail_path = ? WHERE filename = ?",
                                   (random_name+".jpg", file))  # Update with random_name
                    conn.commit()

                except Exception as error:
                    issues = open("issues.txt","a")
                    issues.write(file_path + "\n")
                    issues.close() 
                    pass

    conn.close()

# Replace 'path_to_your_pictures_folder' with the actual path to your pictures folder
scan_folder(settings["pictures_folder"])
