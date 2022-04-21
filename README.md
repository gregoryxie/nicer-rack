# nicer-rack

hopefully nicer and not worser
View [NiceRack](nicerack.mit.edu)

## Installation

After downloading the repo, install all necessary depencies by running in the root folder:
`pip3 install -r requirements.txt`

## Accessing Raspberry Pi

On your own machine, SSH into the Raspi: `ssh putz@18.18.248.96`

Ask for the password if you need it. From here, you can access the Raspberry Pi's Software Configuration Tool (settings): `sudo raspi-config`

**Don't mess around with the settings.** But, if you want to update the Raspi, navigate to `8 Update` using the arrow keys, and hit enter to update. When it's done, tab your way to `Finish`, then hit enter.

You can navigate the filesystem the way any computer works. Some potentially useful commands:
* `sudo reboot`
* `sudo shutdown -h now` will safely shut down the Raspi
* `wget [url]` will download the file at the given URL to the Raspi, in whatever your working directory is.