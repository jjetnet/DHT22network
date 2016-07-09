# DHT22network
wifi dht22 network

Note: there are many similar, and probably better implementation of similar concepts. My python coding in particular is far from optimal or elegant. Look around for better implementations...

Arduino code, eagle files and python script for a wifi based array of  humidity and temperature sensors sending data back periodcially to a server. The server generates plots and tables of current data displayed  on a webpage - on the local server, and/or on a remote web server through ftp. The sensors are meant for indoors reading, with outside temperature read from publicly available data from the Australian bureau of meteorology (data for australia only...).
The number of sensors is not really limited (Although past a certain number i'm sure bugs will emerge), and the server just adapts when a new sensor comes online. 

Each sensor can be battery operated for a number of months or even years depending on refresh settings and battery  - power consumption between readings is minimal. The server can send notificatinos to android and iphone phones using the free pushetta service/app (See www.pushetta.com) when outside temperature goes above or below user defined  thresholds - useful to remember to close windows, curtains or blinds.
Each sensor also reads its battery level, also displayed on the webpage as battery voltage with a crude red/green color coding depending on battery state.

Each sensor is based on an esp8266 - specifically i used a sparkfun esp8266 thing, which includes a convenient LiPo battery charger. Wifi network and key,  location name, and python server addess and port have to be adjusted in the arduino code before uploading. 

The server collecting data is a python script, which has to be run with sufficient priviledges to write onto the web server's  folder (eg /var/www/ ). All server data is defined in a separate configuration script (tempTCPconfig.py).

The current version of eagle file's pcb is awkward - components are on the copper side, which makes for some difficult soldering for some pins. 

The two jpeg files show an example of an assembled sensor module, outside its casing - as mentioned it is a tad awkward in this implementation. There's some hot glue that was requried to stabilise some of the copper wiring which had lifted off when accidentally pushing on the module... The top view with sensor rotated shows the two resistors that make up the voltage divider to bring the battery voltage within the range of the ESP8266 1V ADC, as well as the jumper that needs to be removed for programming (it connects XPD to DTR to enable  deep sleep - see https://learn.sparkfun.com/tutorials/esp8266-thing-hookup-guide/example-sketch-goodnight-thing-sleep-mode). The six open pins are a copy of the programming port of the esp8266 so that the the module can still be programmed.
This particular example uses a DHT22 module from df robotics, but a naked DHT22 can also be used.

For the battery to last months rather than hours or days, the power LED has to be disconnected, see https://learn.sparkfun.com/tutorials/esp8266-thing-hookup-guide/example-sketch-goodnight-thing-sleep-mode

For this example, I used a LiPo 1000mAh LiPo battery, which is of similar size to the esp8266 thing module.



Known issues:
- Arduino code:  If the server is down or a sensor module fails for any other reason to communicate with the server, it will keep trying continuously for ever - the battery will then run out rapidly.
- Python code: the server is not bug free. It is stable for days to weeks at a time, but occasionally stops if communications with sensor module isn't quite as expected. I may now have fixed this bug - but i won't be sure for another few weeks...
- safety: ftp passwords are in clear text in the python configuration file, and  so is the wifi password in the arduino code. MAke sure to protect those files...
