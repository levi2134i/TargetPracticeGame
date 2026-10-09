#!/usr/bin/env python3
import socket
import json
import threading
import pygame
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
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 20
        self.height = 30
        self.speed = 5
        self.score = 0
        self.kills = 0
        self.shots_fired = 0
        self.shots_hit = 0
        self.health = 100
        self.angle = 0

    def update(self, keys):
        if keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_s]:
            self.y += self.speed
        if keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_d]:
            self.x += self.speed

    def draw(self, surface, color=(0, 255, 0)):
        pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.height))
        # Draw direction indicator
        end_x = self.x + 10 + 20 * math.cos(math.radians(self.angle))
        end_y = self.y + 15 + 20 * math.sin(math.radians(self.angle))
        pygame.draw.line(surface, (255, 255, 0), (self.x + 10, self.y + 15), (end_x, end_y), 2)

class Target:
    def __init__(self, x, y, radius=15):
        self.x = x
        self.y = y
        self.radius = radius
        self.health = 100
        self.speed = random.randint(1, 3)
        self.angle = random.uniform(0, 360)

    def update(self):
        self.x += self.speed * math.cos(math.radians(self.angle))
        self.y += self.speed * math.sin(math.radians(self.angle))
        
        # Bounce off walls
        if self.x - self.radius < 0 or self.x + self.radius > 800:
            self.angle = 180 - self.angle
        if self.y - self.radius < 0 or self.y + self.radius > 600:
            self.angle = -self.angle
        
        self.x = max(self.radius, min(800 - self.radius, self.x))
        self.y = max(self.radius, min(600 - self.radius, self.y))

    def draw(self, surface, color=(255, 0, 0)):
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (255, 255, 255), (int(self.x), int(self.y)), self.radius, 2)

class Bullet:
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 8
        self.lifetime = 300  # frames
        self.radius = 3

    def update(self):
        self.x += self.speed * math.cos(math.radians(self.angle))
        self.y += self.speed * math.sin(math.radians(self.angle))
        self.lifetime -= 1
        return self.lifetime > 0

    def draw(self, surface, color=(255, 255, 0)):
        pygame.draw.circle(surface, color, (int(self.x), int(self.y)), self.radius)

