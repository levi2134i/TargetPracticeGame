#!/usr/bin/env python3
import socket
import json
import threading
import random
import math
import arcade
from enum import Enum


class GameState(Enum):
    MENU = 1
    SETTINGS = 2
    PLAYING = 3
    LEADERBOARD = 4
    GAME_OVER = 5


class Weapon:
    def __init__(self, name, damage, fire_rate, spread, pellets, color, recoil):
        self.name = name
        self.damage = damage
        self.fire_rate = fire_rate
        self.spread = spread
        self.pellets = pellets
        self.color = color
        self.recoil = recoil


class Player:
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = 0.0
        self.pitch = 0.0
        self.speed = 8
        self.vertical_velocity = 0
        self.jump_velocity = 10
        self.head_height = 22
        self.health = 100
        self.score = 0
        self.kills = 0
        self.shots_fired = 0
        self.shots_hit = 0
        self.weapon = 'rifle'

    def move(self, forward, strafe):
        dx = math.sin(self.yaw) * forward + math.cos(self.yaw) * strafe
        dz = math.cos(self.yaw) * forward - math.sin(self.yaw) * strafe
        self.x += dx * self.speed
        self.z += dz * self.speed

    def jump(self):
        if self.y <= 0.1:
            self.vertical_velocity = self.jump_velocity

    def update_physics(self):
        self.y += self.vertical_velocity
        self.vertical_velocity -= 0.42
        if self.y < 0:
            self.y = 0
            self.vertical_velocity = 0


class Target:
    def __init__(self, x, y, z, difficulty='veteran'):
        self.x = x
        self.y = y
        self.z = z
        self.health = 100
        self.vx = random.uniform(-1.2, 1.2)
        self.vz = random.uniform(-1.2, 1.2)
        self.ai_speed = {'rookie': 0.7, 'veteran': 1.2, 'elite': 1.8}[difficulty]

    def update(self, arena_width, arena_depth, player):
        dx = player.x - self.x
        dz = player.z - self.z
        dist = math.hypot(dx, dz)
        if dist > 0.01:
            self.x += (dx / dist) * self.ai_speed * 0.45
            self.z += (dz / dist) * self.ai_speed * 0.45
        self.x += self.vx * 0.2
        self.z += self.vz * 0.2
        if self.x < 10 or self.x > arena_width - 10:
            self.vx *= -1
        if self.z < 10 or self.z > arena_depth - 10:
            self.vz *= -1
        self.x = max(10, min(arena_width - 10, self.x))
        self.z = max(10, min(arena_depth - 10, self.z))

    def draw(self, screen_x, screen_y, scale):
        head_r = 7 * scale
        body_y = screen_y + 18 * scale
        arcade.draw_circle_filled(screen_x, screen_y, head_r, arcade.color.RED)
        arcade.draw_line(screen_x, screen_y + head_r, screen_x, body_y, arcade.color.RED, 2)
        arcade.draw_line(screen_x, body_y, screen_x - 10 * scale, body_y + 18 * scale, arcade.color.RED, 2)
        arcade.draw_line(screen_x, body_y, screen_x + 10 * scale, body_y + 18 * scale, arcade.color.RED, 2)
        arcade.draw_line(screen_x, body_y, screen_x - 9 * scale, body_y + 34 * scale, arcade.color.RED, 2)
        arcade.draw_line(screen_x, body_y, screen_x + 9 * scale, body_y + 34 * scale, arcade.color.RED, 2)


class Bullet:
    def __init__(self, x, y, z, yaw, pitch, weapon_name='rifle'):
        self.x = x
        self.y = y
        self.z = z
        self.yaw = yaw
        self.pitch = pitch
        self.weapon_name = weapon_name
        self.speed = {'rifle': 24, 'shotgun': 18, 'sniper': 34}[weapon_name]
        self.life = {'rifle': 120, 'shotgun': 70, 'sniper': 140}[weapon_name]

    def update(self):
        self.x += math.sin(self.yaw) * self.speed * math.cos(self.pitch)
        self.z += math.cos(self.yaw) * self.speed * math.cos(self.pitch)
        self.y += math.sin(self.pitch) * self.speed
        self.life -= 1
        return self.life > 0


