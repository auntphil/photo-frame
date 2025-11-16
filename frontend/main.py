import tkinter as tk
import os, requests, time, json, sys
from PIL import Image, ImageTk, ImageFile, ImageOps
import datetime, time
ImageFile.LOAD_TRUNCATED_IMAGES = True

# Opening JSON file
if os.path.isfile("settings.json"):
    with open('settings.json', 'r') as openfile:
        settings = json.load(openfile)
else:
    settings = {}

def logger(level, message):
    #Get Date
    current_time = datetime.datetime.now()
    formatted_time = current_time.strftime('%Y-%m-%d %H:%M:%S.%f')
    #Debug
    if settings["log_level"] == 7:
        log = open("debug.log","a")
        log.write(f"{formatted_time} - Debug: {message}\n")
        log.close()
    #Warning
    if settings["log_level"] >= level and level == 4:
        log = open("warning.log","a")
        log.write(f"{formatted_time} - Warning: {message}\n")
        log.close()
    #Error
    if settings["log_level"] >= level and level == 3:
        log = open("error.log","a")
        log.write(f"{formatted_time} - Error: {message}\n")
        log.close()
        

#Create Window
window = tk.Tk()
w, h = window.winfo_screenwidth(), window.winfo_screenheight()
window.geometry("%dx%d+0+0" % (w, h))
window.attributes('-fullscreen', settings["fullscreen"])
window.configure(bg="black", cursor="none")


previousPhoto = 0
lastDownload = time.time()
photos = {}
firstRun = True



###
#Settings Frame
frame_settings = tk.Frame()

title_settings = tk.Label(master=frame_settings,  text="Settings", font=(22))
title_settings.pack()

#Get Photo Base URL
title_server = tk.Label(master=frame_settings,  text="Base URL")


frame_picture = tk.Frame(bg="black")
frame_picture.pack(fill="both", expand=True)

while True:

    #TODO Check if piframe is within a time window to run
    #Display Image
    try:
        raw = Image.open("image.jpg")
    except:
        logger(4,"No Image Found")
        raw = Image.open("no-image.jpg")

    try:
        image = ImageOps.exif_transpose(raw)
        image = ImageTk.PhotoImage(image)

        #Creating a new photo
        #Saving to the Dictionary
        #Showing on Screen
        photos[lastDownload] = tk.Label(master=frame_picture, image=image, bg="black")
        photos[lastDownload].image = image
        photos[lastDownload].place(relx = 0.5, rely = 0.5, anchor="c")
        photos[lastDownload].pack(expand=True)

        if previousPhoto in photos:
            #Removing the photo from the screen and dictionary
            photos[previousPhoto].destroy()
            del photos[previousPhoto]

        ###Loading Next Image
        #Checking if the last image update was more than 15 seconds ago
        #Checking to see if the previous image is in the dictionary

        #setting the timestamp for the last loaded image
        previousPhoto = lastDownload
        lastDownload = time.time()

        window.update_idletasks()
        window.update()
    except Exception as e:
        logger(3, e)

    #Setting Error State
    error = True

    #Downloading the new image. Loops while there is an error
    try:
        with open('temp.jpg', 'wb') as handle:
            logger(7,"Requesting New Image")
            response = requests.get("http://{}/generate_image".format(settings["server"]), stream=True)
            if not response.ok:
                #The Response is not 200 or Good
                logger(4, response)
                logger(7, "Server Response: Not Ok")
                error = True
            else:
                logger(7, "Server Response: Ok")
                error = False
        
            for block in response.iter_content(1024):
                if not block:
                    break
        
                handle.write(block)

        #If Not Error Update Image File
        if not error:
            if os.path.isfile('image.jpg'):
                os.remove('image.jpg')
            os.rename('temp.jpg','image.jpg')
    except Exception as e:
        logger(3, e)

            
    while time.time() - lastDownload < float(settings['delay']):
        continue
