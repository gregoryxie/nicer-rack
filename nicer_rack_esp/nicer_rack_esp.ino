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
IPAddress remote = IPAddress(10, 29, 91, 198);        // UDP server IP address, hardcoded for now
const int remote_port = 56971;                        // UDP server port, hardcoded

const int AUDIO_BUF_SIZE = 100;         // number of audio blocks in queue
const int AUDIO_BLOCK_SIZE = 1024;
const int TRANSFER_BUF_SIZE = AUDIO_BLOCK_SIZE;
QueueHandle_t audio_buffer_handle;          // Queue for audio data recieved from UDP
char transfer_buffer[TRANSFER_BUF_SIZE];           // Buffer to transfer audio data from circular buffer to DMA buffers
size_t bytes_written = 0;
int bytes_read = 0;

typedef struct AudioBlockStruct {
  int len;
  char buf[AUDIO_BLOCK_SIZE];
} AudioBlock;

// int16_t test_buffer[AUDIO_BUF_SIZE];
// int test_buf_i = 0;

const i2s_port_t I2S_NUM = I2S_NUM_0;    // ESP32 has 2 I2S peripherals
const uint32_t I2S_SAMPLE_RATE = 44100;
const uint8_t I2S_BUF_COUNT = 8;
const int I2S_MCK_IO = GPIO_NUM_0;       // I2S pin definitions
const int I2S_BCK_IO = GPIO_NUM_17;
const int I2S_WS_IO = GPIO_NUM_4;
const int I2S_DO_IO = GPIO_NUM_16;
const int I2S_DI_IO = I2S_PIN_NO_CHANGE;
QueueHandle_t i2s_queue_handle;

const int out_pin = 12;

TaskHandle_t communication_task_handle = NULL;
TaskHandle_t audio_task_handle = NULL;

enum StreamStates{Started, Paused, Stopped};       // States for state machine
enum StreamStates state;

unsigned long time_last_heartbeat = 0;
int heartbeat_period_ms = 3000;        // Heardbeat message period (send state)

