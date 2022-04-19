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
WiFiClient client;
const int udp_port = 3333;                            // Local UDP port
IPAddress remote = IPAddress(10, 31, 69, 132);        // UDP server IP address, hardcoded for now
const int remote_port = 56971;                        // UDP server port, hardcoded

const int AUDIO_BUF_SIZE = 44100;
const int TRANSFER_BUF_SIZE = 1024;
cbuf audio_buffer = cbuf(AUDIO_BUF_SIZE);          // Circular buffer for audio data recieved from UDP
char transfer_buffer[TRANSFER_BUF_SIZE];           // Buffer to transfer audio data from circular buffer to DMA buffers
size_t bytes_written = 0;
int bytes_read = 0;

// int16_t test_buffer[AUDIO_BUF_SIZE];
// int test_buf_i = 0;

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
int heartbeat_period_ms = 3000;        // Heardbeat message period (send state)

unsigned long time_last_loop = 0;
int loop_period_us = 5000;

unsigned long last = 0;

esp_err_t initI2S() {
   i2s_config_t i2s_config = {
      .mode = (i2s_mode_t) (I2S_MODE_MASTER | I2S_MODE_TX),
      .sample_rate =  I2S_SAMPLE_RATE,
      .bits_per_sample = (i2s_bits_per_sample_t) 16,
      .channel_format = I2S_CHANNEL_FMT_ONLY_RIGHT,
      .communication_format = I2S_COMM_FORMAT_STAND_I2S, // for amazon PCM5102 DAC
      .intr_alloc_flags = 0,
      .dma_buf_count = I2S_BUF_COUNT,
      .dma_buf_len = 1024,    // number of samples, 1024 seems to be the max
      .use_apll = 1,
      .tx_desc_auto_clear = 1,
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

esp_err_t startWIFI() {
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
   return ESP_OK;
}

esp_err_t startTCP() {
   uint8_t count = 0;
   Serial.printf("Attempting to connect to %s:%d \r\n", remote.toString(), remote_port);
   delay(100);
   while (!client.connect(remote, remote_port) && count < 12) {
      delay(500);
      Serial.print(".");
      count++;
   }
   if (!client.connected()) {
      Serial.println("Failed to connect, restarting");
      ESP.restart();
   }
   return ESP_OK;
}

esp_err_t startUDP() {
   uint8_t count = 0;
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

   Serial.println("Starting WiFi");
   if (startWIFI() == ESP_OK) {
      Serial.println("WiFi started!");
   }
   Serial.println("Starting TCP");
   if (startTCP() == ESP_OK) {
      Serial.println("TCP connected!");
   }
   Serial.println("Starting I2S");
   if (initI2S() == ESP_OK) {
      Serial.println("I2S started!");
   }

   // for (int i = 0; i < AUDIO_BUF_SIZE; i++) {
   //    test_buffer[i] = 32768 * i / AUDIO_BUF_SIZE;
   // }

   i2s_event_t tx_done = {
      .type = I2S_EVENT_TX_DONE,
      .size = 0,
   };

   // Put I2S_BUF_COUNT I2S_EVENT_TX_DONE messages on queue, main loop puts more data into DMA buffer when
   // transmission is done (when there is a I2S_EVENT_TX_DONE message), so it needs to be started
   for (int i = 0; i < I2S_BUF_COUNT; i++) {
      xQueueSend(i2s_queue_handle, &tx_done, portMAX_DELAY);
   }

   // audio_buffer.flush();

   start_stream();
}

void start_stream() {
   client.write((uint8_t) 0);
}

void pause_stream() {
   client.write((uint8_t) 1);
}

void stop_stream() {
   client.write((uint8_t) 2);
}

void print_buf_ints(int len) {
   for (int i = 0; i < len; i++) {
      Serial.printf("%i,", transfer_buffer[i]);
   }
   Serial.println();
}

void loop() {
   // Heartbeat to server

   time_last_loop = micros();

   // while (micros() - time_last_loop < loop_period_us) {delayMicroseconds(500);}

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
            Serial.println("p");
            // Serial.println(audio_buffer.room());
            state = Paused;
         }
         break;

      case Paused:
         if (audio_buffer.room() > 15*TRANSFER_BUF_SIZE) {
            start_stream();
            Serial.println("s");
            state = Started;
         }
         break;

      case Stopped:
         break;
   }

   while (client.available() > 0) {
      int len = client.read((uint8_t*) transfer_buffer, TRANSFER_BUF_SIZE); // Number of bytes read
      audio_buffer.write(transfer_buffer, len);
   }

   i2s_event_t i2s_evt;
   bool to_exit = false;

  //  if (audio_buffer.available() == 0) {
  //    audio_buffer.write((char*) test_buffer, AUDIO_BUF_SIZE);
  //  }

   // Deal with all the messages in the queue
   while (uxQueueMessagesWaiting(i2s_queue_handle) > 0 && !to_exit) {
      if (xQueuePeek(i2s_queue_handle, &i2s_evt, portMAX_DELAY) == pdTRUE){ // Doesn't remove item from queue
         switch (i2s_evt.type) {
            case I2S_EVENT_TX_DONE:
               // Serial.printf("loop, q: %d, %d\r\n", uxQueueMessagesWaiting(i2s_queue_handle), micros());
               // Serial.printf("%d, %d\r\n", bytes_written, bytes_read);

               // if (bytes_written == 0 && bytes_read == 0) {
               //   i2s_zero_dma_buffer(I2S_NUM);
               // }

               while (bytes_written != bytes_read) {
                  i2s_write(I2S_NUM, transfer_buffer+bytes_written, bytes_read-bytes_written, &bytes_written, 1);
               }

               while (bytes_written == bytes_read) {
                  // Serial.println(bytes_written);
                  bytes_read = audio_buffer.read(transfer_buffer, TRANSFER_BUF_SIZE);
                  if (bytes_read == 0) {
                    bytes_written = 0;
                  //   Serial.println("BUF EMPTY");
                    break;
                  }
                  bytes_written = 0;
                  i2s_write(I2S_NUM, transfer_buffer, bytes_read, &bytes_written, 1);
                  if (bytes_written == 0) {
                     // Serial.println("DMA BUF FULL");
                     break;
                  }
               }
               xQueueReceive(i2s_queue_handle, &i2s_evt, portMAX_DELAY);
               break;
            default:
               xQueueReceive(i2s_queue_handle, &i2s_evt, portMAX_DELAY);   // Ignore every other message for now
               // Serial.println(i2s_evt.type);
               break;
         }
      }
   }
  //  Serial.println(micros() - time_last_loop);
}
