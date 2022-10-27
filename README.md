# PiFrame
## Overview
An internet connected photo frame using Synology Photos as the backend server.

## Client
*Python*

The client equests a new photo from the server with its ID and screen resolution. Once the image is received the new image is displayed on the screen. 

### Settings
- WiFi
- Frame ID

### Future Settings
- Image Change Interval
- Turn Off Screen Schedule
- Request Schedule

## Server
*PHP*

Using the provided client ID a photo is pulled randomly from the Synology Photos Database. A new photo is generated with the resolution provided by the client. If the image does not fit the resolution, a blurred version of the image is placed behind the image to fill all space. 

### Settings
- Database Connection
- Photos Root Path
- Album ID per Client

### Future Plans
- Track shown photos in DB to ensure no duplicates