class GameClient(arcade.Window):
    def __init__(self, server_ip='localhost', server_port=5000):
        super().__init__(1280, 820, "Target Practice 3D Arena")
        self.server_ip = server_ip
        self.server_port = server_port
        self.socket = None
        self.player_id = None
        self.player_name = ""
        self.input_ip = server_ip
        self.input_name = ""
        self.input_mode = 'ip'
        self.game_state = GameState.MENU
        self.leaderboard = []
        self.current_map = 'forest'
        self.difficulty = 'veteran'
        self.weapons = {
            'rifle': Weapon('rifle', 25, 12, 0.04, 1, arcade.color.LIGHT_GREEN, 0.9),
            'shotgun': Weapon('shotgun', 18, 30, 0.18, 6, arcade.color.ORANGE, 1.6),
            'sniper': Weapon('sniper', 70, 40, 0.01, 1, arcade.color.SKY_BLUE, 1.3),
        }
        self.weapon_key = 'rifle'
        self.arena_width = 240
        self.arena_depth = 240
        self.player = Player(self.arena_width / 2, 0, self.arena_depth / 2)
        self.player.weapon = self.weapon_key
        self.targets = []
        self.bullets = []
        self.keys = set()
        self.game_time = 0
        self.game_duration = 300
        self.game_active = False
        self.last_fire_time = 0.0
        self.hit_marker_timer = 0.0
        self.audio_enabled = True
        self.round_kills = 0
        self.muzzle_flash = 0.0
        self.map_colors = {
            'forest': arcade.color_from_hex('#2E5D2F'),
            'warehouse': arcade.color_from_hex('#434A52'),
            'desert': arcade.color_from_hex('#B4945C'),
            'ice': arcade.color_from_hex('#CFE7F7'),
            'hangar': arcade.color_from_hex('#3A4550')
        }
        self.set_mouse_visible(False)
        self.center_mouse()
        arcade.set_background_color(arcade.color.DARK_SLATE_GRAY)

    def center_mouse(self):
        arcade.window_commands.set_mouse_position(self.width // 2, self.height // 2)

    def connect_to_server(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(0.1)
            self.socket.connect((self.input_ip, self.server_port))
            thread = threading.Thread(target=self.receive_messages, daemon=True)
            thread.start()
            return True
        except Exception as exc:
            print(f"Connection failed: {exc}")
            return False

    def send_message(self, msg):
        try:
            if self.socket:
                self.socket.send((json.dumps(msg) + '\n').encode('utf-8'))
        except Exception:
            pass

    def receive_messages(self):
        buffer = ""
        while True:
            try:
                data = self.socket.recv(4096).decode('utf-8')
                if not data:
                    break
                buffer += data
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    if line:
                        try:
                            msg = json.loads(line)
                            self.handle_message(msg)
                        except Exception:
                            pass
            except socket.timeout:
                continue
            except Exception:
                break

    def handle_message(self, message):
        msg_type = message.get('type')
        if msg_type == 'init':
            self.player_id = message.get('client_id')
        elif msg_type in ('leaderboard_data', 'leaderboard_update'):
            self.leaderboard = message.get('leaderboard', [])
        elif msg_type == 'map_changed':
            self.current_map = message.get('map', self.current_map)
        elif msg_type == 'difficulty_changed':
            self.difficulty = message.get('difficulty', self.difficulty)

    def spawn_targets(self, count=7):
        self.targets = []
        for _ in range(count):
            self.targets.append(Target(random.randint(20, self.arena_width - 20), 0, random.randint(20, self.arena_depth - 20), self.difficulty))

    def start_game(self):
        self.game_state = GameState.PLAYING
        self.game_active = True
        self.game_time = 0
        self.player.score = 0
        self.player.kills = 0
        self.player.shots_fired = 0
        self.player.shots_hit = 0
        self.round_kills = 0
        self.spawn_targets()
        self.send_message({'type': 'join_game', 'player_name': self.input_name or 'Player', 'weapon': self.weapon_key})
        self.send_message({'type': 'change_map', 'map': self.current_map})
        self.send_message({'type': 'set_difficulty', 'difficulty': self.difficulty})

    def project_world_point(self, x, y, z):
        dx = x - self.player.x
        dy = y - self.player.y
        dz = z - self.player.z

        cy = math.cos(-self.player.yaw)
        sy = math.sin(-self.player.yaw)
        tx = dx * cy - dz * sy
        tz = dx * sy + dz * cy

        cp = math.cos(-self.player.pitch)
        sp = math.sin(-self.player.pitch)
        ty = dy * cp - tz * sp
        dist = dy * sp + tz * cp

        if dist <= 0.1:
            return None
        scale = 650 / dist
        sx = self.width / 2 + tx * scale
        sy = self.height / 2 - ty * scale
        return sx, sy, scale

    def draw_floor(self):
        step = 20
        for x in range(0, self.arena_width + step, step):
            for z in range(0, self.arena_depth + step, step):
                p1 = self.project_world_point(x, 0, z)
                p2 = self.project_world_point(x + step, 0, z)
                p3 = self.project_world_point(x, 0, z + step)
                if p1 and p2:
                    arcade.draw_line(p1[0], p1[1], p2[0], p2[1], arcade.color.DARK_CYAN, 1)
                if p1 and p3:
                    arcade.draw_line(p1[0], p1[1], p3[0], p3[1], arcade.color.DARK_CYAN, 1)

    def draw_targets(self):
        for target in self.targets:
            p = self.project_world_point(target.x, target.y + 22, target.z)
            if p is None:
                continue
            sx, sy, scale = p
            target.draw(sx, sy, scale)

    def draw_player(self):
        cx = self.width / 2
        cy = self.height / 2 + 32
        arcade.draw_circle_filled(cx, cy - 28, 12, arcade.color.LIGHT_GREEN)
        arcade.draw_line(cx, cy - 16, cx, cy + 16, arcade.color.LIGHT_GREEN, 3)
        arcade.draw_line(cx, cy + 8, cx - 16, cy + 26, arcade.color.LIGHT_GREEN, 3)
        arcade.draw_line(cx, cy + 8, cx + 16, cy + 26, arcade.color.LIGHT_GREEN, 3)
        arcade.draw_line(cx, cy + 16, cx - 12, cy + 56, arcade.color.LIGHT_GREEN, 3)
        arcade.draw_line(cx, cy + 16, cx + 12, cy + 56, arcade.color.LIGHT_GREEN, 3)

    def draw_crosshair(self):
        cx = self.width / 2
        cy = self.height / 2
        size = 20
        arcade.draw_line(cx - size, cy, cx + size, cy, arcade.color.GREEN, 2)
        arcade.draw_line(cx, cy - size, cx, cy + size, arcade.color.GREEN, 2)
        arcade.draw_circle_filled(cx, cy, 3, arcade.color.GREEN)
        if self.hit_marker_timer > 0:
            arcade.draw_line(cx - 10, cy - 10, cx + 10, cy + 10, arcade.color.WHITE, 2)
            arcade.draw_line(cx + 10, cy - 10, cx - 10, cy + 10, arcade.color.WHITE, 2)
            self.hit_marker_timer -= 0.016

    def _beep(self, freq=440, duration=80):
        if self.audio_enabled:
            try:
                import winsound
                winsound.Beep(freq, duration)
            except Exception:
                pass

    def draw_hud(self):
        time_left = max(0, self.game_duration - int(self.game_time / 60))
        arcade.draw_text(f"Time: {time_left}s", 20, self.height - 30, 16, arcade.color.WHITE)
        arcade.draw_text(f"Score: {self.player.score}", 20, self.height - 60, 16, arcade.color.GREEN)
        arcade.draw_text(f"Kills: {self.player.kills}", 20, self.height - 90, 16, arcade.color.YELLOW)
        accuracy = (self.player.shots_hit / max(1, self.player.shots_fired)) * 100
        arcade.draw_text(f"Accuracy: {accuracy:.1f}%", 20, self.height - 120, 16, arcade.color.LIGHT_BLUE)
        arcade.draw_text(f"Weapon: {self.player.weapon.upper()}", 20, self.height - 150, 16, self.weapons[self.player.weapon].color)
        arcade.draw_text(f"Map: {self.current_map.capitalize()}", self.width - 180, self.height - 30, 16, arcade.color.WHITE)
        arcade.draw_text(f"Difficulty: {self.difficulty.capitalize()}", self.width - 240, self.height - 60, 16, arcade.color.WHITE)
        arcade.draw_text(f"Health: {int(self.player.health)}", 20, 20, 16, arcade.color.RED)

    def draw_menu(self):
        arcade.draw_rectangle_filled(self.width / 2, self.height / 2, self.width, self.height, arcade.color.BLACK)
        arcade.draw_text("TARGET PRACTICE 3D ARENA", self.width / 2, self.height - 90, 26, arcade.color.GREEN, anchor_x='center', bold=True)
        arcade.draw_text("Server IP:", 150, self.height - 170, 16, arcade.color.WHITE)
        arcade.draw_text(self.input_ip, 150, self.height - 200, 16, arcade.color.GREEN)
        arcade.draw_text("Player Name:", 150, self.height - 260, 16, arcade.color.WHITE)
        arcade.draw_text(self.input_name or "Enter name...", 150, self.height - 290, 16, arcade.color.GREEN)
        arcade.draw_text("WASD move | Mouse aim | Click shoot | Space jump", self.width / 2, 190, 16, arcade.color.LIGHT_GRAY, anchor_x='center')
        arcade.draw_text("1 Rifle | 2 Shotgun | 3 Sniper | L Leaderboard | S Settings", self.width / 2, 155, 15, arcade.color.LIGHT_GRAY, anchor_x='center')
        arcade.draw_text("Press ENTER to connect", self.width / 2, 110, 18, arcade.color.GREEN, anchor_x='center')

    def draw_settings(self):
        arcade.draw_rectangle_filled(self.width / 2, self.height / 2, self.width, self.height, arcade.color.BLACK)
        arcade.draw_text("SETTINGS", self.width / 2, self.height - 80, 26, arcade.color.GREEN, anchor_x='center', bold=True)
        arcade.draw_text(f"Weapon: {self.weapon_key.upper()}", self.width / 2, self.height - 180, 18, arcade.color.WHITE, anchor_x='center')
        arcade.draw_text(f"Difficulty: {self.difficulty.capitalize()}", self.width / 2, self.height - 230, 18, arcade.color.WHITE, anchor_x='center')
        arcade.draw_text(f"Map: {self.current_map.capitalize()}", self.width / 2, self.height - 280, 18, arcade.color.WHITE, anchor_x='center')
        arcade.draw_text("1 Rifle | 2 Shotgun | 3 Sniper", self.width / 2, 240, 16, arcade.color.LIGHT_GRAY, anchor_x='center')
        arcade.draw_text("Q Difficulty | E Map | M Back", self.width / 2, 200, 16, arcade.color.LIGHT_GRAY, anchor_x='center')

    def draw_leaderboard(self):
        arcade.draw_rectangle_filled(self.width / 2, self.height / 2, self.width, self.height, arcade.color.BLACK)
        arcade.draw_text("LEADERBOARD", self.width / 2, self.height - 60, 22, arcade.color.GREEN, anchor_x='center', bold=True)
        y = self.height - 120
        for i, entry in enumerate(self.leaderboard[:10]):
            name = entry.get('player_name', 'Unknown')
            score = entry.get('score', 0)
            weapon = entry.get('weapon', 'rifle')
            arcade.draw_text(f"#{i + 1} {name}: {score} ({weapon})", 80, y, 16, arcade.color.WHITE)
            y -= 34
        arcade.draw_text("Press M to go back", self.width / 2, 40, 14, arcade.color.LIGHT_GRAY, anchor_x='center')

    def draw_game_over(self):
        arcade.draw_rectangle_filled(self.width / 2, self.height / 2, self.width, self.height, arcade.color.BLACK)
        arcade.draw_text("GAME OVER", self.width / 2, self.height - 100, 22, arcade.color.RED, anchor_x='center', bold=True)
        arcade.draw_text(f"Final Score: {self.player.score}", self.width / 2, self.height - 150, 18, arcade.color.GREEN, anchor_x='center')
        arcade.draw_text(f"Targets Destroyed: {self.player.kills}", self.width / 2, self.height - 200, 16, arcade.color.YELLOW, anchor_x='center')
        accuracy = (self.player.shots_hit / max(1, self.player.shots_fired)) * 100
        arcade.draw_text(f"Accuracy: {accuracy:.1f}%", self.width / 2, self.height - 250, 16, arcade.color.LIGHT_BLUE, anchor_x='center')
        arcade.draw_text("Press ENTER to return to menu", self.width / 2, 70, 14, arcade.color.LIGHT_GRAY, anchor_x='center')

    def on_draw(self):
        arcade.start_render()
        if self.game_state == GameState.MENU:
            self.draw_menu()
        elif self.game_state == GameState.SETTINGS:
            self.draw_settings()
        elif self.game_state == GameState.PLAYING:
            self.draw_game()
        elif self.game_state == GameState.LEADERBOARD:
            self.draw_leaderboard()
        elif self.game_state == GameState.GAME_OVER:
            self.draw_game_over()

    def draw_game(self):
        base = self.map_colors.get(self.current_map, arcade.color_from_hex('#2E5D2F'))
        arcade.draw_rectangle_filled(self.width / 2, self.height / 2, self.width, self.height, base)
        self.draw_floor()
        self.draw_targets()
        self.draw_player()
        self.draw_crosshair()
        self.draw_hud()

    def set_weapon(self, name):
        if name in self.weapons:
            self.weapon_key = name
            self.player.weapon = name
            self.send_message({'type': 'set_weapon', 'weapon': name})

    def on_key_press(self, key, modifiers):
        if self.game_state == GameState.MENU:
            if key == arcade.key.RETURN:
                if self.connect_to_server():
                    self.start_game()
            elif key == arcade.key.L:
                self.send_message({'type': 'get_leaderboard'})
                self.game_state = GameState.LEADERBOARD
            elif key == arcade.key.S:
                self.game_state = GameState.SETTINGS
            elif key == arcade.key.BACKSPACE:
                if self.input_mode == 'ip':
                    self.input_ip = self.input_ip[:-1]
                else:
                    self.input_name = self.input_name[:-1]
            elif key == arcade.key.TAB:
                self.input_mode = 'name' if self.input_mode == 'ip' else 'ip'
            elif self.input_mode == 'ip':
                if key == arcade.key.PERIOD:
                    self.input_ip += '.'
                elif 48 <= key <= 57:
                    self.input_ip += chr(key)
            elif self.input_mode == 'name':
                if 32 <= key <= 126 and len(self.input_name) < 20:
                    self.input_name += chr(key)
            return

        if self.game_state == GameState.SETTINGS:
            if key == arcade.key.M:
                self.game_state = GameState.MENU
            elif key == arcade.key.Q:
                cycle = ['rookie', 'veteran', 'elite']
                idx = cycle.index(self.difficulty)
                self.difficulty = cycle[(idx + 1) % len(cycle)]
                self.send_message({'type': 'set_difficulty', 'difficulty': self.difficulty})
            elif key == arcade.key.E:
                cycle = ['forest', 'warehouse', 'desert', 'ice', 'hangar']
                idx = cycle.index(self.current_map)
                self.current_map = cycle[(idx + 1) % len(cycle)]
                self.send_message({'type': 'change_map', 'map': self.current_map})
            elif key == arcade.key.KEY_1:
                self.set_weapon('rifle')
            elif key == arcade.key.KEY_2:
                self.set_weapon('shotgun')
            elif key == arcade.key.KEY_3:
                self.set_weapon('sniper')
            return

        if self.game_state == GameState.PLAYING:
            if key == arcade.key.SPACE:
                self.player.jump()
            if key in (arcade.key.W, arcade.key.A, arcade.key.S, arcade.key.D):
                self.keys.add(key)
            if key == arcade.key.ESCAPE:
                self.game_state = GameState.MENU
                self.set_mouse_visible(True)
            elif key == arcade.key.KEY_1:
                self.set_weapon('rifle')
            elif key == arcade.key.KEY_2:
                self.set_weapon('shotgun')
            elif key == arcade.key.KEY_3:
                self.set_weapon('sniper')
            return

        if self.game_state == GameState.LEADERBOARD:
            if key in (arcade.key.M, arcade.key.ESCAPE):
                self.game_state = GameState.MENU
            return

        if self.game_state == GameState.GAME_OVER and key == arcade.key.RETURN:
            self.game_state = GameState.MENU
            self.set_mouse_visible(True)
            self.input_name = ""

    def on_key_release(self, key, modifiers):
        if self.game_state == GameState.PLAYING:
            self.keys.discard(key)

    def on_mouse_motion(self, x, y, dx, dy):
        if self.game_state == GameState.PLAYING:
            center_x = self.width / 2
            center_y = self.height / 2
            mouse_dx = x - center_x
            mouse_dy = y - center_y
            self.player.yaw += mouse_dx * 0.003
            self.player.pitch = max(-1.2, min(1.2, self.player.pitch + mouse_dy * 0.002))
            self.center_mouse()

    def on_mouse_press(self, x, y, button, modifiers):
        if self.game_state == GameState.PLAYING and button == arcade.MOUSE_BUTTON_LEFT:
            weapon = self.weapons[self.player.weapon]
            now = arcade.get_time()
            if now - self.last_fire_time < 1.0 / weapon.fire_rate:
                return
            self.last_fire_time = now
            self.player.shots_fired += 1
            self.muzzle_flash = 0.12
            self._beep(440 + weapon.damage * 5, 35)
            for _ in range(weapon.pellets):
                spread = random.uniform(-weapon.spread, weapon.spread)
                yaw = self.player.yaw + spread
                pitch = self.player.pitch + random.uniform(-weapon.spread * 0.8, weapon.spread * 0.8)
                muzzle_x = self.player.x + math.sin(yaw) * 8
                muzzle_y = self.player.y + self.player.head_height
                muzzle_z = self.player.z + math.cos(yaw) * 8
                self.bullets.append(Bullet(muzzle_x, muzzle_y, muzzle_z, yaw, pitch, self.player.weapon))

    def on_update(self, delta_time):
        if self.game_state != GameState.PLAYING or not self.game_active:
            return

        self.game_time += 1
        self.player.update_physics()
        self.muzzle_flash = max(0, self.muzzle_flash - delta_time * 2.5)

        forward = 0.0
        strafe = 0.0
        if arcade.key.W in self.keys:
            forward += 1
        if arcade.key.S in self.keys:
            forward -= 1
        if arcade.key.A in self.keys:
            strafe -= 1
        if arcade.key.D in self.keys:
            strafe += 1
        self.player.move(forward, strafe)
        self.player.x = max(10, min(self.arena_width - 10, self.player.x))
        self.player.z = max(10, min(self.arena_depth - 10, self.player.z))

        for target in self.targets:
            target.update(self.arena_width, self.arena_depth, self.player)

        for bullet in list(self.bullets):
            if not bullet.update():
                self.bullets.remove(bullet)
                continue
            for target in list(self.targets):
                dist = math.hypot(bullet.x - target.x, bullet.z - target.z)
                if dist < 12:
                    self.player.score += 10
                    self.player.kills += 1
                    self.player.shots_hit += 1
                    self.hit_marker_timer = 0.18
                    self.targets.remove(target)
                    self.bullets.remove(bullet)
                    self.targets.append(Target(random.randint(20, self.arena_width - 20), 0, random.randint(20, self.arena_depth - 20), self.difficulty))
                    self.send_message({'type': 'update_score', 'score': self.player.score, 'kills': self.player.kills, 'accuracy': (self.player.shots_hit / max(1, self.player.shots_fired)) * 100})
                    break

        if self.game_time >= self.game_duration * 60:
            self.game_active = False
            self.game_state = GameState.GAME_OVER
            accuracy = (self.player.shots_hit / max(1, self.player.shots_fired)) * 100
            self.send_message({
                'type': 'update_score',
                'score': self.player.score,
                'kills': self.player.kills,
                'accuracy': accuracy
            })
            self.send_message({
                'type': 'end_game',
                'player_id': self.player_id,
                'final_score': self.player.score,
                'player_name': self.input_name or 'Player',
                'weapon': self.player.weapon
            })

    def draw_bullets(self):
        for bullet in self.bullets:
            p = self.project_world_point(bullet.x, bullet.y, bullet.z)
            if p is None:
                continue
            sx, sy, scale = p
            arcade.draw_circle_filled(sx, sy, 3, self.weapons[self.player.weapon].color)

    def draw_game(self):
        color = self.map_colors.get(self.current_map, arcade.color_from_hex('#2E5D2F'))
        arcade.draw_rectangle_filled(self.width / 2, self.height / 2, self.width, self.height, color)
        self.draw_floor()
        self.draw_targets()
        self.draw_bullets()
        self.draw_player()
        self.draw_crosshair()
        self.draw_hud()
        if self.muzzle_flash > 0:
            arcade.draw_circle_filled(self.width / 2 + 18, self.height / 2 + 24, 12 + self.muzzle_flash * 30, arcade.color.WHITE)


if __name__ == '__main__':
    import sys
    ip = sys.argv[1] if len(sys.argv) > 1 else 'localhost'
    GameClient(ip).run()














































































































































































































































































































































































































































































































































































































































