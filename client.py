#!/usr/bin/env python3
import socket
import json
import threading
import arcade
import random
import math
from enum import Enum

class GameState(Enum):
    MENU = 1
    JOINING = 2
    PLAYING = 3
    SETTINGS = 4
    LEADERBOARD = 5
    GAME_OVER = 6

class Player:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.width = 20
        self.height = 40  # Full body height
        self.depth = 15
        self.speed = 5
        self.score = 0
        self.kills = 0
        self.shots_fired = 0
        self.shots_hit = 0
        self.health = 100
        self.pitch = 0  # Head angle up/down
        self.yaw = 0    # Head angle left/right
        self.head_height = 35  # Head level from ground

    def update(self, keys):
        if keys[arcade.key.W]:
            self.z -= self.speed
        if keys[arcade.key.S]:
            self.z += self.speed
        if keys[arcade.key.A]:
            self.x -= self.speed
        if keys[arcade.key.D]:
            self.x += self.speed
        if keys[arcade.key.SPACE]:
            self.y = min(self.y + self.speed, 20)  # Jump
        else:
            self.y = max(self.y - self.speed * 0.5, 0)  # Fall

    def draw_3d_projection(self, surface, width, height, camera_distance=50):
        """Draw stick figure in 3D perspective"""
        # Project 3D position to 2D screen
        scale = camera_distance / (self.z + camera_distance)
        screen_x = width // 2 + (self.x - width // 2) * scale
        screen_y = height // 2 + (self.y - height // 2) * scale
        
        # Draw stick figure
        # Head
        head_radius = int(8 * scale)
        arcade.draw_circle_filled(screen_x, screen_y + int(30 * scale), head_radius, arcade.GREEN)
        
        # Body
        body_y = screen_y + int(10 * scale)
        arcade.draw_line(screen_x, screen_y + int(28 * scale), screen_x, body_y, arcade.GREEN, 2)
        
        # Left arm
        arcade.draw_line(screen_x, body_y, screen_x - int(10 * scale), body_y + int(5 * scale), arcade.GREEN, 2)
        # Right arm
        arcade.draw_line(screen_x, body_y, screen_x + int(10 * scale), body_y + int(5 * scale), arcade.GREEN, 2)
        
        # Left leg
        arcade.draw_line(screen_x, body_y, screen_x - int(5 * scale), body_y - int(15 * scale), arcade.GREEN, 2)
        # Right leg
        arcade.draw_line(screen_x, body_y, screen_x + int(5 * scale), body_y - int(15 * scale), arcade.GREEN, 2)

class StickFigureTarget:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.vx = random.uniform(-1, 1)
        self.vy = 0
        self.vz = random.uniform(-1, 1)
        self.health = 100
        self.scale = 1.0

    def update(self, arena_width, arena_height, arena_depth):
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz
        
        # Gravity
        if self.y > 0:
            self.vy -= 0.2
        else:
            self.y = 0
            self.vy = random.uniform(0.5, 2)  # Bounce
        
        # Bounce off walls
        if self.x <= 0 or self.x >= arena_width:
            self.vx *= -1
        if self.z <= 0 or self.z >= arena_depth:
            self.vz *= -1
        
        self.x = max(0, min(arena_width, self.x))
        self.z = max(0, min(arena_depth, self.z))

    def draw_3d_projection(self, screen_width, screen_height, player_z, camera_distance=50):
        """Draw stick figure target in 3D perspective"""
        # Distance from camera (player)
        depth_diff = self.z - player_z + camera_distance
        if depth_diff <= 0:
            return  # Behind camera
        
        scale = camera_distance / depth_diff
        screen_x = screen_width // 2 + (self.x - screen_width // 2) * scale
        screen_y = screen_height // 2 - (self.y - screen_height // 2) * scale
        
        # Draw stick figure enemy
        # Head
        head_radius = int(6 * scale)
        arcade.draw_circle_filled(screen_x, screen_y + int(25 * scale), head_radius, arcade.RED)
        
        # Body
        body_y = screen_y + int(8 * scale)
        arcade.draw_line(screen_x, screen_y + int(23 * scale), screen_x, body_y, arcade.RED, 2)
        
        # Left arm
        arcade.draw_line(screen_x, body_y, screen_x - int(8 * scale), body_y + int(4 * scale), arcade.RED, 2)
        # Right arm
        arcade.draw_line(screen_x, body_y, screen_x + int(8 * scale), body_y + int(4 * scale), arcade.RED, 2)
        
        # Left leg
        arcade.draw_line(screen_x, body_y, screen_x - int(4 * scale), body_y - int(12 * scale), arcade.RED, 2)
        # Right leg
        arcade.draw_line(screen_x, body_y, screen_x + int(4 * scale), body_y - int(12 * scale), arcade.RED, 2)
        
        # Health bar
        bar_width = 20 * scale
        bar_height = 3
        arcade.draw_rectangle_outline(screen_x, screen_y + int(32 * scale), bar_width, bar_height, arcade.WHITE)
        arcade.draw_rectangle_filled(screen_x, screen_y + int(32 * scale), bar_width * (self.health / 100), bar_height, arcade.GREEN)

