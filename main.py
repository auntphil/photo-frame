import tkinter as tk
import subprocess

#Create Window
window = tk.Tk()

def select_ssid(ssid):
    print(ssid)

#Title
title_ssid = tk.Label(text="Available Networks")
title_ssid.pack()


#Get List of SSIDs
r = subprocess.run(["netsh", "wlan", "show", "network"], capture_output=True, text=True).stdout
ls = r.split("\n")
ssids = [v.strip() for k,v in (p.split(':') for p in ls if 'SSID' in p)]

#Create a list of Buttons for SSIDs
for ssid in ssids:
    btn_ssid = tk.Button(
        text=ssid,
        command=select_ssid
    )
    btn_ssid.pack()

#Title
title_passphrase = tk.Label(text="Network Password")
title_passphrase.pack()
entry_passphrase = tk.Entry()
entry_passphrase.pack()

passphrase = entry_passphrase.get()

#Show Window Loop
window.mainloop()