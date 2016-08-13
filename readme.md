# DHT22network
wifi dht22 network

Note: there are many similar, and probably better implementation of
similar concepts. My python coding in particular is far from optimal
or elegant. This implementation has mobile notifications, plots and water partial pressure
calculations which distinguishes it from others, but if you don't need
this look around for better implementations.

## Overview:

Arduino code, eagle files and python script for a wifi based array of
humidity and temperature sensors sending data back periodically to a
server. The server generates plots and tables of current data
displayed on a webpage - on the local server, and/or on a remote web
server through ftp. The sensors are meant for indoors reading, with
outside temperature read from publicly available data from the
Australian bureau of meteorology (data for australia only...).  The
number of sensors is not really limited (Although past a certain
number i'm sure bugs will emerge), and the server just adapts when a
new sensor comes online.

Each sensor can be battery operated for a number of months or even
years depending on refresh settings and battery - power consumption
between readings is minimal. The server can send notificatinos to
android and iphone phones using the free pushetta service/app (See
www.pushetta.com) when outside temperature goes above or below user
defined thresholds - useful to remember to close windows, curtains or
blinds.  Each sensor also reads its battery level, also displayed on
the webpage as battery voltage with a crude red/green color coding
depending on battery state.

For example of what the webpage looks like see
webpageexample.png. Data displayed includes temperature, relative
humidity and the water partial pressure - the latter is absolute
rather than relative, and is more informative if you want to control
the flow of humidity between two rooms or between outdoows and
indoors: if two rooms are at different temperatures but identical
relative humidity, there will still be a net flow of water vapour from
the space with the higher partial water pressure to the room with the
lower one. If you want to keep humidity down indoors in summer, this
is the quantity to watch to close/open windows, rather than the
relative humidity.


Each sensor is based on an esp8266 - specifically i used a sparkfun
esp8266 thing, which includes a convenient LiPo battery charger. Wifi
network and key, location name, and python server addess and port have
to be adjusted in the arduino code before uploading.

The server collecting data is a python script, which has to be run
with sufficient priviledges to write onto the web server's folder (eg
`/var/www/` ). All server data is defined in a separate configuration
script (tempTCPconfig.py). I run mine on a raspbery pi.

## Hardware

A minimal version can be assembled without PCB, using a ESP8266 thing the DHT22 sensor, and a jumper wire between XPD and DTR (which needs to be removed for programming). To add battery monitoring, two resistors straight onto the ESP8266 thing between Vin, Gnd and Analog in forming a ~1/5 voltage divider is enough. (220k between Vin and Analog in, 56k between gnd and Analog in) (see eagle schematic for details).

Alternatively, a PCB can be used to clean up the circuit: 

The current version of the pcb (eagle file) is awkward - components are on
the copper side, which makes for some difficult soldering for some
pins.

The two jpeg files show an example of an assembled sensor module using PCB,
outside its casing - as mentioned it is a tad awkward in this
implementation. There's some hot glue that was requried to stabilise
some of the copper wiring which had lifted off when accidentally
pushing on the module... The top view with sensor rotated shows the
two resistors that make up the voltage divider to bring the battery
voltage within the range of the ESP8266 1V ADC, as well as the jumper
that needs to be removed for programming (it connects XPD to DTR to
enable deep sleep - see [sparkfun's sleepmode tutorial](https://learn.sparkfun.com/tutorials/esp8266-thing-hookup-guide/example-sketch-goodnight-thing-sleep-mode). The
six open pins are a copy of the programming port of the esp8266 so
that the the module can still be programmed.  This particular example
uses a DHT22 module from df robotics, but a naked DHT22 can also be
used.

For the battery to last months rather than hours or days, the power LED has to be disconnected, see [sparkfun's sleepmode tutorial](https://learn.sparkfun.com/tutorials/esp8266-thing-hookup-guide/example-sketch-goodnight-thing-sleep-mode)

For this example, I used a LiPo 1000mAh LiPo battery, which is of similar size to the esp8266 thing module.

## Installation:
The python-based server requires a number of libraries,
some of which are not in the default python install for raspberry
pi (if you chose to run the server on a raspberry pi). In particular pushetta, matplotlib and a recent version of numpy
are requried, which you may have to install from source depending on
your distribution/package manager. I'm not sure which version is
required, but it runs with numpy 1.11.0, matplotlib 1.1.1rc2, pushetta
1.0.15.
Notifications require a free account with the pushetta service. For this, and how to install the pushetta python package, see [the puhsetta help page](http://pushetta.com/pushetta-docs).
Feel free to contact me if you have any trouble installing or running the server.


## Updates:
### 13/08/16
* increased stability: exception handling for ftp and pushetta. The python server seems very stable now.
* remover redundant, unused plot routine.

### 30/07/16
* fixed stability issues when remote ftp server or bureau of meteorology websites are not responsive.
* fixed plotting - no more error messages when insufficient data points, and limited long-term plot to last 30 days for readability


## Known issues:
* Arduino code:  If the server is down or a sensor module fails for any other reason to communicate with the server, it will keep trying continuously for ever - the battery will then run out rapidly.
* safety: ftp passwords are in clear text in the python configuration file, and  so is the wifi password in the arduino code. MAke sure to protect those files. TCP communications between sensor module and server are unencrypted.