class Bullet:
    def __init__(self, x, y, z, pitch, yaw, speed=15):
        self.x = x
        self.y = y
        self.z = z
        self.pitch = pitch
        self.yaw = yaw
        self.speed = speed
        self.lifetime = 300
        self.radius = 2

    def update(self):
        # Convert pitch/yaw to direction
        dx = self.speed * math.cos(math.radians(self.pitch)) * math.sin(math.radians(self.yaw))
        dy = self.speed * math.sin(math.radians(self.pitch))
        dz = self.speed * math.cos(math.radians(self.pitch)) * math.cos(math.radians(self.yaw))
        
        self.x += dx
        self.y += dy
        self.z += dz
        self.lifetime -= 1
        return self.lifetime > 0

    def distance_to(self, target):
        return math.sqrt((self.x - target.x)**2 + (self.y - target.y)**2 + (self.z - target.z)**2)

class GameClient(arcade.Window):
    def __init__(self, server_ip='localhost', server_port=5000):
        super().__init__(1200, 800, "Target Practice - 3D Arena")
        
        self.socket = None
        self.server_ip = server_ip
        self.server_port = server_port
        self.player_id = None
        self.player_name = ""
        self.game_state = GameState.MENU
        self.current_map = 'forest'
        self.leaderboard = []
        self.remote_players = {}
        
        # 3D Arena dimensions
        self.arena_width = 200
        self.arena_height = 100
        self.arena_depth = 200
        
        self.player = Player(self.arena_width // 2, 5, self.arena_depth // 2)
        self.targets = []
        self.bullets = []
        self.game_active = False
        self.game_time = 0
        self.game_duration = 300  # 5 minutes
        
        self.input_name = ""
        self.input_server_ip = server_ip
        self.input_mode = "ip"  # Current input field
        
        # Mouse tracking for aiming
        self.mouse_x = 0
        self.mouse_y = 0
        
        arcade.set_background_color(arcade.DARK_SLATE_GRAY)

    def connect_to_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.input_server_ip, self.server_port))
            self.socket.settimeout(0.1)
            print(f"Connected to server at {self.input_server_ip}:{self.server_port}")
            
            # Start receiver thread
            recv_thread = threading.Thread(target=self.receive_messages, daemon=True)
            recv_thread.start()
            
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False

    def send_message(self, message):
        try:
            if self.socket:
                self.socket.send((json.dumps(message) + '\n').encode('utf-8'))
        except Exception as e:
            print(f"Send error: {e}")

    def receive_messages(self):
        buffer = ""
        while True:
            try:
                data = self.socket.recv(1024).decode('utf-8')
                if not data:
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line:
                        message = json.loads(line)
                        self.handle_message(message)
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Receive error: {e}")
                break

    def handle_message(self, message):
        msg_type = message.get('type')
        
        if msg_type == 'init':
            self.player_id = message.get('client_id')
            print(f"Player ID: {self.player_id}")
            
        elif msg_type == 'player_joined':
            players = message.get('players', {})
            self.remote_players = players
            
        elif msg_type == 'score_update':
            pass
            
        elif msg_type == 'map_changed':
            self.current_map = message.get('map')
            self.spawn_targets()
            
        elif msg_type == 'leaderboard_update':
            self.leaderboard = message.get('leaderboard', [])
            
        elif msg_type == 'leaderboard_data':
            self.leaderboard = message.get('leaderboard', [])

    def spawn_targets(self, count=5):
        self.targets = []
        for _ in range(count):
            x = random.randint(20, self.arena_width - 20)
            y = random.randint(5, 30)
            z = random.randint(20, self.arena_depth - 20)
            self.targets.append(StickFigureTarget(x, y, z))

    def start_game(self):
        self.game_state = GameState.PLAYING
        self.game_active = True
        self.game_time = 0
        self.player.score = 0
        self.player.kills = 0
        self.player.shots_fired = 0
        self.player.shots_hit = 0
        self.spawn_targets()
        
        self.send_message({
            'type': 'join_game',
            'player_name': self.input_name or 'Player'
        })

    def draw_3d_arena(self):
        """Draw the 3D arena wireframe"""
        screen_width = self.width
        screen_height = self.height
        camera_distance = 80
        player_z = self.player.z
        
        # Draw floor grid
        grid_size = 20
        for x in range(0, self.arena_width, grid_size):
            for z in range(0, self.arena_depth, grid_size):
                # Project to 2D
                scale = camera_distance / (z - player_z + camera_distance)
                if scale > 0:
                    x1 = screen_width // 2 + (x - screen_width // 2) * scale
                    y1 = screen_height // 2
                    x2 = screen_width // 2 + ((x + grid_size) - screen_width // 2) * scale
                    z_next_scale = camera_distance / ((z + grid_size) - player_z + camera_distance)
                    y2 = screen_height // 2 - grid_size * z_next_scale
                    
                    if 0 <= x1 < screen_width and 0 <= x2 < screen_width:
                        arcade.draw_line(int(x1), int(y1), int(x2), int(y1), arcade.DARK_CYAN, 1)
        
        # Draw depth lines
        for z in range(0, self.arena_depth, grid_size):
            scale = camera_distance / (z - player_z + camera_distance)
            if scale > 0:
                x_left = screen_width // 2 - screen_width // 4 * scale
                y = screen_height // 2
                x_right = screen_width // 2 + screen_width // 4 * scale
                if 0 <= y < screen_height:
                    arcade.draw_line(int(x_left), int(y), int(x_right), int(y), arcade.DARK_CYAN, 1)

    def draw_crosshair(self):
        """Draw centered crosshair"""
        center_x = self.width // 2
        center_y = self.height // 2
        crosshair_size = 15
        thickness = 2
        
        # Vertical line
        arcade.draw_line(center_x, center_y - crosshair_size, center_x, center_y + crosshair_size, 
                        arcade.GREEN, thickness)
        # Horizontal line
        arcade.draw_line(center_x - crosshair_size, center_y, center_x + crosshair_size, center_y, 
                        arcade.GREEN, thickness)
        # Center dot
        arcade.draw_circle_filled(center_x, center_y, 2, arcade.GREEN)

    def on_draw(self):
        arcade.start_render()
        
        if self.game_state == GameState.MENU:
            self.draw_menu()
        elif self.game_state == GameState.PLAYING:
            self.draw_game()
        elif self.game_state == GameState.LEADERBOARD:
            self.draw_leaderboard()
        elif self.game_state == GameState.GAME_OVER:
            self.draw_game_over()

    def draw_menu(self):
        arcade.draw_rectangle_filled(self.width // 2, self.height // 2, self.width, self.height, 
                                     arcade.BLACK)
        
        arcade.draw_text("TARGET PRACTICE - 3D ARENA", 
                        self.width // 2, self.height - 100,
                        20, arcade.GREEN, anchor_x="center", bold=True)
        
        arcade.draw_text("Server IP:", 100, self.height - 200, 14, arcade.WHITE)
        arcade.draw_text(self.input_server_ip, 100, self.height - 230, 14, arcade.GREEN)
        
        arcade.draw_text("Player Name:", 100, self.height - 300, 14, arcade.WHITE)
        arcade.draw_text(self.input_name or "Enter name...", 100, self.height - 330, 14, arcade.GREEN)
        
        arcade.draw_text("Controls:", self.width // 2, 250, 14, arcade.YELLOW, anchor_x="center")
        arcade.draw_text("WASD: Move | Mouse: Aim | Click: Shoot | SPACE: Jump", 
                        self.width // 2, 220, 12, arcade.LIGHT_GRAY, anchor_x="center")
        arcade.draw_text("Press ENTER to Connect & Play", 
                        self.width // 2, 100, 14, arcade.GREEN, anchor_x="center")
        arcade.draw_text("Press L to view Leaderboard", 
                        self.width // 2, 50, 12, arcade.LIGHT_BLUE, anchor_x="center")

    def draw_game(self):
        # Draw 3D arena background
        map_colors = {
            'forest': (34, 89, 34),
            'urban': (80, 80, 80),
            'desert': (180, 160, 100),
            'arctic': (200, 220, 240)
        }
        bg_color = map_colors.get(self.current_map, (40, 40, 40))
        arcade.draw_rectangle_filled(self.width // 2, self.height // 2, self.width, self.height, bg_color)
        
        # Draw arena grid
        self.draw_3d_arena()
        
        # Draw targets
        for target in self.targets:
            target.draw_3d_projection(self.width, self.height, self.player.z)
        
        # Draw bullets (small dots)
        for bullet in self.bullets:
            scale = 80 / (bullet.z - self.player.z + 80) if bullet.z > self.player.z else 0.1
            screen_x = self.width // 2 + (bullet.x - self.width // 2) * scale
            screen_y = self.height // 2 - (bullet.y - self.height // 2) * scale
            if 0 <= screen_x < self.width and 0 <= screen_y < self.height:
                arcade.draw_circle_filled(int(screen_x), int(screen_y), 3, arcade.YELLOW)
        
        # Draw crosshair
        self.draw_crosshair()
        
        # Draw HUD
        time_left = max(0, self.game_duration - self.game_time // 60)
        arcade.draw_text(f"Time: {time_left}s", 10, self.height - 30, 14, arcade.WHITE)
        arcade.draw_text(f"Score: {self.player.score}", 10, self.height - 60, 14, arcade.GREEN)
        arcade.draw_text(f"Kills: {self.player.kills}", 10, self.height - 90, 14, arcade.YELLOW)
        
        accuracy = (self.player.shots_hit / max(1, self.player.shots_fired)) * 100
        arcade.draw_text(f"Accuracy: {accuracy:.1f}%", 10, self.height - 120, 14, arcade.LIGHT_BLUE)
        arcade.draw_text(f"Map: {self.current_map.capitalize()}", 
                        self.width - 200, self.height - 30, 14, arcade.LIGHT_GRAY)
        
        # Player position indicator
        arcade.draw_text(f"Pos: ({int(self.player.x)}, {int(self.player.z)})", 
                        10, 10, 12, arcade.LIGHT_GRAY)

    def draw_leaderboard(self):
        arcade.draw_rectangle_filled(self.width // 2, self.height // 2, self.width, self.height, 
                                     arcade.BLACK)
        
        arcade.draw_text("LEADERBOARD", self.width // 2, self.height - 50, 
                        20, arcade.GREEN, anchor_x="center", bold=True)
        
        y_offset = self.height - 120
        for i, entry in enumerate(self.leaderboard[:10]):
            name = entry.get('player_name', 'Unknown')
            score = entry.get('score', 0)
            text = f"#{i+1} {name}: {score}"
            color = (100 + i*15, 255 - i*15, 100)
            arcade.draw_text(text, 50, y_offset, 14, color)
            y_offset -= 50
        
        arcade.draw_text("Press MENU/M to go back", self.width // 2, 50, 12, 
                        arcade.LIGHT_GRAY, anchor_x="center")

    def draw_game_over(self):
        arcade.draw_rectangle_filled(self.width // 2, self.height // 2, self.width, self.height, 
                                     arcade.BLACK)
        
        arcade.draw_text("GAME OVER", self.width // 2, self.height - 100, 
                        20, arcade.RED, anchor_x="center", bold=True)
        arcade.draw_text(f"Final Score: {self.player.score}", self.width // 2, self.height - 180, 
                        18, arcade.GREEN, anchor_x="center")
        arcade.draw_text(f"Targets Destroyed: {self.player.kills}", self.width // 2, self.height - 240, 
                        14, arcade.YELLOW, anchor_x="center")
        
        accuracy = (self.player.shots_hit / max(1, self.player.shots_fired)) * 100
        arcade.draw_text(f"Accuracy: {accuracy:.1f}%", self.width // 2, self.height - 290, 
                        14, arcade.LIGHT_BLUE, anchor_x="center")
        
        self.send_message({
            'type': 'end_game',
            'player_id': self.player_id,
            'final_score': self.player.score,
            'player_name': self.input_name or 'Player'
        })
        
        arcade.draw_text("Press ENTER to return to menu", self.width // 2, 100, 14, 
                        arcade.LIGHT_GRAY, anchor_x="center")

    def on_key_press(self, key, modifiers):
        if self.game_state == GameState.MENU:
            if key == arcade.key.RETURN:
                if self.connect_to_server():
                    self.start_game()
            elif key == arcade.key.L:
                self.send_message({'type': 'get_leaderboard'})
                self.game_state = GameState.LEADERBOARD
            elif key == arcade.key.BACKSPACE:
                if self.input_mode == "ip":
                    self.input_server_ip = self.input_server_ip[:-1]
                else:
                    self.input_name = self.input_name[:-1]
            elif key >= arcade.key.KEY_0 and key <= arcade.key.KEY_9:
                if self.input_mode == "ip":
                    if len(self.input_server_ip) < 15:
                        self.input_server_ip += chr(key)
            elif key == arcade.key.PERIOD:
                if self.input_mode == "ip":
                    self.input_server_ip += "."
            elif key == arcade.key.TAB:
                self.input_mode = "name" if self.input_mode == "ip" else "ip"
            elif key >= 32 and key <= 126:  # Printable ASCII
                if self.input_mode == "name" and len(self.input_name) < 20:
                    self.input_name += chr(key)
        
        elif self.game_state == GameState.PLAYING:
            if key == arcade.key.ESCAPE:
                self.game_active = False
                self.game_state = GameState.MENU
        
        elif self.game_state == GameState.LEADERBOARD:
            if key == arcade.key.M or key == arcade.key.ESCAPE:
                self.game_state = GameState.MENU
        
        elif self.game_state == GameState.GAME_OVER:
            if key == arcade.key.RETURN:
                self.game_state = GameState.MENU
                self.input_name = ""

    def on_mouse_motion(self, x, y, dx, dy):
        self.mouse_x = x
        self.mouse_y = y
        
        if self.game_state == GameState.PLAYING:
            # Calculate head angles based on mouse position
            center_x = self.width // 2
            center_y = self.height // 2
            
            # Pitch (up/down)
            mouse_y_offset = y - center_y
            self.player.pitch = max(-80, min(80, mouse_y_offset / 10))
            
            # Yaw (left/right)
            mouse_x_offset = x - center_x
            self.player.yaw = mouse_x_offset / 10

    def on_mouse_press(self, x, y, button, modifiers):
        if self.game_state == GameState.PLAYING and button == arcade.MOUSE_BUTTON_LEFT:
            # Fire bullet from player's head level
            bullet = Bullet(
                self.player.x,
                self.player.y + self.player.head_height,
                self.player.z,
                self.player.pitch,
                self.player.yaw
            )
            self.bullets.append(bullet)
            self.player.shots_fired += 1

    def on_update(self, delta_time):
        if self.game_state == GameState.PLAYING and self.game_active:
            self.game_time += 1
            
            # Get keys
            keys = arcade.key.key_is_pressed
            key_list = arcade.key.key_list
            
            self.player.update(key_list)
            
            # Boundary check
            self.player.x = max(5, min(self.arena_width - 5, self.player.x))
            self.player.z = max(10, min(self.arena_depth - 10, self.player.z))
            self.player.y = max(0, self.player.y)
            
            # Update targets
            for target in self.targets[:]:
                target.update(self.arena_width, self.arena_height, self.arena_depth)
            
            # Update bullets
            for bullet in self.bullets[:]:
                if not bullet.update():
                    self.bullets.remove(bullet)
                else:
                    # Check collision with targets
                    for target in self.targets[:]:
                        if bullet.distance_to(target) < 8:
                            self.player.score += 10
                            self.player.kills += 1
                            self.player.shots_hit += 1
                            self.targets.remove(target)
                            if bullet in self.bullets:
                                self.bullets.remove(bullet)
                            
                            # Spawn new target
                            x = random.randint(20, self.arena_width - 20)
                            y = random.randint(5, 30)
                            z = random.randint(20, self.arena_depth - 20)
                            self.targets.append(StickFigureTarget(x, y, z))
                            break
            
            # Check game end
            if self.game_time >= self.game_duration * 60:
                self.game_active = False
                self.game_state = GameState.GAME_OVER
                self.send_message({
                    'type': 'update_score',
                    'player_id': self.player_id,
                    'score': self.player.score,
                    'kills': self.player.kills,
                    'accuracy': (self.player.shots_hit / max(1, self.player.shots_fired)) * 100
                })

if __name__ == '__main__':
    import sys
    server_ip = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    app = GameClient(server_ip=server_ip)
    app.run()
