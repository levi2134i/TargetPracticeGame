#!/usr/bin/env python3
import socket
import json
import threading
import os
from datetime import datetime


class GameServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}
        self.lock = threading.Lock()
        self.leaderboard_file = 'leaderboard.json'
        self.maps = ['forest', 'warehouse', 'desert', 'ice', 'hangar']
        self.difficulties = ['rookie', 'veteran', 'elite']
        self.game_state = {
            'players': {},
            'leaderboard': [],
            'current_map': 'forest',
            'difficulty': 'veteran',
            'round_time': 300,
            'status': 'waiting'
        }
        self.load_leaderboard()

    def load_leaderboard(self):
        if os.path.exists(self.leaderboard_file):
            try:
                with open(self.leaderboard_file, 'r', encoding='utf-8') as f:
                    self.game_state['leaderboard'] = json.load(f)
            except Exception:
                self.game_state['leaderboard'] = []
        else:
            self.game_state['leaderboard'] = []

    def save_leaderboard(self):
        with open(self.leaderboard_file, 'w', encoding='utf-8') as f:
            json.dump(self.game_state['leaderboard'], f, indent=2)

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(10)
        print(f"[SERVER] LAN server started on {self.host}:{self.port}")
        print(f"[SERVER] Maps: {self.maps}")
        print(f"[SERVER] Waiting for players...")
        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                thread = threading.Thread(target=self.handle_client, args=(client_socket, addr), daemon=True)
                thread.start()
            except KeyboardInterrupt:
                break
        self.server_socket.close()

    def handle_client(self, client_socket, addr):
        client_id = f"{addr[0]}:{addr[1]}"
        self.clients[client_id] = client_socket
        self.send_message(client_socket, {
            'type': 'init',
            'client_id': client_id,
            'maps': self.maps,
            'difficulties': self.difficulties,
            'current_map': self.game_state['current_map'],
            'difficulty': self.game_state['difficulty']
        })

        try:
            while True:
                data = client_socket.recv(4096)
                if not data:
                    break
                payload = data.decode('utf-8', errors='ignore').strip()
                if not payload:
                    continue
                try:
                    msg = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                self.process_message(client_id, msg)
        except Exception as exc:
            print(f"[ERROR] {client_id}: {exc}")
        finally:
            with self.lock:
                self.game_state['players'].pop(client_id, None)
            self.clients.pop(client_id, None)
            self.broadcast({'type': 'player_left', 'player_id': client_id})
            client_socket.close()

    def process_message(self, client_id, msg):
        msg_type = msg.get('type')

        if msg_type == 'join_game':
            player_name = msg.get('player_name', f'Player_{client_id[-4:]}')
            weapon = msg.get('weapon', 'rifle')
            with self.lock:
                self.game_state['players'][client_id] = {
                    'name': player_name,
                    'weapon': weapon,
                    'score': 0,
                    'kills': 0,
                    'accuracy': 0,
                    'joined_at': datetime.now().isoformat()
                }
            self.broadcast({
                'type': 'player_joined',
                'player_id': client_id,
                'player_name': player_name,
                'players': self.game_state['players'],
                'maps': self.maps,
                'difficulty': self.game_state['difficulty']
            })

        elif msg_type == 'set_weapon':
            weapon = msg.get('weapon', 'rifle')
            with self.lock:
                if client_id in self.game_state['players']:
                    self.game_state['players'][client_id]['weapon'] = weapon

        elif msg_type == 'set_difficulty':
            difficulty = msg.get('difficulty', 'veteran')
            if difficulty in self.difficulties:
                with self.lock:
                    self.game_state['difficulty'] = difficulty
                self.broadcast({'type': 'difficulty_changed', 'difficulty': difficulty})

        elif msg_type == 'change_map':
            chosen = msg.get('map', 'forest')
            if chosen in self.maps:
                with self.lock:
                    self.game_state['current_map'] = chosen
                self.broadcast({'type': 'map_changed', 'map': chosen})

        elif msg_type == 'update_score':
            with self.lock:
                if client_id in self.game_state['players']:
                    player = self.game_state['players'][client_id]
                    player['score'] = int(msg.get('score', player.get('score', 0)))
                    player['kills'] = int(msg.get('kills', player.get('kills', 0)))
                    player['accuracy'] = float(msg.get('accuracy', player.get('accuracy', 0)))
            self.broadcast({
                'type': 'score_update',
                'player_id': client_id,
                'score': msg.get('score', 0),
                'kills': msg.get('kills', 0),
                'accuracy': msg.get('accuracy', 0)
            })

        elif msg_type == 'end_game':
            player_name = msg.get('player_name', 'Unknown')
            score = int(msg.get('final_score', 0))
            weapon = msg.get('weapon', 'rifle')
            timestamp = datetime.now().isoformat()
            with self.lock:
                self.game_state['leaderboard'].append({
                    'player_name': player_name,
                    'score': score,
                    'weapon': weapon,
                    'map': self.game_state['current_map'],
                    'difficulty': self.game_state['difficulty'],
                    'timestamp': timestamp
                })
                self.game_state['leaderboard'] = sorted(
                    self.game_state['leaderboard'], key=lambda x: x['score'], reverse=True
                )[:150]
                self.save_leaderboard()
            self.broadcast({'type': 'leaderboard_update', 'leaderboard': self.game_state['leaderboard']})

        elif msg_type == 'get_leaderboard':
            with self.lock:
                leaderboard = self.game_state['leaderboard']
            self.send_message(client_socket, {'type': 'leaderboard_data', 'leaderboard': leaderboard})

        elif msg_type == 'get_state':
            self.send_message(client_socket, {'type': 'state_data', 'state': self.game_state})

    def send_message(self, client_socket, msg):
        try:
            client_socket.send((json.dumps(msg) + '\n').encode('utf-8'))
        except Exception:
            pass

    def broadcast(self, msg):
        payload = (json.dumps(msg) + '\n').encode('utf-8')
        for client_socket in list(self.clients.values()):
            try:
                client_socket.send(payload)
            except Exception:
                pass


if __name__ == '__main__':
    server = GameServer()
    server.start()

































































































































































































































































































































