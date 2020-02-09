import random
import socket
import time
from _thread import *
import threading
from datetime import datetime
import json

clients_lock = threading.Lock()
connected = 0

clients = {}

def connectionLoop(sock):
   while True:
      data, addr = sock.recvfrom(1024)
      data = str(data)
      data = data[2:-1] #remove b', put after convert json to string
      #print(data)
      if addr in clients:
         #if 'heartbeat' in data:
         if 'sendPos' and 'sendRot' in data:
            clients[addr]['lastBeat'] = datetime.now()
            playerInfo = {}
            playerInfo = json.loads(data)
            #print(playerInfo)
            # save position and rotation
            clients[addr]['position'] = playerInfo['sendPos']
            clients[addr]['rotation'] = playerInfo['sendRot']
      else:
         if 'connect' in data: #call when there is a new client
            clients[addr] = {}
            clients[addr]['lastBeat'] = datetime.now()
            clients[addr]['color'] = 0
            clients[addr]['position'] = 0
            clients[addr]['rotation'] = 0
            message = {"cmd": 4,"player":[{"id":str(addr)}]}
            m = json.dumps(message)
            sock.sendto(bytes(m, 'utf8'), (addr[0],addr[1]))
            
            message = {"cmd": 0,"player":[{"id":str(addr)}]}
            m = json.dumps(message)
            
            newMessage = {"cmd": 2, "player":[]}
            for c in clients:
               sock.sendto(bytes(m,'utf8'), (c[0],c[1]))
               player = {}
               player['id'] = str(c)
               newMessage['player'].append(player)
               nm = json.dumps(newMessage)
               sock.sendto(bytes(nm, 'utf8'), (addr[0],addr[1]))


def cleanClients(sock):
   while True:
      newMessage = {"cmd": 3,"player": []}
      flag = False
      for c in list(clients.keys()):
         if (datetime.now() - clients[c]['lastBeat']).total_seconds() > 5:
            print('Dropped Client: ', c)
            flag = True
            player = {}
            player['id'] = str(c)
            newMessage["player"].append(player)
            clients_lock.acquire()
            del clients[c]
            clients_lock.release()
      nm = json.dumps(newMessage)
      
      if flag:
         for c in clients:
            sock.sendto(bytes(nm, 'utf8'), (c[0],c[1]))
      time.sleep(1)

def gameLoop(sock):
   while True:
      GameState = {"cmd": 1, "players": []}
      clients_lock.acquire()
      print (clients)
      for c in clients:
         #clients[c]['color'] = {"R": random.random(), "G": random.random(), "B": random.random()}
         player = {}
         player['id'] = str(c)
         player['color'] = clients[c]['color']
         player['position'] = clients[c]['position']
         player['rotation'] = clients[c]['rotation']
         GameState['players'].append(player)
      s = json.dumps(GameState)
      print(s)
      for c in clients:
         sock.sendto(bytes(s,'utf8'), (c[0],c[1]))
      print("Current Connected: %d" % len (clients))
      clients_lock.release()
      time.sleep(1/30)

def main():
   port = 12345
   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
   s.bind(('', port))
   start_new_thread(gameLoop, (s,))
   start_new_thread(connectionLoop, (s,))
   start_new_thread(cleanClients,(s,))
   while True:
      time.sleep(1)

if __name__ == '__main__':
   main()