esp_err_t initI2S() {
   i2s_config_t i2s_config = {
      .mode = (i2s_mode_t) (I2S_MODE_MASTER | I2S_MODE_TX),
      .sample_rate =  I2S_SAMPLE_RATE,
      .bits_per_sample = (i2s_bits_per_sample_t) 16,
      .channel_format = I2S_CHANNEL_FMT_ONLY_RIGHT,
      .communication_format = I2S_COMM_FORMAT_STAND_I2S,       // for amazon PCM5102 DAC
      .intr_alloc_flags = 0,
      .dma_buf_count = I2S_BUF_COUNT,
      .dma_buf_len = 1024,       // number of samples, 1024 seems to be the max
      .use_apll = 1,
      .tx_desc_auto_clear = 1,         // Automatically clear DMA buffers when sent
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

   client.setNoDelay(true);   // No delay when sending packets
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

void commTaskFunc(void * pvParameters) {
   enum StreamStates state_to_send;
   bool to_send = false;

   start_stream();

   while (true) {
      // Serial.printf("comm task %d\r\n", millis());
      to_send = false;

      // Receive data from TCP server
      int buf_room = uxQueueSpacesAvailable(audio_buffer_handle);
      if (client.available() > TRANSFER_BUF_SIZE && buf_room > 1) {
         AudioBlock audio_block;
         audio_block.len = client.read((uint8_t*) audio_block.buf, TRANSFER_BUF_SIZE); // Number of bytes read
         xQueueSend(audio_buffer_handle, &audio_block, portMAX_DELAY);
      }

      switch (state) {
         case Paused:
            if (buf_room > AUDIO_BUF_SIZE*0.7) {
               state = Started;
               to_send = true;
            }
            break;
         case Started:
            if (buf_room < AUDIO_BUF_SIZE*0.3) {
               state = Paused;
               to_send = true;
            }
            break;
         case Stopped:
            break;
      }

      if (to_send || millis() - time_last_heartbeat > heartbeat_period_ms) {
         to_send = false;
         time_last_heartbeat = millis();
         switch (state) {
            case Started:
               start_stream();
               break;
            case Paused:
               pause_stream();
               break;
            case Stopped:
               stop_stream();
               break;
         }
      }

      vTaskDelay(3.0 / portTICK_PERIOD_MS);
   }
}

void audioTaskFunc(void * pvParameters) {
   i2s_event_t i2s_evt;
   AudioBlock audio_block;

   bool wrote_i2s = false;

   while (true) {
      //  if (audio_buffer.available() == 0) {
      //    audio_buffer.write((char*) test_buffer, AUDIO_BUF_SIZE);
      //  }

      // Serial.printf("audio task %d\r\n", millis());      
      wrote_i2s = false;
      // Deal with all the messages in the queue
      while (uxQueueMessagesWaiting(i2s_queue_handle) > 0) {
         if (xQueuePeek(i2s_queue_handle, &i2s_evt, 0) == pdTRUE){ // Doesn't remove item from queue
            switch (i2s_evt.type) {
               case I2S_EVENT_TX_DONE:
                  while (bytes_written != bytes_read) {
                     i2s_write(I2S_NUM, audio_block.buf+bytes_written, bytes_read-bytes_written, &bytes_written, 1);
                  }
                  wrote_i2s = true;

                  while (bytes_written == bytes_read) {
                     if (xQueueReceive(audio_buffer_handle, &audio_block, portMAX_DELAY) == pdTRUE) {
                        bytes_read = audio_block.len;

                        if (bytes_read == 0) {
                        bytes_written = 0;
                        //   Serial.println("BUF EMPTY");
                        break;
                        }
                        bytes_written = 0;
                        i2s_write(I2S_NUM, audio_block.buf, bytes_read, &bytes_written, 1);
                        if (bytes_written == 0) {
                           // Serial.println("DMA BUF FULL");
                           break;
                        }
                        wrote_i2s = true;
                     } else {
                        bytes_written = 0;
                        //   Serial.println("BUF EMPTY");
                        break;
                     }
                  }
                  if (wrote_i2s) {xQueueReceive(i2s_queue_handle, &i2s_evt, portMAX_DELAY);}
                  break;
               default:
                  xQueueReceive(i2s_queue_handle, &i2s_evt, portMAX_DELAY);   // Ignore every other message for now
                  break;
            }
         }
      }

   }
}

void setup() {
   Serial.begin(57600);

   pinMode(out_pin, OUTPUT);

   Serial.println("Starting WiFi");
   if (startWIFI() == ESP_OK) {
      Serial.println("WiFi started!");
   } else {ESP.restart();}
   Serial.println("Starting TCP");
   if (startTCP() == ESP_OK) {
      Serial.println("TCP connected!");
   } else {ESP.restart();}
   Serial.println("Starting I2S");
   if (initI2S() == ESP_OK) {
      Serial.println("I2S started!");
   } else {ESP.restart();}

   // for (int i = 0; i < AUDIO_BUF_SIZE; i++) {
   //    test_buffer[i] = 32768 * i / AUDIO_BUF_SIZE;
   // }

   // i2s_event_t tx_done = {
   //    .type = I2S_EVENT_TX_DONE,
   //    .size = 0,
   // };

   audio_buffer_handle = xQueueCreate(AUDIO_BUF_SIZE, sizeof(AudioBlock));

   BaseType_t task_made;

   task_made = xTaskCreatePinnedToCore(
                  audioTaskFunc,
                  "AUDIO_TASK",
                  5000,
                  NULL,
                  1,   // Task Priority, IPC priority: 24, idle priority: 0
                  &audio_task_handle,
                  0);

   if(task_made != pdPASS){
      Serial.println("Failed to create audio task!");
      ESP.restart();
   }

   task_made = xTaskCreatePinnedToCore(
                  commTaskFunc,
                  "COMM_TASK",
                  5000,
                  NULL,
                  0,   // Task Priority, IPC priority: 24, idle priority: 0
                  &communication_task_handle,
                  1);

   if(task_made != pdPASS){
      Serial.println("Failed to create communication task!");
      ESP.restart();
   }

   
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
   vTaskDelay(1.0 / portTICK_PERIOD_MS);
}