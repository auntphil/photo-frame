import tkinter as tk
import subprocess
import os
from functools import partial

#Create Window
window = tk.Tk()
network = {
    "ssid":"",
    "password":""
}
passwordInput = tk.StringVar()

def select_ssid(ssid):
    network["ssid"] = ssid

def connect():
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
title_passphrase.pack()
entry_passphrase = tk.Entry(
    master=frame_settings, 
    textvariable = passwordInput
)
entry_passphrase.pack()


#Save Button
btn_save = tk.Button(
    master=frame_settings,  
    text="Connect",
    command=connect
)
btn_save.pack()

frame_settings.pack()

#Show Window Loop
window.mainloop()
