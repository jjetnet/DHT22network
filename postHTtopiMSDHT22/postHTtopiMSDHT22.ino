// Humidity and tmeperature sensor sending data to python server over wifi - based on phant post example on sparkfun
// Include the ESP8266 WiFi library. (Works a lot like the
// Arduino WiFi library.)
// REMOVE SLEEP JUMPER BEFORE UPLOADING
// apart from DHT: connect 56kOhm between ground and AD0 and 220kOhm between Vin and ground
// to measure battery voltage, mutiply AD read by 5 to get voltage
// I started from the post to phant example code of sparkfun - there are some remanents of it in here (but the code does something quite different now...)
// data is sent as a json string to the python server
// You will need to adapt WiFi definitions and server host IP/port below
#include <ESP8266WiFi.h>
#include <dht.h> //use dht

/************* uncomment this to read vdd - but useless for sparkfun thing as after regulator
extern "C" {
uint16 readvdd33(void);
}
*/

//////////////////////
// WiFi Definitions //
//////////////////////
const char WiFiSSID[] = "wifinetwork";
const char WiFiPSK[] = "yourwifipassword";
////// Each sensor needs to have a different sensor name
const char SensorID[]="Living room";

///////////////////////////////////
// Python server host definitons - adapt to your own  //
///////////////////////////////////
const char PiHost[] = "192.168.2.101";
const int PiPort = 8888;


/////////////////////
// Pin Definitions //
/////////////////////
const int LED_PIN = 5; // Thing's onboard, green LED
const int ANALOG_PIN = A0; // Analog pin (only one on ESP8266)


dht DHT;

#define DHT22_PIN 2

/////////////////
// Post Timing //
/////////////////
// Time to sleep (in minutes):
// can be updated remotely (to be implemented)
const int sleepTimeS = 15*60; //seconds (or minutes if modifying line for esp.deepsleep)

// string variables needed for posting to server
char postString[40]; // output string for client write
char charbuf[40];

void setup() 
{
  initHardware();
  connectWiFi();
  digitalWrite(LED_PIN, HIGH);
  
  while(postToPi() != 1){
    delay(200);
    }
  // deepSleep time is defined in microseconds. Multiply
  // seconds by 1e6 
  ESP.deepSleep(sleepTimeS * 1000000); //60*1000000);
}

void loop() 
{

}

void connectWiFi()
{
  byte ledStatus = LOW;

  // Set WiFi mode to station (as opposed to AP or AP_STA)
  WiFi.mode(WIFI_STA);

  // WiFI.begin([ssid], [passkey]) initiates a WiFI connection
  // to the stated [ssid], using the [passkey] as a WPA, WPA2,
  // or WEP passphrase.
  WiFi.begin(WiFiSSID, WiFiPSK);

  // Use the WiFi.status() function to check if the ESP8266
  // is connected to a WiFi network.
  while (WiFi.status() != WL_CONNECTED)
  {
    // Blink the LED
    digitalWrite(LED_PIN, ledStatus); // Write LED high/low
    ledStatus = (ledStatus == HIGH) ? LOW : HIGH;

    // Delays allow the ESP8266 to perform critical tasks
    // defined outside of the sketch. These tasks include
    // setting up, and maintaining, a WiFi connection.
    delay(200); // was 100 in original example
    // Potentially infinite loops are generally dangerous.
    // Add delays -- allowing the processor to perform other
    // tasks -- wherever possible.
  }
}

void initHardware()
{
  //Serial.begin(9600);
  pinMode(DIGITAL_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  // Don't need to set ANALOG_PIN as input, 
  // that's all it can be.
}

int postToPi()
{
  // LED turns on when we enter, it'll go off when we 
  // successfully post.
  
  digitalWrite(LED_PIN, HIGH);

  
   int chk = DHT.read22(DHT22_PIN);
   switch (chk)
  {
    case DHTLIB_OK:     
   {
       dtostrf(DHT.humidity,5,1,charbuf);
       strcpy(postString,"{\"H\": ");
       strcat(postString,charbuf );
       strcat(postString,", \"T\": ");
       dtostrf(DHT.temperature,5,1,charbuf);
       strcat(postString,charbuf );
       strcat(postString,", \"S\": \"");
       strcat(postString,SensorID);
       strcat(postString,"\", \"B\": " );  
       sprintf (charbuf, "%i", analogRead(A0)*5); // there's a /5 voltage divider
       strcat(postString,charbuf);
       strcat(postString,"}\n" );  
       break;
  }
    case DHTLIB_ERROR_CHECKSUM: 
      strcpy(postString,"{\"T\": -1,\"H\": -1, \"S\": \""); 
      strcat(postString,SensorID);
      strcat(postString,"\"}\n" );  

      break;
    case DHTLIB_ERROR_TIMEOUT: 
      strcpy(postString,"{\"T\": -2,\"H\": -2, \"S\": \""); 
      strcat(postString,SensorID);
      strcat(postString,"\"}\n" );  
      break;
    case DHTLIB_ERROR_CONNECT:
      strcpy(postString,"{\"T\": -3,\"H\": -3, \"S\": \""); 
      strcat(postString,SensorID);
      strcat(postString,"\"}\n" );  
      break;
    case DHTLIB_ERROR_ACK_L:
      strcpy(postString,"{\"T\": -4,\"H\": -4, \"S\": \""); 
      strcat(postString,SensorID);
      strcat(postString,"\"}\n" );  
        break;
    case DHTLIB_ERROR_ACK_H:
      strcpy(postString,"{\"T\": -5,\"H\": -5, \"S\": \""); 
      strcat(postString,SensorID);
      strcat(postString,"\"}\n" );  
      break;
    default: 
      strcpy(postString,"{\"T\": -6,\"H\": -6, \"S\": \""); 
      strcat(postString,SensorID);
      strcat(postString,"\"}\n" );  
      break;
  }
  // check if returns are valid, if they are NaN (not a number) then something went wrong!
    
  // Now connect to data.sparkfun.com, and post our data:
  WiFiClient client;
  
  if (!client.connect(PiHost, PiPort)) 
  {
    // If we fail to connect, return 0. double blink to show
    digitalWrite(LED_PIN,HIGH);
    delay(100);
    digitalWrite(LED_PIN,LOW);
    delay(100);
    digitalWrite(LED_PIN,HIGH);
    delay(100);
    digitalWrite(LED_PIN,LOW);
    delay(100);

    return 0;
  }
  // If we successfully connected, print our Phant post:
  client.print(postString);

  // Read all the lines of the reply from server and print them to Serial
  //while(client.available()){
    //String line = client.readStringUntil('\r');
    //Serial.print(line); // Trying to avoid using serial
  //}
  //delay(300); // so i can see LED
  // Before we exit, turn the LED off.
  digitalWrite(LED_PIN, LOW);

  return 1; // Return success
}
