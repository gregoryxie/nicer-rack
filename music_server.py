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

HOST = '' # bind to all available 
PORT = 56971 # random port between 49152–65535
PORT_WEB = 8080

clients_lock = threading.Condition()
clients = {} # client_address: {'last_seen': datetime, 'state': int, 'song_i':int, 'done':bool}

esp_timeout = 120 # seconds

samples_per_second = 44000
samples_per_loop = 500 # Also the size of the UDP message, MTU max 1300 bytes per message
song_rate = 5   # Rate at which song is streamed, should be > 1
loop_time = samples_per_loop/samples_per_second/song_rate
bytes_per_sample = 2
bytes_per_loop = samples_per_loop*bytes_per_sample

paused = False
curr_song = 0
next_song = []
command_queue = []   # Queue for commands, so that each command will be run sequentially as received
song_cv = threading.Condition()
command_lock = threading.Condition()

def try_recv_esp(conn, client_addr, first_recv=False):
   """
   Try to recieve data from the ESP32, if the ESP32 has not been seen before,
   add it to list of clients. Otherwise, update the ESP32s state based on the 
   message receieved.
   """
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
   """
   Try to send a block of data to the ESP32 from the current song. 
   Does not send data if the ESP32 is in the "pause" or "stop" state
   """
   global clients
   start = None
   temp_clients = None
   with clients_lock:
      start = clients[client_addr]['song_i']
      temp_clients = clients
      clients_lock.notify()

   if temp_clients[client_addr]['state'] == 1 or temp_clients[client_addr]['state'] == 2:
      temp_clients[client_addr]['done'] = False
      return True

   if not paused:
      if start + bytes_per_loop > len(curr_song):
         with song_cv:
            data_bytes = curr_song[start:]
            song_cv.notify()
         temp_clients[client_addr]['song_i'] = len(curr_song)
         temp_clients[client_addr]['done'] = True
      else:
         with song_cv:
            data_bytes = curr_song[start:start + bytes_per_loop]
            song_cv.notify()
         temp_clients[client_addr]['song_i'] += bytes_per_loop
         temp_clients[client_addr]['done'] = False

      try:
         conn.send(data_bytes)      #TCP
         # sock.sendto(data_bytes, client_addr)       # UDP
      except BrokenPipeError:
         return False
      except BlockingIOError:
         pass

   with clients_lock:
      clients = temp_clients
      clients_lock.notify()
   return True
   
  # try to receive bytes from ESP
def try_recv_web(conn, first_recv=False):
   """COMMUNICATION PROTOCOL: Messages from the API server should always be of the 
   form: [msg_length (1 byte), command (1 byte), msg (msg_length - 1 bytes)]. With this,
   the first byte says how long the remaining message is, the next byte is a command,
   and the msg is the Youtube unique link descriptor."""
   global command_queue
   try:
      if first_recv:
         data = conn.recv(1)
      else:
         data = conn.recv(1, socket.MSG_DONTWAIT)

      # Invariant: Assumes that the length of any youtube link url descriptor is within 1 byte
      # Very reasonable assumption
      int_data = int.from_bytes(data, "big")
      if (int_data):
         command_bytes = conn.recv(1, socket.MSG_DONTWAIT)
         msg_bytes = conn.recv(int_data, socket.MSG_DONTWAIT)

         # Get the command and message
         command = int.from_bytes(command_bytes, "big")
         msg = msg_bytes.decode("utf-8")

         # print("Received message")
         # print("Command: " + str(command))
         # print("Message: " + str(msg))

         with command_lock:
            command_queue.append({"cmd": command, "msg": msg})
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
      
def handle_command_queue():
   """Handle the command queue, which is only added to through socket messages.
   Commands:
      1 - play
      2 - pause
      3 - current song skip
      4 - next song skip
      5 - denote msg is next song
      6 - denote msg is current song (play from beginning)"""
   global paused
   global curr_song
   global next_song
   global command_queue
   
   # Acquire lock for command queue, and take off first command if it exists
   with command_lock:
      if not command_queue:
         return True
      cmd = command_queue[0]["cmd"]
      msg = command_queue[0]["msg"]
      command_queue = command_queue[1:]

      # print("Running command")
      # print("Command: " + str(cmd))
      # print("Message: " + str(msg))

   # If audio samples needed, retrieve from link
   if cmd in [5,6]:
      link_data = retrieve_data(msg)
      samples = convert_mp3_to_wav(link_data[4])
   
   # Per command, change curr_song, next_song, or paused variables
   if cmd == 1:
      paused = False
   elif cmd == 2:
      paused = True
   elif cmd == 3:
      paused = True
      with song_cv:
         curr_song = next_song
         next_song = int_array_to_bytes(np.zeros(44100))
         song_cv.notify()
      reset_song_i()
      paused = False
   elif cmd == 4:
      next_song = int_array_to_bytes(np.zeros(44100))
   if cmd == 5:
      next_song = int_array_to_bytes(samples, len=2)
   elif cmd == 6:
      paused = True
      with song_cv:
         curr_song = int_array_to_bytes(samples, len=2)
         song_cv.notify()
      reset_song_i()
      paused = False

   return True

def check_timeout_esp(conn, client_addr):
   """
   Check to see if an ESP32 has timed out. If we have not received a message
   from the ESP in esp_timeout seconds, we remove it from the list of clients
   """
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
   """
   Function to serve a ESP32 client forever
   Tries to receive data from the ESP, checks if it has timed out,
   and then tries to send song data to the ESP. 
   """
   start = datetime.now()

   with conn:
      if not try_recv_esp(conn, client_addr, first_recv=True):
         return

      while True:
         while (datetime.now() - start).total_seconds() < loop_time:
            time.sleep(loop_time/20)
         
         start = datetime.now()

         if not try_recv_esp(conn, client_addr):
            with clients_lock:
                  clients.pop(client_addr)
                  clients_lock.notify()
            break

         if check_timeout_esp(conn, client_addr):
            break

         if not try_send_esp(conn, client_addr):
            with clients_lock:
                  clients.pop(client_addr)
                  clients_lock.notify()
            break

def web_serve_func(conn):
   """
   Function to serve the web server forever
   Tries to receive data from the web socket, and updates
   the current song, next song, etc.
   """
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

         if not handle_command_queue():
            break
         

def server_thread_func():
   """
   Function that runs the audio server. Spawns
   more threads to serve each client that connects to 
   the socket. One ESP32 is one client.
   """
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
   """
   Function that runs the web server socket. Spawns
   more threads to serve each client that connects to 
   the socket. There should only be one client that connects!
   """
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
   """
   Reset the current index of all ESP32s for the song
   When sending is started again, all client serve threads
   start from the beginning of the current song. 
   """
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
   global next_song

   curr_song = int_array_to_bytes(np.zeros(44100))
   next_song = int_array_to_bytes(np.zeros(44100))

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

      # Switch to the next song if all the client threads have finished sending.
      with clients_lock:
         done = np.prod([clients[client_addr]["done"] for client_addr in clients.keys()])
         clients_lock.notify()
      if done:
         reset_song_i()
         curr_song = next_song
         next_song = int_array_to_bytes(np.zeros(44100))


if __name__ == "__main__":
   run_server()
