#include <WiFiClient.h>
#include <WiFiUDP.h>
#include <Wifi.h>
#include <cbuf.h>
// #include <ESPm.h>

const char NETWORK[] = "MIT";
const char PASSWORD[] = "";

WiFiUDP udp;
const int udp_port = 3333;
IPAddress remote = IPAddress(10, 31, 69, 31);
const int remote_port = 56971;


const int AUDIO_BUF_SIZE = 44000;
const int TRANSFER_BUF_SIZE = 1024;
cbuf audio_buffer = cbuf(AUDIO_BUF_SIZE);
char transfer_buffer[TRANSFER_BUF_SIZE];

enum StreamStates{Started, Paused, Stopped};
enum StreamStates state;

unsigned long time_last_heartbeat = 0;
int heartbeat_period_ms = 1000;

void setup() {
   Serial.begin(115200);
   WiFi.begin(NETWORK, PASSWORD);

   // Connect to WiFi, start attach to UDP socket

   uint8_t count = 0;
   Serial.printf("Attempting to connect to %s \r\n", NETWORK);
   while (WiFi.status() != WL_CONNECTED && count < 12) {
      delay(500);
      Serial.print(".");
      count++;
   }
   delay(2000);
   if (WiFi.isConnected()) {
      Serial.println("CONNECTED!");
      Serial.printf("%d:%d:%d:%d (%s) (%s)\n", WiFi.localIP()[3], WiFi.localIP()[2],
                     WiFi.localIP()[1], WiFi.localIP()[0],
                     WiFi.macAddress().c_str() , WiFi.SSID().c_str());
      delay(500);
   } else {
      Serial.println("Failed to connect, restarting");
      Serial.println(WiFi.status());
      ESP.restart();
   }

   count = 0;
   Serial.printf("Starting UDP, port: %d", udp_port);
   while (udp.begin(WiFi.localIP(),udp_port) != 1 && count < 12) {
      delay(500);
      Serial.print(".");
      count++;
   }
   delay(100);
   start_stream();
}

void start_stream() {
   udp.beginPacket(remote, remote_port);
   udp.write(0);
   udp.endPacket();
}

void pause_stream() {
   udp.beginPacket(remote, remote_port);
   udp.write(1);
   udp.endPacket();
}

void stop_stream() {
   udp.beginPacket(remote, remote_port);
   udp.write(2);
   udp.endPacket();
}

void print_buf_ints(int len) {
   for (int i = 0; i < len; i++) {
      Serial.printf("%i,", transfer_buffer[i]);
   }
   Serial.println();
}

void loop() {
   // Heartbeat to server
   if (millis() - time_last_heartbeat > heartbeat_period_ms) {
      time_last_heartbeat = millis();
      if (state == Started) {start_stream();}
      else if (state == Paused) {pause_stream();}
      else if (state == Stopped) {stop_stream();}
   }

   switch (state) {
      case Started:
         if (audio_buffer.room() < 2*TRANSFER_BUF_SIZE) {
            pause_stream();
            state = Paused;
         }
         break;

      case Paused:
         if (audio_buffer.room() > 4*TRANSFER_BUF_SIZE) {
            start_stream();
            state = Started;
         }
         break;

      case Stopped:
         break;
   }


   unsigned long start = micros();

   // Takes ~200 us to do this stuff
   int packetSize = udp.parsePacket();
   if (packetSize) {
      int len = udp.read(transfer_buffer, TRANSFER_BUF_SIZE); // Number of bytes read
      audio_buffer.write(transfer_buffer, len);
      // Serial.printf("%d\r\n", len);
   }

   if (audio_buffer.available() > 0) {
      int read = audio_buffer.read(transfer_buffer, TRANSFER_BUF_SIZE-1);
      transfer_buffer[read] = 0;
      // Serial.printf("%d\r\n", read);
      // print_buf_ints(read);
      
   }
   // Serial.printf("%d\r\n", audio_buffer.room());
   Serial.println(micros() - start);
   delay(50);
}
