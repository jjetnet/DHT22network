# file name radix - all file names will start with this
fradix='climate'
# local web page path
wpath='/var/www/'
#  file for error&message logging (note at this stage some is also output to stdout for debugging - run with &> logfile redirect
errfilename='tempTCPerr.log'

# listening port for sensor data - needs to be the same in ino file
TCPport=8888

# webpage of json file with weather data, from australian bureau of meteorology - 
# outside temperature and humidity are read from there
# adapt to closest weather station - list can be found on www.bom.gov.au
# obviously only works in Australia... but wouldn't be to hard ot adapt to other countries
# The following is for inner west of sydney
BOMpath='http://www.bom.gov.au/fwo/IDN60901/IDN60901.94766.json'

# for pushetta notification - define API_KEY and the channel name
# set API_KEY to '' if not needed.
# see www.pushetta.com on how to get this
API_KEY=''
CHANNEL_NAME='MyClimateChannel'
# Pushetta alerts are sent when temperatures exceed AlertHighT or go below AlertLowT - defined in celsius here:
AlertHighT=27
AlertLowT=22


#  remote ftp server to copy files onto
# useful if you don't have a static ip and want to access the webpage from outside your local network - eg ftp to your internet provider's personal webapges
# password is in plain text (!)
# if no copying to ftp server is required, set ftpserver=''
ftpserver='yourftpservername'
ftplogin='yourftplogin'
ftppwd='yourftppassword'
