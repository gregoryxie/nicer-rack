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
clients = {} # client_address: {'socket': socket, 'last_seen': datetime, 'state': int, 'song_i':int}

esp_timeout = 120 # seconds

samples_per_second = 44000
samples_per_loop = 500 # Also the size of the UDP message, MTU max 1300 bytes per message
song_rate = 4   # Rate at which song is streamed, should be > 1
loop_time = 1000/44000/song_rate
bytes_per_sample = 2

curr_song = None

def client_serve_func(conn, client_addr):
   with conn:
      while True:
         try:
            data = conn.recv(1, socket.MSG_DONTWAIT)
            now = datetime.now()
            int_data = int.from_bytes(data, "big")

            with socket_lock:
               # client has not been seen before
               if client_addr not in clients.keys():
                  clients[client_addr] = {'socket': conn, 'last_seen': now, 'state': int_data, 'song_i': 0}
                  print(f"New Client: {clients[client_addr]}")
                  new_client = True
               else:
                  clients[client_addr]['last_seen'] = now
                  clients[client_addr]['state'] = int_data

               if clients[client_addr]['state'] == 1:
                  print("PAUSE")
               if clients[client_addr]['state'] == 0:
                  print("GO")

               # print(clients)
               
               socket_lock.notify()
         except (TypeError,BlockingIOError) as e:
            # print(e)
            pass
         except TimeoutError as e:
            print("socket timeout")
            print(e)
            return
         except Exception as e:
            print(type(e))
            print(e)



def server_thread_func():
   with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      s.bind((HOST, PORT))
      s.listen(1)

      while True:
         conn, client_addr = s.accept()

         client_thread = threading.Thread(target=client_serve_func, args=(conn, client_addr))
         client_thread.daemon = True
         client_thread.start()

def remove_timeout_esp():
   with socket_lock:
      now = datetime.now()
      to_remove = []
      for client_addr in clients.keys():
         last_seen = clients[client_addr]['last_seen']
         diff = now - last_seen
         diff = diff.total_seconds()

         if diff > esp_timeout:
            to_remove.append(client_addr)

      for client_addr in to_remove:
         clients.pop(client_addr)
   
      socket_lock.notify()

def send_data_esp(data):
   data_bytes = int_array_to_bytes(data, 2)
   with socket_lock:
      for client_addr in clients.keys():
         sock = clients[client_addr]['socket']
         start = clients[client_addr]['song_i']

         if clients[client_addr]['state'] == 1 or clients[client_addr]['state'] == 2:
            # ESP wants to pause stream
            continue
         print(f"send: {len(data_bytes)}, {client_addr}")
         
         sock.send(data_bytes)
         # print(f"sent to {client_addr}")

def send_song_segment_esp(n_bytes):
   done = []
   to_kill = []
   with socket_lock:
      for client_addr in clients.keys():
         sock = clients[client_addr]['socket']
         start = clients[client_addr]['song_i']

         if clients[client_addr]['state'] == 1 or clients[client_addr]['state'] == 2:
            done.append(False)
            # ESP wants to pause stream
            continue

         if start + n_bytes > len(curr_song):
            data_bytes = curr_song[start:]
            clients[client_addr]['song_i'] = len(curr_song)
            done.append(True)
         else:
            data_bytes = curr_song[start:start + n_bytes]
            clients[client_addr]['song_i'] += n_bytes
            done.append(False)

         try:

            # print(f"send: {len(data_bytes)}, {client_addr}")
            sock.send(data_bytes, socket.MSG_DONTWAIT)      #TCP
            # sock.sendto(data_bytes, client_addr)       # UDP
            # print(f"sent to {client_addr}")
         except BrokenPipeError:
            to_kill.append(client_addr)

   for client in to_kill:
      clients.pop(client)
   return done

def reset_song_i():
   with socket_lock:
      for client_addr in clients.keys():
         clients[client_addr]['song_i'] = 0 

def int_array_to_bytes(data, len=2):
   """
      data: array of integers
      len: number of bytes per element, elements will be clipped to fit in desired number of bytes
            (-2**(len-1), 2**(len-1)-1)
   
   """

   # data_clip = np.clip(data, -2**(len*8-1), 2**(len*8-1)-1)

   # out = [i.to_bytes(2, byteorder='big') for i in data]
   # out = [item for sub in out for item in sub]
   # return bytes(out)
   data_clip = np.clip(data, -2**(len*8-1), 2**(len*8-1)-1)
   # print(data_clip)
   return data_clip.astype(np.dtype('<i2')).tobytes()

if __name__ == "__main__":
   x_axis = np.linspace(0, 261*2*np.pi, 44100)
   curr_song = int_array_to_bytes(2**14*np.sin(x_axis))
   # x_axis = np.linspace(0, 1, 10000)
   # curr_song = int_array_to_bytes(2**15*x_axis)
   # curr_song = int_array_to_bytes(np.ones(44000, dtype=np.int16)*2**14)
   # curr_song = bytes([0, 64, 32, 64]*22000)

   server_thread = threading.Thread(target=server_thread_func)
   server_thread.daemon = True
   server_thread.start()

   start = datetime.now()

   count = 0
   large_count = 0
   # input("press to start")
   while True:
      while (datetime.now() - start).total_seconds() < loop_time:
         time.sleep(loop_time/20)

      start = datetime.now()

      count += 1
      large_count += 1
      large_count = large_count % 10
      if count % 100 == 0:
         # print(clients)
         count = 0

      # check if any ESP32 timeout, remove them
      remove_timeout_esp()

      # send batch of music to all connected ESP32S
      done = np.prod(send_song_segment_esp(samples_per_loop*bytes_per_sample))
      if done:
         # print("Finished sending song")
         reset_song_i()
         # break
         # go to next song

      # data = np.ones(samples_per_loop)*2**14*large_count/10
      # send_data_esp(data)