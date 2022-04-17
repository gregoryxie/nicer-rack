import socket
import threading
import socketserver
from datetime import datetime
import time
import numpy as np
import math
import queue

HOST = '' # bind to a bunch of stuff? idk lol
PORT = 56971 # random port between 49152–65535

socket_lock = threading.Condition()
esp_sockets = {} # client_address: {'socket': socket, 'last_seen': datetime, 'state': int, 'song_i':int}

esp_timeout = 120 # seconds

samples_per_second = 44000
loop_time = 1/100
song_rate = 1.1   # Rate at which song is streamed, should be > 1
samples_per_loop = math.ceil(loop_time*samples_per_second*song_rate)

curr_song = None


class MusicRequestHandler(socketserver.BaseRequestHandler):
   def setup(self):
      pass

   def finish(self):
      pass

   def handle(self):
      # self.request = (data, socket)

      # print("GOT")

      data = self.request[0]
      int_data = int.from_bytes(data, "big")
      # print(data)
      client_addr = self.client_address
      sock = self.request[1]
      now = datetime.now()

      # print(self.request)

      with socket_lock:
         # client has not been seen before
         if client_addr not in esp_sockets.keys():
            esp_sockets[client_addr] = {'socket': sock, 'last_seen': now, 'state': int_data, 'song_i': 0}
            print(f"New Client: {esp_sockets[client_addr]}")
         else:
            esp_sockets[client_addr]['last_seen'] = now
            esp_sockets[client_addr]['state'] = int_data

         print(esp_sockets)
         
         socket_lock.notify()
         

def remove_timeout_esp():
   with socket_lock:
      now = datetime.now()
      to_remove = []
      for client_addr in esp_sockets.keys():
         last_seen = esp_sockets[client_addr]['last_seen']
         diff = now - last_seen
         diff = diff.total_seconds()

         if diff > esp_timeout:
            to_remove.append(client_addr)

      for client_addr in to_remove:
         esp_sockets.pop(client_addr)
   
      socket_lock.notify()

def send_data_esp(data):
   data_bytes = int_array_to_bytes(data, 2)
   with socket_lock:
      for client_addr in esp_sockets.keys():
         sock = esp_sockets[client_addr]['socket']
         start = esp_sockets[client_addr]['song_i']

         if esp_sockets[client_addr]['state'] == 1 or esp_sockets[client_addr]['state'] == 2:
            # ESP wants to pause stream
            continue
         print(f"send: {len(data_bytes)}, {client_addr}")
         
         sock.sendto(data_bytes, client_addr)
         # print(f"sent to {client_addr}")

def send_song_segment_esp(n_bytes):
   done = []
   with socket_lock:
      for client_addr in esp_sockets.keys():
         sock = esp_sockets[client_addr]['socket']
         start = esp_sockets[client_addr]['song_i']

         if esp_sockets[client_addr]['state'] == 1 or esp_sockets[client_addr]['state'] == 2:
            done.append(False)
            # ESP wants to pause stream
            continue

         if start + n_bytes > len(curr_song):
            data_bytes = curr_song[start:]
            esp_sockets[client_addr]['song_i'] = len(curr_song)
            done.append(True)
         else:
            data_bytes = curr_song[start:start + n_bytes]
            esp_sockets[client_addr]['song_i'] += n_bytes
            done.append(False)

         print(f"send: {len(data_bytes)}, {client_addr}")
         
         sock.sendto(data_bytes, client_addr)
         # print(f"sent to {client_addr}")
   return done

def reset_song_i():
   with socket_lock:
      for client_addr in esp_sockets.keys():
         esp_sockets[client_addr]['song_i'] = 0 

def int_array_to_bytes(data, len=2):
   """
      data: array of integers
      len: number of bytes per element, elements will be clipped to fit in desired number of bytes
            (-2**(len-1), 2**(len-1)-1)
   
   """
   data_clip = np.clip(data, -2**(len*8-1), 2**(len*8-1)-1)
   # print(data_clip)
   return data_clip.astype(np.dtype('>i2')).tobytes()

if __name__ == "__main__":
   # curr_song = int_array_to_bytes(np.random.randint(48, 500, size=(20000)))

   server = socketserver.ThreadingUDPServer((HOST, PORT), MusicRequestHandler)
   with server:
      server_thread = threading.Thread(target=server.serve_forever)
      server_thread.daemon = True
      server_thread.start()

      start = datetime.now()

      count = 0
      # input("press to start")
      while True:
         while (datetime.now() - start).total_seconds() < loop_time:
            time.sleep(loop_time/20)

         start = datetime.now()

         count += 1
         if count % 500 == 0:
            print(esp_sockets.keys())
            count = 0

         # check if any ESP32 timeout, remove them
         remove_timeout_esp()

         # send batch of music to all connected ESP32S
         # done = np.prod(send_song_segment_esp(1000))
         # if done:
         #    print("Finished sending song")
            # reset_song_i()
            # go to next song

         data = np.random.randint(48, 500, size=(500))
         send_data_esp(data)


