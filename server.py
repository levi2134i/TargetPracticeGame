#!/usr/bin/env python3
import socket
import threading
import json
import time
from datetime import datetime
import os

class GameServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}
        self.game_state = {
            'players': {},
            'leaderboard': [],
            'current_map': 'forest',
            'game_active': True
        }
        self.lock = threading.Lock()
        self.leaderboard_file = 'leaderboard.json'
        self.load_leaderboard()

    def load_leaderboard(self):
        if os.path.exists(self.leaderboard_file):
            try:
                with open(self.leaderboard_file, 'r') as f:
                    self.game_state['leaderboard'] = json.load(f)
            except:
                self.game_state['leaderboard'] = []
        else:
            self.game_state['leaderboard'] = []

    def save_leaderboard(self):
        with open(self.leaderboard_file, 'w') as f:
            json.dump(self.game_state['leaderboard'], f, indent=2)

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"[SERVER] Started on {self.host}:{self.port}")
        print(f"[SERVER] Waiting for connections...")
        
        try:
            while True:
                try:
                    client_socket, addr = self.server_socket.accept()
                    print(f"[CONNECTION] Client connected from {addr}")
                    thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                    thread.daemon = True
                    thread.start()
                except:
                    pass
        except KeyboardInterrupt:
            print("[SERVER] Shutting down...")
            self.server_socket.close()

    def handle_client(self, client_socket, addr):
        client_id = f"{addr[0]}:{addr[1]}"
        self.clients[client_id] = client_socket
        
        try:
            # Send initial game state
            self.send_message(client_socket, {
                'type': 'init',
                'client_id': client_id,
                'game_state': self.game_state,
                'maps': self.get_available_maps()
            })
            
            while True:
                data = client_socket.recv(1024).decode('utf-8')
                if not data:
                    break
                
                message = json.loads(data)
                self.process_message(client_id, message, client_socket)
                
        except Exception as e:
            print(f"[ERROR] Client {client_id}: {e}")
        finally:
            if client_id in self.clients:
                del self.clients[client_id]
            client_socket.close()
            print(f"[DISCONNECT] Client {client_id} disconnected")
            self.broadcast({
                'type': 'player_left',
                'player_id': client_id
            })

    def process_message(self, client_id, message, client_socket):
        msg_type = message.get('type')
        
        if msg_type == 'join_game':
            player_name = message.get('player_name', f"Player_{client_id[-4:]}")
            with self.lock:
                self.game_state['players'][client_id] = {
                    'name': player_name,
                    'score': 0,
                    'kills': 0,
                    'accuracy': 100,
                    'joined_at': datetime.now().isoformat()
                }
            self.broadcast({
                'type': 'player_joined',
                'player_id': client_id,
                'player_name': player_name,
                'players': self.game_state['players']
            })
            
        elif msg_type == 'update_score':
            player_id = message.get('player_id')
            score = message.get('score')
            kills = message.get('kills')
            accuracy = message.get('accuracy')
            
            with self.lock:
                if player_id in self.game_state['players']:
                    self.game_state['players'][player_id]['score'] = score
                    self.game_state['players'][player_id]['kills'] = kills
                    self.game_state['players'][player_id]['accuracy'] = accuracy
            
            self.broadcast({
                'type': 'score_update',
                'player_id': player_id,
                'score': score,
                'kills': kills,
                'accuracy': accuracy
            })
            
        elif msg_type == 'change_map':
            new_map = message.get('map')
            with self.lock:
                self.game_state['current_map'] = new_map
            self.broadcast({
                'type': 'map_changed',
                'map': new_map
            })
            
        elif msg_type == 'end_game':
            player_id = message.get('player_id')
            final_score = message.get('final_score')
            player_name = message.get('player_name')
            
            with self.lock:
                # Add to leaderboard
                self.game_state['leaderboard'].append({
                    'player_name': player_name,
                    'score': final_score,
                    'timestamp': datetime.now().isoformat(),
                    'map': self.game_state['current_map']
                })
                # Sort and keep top 100
                self.game_state['leaderboard'].sort(key=lambda x: x['score'], reverse=True)
                self.game_state['leaderboard'] = self.game_state['leaderboard'][:100]
                self.save_leaderboard()
            
            self.broadcast({
                'type': 'leaderboard_update',
                'leaderboard': self.game_state['leaderboard']
            })
            
        elif msg_type == 'get_leaderboard':
            with self.lock:
                leaderboard = self.game_state['leaderboard']
            self.send_message(client_socket, {
                'type': 'leaderboard_data',
                'leaderboard': leaderboard
            })

    def send_message(self, client_socket, message):
        try:
            client_socket.send((json.dumps(message) + '\n').encode('utf-8'))
        except:
            pass

    def broadcast(self, message):
        msg_str = json.dumps(message) + '\n'
        for client_id, client_socket in list(self.clients.items()):
            try:
                client_socket.send(msg_str.encode('utf-8'))
            except:
                pass

    def get_available_maps(self):
        return ['forest', 'urban', 'desert', 'arctic']

if __name__ == '__main__':
    server = GameServer()
    server.start()
