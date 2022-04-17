#include <WiFiClient.h>
#include <WiFiUDP.h>
#include <Wifi.h>
#include <cbuf.h>
#include "freertos/queue.h"
#include "driver/i2s.h"
#include "esp_system.h"
#include "esp_types.h"
#include "esp_err.h"
#include "esp_check.h"
// #include <ESPm.h>

const char NETWORK[] = "MIT";
const char PASSWORD[] = "";

WiFiUDP udp;
const int udp_port = 3333;                            // Local UDP port
IPAddress remote = IPAddress(10, 31, 62, 16);        // UDP server IP address, hardcoded for now
const int remote_port = 56971;                        // UDP server port, hardcoded

const int AUDIO_BUF_SIZE = 44100;
const int TRANSFER_BUF_SIZE = 1024;
cbuf audio_buffer = cbuf(AUDIO_BUF_SIZE);          // Circular buffer for audio data recieved from UDP
char transfer_buffer[TRANSFER_BUF_SIZE];           // Buffer to transfer audio data from circular buffer to DMA buffers

static const i2s_port_t I2S_NUM = I2S_NUM_0;    // ESP32S2 only has 1 I2S peripheral
static const uint32_t I2S_SAMPLE_RATE = 44100;
static const uint8_t I2S_BUF_COUNT = 8;
static const int I2S_MCK_IO = GPIO_NUM_6;       // I2S pin definitions
static const int I2S_BCK_IO = GPIO_NUM_4;
static const int I2S_WS_IO = GPIO_NUM_2;
static const int I2S_DO_IO = GPIO_NUM_3;
static const int I2S_DI_IO = GPIO_NUM_5;
static QueueHandle_t i2s_queue_handle;

enum StreamStates{Started, Paused, Stopped};       // States for state machine
enum StreamStates state;

unsigned long time_last_heartbeat = 0;
int heartbeat_period_ms = 1000;        // Heardbeat message period (send state)

unsigned long time_last_loop = 0;
int loop_period_us = 10000;

esp_err_t initI2S() {
   i2s_config_t i2s_config = {
      .mode = (i2s_mode_t) (I2S_MODE_MASTER | I2S_MODE_TX),
      .sample_rate =  I2S_SAMPLE_RATE,
      .bits_per_sample = (i2s_bits_per_sample_t) 16,
      .channel_format = I2S_CHANNEL_FMT_ALL_RIGHT,
      .communication_format = I2S_COMM_FORMAT_STAND_I2S,
      .intr_alloc_flags = 0,
      .dma_buf_count = I2S_BUF_COUNT,
      .dma_buf_len = 1024,    // number of samples, 1024 seems to be the max
      .use_apll = 1,
   };

   i2s_pin_config_t i2s_pin_cfg = {
      .mck_io_num = I2S_MCK_IO,
      .bck_io_num = I2S_BCK_IO,
      .ws_io_num = I2S_WS_IO,
      .data_out_num = I2S_DO_IO,
      .data_in_num = I2S_DI_IO
   };

   ESP_RETURN_ON_ERROR(i2s_driver_install(I2S_NUM, &i2s_config, 100, &i2s_queue_handle), "", "i2s config failed");
   ESP_RETURN_ON_ERROR(i2s_set_pin(I2S_NUM, &i2s_pin_cfg), "", "i2s pin config failed");
   ESP_RETURN_ON_ERROR(i2s_set_sample_rates(I2S_NUM, 44100), "", "i2s sample rate config failed");
   return ESP_OK;
}

esp_err_t startWIFIandUDP() {
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
   Serial.printf("Starting UDP, port: %d\r\n", udp_port);
   while (udp.begin(WiFi.localIP(),udp_port) != 1 && count < 12) {
      delay(500);
      Serial.print(".");
      count++;
   }
   Serial.println("UDP Connected!");

   return ESP_OK;
}

void setup() {
   Serial.begin(115200);

   Serial.println("Starting WiFi and UDP");
   if (startWIFIandUDP() == ESP_OK) {
      Serial.println("WiFi and UDP started!");
   }
   Serial.println("Starting I2S");
   if (initI2S() == ESP_OK) {
      Serial.println("I2S started!");
   }

   i2s_event_t tx_done = {
      .type = I2S_EVENT_TX_DONE,
      .size = 0,
   };

   // Put I2S_BUF_COUNT I2S_EVENT_TX_DONE messages on queue, main loop puts more data into DMA buffer when
   // transmission is done (when there is a I2S_EVENT_TX_DONE message), so it needs to be started
   for (int i = 0; i < I2S_BUF_COUNT; i++) {
      xQueueSend(i2s_queue_handle, &tx_done, portMAX_DELAY);
   }

   audio_buffer.flush();

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

   while (micros() - time_last_loop < loop_period_us) {delayMicroseconds(500);}

   if (millis() - time_last_heartbeat > heartbeat_period_ms) {
      time_last_heartbeat = millis();
      if (state == Started) {start_stream();}
      else if (state == Paused) {pause_stream();}
      else if (state == Stopped) {stop_stream();}
   }

   switch (state) {
      case Started:
         if (audio_buffer.room() < 10*TRANSFER_BUF_SIZE) {
            pause_stream();
            // Serial.println("PAUSING!!!");
            // Serial.println(audio_buffer.room());
            state = Paused;
         }
         break;

      case Paused:
         if (audio_buffer.room() > 15*TRANSFER_BUF_SIZE) {
            start_stream();
            state = Started;
         }
         break;

      case Stopped:
         break;
   }

   // Takes ~200 us to do this stuff
   int packetSize = udp.parsePacket();
   if (packetSize) {
      int len = udp.read(transfer_buffer, TRANSFER_BUF_SIZE); // Number of bytes read
      audio_buffer.write(transfer_buffer, len);
      // Serial.printf("recv: %d\r\n", len);
   }

   i2s_event_t i2s_evt;
   size_t bytes_written;
   bool to_exit = false;

   // if (audio_buffer.available()) {
   //    int read = audio_buffer.read(transfer_buffer, 2);
   //    Serial.println(read);
   //    int16_t* to_int16 = (int16_t * ) transfer_buffer;
   //    Serial.println(to_int16[0]);
   //    i2s_write(I2S_NUM, to_int16, 1, &bytes_written, 1000);
   // }


   // Deal with all the messages in the queue
   while (uxQueueMessagesWaiting(i2s_queue_handle) > 0 && !to_exit) {
      xQueuePeek(i2s_queue_handle, &i2s_evt, 1); // Doesn't remove item from queue
      switch (i2s_evt.type) {
         case I2S_EVENT_TX_DONE:
            if (audio_buffer.available() > TRANSFER_BUF_SIZE) {
               int read = audio_buffer.read(transfer_buffer, TRANSFER_BUF_SIZE);
               // read should == TRANSFER_BUF_SIZE so we don't have to deal with half full DMA buffers
               int16_t* transfer_to_int16 = (int16_t * ) transfer_buffer;
               Serial.printf("%x, %x\r\n", transfer_buffer[0], transfer_buffer[1]);
               Serial.println(transfer_to_int16[0]);
               i2s_write(I2S_NUM, transfer_buffer, read, &bytes_written, 1);
               xQueueReceive(i2s_queue_handle, &i2s_evt, 1);
            } else {
               to_exit = true;   // Exit loop if we cannot deal with a TX_DONE message
            }
            break;
         default:
            xQueueReceive(i2s_queue_handle, &i2s_evt, 1);   // Ignore every other message for now
            break;
      }
   }
}