class GameClient:
    def __init__(self, server_ip='localhost', server_port=5000):
        pygame.init()
        self.width = 800
        self.height = 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Target Practice - LAN Game")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.socket = None
        self.server_ip = server_ip
        self.server_port = server_port
        self.player_id = None
        self.player_name = ""
        self.game_state = GameState.MENU
        self.current_map = 'forest'
        self.leaderboard = []
        self.remote_players = {}
        
        self.player = Player(self.width // 2, self.height // 2)
        self.targets = []
        self.bullets = []
        self.game_active = False
        self.game_time = 0
        self.game_duration = 300  # 5 minutes
        
        self.input_name = ""
        self.input_server_ip = server_ip

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
            pass  # Update remote player score if needed
            
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
            x = random.randint(50, self.width - 50)
            y = random.randint(50, self.height - 50)
            self.targets.append(Target(x, y))

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

    def draw_menu(self):
        self.screen.fill((20, 20, 20))
        
        title = self.font.render("TARGET PRACTICE", True, (0, 255, 0))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 50))
        
        # Input fields
        ip_label = self.small_font.render("Server IP:", True, (255, 255, 255))
        self.screen.blit(ip_label, (150, 150))
        ip_input = self.small_font.render(self.input_server_ip, True, (0, 255, 0))
        self.screen.blit(ip_input, (150, 180))
        
        name_label = self.small_font.render("Player Name:", True, (255, 255, 255))
        self.screen.blit(name_label, (150, 250))
        name_input = self.small_font.render(self.input_name or "Enter name...", True, (0, 255, 0))
        self.screen.blit(name_input, (150, 280))
        
        instructions = self.small_font.render("WASD: Move | Mouse: Aim | Click: Shoot", True, (200, 200, 200))
        self.screen.blit(instructions, (self.width // 2 - instructions.get_width() // 2, 400))
        
        connect_text = self.font.render("Press ENTER to Connect & Play", True, (0, 255, 0))
        self.screen.blit(connect_text, (self.width // 2 - connect_text.get_width() // 2, 480))
        
        leaderboard_text = self.small_font.render("Press L to view Leaderboard", True, (100, 100, 255))
        self.screen.blit(leaderboard_text, (self.width // 2 - leaderboard_text.get_width() // 2, 520))

    def draw_game(self):
        # Map background
        map_colors = {
            'forest': (34, 139, 34),
            'urban': (100, 100, 100),
            'desert': (210, 180, 140),
            'arctic': (240, 248, 255)
        }
        self.screen.fill(map_colors.get(self.current_map, (0, 0, 0)))
        
        # Draw grid
        for x in range(0, self.width, 50):
            pygame.draw.line(self.screen, (50, 50, 50), (x, 0), (x, self.height), 1)
        for y in range(0, self.height, 50):
            pygame.draw.line(self.screen, (50, 50, 50), (0, y), (self.width, y), 1)
        
        # Draw targets
        for target in self.targets:
            target.draw(self.screen)
        
        # Draw player
        self.player.draw(self.screen)
        
        # Draw bullets
        for bullet in self.bullets:
            bullet.draw(self.screen)
        
        # Draw HUD
        time_left = max(0, self.game_duration - self.game_time // 60)
        time_text = self.small_font.render(f"Time: {time_left}s", True, (255, 255, 255))
        score_text = self.small_font.render(f"Score: {self.player.score}", True, (0, 255, 0))
        kills_text = self.small_font.render(f"Kills: {self.player.kills}", True, (255, 100, 0))
        accuracy = (self.player.shots_hit / max(1, self.player.shots_fired)) * 100
        accuracy_text = self.small_font.render(f"Accuracy: {accuracy:.1f}%", True, (100, 200, 255))
        map_text = self.small_font.render(f"Map: {self.current_map.capitalize()}", True, (200, 200, 200))
        
        self.screen.blit(time_text, (10, 10))
        self.screen.blit(score_text, (10, 40))
        self.screen.blit(kills_text, (10, 70))
        self.screen.blit(accuracy_text, (10, 100))
        self.screen.blit(map_text, (self.width - 200, 10))

    def draw_leaderboard(self):
        self.screen.fill((20, 20, 20))
        
        title = self.font.render("LEADERBOARD", True, (0, 255, 0))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 20))
        
        y_offset = 70
        for i, entry in enumerate(self.leaderboard[:10]):
            rank = f"#{i+1}"
            name = entry.get('player_name', 'Unknown')
            score = entry.get('score', 0)
            text = f"{rank} {name}: {score}"
            text_surface = self.small_font.render(text, True, (100 + i*15, 255 - i*15, 100))
            self.screen.blit(text_surface, (50, y_offset))
            y_offset += 40
        
        back_text = self.small_font.render("Press MENU to go back", True, (200, 200, 200))
        self.screen.blit(back_text, (self.width // 2 - back_text.get_width() // 2, 550))

    def draw_game_over(self):
        self.screen.fill((20, 20, 20))
        
        title = self.font.render("GAME OVER", True, (255, 0, 0))
        self.screen.blit(title, (self.width // 2 - title.get_width() // 2, 100))
        
        final_score = self.font.render(f"Final Score: {self.player.score}", True, (0, 255, 0))
        self.screen.blit(final_score, (self.width // 2 - final_score.get_width() // 2, 200))
        
        kills_text = self.small_font.render(f"Targets Destroyed: {self.player.kills}", True, (255, 200, 0))
        self.screen.blit(kills_text, (self.width // 2 - kills_text.get_width() // 2, 280))
        
        accuracy = (self.player.shots_hit / max(1, self.player.shots_fired)) * 100
        accuracy_text = self.small_font.render(f"Accuracy: {accuracy:.1f}%", True, (100, 200, 255))
        self.screen.blit(accuracy_text, (self.width // 2 - accuracy_text.get_width() // 2, 320))
        
        # Send final score to server
        self.send_message({
            'type': 'end_game',
            'player_id': self.player_id,
            'final_score': self.player.score,
            'player_name': self.input_name or 'Player'
        })
        
        restart_text = self.small_font.render("Press ENTER to return to menu", True, (200, 200, 200))
        self.screen.blit(restart_text, (self.width // 2 - restart_text.get_width() // 2, 450))

    def update(self, events):
        if self.game_state == GameState.MENU:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        if self.connect_to_server():
                            self.start_game()
                    elif event.key == pygame.K_l:
                        self.send_message({'type': 'get_leaderboard'})
                        self.game_state = GameState.LEADERBOARD
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_name = self.input_name[:-1]
                    elif event.unicode.isprintable():
                        if len(self.input_name) < 20:
                            self.input_name += event.unicode
        
        elif self.game_state == GameState.PLAYING:
            if self.game_active:
                self.game_time += 1
                
                keys = pygame.key.get_pressed()
                self.player.update(keys)
                
                # Get mouse angle
                mouse_x, mouse_y = pygame.mouse.get_pos()
                dx = mouse_x - (self.player.x + 10)
                dy = mouse_y - (self.player.y + 15)
                self.player.angle = math.degrees(math.atan2(dy, dx))
                
                # Update targets
                for target in self.targets[:]:
                    target.update()
                
                # Update bullets
                for bullet in self.bullets[:]:
                    if not bullet.update():
                        self.bullets.remove(bullet)
                    else:
                        # Check collision with targets
                        for target in self.targets[:]:
                            dist = math.hypot(bullet.x - target.x, bullet.y - target.y)
                            if dist < target.radius + bullet.radius:
                                self.player.score += 10
                                self.player.kills += 1
                                self.player.shots_hit += 1
                                self.targets.remove(target)
                                self.bullets.remove(bullet)
                                
                                # Spawn new target
                                x = random.randint(50, self.width - 50)
                                y = random.randint(50, self.height - 50)
                                self.targets.append(Target(x, y))
                                break
                
                # Boundary check for player
                self.player.x = max(0, min(self.width - self.player.width, self.player.x))
                self.player.y = max(0, min(self.height - self.player.height, self.player.y))
                
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
            
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        bullet = Bullet(self.player.x + 10, self.player.y + 15, self.player.angle)
                        self.bullets.append(bullet)
                        self.player.shots_fired += 1
                
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.game_active = False
                        self.game_state = GameState.MENU
        
        elif self.game_state == GameState.LEADERBOARD:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m or event.key == pygame.K_ESCAPE:
                        self.game_state = GameState.MENU
        
        elif self.game_state == GameState.GAME_OVER:
            for event in events:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        self.game_state = GameState.MENU
                        self.input_name = ""

    def run(self):
        running = True
        while running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    running = False
            
            self.update(events)
            
            if self.game_state == GameState.MENU:
                self.draw_menu()
            elif self.game_state == GameState.PLAYING:
                self.draw_game()
            elif self.game_state == GameState.LEADERBOARD:
                self.draw_leaderboard()
            elif self.game_state == GameState.GAME_OVER:
                self.draw_game_over()
            
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()
        if self.socket:
            self.socket.close()

if __name__ == '__main__':
    import sys
    server_ip = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    client = GameClient(server_ip=server_ip)
    client.run()
