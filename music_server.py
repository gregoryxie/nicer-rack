import socket
import threading
import socketserver
from datetime import datetime
import time
from data_handler import retrieve_all_data, retrieve_data
from link_handler import convert_mp3_to_wav
import numpy as np
import math
import queue

HOST = '127.0.0.1' # bind to a bunch of stuff? idk lol
PORT = 56971 # random port between 49152–65535
PORT_WEB = 8080

clients_lock = threading.Condition()
clients = {} # client_address: {'last_seen': datetime, 'state': int, 'song_i':int, 'done':bool}

esp_timeout = 120 # seconds

samples_per_second = 44000
samples_per_loop = 500 # Also the size of the UDP message, MTU max 1300 bytes per message
song_rate = 3   # Rate at which song is streamed, should be > 1
loop_time = samples_per_loop/samples_per_second/song_rate
bytes_per_sample = 2
bytes_per_loop = samples_per_loop*bytes_per_sample

# print(loop_time)

curr_song = 0

# try to receive bytes from ESP, try to send
def try_recv_esp(conn, client_addr, first_recv=False):
   try:
      if first_recv:
         data = conn.recv(1)
      else:
         data = conn.recv(1, socket.MSG_DONTWAIT)
      now = datetime.now()
      int_data = int.from_bytes(data, "big")

      with clients_lock:
         # client has not been seen before
         if client_addr not in clients.keys():
            clients[client_addr] = {'last_seen': now, 'state': int_data, 'song_i': 0, 'done':False}
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
         
         clients_lock.notify()
      return True
   except TimeoutError as e:
      print("socket timeout")
      return False
   except (TypeError,BlockingIOError) as e:
      return True
   except Exception as e:
      print(type(e))
      print(e)
      return True

def try_send_esp(conn, client_addr):
   with clients_lock:
      start = clients[client_addr]['song_i']

      if clients[client_addr]['state'] == 1 or clients[client_addr]['state'] == 2:
         clients[client_addr]['done'] = False
         return True

      if start + bytes_per_loop > len(curr_song):
         data_bytes = curr_song[start:]
         clients[client_addr]['song_i'] = len(curr_song)
         clients[client_addr]['done'] = True
      else:
         data_bytes = curr_song[start:start + bytes_per_loop]
         clients[client_addr]['song_i'] += bytes_per_loop
         clients[client_addr]['done'] = False

      try:
         conn.send(data_bytes)      #TCP
         # sock.sendto(data_bytes, client_addr)       # UDP
      except BrokenPipeError:
         clients_lock.notify()
         return False
      except BlockingIOError:
         pass

      clients_lock.notify()
      return True
   
  # try to receive bytes from ESP
def try_recv_web(conn, first_recv=False):
   try:
      if first_recv:
         data = conn.recv(1)
      else:
         data = conn.recv(1, socket.MSG_DONTWAIT)

      # Invariant: Assumes that the length of any youtube link url descriptor is within 1 byte
      # Very reasonable assumption
      int_data = int.from_bytes(data, "big")
      if (int_data):
         print("Received this message from webserver:")
         data = conn.recv(int_data, socket.MSG_DONTWAIT)

         # This is the youtube url argument of the song to play.
         link = data.decode("utf-8")
         print(link)
         print("Extracted this data from message:")
         data = retrieve_data(link)
         print(data)

         # samples = convert_mp3_to_wav(path)

      return True
   except TimeoutError as e:
      print("socket timeout")
      return False
   except (TypeError,BlockingIOError) as e:
      return True
   except Exception as e:
      print(type(e))
      print(e)
      return True 
      
def check_timeout_esp(conn, client_addr):
   now = datetime.now()
   with clients_lock:
      last_seen = clients[client_addr]['last_seen']
      diff = now - last_seen
      diff = diff.total_seconds()

      if diff > esp_timeout:
         clients.pop(client_addr)
         clients_lock.notify()
         return True
      
      clients_lock.notify()
   return False

def client_serve_func(conn, client_addr):
   start = datetime.now()

   with conn:
      if not try_recv_esp(conn, client_addr, first_recv=True):
         return

      while True:
         while (datetime.now() - start).total_seconds() < loop_time:
            time.sleep(loop_time/20)
         
         start = datetime.now()

         if not try_recv_esp(conn, client_addr):
            break

         if check_timeout_esp(conn, client_addr):
            break

         if not try_send_esp(conn, client_addr):
            break

def web_serve_func(conn):
   start = datetime.now()

   with conn:
      if not try_recv_web(conn, first_recv=True):
         return

      while True:
         while (datetime.now() - start).total_seconds() < loop_time:
            time.sleep(loop_time/20)
         
         start = datetime.now()

         if not try_recv_web(conn):
            break

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

def web_thread_func():
   with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
      s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      s.bind((HOST, PORT_WEB))
      s.listen(1)

      while True:
         conn, web_addr = s.accept()

         web_thread = threading.Thread(target=web_serve_func, args=(conn,))
         web_thread.daemon = True
         web_thread.start()

def reset_song_i():
   with clients_lock:
      for client_addr in clients.keys():
         clients[client_addr]['song_i'] = 0
         clients[client_addr]['done'] = False
      clients_lock.notify()

def int_array_to_bytes(data, len=2):
   """
      data: array of integers
      len: number of bytes per element, elements will be clipped to fit in desired number of bytes
            (-2**(len-1), 2**(len-1)-1)
   
   """
   data_clip = np.clip(data, -2**(len*8-1), 2**(len*8-1)-1)
   return data_clip.astype(np.dtype('<i2')).tobytes()

def run_server():
   global curr_song

   x_axis = np.linspace(0, 440*2*np.pi, 44100)
   curr_song = int_array_to_bytes(2**14*np.sin(x_axis))
   # x_axis = np.linspace(0, 1, 10000)
   # curr_song = int_array_to_bytes(2**15*x_axis)
   # curr_song = int_array_to_bytes(np.ones(44000, dtype=np.int16)*2**14)
   # curr_song = bytes([0, 64, 32, 64]*22000)

   # Thread for ESP communication
   server_thread = threading.Thread(target=server_thread_func)
   server_thread.daemon = True
   server_thread.start()

   # Thread for Webserver communication
   web_thread = threading.Thread(target=web_thread_func)
   web_thread.daemon = True
   web_thread.start()

   start = datetime.now()

   count = 0
   large_count = 0
   while True:
      while (datetime.now() - start).total_seconds() < loop_time:
         time.sleep(loop_time/20)

      start = datetime.now()

      count += 1
      large_count += 1
      large_count = large_count % 10
      if count % 100 == 0:
         print(clients)
         count = 0

      with clients_lock:
         done = np.prod([clients[client_addr]["done"] for client_addr in clients.keys()])
         clients_lock.notify()
      if done:
         reset_song_i()
         # break
         # go to next song
      


if __name__ == "__main__":
   run_server()