import tkinter as tk
import os, requests, time, json
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
running = True
ChangePhoto = True

# Opening JSON file
if os.path.isfile("settings.json"):
    with open('settings.json', 'r') as openfile:
        settings = json.load(openfile)
else:
    settings = {}

def settings_open(event):
    window.configure(bg="black", cursor="arrow")
    frame_picture.pack_forget()
    frame_settings.pack()

def settings_close():
    window.configure(bg="black", cursor="none")
    frame_settings.pack_forget()
    frame_picture.pack(expand=True)

def save_settings():
    settings["pfid"] = pfid.get()
    settings["burl"] = burl.get()
    settings["delay"] = delay.get()
    # Serializing json
    json_object = json.dumps(settings, indent=4)

    # Writing JSON
    with open("settings.json", "w") as outfile:
        outfile.write(json_object)

    settings_close()

def exit_program():
    global running
    running = False

###
#Settings Frame
frame_settings = tk.Frame()

title_settings = tk.Label(master=frame_settings,  text="Settings", font=(22))
title_settings.pack()

#Get Photo Frame ID
title_pfid = tk.Label(master=frame_settings,  text="Photo Frame ID")

pfid = tk.StringVar()
entry_pfid = tk.Entry(
    master=frame_settings, 
    textvariable = pfid
)
if "pfid" in settings:
    entry_pfid.insert(0,settings["pfid"])
title_pfid.pack()
entry_pfid.pack()

#Get Photo Base URL
title_burl = tk.Label(master=frame_settings,  text="Base URL")

burl = tk.StringVar()
entry_burl = tk.Entry(
    master=frame_settings, 
    textvariable = burl
)
if "burl" in settings:
    entry_burl.insert(0,settings["burl"])
title_burl.pack()
entry_burl.pack()

#Get Photo Rotation
title_delay = tk.Label(master=frame_settings,  text="Rotation Delay")

delay = tk.StringVar()
entry_delay = tk.Entry(
    master=frame_settings, 
    textvariable = delay
)
if "delay" in settings:
    entry_delay.insert(0,settings["delay"])
title_delay.pack()
entry_delay.pack()

#Save Button
btn_save = tk.Button(
    master=frame_settings,  
    text="Save & Close",
    command=save_settings
)
btn_save.pack()

btn_close = tk.Button(
    master=frame_settings,
    text="Cancel",
    command=settings_close
)
btn_close.pack()

btn_exit = tk.Button(
    master=frame_settings,
    text="Exit Program",
    command=exit_program
)
btn_exit.pack()

frame_picture = tk.Frame(bg="black")
frame_picture.pack(fill="both", expand=True)

while running:

    #Display Image

    if ChangePhoto:

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
        photos[lastDownload].bind("<Button-1>", settings_open)
        photos[lastDownload].pack(expand=True)

        if previousPhoto in photos:
            #Removing the photo from the screen and dictionary
            photos[previousPhoto].destroy()
            del photos[previousPhoto]

        ChangePhoto = False

    ###Loading Next Image
    if not ChangePhoto:
        #Checking if the last image update was more than 15 seconds ago
        if time.time() - lastDownload > float(settings['delay']):
            #Checking to see if the previous image is in the dictionary

            #setting the timestamp for the last loaded image
            previousPhoto = lastDownload
            lastDownload = time.time()


            #Downloading the new image
            try:
                with open('image.jpg', 'wb') as handle:
                    response = requests.get("http://{}/image.php?frame={}".format(settings["burl"],settings["pfid"]), stream=True)
                    if not response.ok:
                        print(response)
                
                    for block in response.iter_content(1024):
                        if not block:
                            break
                
                        handle.write(block)
                ChangePhoto = True
            except:
                print('Error')
                
        window.update_idletasks()
        window.update()
