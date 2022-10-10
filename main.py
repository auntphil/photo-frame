import tkinter as tk
import subprocess, os, requests, time, json
from functools import partial
from PIL import Image, ImageTk, ImageFile
ImageFile.LOAD_TRUNCATED_IMAGES = True


#Create Window
window = tk.Tk()
w, h = window.winfo_screenwidth(), window.winfo_screenheight()
window.geometry("%dx%d+0+0" % (w, h))
window.attributes('-fullscreen', True)
window.configure(bg="black")

network = {
    "ssid":"",
    "password":""
}
passwordInput = tk.StringVar()
lastDownload = 0
photos = {}
running = True

# Opening JSON file
if os.path.isfile("settings.json"):
    with open('settings.json', 'r') as openfile:
        settings = json.load(openfile)
else:
    settings = {}

def download_next():
    global lastDownload
    #Checking if the last image update was more than 15 seconds ago
    if time.time() - lastDownload > 15:

        #Checking to see if the previous image is in the dictionary
        if lastDownload in photos:
            #Removing the photo from the screen and dictionary
            photos[lastDownload].destroy()
            del photos[lastDownload]

        #setting the timestamp for the last loaded image
        lastDownload = time.time()

        goodUrl = True

        #Downloading the new image
        try:
            with open('image.jpg', 'wb') as handle:
                response = requests.get("http://{}/{}/image.jpg".format(settings["burl"],settings["pfid"]), stream=True)
            
                if not response.ok:
                    print(response)
                    goodUrl = False
            
                for block in response.iter_content(1024):
                    if not block:
                        break
            
                    handle.write(block)
        except:
            goodUrl = False
            
        #loading the new image to the screen
        loadImage(goodUrl)

def loadImage(goodUrl):
    global lastDownload, w, h
    if os.path.isfile("image.jpg") and goodUrl:
            try:
                raw = Image.open("image.jpg")
            except:
                raw = Image.open("no-image.jpg")
    else:
        raw = Image.open("no-image.jpg")


    #Getting Image Sizes
    imgWidth, imgHeight = raw.size
    ratio = min(w/imgWidth, h/imgHeight)
    imgWidth = int(imgWidth*ratio)
    imgHeight = int(imgHeight*ratio)
    raw = raw.resize((imgWidth, imgHeight), Image.Resampling.LANCZOS)
    image = ImageTk.PhotoImage(raw)

    #Creating a new photo
    #Saving to the Dictionary
    #Showing on Screen
    photos[lastDownload] = tk.Label(master=frame_picture, image=image, bg="black")
    photos[lastDownload].image = image
    photos[lastDownload].place(relx = 0.5, rely = 0.5, anchor="c")
    photos[lastDownload].bind("<Button-1>", settings_open)
    photos[lastDownload].pack(expand=True)

def select_ssid(ssid):
    network["ssid"] = ssid

def settings_open(event):
    frame_picture.pack_forget()
    frame_settings.pack()

def settings_close():
    frame_settings.pack_forget()
    frame_picture.pack(expand=True)

def save_settings():
    settings["pfid"] = pfid.get()
    settings["burl"] = burl.get()
    # Serializing json
    json_object = json.dumps(settings, indent=4)

    # Writing JSON
    with open("settings.json", "w") as outfile:
        outfile.write(json_object)

    if network['ssid'] != "":

        network["password"] = passwordInput.get()
        config = """<?xml version=\"1.0\"?>
<WLANProfile xmlns="http://www.microsoft.com/networking/WLAN/profile/v1">
    <name>"""+network['ssid']+"""</name>
    <SSIDConfig>
        <SSID>
            <name>"""+network['ssid']+"""</name>
        </SSID>
    </SSIDConfig>
    <connectionType>ESS</connectionType>
    <connectionMode>auto</connectionMode>
    <MSM>
        <security>
            <authEncryption>
                <authentication>WPA2PSK</authentication>
                <encryption>AES</encryption>
                <useOneX>false</useOneX>
            </authEncryption>
            <sharedKey>
                <keyType>passPhrase</keyType>
                <protected>false</protected>
                <keyMaterial>"""+network['password']+"""</keyMaterial>
            </sharedKey>
        </security>
    </MSM>
</WLANProfile>"""
        with open(network['ssid']+".xml",'w') as file:
            file.write(config)
        subprocess.run("netsh wlan add profile filename=\""+network['ssid']+".xml\"")
        subprocess.run("netsh wlan connect name=\""+network['ssid']+"\"")
        os.remove(network['ssid']+".xml")
    settings_close()

def exit_program():
    global running
    running = False

###
#Settings Frame
frame_settings = tk.Frame()

title_settings = tk.Label(master=frame_settings,  text="Settings", font=(22))
title_settings.pack()

#Title
title_ssid = tk.Label(master=frame_settings,  text="Available Networks")
title_ssid.pack()


#Get List of SSIDs
r = subprocess.run(["netsh", "wlan", "show", "network"], capture_output=True, text=True).stdout
ls = r.split("\n")
ssids = [v.strip() for k,v in (p.split(':') for p in ls if 'SSID' in p)]

#Create a list of Buttons for SSIDs
for ssid in ssids:
    if ssid != "":
        btn_ssid = tk.Button(
            master=frame_settings,  
            text=ssid,
            command=partial(
                select_ssid, ssid
            )
        )
        btn_ssid.pack()

#Get Network Password
title_passphrase = tk.Label(master=frame_settings,  text="Network Password")
entry_passphrase = tk.Entry(
    master=frame_settings, 
    textvariable = passwordInput
)
title_passphrase.pack()
entry_passphrase.pack()

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
#Show Window Loop
    download_next()
    window.update_idletasks()
    window.update()
