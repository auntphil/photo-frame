import tkinter as tk
import os, requests, time, json, sys
from PIL import Image, ImageTk, ImageFile, ImageOps
ImageFile.LOAD_TRUNCATED_IMAGES = True


#Create Window
window = tk.Tk()
w, h = window.winfo_screenwidth(), window.winfo_screenheight()
window.geometry("%dx%d+0+0" % (w, h))
window.attributes('-fullscreen', True)
window.configure(bg="black", cursor="none")


previousPhoto = 0
lastDownload = time.time()
photos = {}
firstRun = True

# Opening JSON file
if os.path.isfile("settings.json"):
    with open('settings.json', 'r') as openfile:
        settings = json.load(openfile)
else:
    settings = {}


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

    #Display Image
    try:
        raw = Image.open("image.jpg")
    except:
        raw = Image.open("no-image.jpg")


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

    ChangePhoto = False

    ###Loading Next Image
    #Checking if the last image update was more than 15 seconds ago
    #Checking to see if the previous image is in the dictionary

    #setting the timestamp for the last loaded image
    previousPhoto = lastDownload
    lastDownload = time.time()

    window.update_idletasks()
    window.update()

    #Downloading the new image
    try:
        with open('image.jpg', 'wb') as handle:
            response = requests.get("http://{}/generate_image".format(settings["server"]), stream=True)
            if not response.ok:
                print(response)
        
            for block in response.iter_content(1024):
                if not block:
                    break
        
                handle.write(block)
        ChangePhoto = True
    except:
        print('Error')
            

    while time.time() - lastDownload < float(settings['delay']):
        continue
