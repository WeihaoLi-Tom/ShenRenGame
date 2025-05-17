import pygame
import os
import time
import math
import random

class Player:
    def __init__(self, spawn_pos, tile_size):
        self.tile_width, self.tile_height = tile_size
        # 更贴合人物的碰撞体
        sprite_w, sprite_h = 48, 48
        rect_w, rect_h = 20, 28
        rect_x = spawn_pos[0] + (sprite_w - rect_w) // 2
        rect_y = spawn_pos[1] + (sprite_h - rect_h)
        self.rect = pygame.Rect(rect_x, rect_y, rect_w, rect_h)
        self.move_speed = 1.8
        self.max_health = 200
        self.current_health = 200
        self.is_dead = False
        self.attacking = False
        self.attack_timer = 0
        self.attack_duration = 0.3
        self.attack_cooldown = 1
        self.attack_last_time = 0
        self.is_jumping = False
        self.jump_timer = 0
        self.jump_duration = 0.5
        self.facing_left = False
        self.is_moving = False
        self.action = "idle"
        self.direction = "down"  # 新增：当前朝向（down, right, up, left）
        self.frame_idx = 0
        self.frame_timer = 0
        self.frame_interval = 0.1  # 每帧间隔秒数
        self.frames = self._load_all_frames()
        self.position = list(spawn_pos)
        # 攻击相关属性
        self.attack_range = self.tile_width  # 攻击范围
        self.attack_damage = 100
        self.attack_rect = pygame.Rect(0, 0, 0, 0)  # 恢复attack_rect属性
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 1.0  # 受伤后无敌时间
        # 环绕攻击相关
        self.attack_mode = "stab"  # "stab"为突刺，"orbit"为环绕
        self.orbit_attack_anim = False
        self.orbit_attack_start_time = 0
        self.orbit_attack_duration = 0.5  # 环绕动画时长（秒）
        self.orbit_attack_angle = 0
        self.orbit_attack_hit = False  # 防止多次判定
        self.orbit_trail_length = 8  # 剑影数量
        self.orbit_particles = []  # 粒子特效
        self.attack_sound = pygame.mixer.Sound("assets/sound/hit.wav")
        self.attack_sound.set_volume(0.5)
        self.attack_none_sound = pygame.mixer.Sound("assets/sound/hitnone.wav")
        self.attack_none_sound.set_volume(0.5)
        self.is_dashing = False
        self.dash_cooldown = 1.0  # 冲刺冷却（秒）
        self.dash_last_time = 0
        self.dash_duration = 0.2  # 冲刺持续时间（秒）
        self.dash_timer = 0
        self.dash_speed = self.move_speed * 1.8  # 冲刺速度
        self.dash_sound = pygame.mixer.Sound("assets/sound/dash.wav")
        self.dash_sound.set_volume(0.3)
        self.walk_sound = pygame.mixer.Sound("assets/sound/walk.wav")
        self.walk_sound.set_volume(0.2)
        self.walk_channel = None  # 用于控制走路音效的播放
        
        # 受伤音效
        try:
            self.hurt_sound = pygame.mixer.Sound("assets/sound/hurt_out.wav")
            self.hurt_sound.set_volume(0.3)
            print("受伤音效加载成功")
        except Exception as e:
            print(f"受伤音效初始化失败: {e}")
            self.hurt_sound = None
        
        # 死亡音效相关设置
        try:
            self.death_sound = pygame.mixer.Sound("assets/sound/death.wav")
            self.death_sound.set_volume(0.5)
            print("死亡音效加载成功")
            # 预先尝试播放一次（音量为0）以确保声道正常工作
            temp_channel = pygame.mixer.Channel(1)
            temp_channel.set_volume(0)
            temp_channel.play(self.death_sound, maxtime=1)  # 只播放1毫秒
            temp_channel.stop()
            print("死亡音效声道测试成功")
        except Exception as e:
            print(f"死亡音效初始化失败: {e}")
            self.death_sound = None
            
        self.death_sound_played = False
        self.death_channel = None  # 专用于死亡音效的声道
    
    def _load_frames(self, action):
        img_dir = "assets/characters/player_frames"
        frames = []
        idx = 1
        while True:
            fname = f"{action}_{idx:02d}.png"
            fpath = os.path.join(img_dir, fname)
            if not os.path.exists(fpath):
                break
            frames.append(pygame.image.load(fpath).convert_alpha())
            idx += 1
        return frames

    def _load_all_frames(self):
        frames = {}
        # idle
        frames["idle_down"] = self._load_frames("idle_down")
        frames["idle_right"] = self._load_frames("idle_right")
        frames["idle_up"] = self._load_frames("idle_up")
        # move
        frames["move_down"] = self._load_frames("move_down")
        frames["move_right"] = self._load_frames("move_right")
        frames["move_up"] = self._load_frames("move_up")
        # attack
        frames["attack_down"] = self._load_frames("attack_down")
        frames["attack_right"] = self._load_frames("attack_right")
        frames["attack_up"] = self._load_frames("attack_up")
        # death
        frames["death"] = self._load_frames("death")
        return frames

    def move(self, keys, is_valid_position):
        if self.is_dead:
            return  # 死亡后不能移动
        if self.is_dashing:
            return  # 冲刺期间不能手动移动
        old_x, old_y = self.rect.topleft
        self.is_moving = False
        
        # 处理水平移动
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.move_speed
            self.facing_left = True
            self.direction = "left"  # 向左移动时使用left方向
            self.is_moving = True
            # 检查左边缘的多个点
            if not all(is_valid_position(self.rect.left, y) for y in range(self.rect.top + 4, self.rect.bottom - 4, 4)):
                self.rect.x = old_x
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.move_speed
            self.facing_left = False
            self.direction = "right"  # 向右移动时使用right方向
            self.is_moving = True
            # 检查右边缘的多个点
            if not all(is_valid_position(self.rect.right - 1, y) for y in range(self.rect.top + 4, self.rect.bottom - 4, 4)):
                self.rect.x = old_x
                
        # 处理垂直移动
        if keys[pygame.K_UP]:
            self.rect.y -= self.move_speed
            self.direction = "up"  # 向上移动时使用up方向
            self.is_moving = True
            # 检查上边缘的多个点
            if not all(is_valid_position(x, self.rect.top) for x in range(self.rect.left + 4, self.rect.right - 4, 4)):
                self.rect.y = old_y
        if keys[pygame.K_DOWN]:
            self.rect.y += self.move_speed
            self.direction = "down"  # 向下移动时使用down方向
            self.is_moving = True
            # 检查下边缘的多个点
            if not all(is_valid_position(x, self.rect.bottom - 1) for x in range(self.rect.left + 4, self.rect.right - 4, 4)):
                self.rect.y = old_y

    def attack(self):
        current_time = time.time()
        if not self.attacking and current_time - self.attack_last_time >= self.attack_cooldown:
            self.attacking = True
            self.attack_timer = current_time
            self.attack_last_time = current_time
            self.generate_attack_rect()  # 攻击时生成判定区域
            # 只要攻击动作触发，无论是否移动，都播放空挥音效
            if hasattr(self, 'attack_none_sound') and self.attack_none_sound:
                try:
                    channel = pygame.mixer.Channel(7)
                    channel.stop()
                    channel.set_volume(0.5)
                    channel.play(self.attack_none_sound)
                except Exception as e:
                    print(f"播放空挥音效失败: {e}")
                    self.attack_none_sound.play()
            return True
        return False

    def generate_attack_rect(self):
        # 生成一个更大范围的攻击判定区域（突刺方向）
        attack_distance = 30
        attack_width = self.tile_width * 1.5
        attack_height = self.tile_height * 1.5
        # 简单用左右方向判定
        if self.facing_left:
            # 向左攻击
            self.attack_rect = pygame.Rect(
                self.rect.left - attack_distance,
                self.rect.centery - attack_height // 2,
                attack_distance,
                attack_height
            )
        else:
            # 向右攻击
            self.attack_rect = pygame.Rect(
                self.rect.right,
                self.rect.centery - attack_height // 2,
                attack_distance,
                attack_height
            )

    def update(self):
        now = time.time()
        prev_action = self.action
        if self.is_dead:
            self.action = "death"
            frames_list = self.frames.get("death")
            
            # 确保死亡音效播放
            if not self.death_sound_played and hasattr(self, 'death_sound') and self.death_sound:
                try:
                    print("update中检测到死亡状态，尝试播放死亡音效")
                    # 直接使用pygame.mixer.Sound.play()方法播放
                    self.death_sound.play()
                    self.death_sound_played = True
                except Exception as e:
                    print(f"update中播放死亡音效失败: {e}")
            
            if frames_list and self.frame_idx < len(frames_list) - 1:
                self.frame_timer += 1/60
                if self.frame_timer >= self.frame_interval:
                    self.frame_timer = 0
                    self.frame_idx += 1
            # 死亡时停止走路音效
            if self.walk_channel and self.walk_channel.get_busy():
                self.walk_channel.stop()
            return  # 死亡时不再处理其它状态
        # 冲刺逻辑
        if self.is_dashing:
            # 冲刺时也停止走路音效
            if self.walk_channel and self.walk_channel.get_busy():
                self.walk_channel.stop()
            speed = self.dash_speed
            if self.direction == "left":
                self.rect.x -= speed
            elif self.direction == "right":
                self.rect.x += speed
            elif self.direction == "up":
                self.rect.y -= speed
            elif self.direction == "down":
                self.rect.y += speed
            self.action = "move"  # 用move动画代替
            self.is_moving = True
            if now - self.dash_timer >= self.dash_duration:
                self.is_dashing = False
                self.invincible = False
            return
        elif self.attacking:
            self.action = "attack"
            if now - self.attack_timer >= self.attack_duration:
                self.attacking = False
        elif self.is_jumping:
            self.action = "jump"
            if now - self.jump_timer >= self.jump_duration:
                self.is_jumping = False
        elif self.is_moving:
            self.action = "move"
        else:
            self.action = "idle"
        if self.action != prev_action:
            self.frame_idx = 0
        # 帧动画播放（按时间）
        # 攻击动画也支持方向
        if self.action == "attack":
            if self.direction == "left":
                action_key = "attack_right"
            else:
                action_key = f"attack_{self.direction}"
        else:
            action_key = f"{self.action}_{self.direction}"
        frames_list = self.frames.get(action_key)
        if not frames_list and self.direction == "left" and self.action != "attack":
            frames_list = self.frames.get(f"{self.action}_right")
        if not frames_list:
            frames_list = self.frames.get("idle_down")
        self.frame_timer += 1/60
        if self.frame_timer >= self.frame_interval:
            self.frame_timer = 0
            self.frame_idx = (self.frame_idx + 1) % len(frames_list)
        if self.action == "death" and self.frame_idx == len(frames_list) - 1:
            self.frame_idx = len(frames_list) - 1
        if self.invincible:
            if now - self.invincible_timer >= self.invincible_duration:
                self.invincible = False
        # 走路音效控制
        if self.is_moving and not self.is_dead:
            if not self.walk_channel or not self.walk_channel.get_busy():
                self.walk_channel = self.walk_sound.play(loops=-1)
        else:
            if self.walk_channel and self.walk_channel.get_busy():
                self.walk_channel.stop()

    def take_damage(self, damage):
        if not self.is_dead and not self.invincible:
            self.current_health = max(0, self.current_health - damage)
            self.invincible = True
            self.invincible_timer = time.time()
            # 播放受伤音效
            if hasattr(self, 'hurt_sound') and self.hurt_sound:
                try:
                    channel = pygame.mixer.Channel(6)
                    channel.stop()
                    channel.set_volume(0.3)
                    channel.play(self.hurt_sound)
                    print("播放受伤音效")
                except Exception as e:
                    print(f"播放受伤音效失败: {e}")
                    self.hurt_sound.play()
            if self.current_health <= 0:
                self.die()
            return True
        return False

    def die(self):
        if not self.is_dead:
            self.is_dead = True
            self.frame_idx = 0
            print("角色死亡，播放死亡音效")  # 调试用
            
            # 停止走路音效
            if self.walk_channel and self.walk_channel.get_busy():
                self.walk_channel.stop()
                
            # 确保音效只播放一次
            if not self.death_sound_played and hasattr(self, 'death_sound') and self.death_sound:
                try:
                    # 先停止可能干扰的其他音效
                    pygame.mixer.stop()
                    
                    # 死亡音效用1号声道
                    death_channel = pygame.mixer.Channel(1)
                    death_channel.stop()
                    death_channel.set_volume(0.5)
                    death_channel.play(self.death_sound)
                    self.death_sound_played = True
                    print("死亡音效已尝试播放")
                    
                except Exception as e:
                    print(f"播放死亡音效时出错: {e}")  # 调试用

    def heal(self, amount):
        self.current_health = min(self.max_health, self.current_health + amount)
        if self.current_health > 0 and self.is_dead:
            self.is_dead = False
            self.death_sound_played = False  # 重置死亡音效播放标志，以便复活后再次死亡时能播放

    def jump(self):
        if not self.is_jumping and not self.is_dead:
            self.is_jumping = True
            self.jump_timer = time.time()
            self.frame_idx = 0

    def draw(self, surface, camera_x, camera_y, show_debug_hitbox=False):
        # 死亡时只用death动画帧
        if self.action == "death":
            frames_list = self.frames.get("death")
            flip = False
        else:
            if self.action == "attack":
                if self.direction == "left":
                    action_key = "attack_right"
                else:
                    action_key = f"attack_{self.direction}"
            else:
                action_key = f"{self.action}_{self.direction}"
            frames_list = self.frames.get(action_key)
            flip = False
            if self.action == "attack" and self.direction == "left":
                flip = True
            elif not frames_list and self.direction == "left":
                frames_list = self.frames.get(f"{self.action}_right")
                flip = True
        if not frames_list:
            frames_list = self.frames.get("idle_down")
        if not frames_list:
            return
        idx = min(self.frame_idx, len(frames_list)-1)
        frame = frames_list[idx]
        if flip:
            frame = pygame.transform.flip(frame, True, False)
        draw_x = self.rect.x - (48 - self.rect.width) // 2
        draw_y = self.rect.y - (48 - self.rect.height)
        # 新增：无敌时闪烁
        visible = True
        if self.invincible:
            visible = int(time.time() * 10) % 2 == 0
        if visible:
            surface.blit(frame, (draw_x - camera_x, draw_y - camera_y))
        # 只在show_debug_hitbox为True时绘制碰撞体和攻击范围
        if show_debug_hitbox:
            collision_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            pygame.draw.rect(collision_surface, (255, 0, 0, 128), collision_surface.get_rect())
            surface.blit(collision_surface, (self.rect.x - camera_x, self.rect.y - camera_y))
            margin = 4
            for y in range(self.rect.top + margin, self.rect.bottom - margin, 4):
                pygame.draw.circle(surface, (0, 255, 0), (self.rect.left + margin - camera_x, y - camera_y), 1)
                pygame.draw.circle(surface, (0, 255, 0), (self.rect.right - 1 - margin - camera_x, y - camera_y), 1)
            for x in range(self.rect.left + margin, self.rect.right - margin, 4):
                pygame.draw.circle(surface, (0, 255, 0), (x - camera_x, self.rect.top + margin - camera_y), 1)
                pygame.draw.circle(surface, (0, 255, 0), (x - camera_x, self.rect.bottom - 1 - margin - camera_y), 1)
            if self.attacking:
                pygame.draw.rect(surface, (0, 0, 255, 120), self.attack_rect.move(-camera_x, -camera_y), 2)

    def draw_health_bar(self, surface, x, y, width=100, height=16):
        radius = height // 2
        shadow_rect = pygame.Rect(x+2, y+2, width, height)
        pygame.draw.rect(surface, (30, 30, 30), shadow_rect, border_radius=radius)
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (64, 64, 64), bg_rect, border_radius=radius)
        percent = self.current_health / self.max_health
        if percent > 0.7:
            color1 = (0, 255, 0)
            color2 = (255, 255, 0)
            blend = (percent-0.7)/0.3
        elif percent > 0.3:
            color1 = (255, 255, 0)
            color2 = (255, 0, 0)
            blend = (percent-0.3)/0.4
        else:
            color1 = (255, 0, 0)
            color2 = (128, 0, 0)
            blend = percent/0.3
        r = int(color1[0] + (color2[0]-color1[0])*blend)
        g = int(color1[1] + (color2[1]-color1[1])*blend)
        b = int(color1[2] + (color2[2]-color1[2])*blend)
        health_color = (r, g, b)
        health_width = int(width * percent)
        health_rect = pygame.Rect(x, y, health_width, height)
        pygame.draw.rect(surface, health_color, health_rect, border_radius=radius)
        highlight_rect = pygame.Rect(x, y, health_width, height//2)
        highlight_color = (255, 255, 255, 60)
        highlight_surface = pygame.Surface((health_width, height//2), pygame.SRCALPHA)
        highlight_surface.fill(highlight_color)
        surface.blit(highlight_surface, (x, y))
        pygame.draw.rect(surface, (220, 220, 220), bg_rect, 2, border_radius=radius)
        font = pygame.font.Font(None, height)
        text = f"{self.current_health}/{self.max_health}"
        text_surf = font.render(text, True, (30, 30, 30))
        text_rect = text_surf.get_rect(center=(x+width//2, y+height//2))
        surface.blit(text_surf, text_rect)

    def set_position(self, pos):
        self.rect.topleft = pos

    @property
    def health_percent(self):
        return self.current_health / self.max_health 

    def play_hit_sound(self):
        print("命中敌人音效触发")  # 调试
        if hasattr(self, 'attack_sound') and self.attack_sound:
            try:
                channel = pygame.mixer.Channel(5)
                channel.stop()
                channel.set_volume(0.5)
                channel.play(self.attack_sound)
            except Exception as e:
                print(f"播放攻击音效失败: {e}")
                self.attack_sound.play()

    @property
    def death_anim_finished(self):
        # 死亡动画帧是否已到最后一帧
        frames_list = self.frames.get("death")
        return self.is_dead and frames_list and self.frame_idx == len(frames_list) - 1 

    def dash(self):
        now = time.time()
        if not self.is_dead and not self.is_dashing and now - self.dash_last_time >= self.dash_cooldown:
            self.is_dashing = True
            self.dash_timer = now
            self.dash_last_time = now
            self.invincible = True  # 冲刺期间无敌
            # 无论是否移动，都播放冲刺音效
            if hasattr(self, 'dash_sound') and self.dash_sound:
                try:
                    channel = pygame.mixer.Channel(4)
                    channel.stop()
                    channel.set_volume(0.3)
                    channel.play(self.dash_sound)
                except Exception as e:
                    print(f"播放冲刺音效失败: {e}")
                    self.dash_sound.play() 