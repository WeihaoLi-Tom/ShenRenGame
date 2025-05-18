import pygame
import os
import time
import math
import random
from audio_manager import SoundCategory  # 新增导入

class SkillBullet:
    def __init__(self, pos, direction, frames, enemy_manager, speed=1.8):
        self.frames = frames
        self.frame_idx = 0
        self.frame_timer = 0
        self.frame_interval = 0.08
        self.pos = list(pos)
        self.direction = direction
        self.speed = speed
        self.alive = True
        self.width = frames[0].get_width() if frames else 32
        self.height = frames[0].get_height() if frames else 32
        if direction == 'left':
            self.frames = [pygame.transform.flip(frame, True, False) for frame in frames]
        self.damage = 50
        self.damage_interval = 0.2
        self.last_damage_time = 0
        self.hit_enemies = set()
        self.rect = pygame.Rect(0, 0, self.width - 20, self.height - 40)
        self.update_rect()
        self.enemy_manager = enemy_manager

    def update_rect(self):
        self.rect.center = (int(self.pos[0]), int(self.pos[1]))

    def update(self, enemies=None, camera_x=0, camera_y=0):
        if self.direction == 'left':
            self.pos[0] -= self.speed
        elif self.direction == 'right':
            self.pos[0] += self.speed
        elif self.direction == 'up':
            self.pos[1] -= self.speed
        elif self.direction == 'down':
            self.pos[1] += self.speed
        self.update_rect()
        self.frame_timer += 1/60
        if self.frame_timer >= self.frame_interval:
            self.frame_timer = 0
            self.frame_idx += 1
            if self.frame_idx >= len(self.frames):
                self.alive = False
        if enemies:
            current_time = time.time()
            if current_time - self.last_damage_time >= self.damage_interval:
                self.last_damage_time = current_time
                for enemy in enemies:
                    if enemy not in self.hit_enemies and enemy.alive:
                        enemy_rect = pygame.Rect(
                            enemy.rect.x - 15,
                            enemy.rect.y - 15,
                            enemy.rect.width + 30,
                            enemy.rect.height + 30
                        )
                        if self.rect.colliderect(enemy_rect):
                            try:
                                enemy.take_damage(self.damage)
                                if not enemy.alive and hasattr(self.enemy_manager, 'on_enemy_dead'):
                                    self.enemy_manager.on_enemy_dead(enemy.rect.center)
                            except Exception as e:
                                pass
                            self.hit_enemies.add(enemy)

    def draw(self, surface, camera_x, camera_y):
        if self.frames:
            frame = self.frames[self.frame_idx]
            rect = frame.get_rect(center=(int(self.pos[0]) - camera_x, int(self.pos[1]) - camera_y - 10))
            surface.blit(frame, rect)

class Player:
    def __init__(self, spawn_pos, tile_size, is_valid_position, enemy_manager=None):
        self.tile_width, self.tile_height = tile_size
        # 更贴合人物的碰撞体
        sprite_w, sprite_h = 48, 48
        rect_w, rect_h = 20, 28
        rect_x = spawn_pos[0] + (sprite_w - rect_w) // 2
        rect_y = spawn_pos[1] + (sprite_h - rect_h)
        self.rect = pygame.Rect(rect_x, rect_y, rect_w, rect_h)
        self.move_speed = 1.8
        self.max_health = 1000
        self.current_health = 1000
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
        self.enemies = []  # 存储敌人列表
        self.camera_x = 0  # 相机X偏移
        self.camera_y = 0  # 相机Y偏移
        # 攻击相关属性
        self.attack_range = self.tile_width  # 攻击范围
        self.base_attack_damage = 15
        self.attack_damage = self.base_attack_damage
        self.attack_rect = pygame.Rect(0, 0, 0, 0)  # 恢复attack_rect属性
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 1.0  # 受伤后无敌时间
        # 环绕攻击相关
        self.attack_mode = "stab"  # "stab"为突刺，"orbit"为环绕
        self.orbit_attack_anim = False
        self.orbit_attack_start_time = 0
        self.orbit_attack_duration = 0.5
        self.orbit_attack_angle = 0
        self.orbit_attack_hit = False  # 防止多次判定
        self.orbit_trail_length = 8  # 剑影数量
        self.orbit_particles = []  # 粒子特效
        self.attack_sound = pygame.mixer.Sound("assets/sound/hit.wav")
        self.attack_sound.set_volume(0.5)
        self.attack_none_sound = pygame.mixer.Sound("assets/sound/hitnone.wav")
        self.attack_none_sound.set_volume(0.5)
        self.firehit_sound = pygame.mixer.Sound("assets/sound/firehit.wav")
        self.firehit_sound.set_volume(0.5)
        self.is_dashing = False
        self.dash_cooldown = 1.8  # 冲刺冷却（秒）
        self.dash_last_time = 0
        self.dash_duration = 0.25  # 冲刺持续时间（秒）
        self.dash_invincible_duration = 0.5  # 冲刺无敌时长（秒）
        self.dash_timer = 0
        self.base_dash_speed = self.move_speed * 1.8
        self.dash_speed = self.base_dash_speed
        self.dash_sound = pygame.mixer.Sound("assets/sound/dash.wav")
        self.dash_sound.set_volume(0.3)
        self.firedash_sound = pygame.mixer.Sound("assets/sound/firedash.wav")
        self.firedash_sound.set_volume(0.3)
        self.walk_sound = pygame.mixer.Sound("assets/sound/walk.wav")
        self.walk_sound.set_volume(0.3)
        self.walk_channel = None  # 用于控制走路音效的播放
        
        # 受伤音效
        self.hurt_sound = pygame.mixer.Sound("assets/sound/hurt_out.wav")
        self.hurt_sound.set_volume(0.1)
        self.scream_sound = pygame.mixer.Sound("assets/sound/Tom_Scream.wav")
        self.scream_sound.set_volume(1)
        self.hurt_sound_toggle = False
        
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
        self.dash_trail = []  # 拖尾记录（x, y, t）
        self.is_valid_position = is_valid_position  # 保存碰撞检测函数
        
        # 变身相关
        self.has_maoluan = False  # 是否拥有耄耋之卵
        self.transformed = False  # 是否处于变身状态
        self.transform_frames = {}  # 变身后的动画帧
        # 变身动画相关
        self.is_transforming = False  # 是否正在播放变身动画
        self.transform_anim_frames = self._load_bianshen_frames()
        self.transform_anim_idx = 0
        self.transform_anim_timer = 0
        self.transform_anim_interval = 0.08  # 变身动画帧间隔
        # 技能动画相关
        self.is_using_skill = False
        self.skill_frames = self._load_skill_frames()
        self.skill_idx = 0
        self.skill_timer = 0
        self.skill_interval = 0.08  # 技能动画帧间隔
        # 技能弹幕相关
        self.bullet_frames = self._load_bullet_frames()
        self.skill_bullets = []
        self.enemy_manager = enemy_manager  # 新增
        # 技能冷却相关
        self.skill_cooldown = 5.0
        self.skill_last_time = 0   # 上次释放技能的时间
        # 变身冷却相关
        self.transform_duration = 15.0  # 变身维持时间（秒）
        self.transform_cooldown = 40.0  # 变身冷却时间（秒）
        self.transform_last_time = 0    # 上次解除变身的时间
        self.transform_start_time = 0   # 变身开始时间
        self.transform_end_invincible = 0  # 变身解除后无敌结束时间
        self.wuhu_sound = pygame.mixer.Sound("assets/sound/wuhu.wav")
        self.wuhu_sound.set_volume(0.5)
        self.fireskill_sound = pygame.mixer.Sound("assets/sound/fireskill.wav")
        self.fireskill_sound.set_volume(0.5)
        
        # 添加audio_manager引用
        self.audio_manager = None  # 将在main.py中设置
    
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

    def _load_transform_frames(self):
        """加载变身后的角色动画帧"""
        frames = {}
        base_dir = "assets/characters/transform"
        # 加载idle动画
        frames["idle_down"] = self._load_dir_frames(f"{base_dir}/idle")
        frames["idle_right"] = frames["idle_down"]  # 共用相同动画
        frames["idle_up"] = frames["idle_down"]  # 共用相同动画
        
        # 加载move动画
        frames["move_down"] = self._load_dir_frames(f"{base_dir}/move")
        frames["move_right"] = frames["move_down"]  # 共用相同动画
        frames["move_up"] = frames["move_down"]  # 共用相同动画
        
        # 加载attack动画
        frames["attack_down"] = self._load_dir_frames(f"{base_dir}/attack")
        frames["attack_right"] = frames["attack_down"]  # 共用相同动画 
        frames["attack_up"] = frames["attack_down"]  # 共用相同动画
        
        # 加载其他动画
        frames["death"] = self._load_dir_frames(f"{base_dir}/die")
        frames["hurt"] = self._load_dir_frames(f"{base_dir}/hurt")
        frames["dash"] = self._load_dir_frames(f"{base_dir}/dash")
        
        return frames
    
    def _load_dir_frames(self, dir_path):
        """从目录加载所有png文件作为动画帧"""
        frames = []
        try:
            if not os.path.exists(dir_path):
                print(f"警告: 目录不存在 {dir_path}")
                return frames
                
            files = sorted([f for f in os.listdir(dir_path) if f.endswith('.png')])
            for file in files:
                fpath = os.path.join(dir_path, file)
                try:
                    frames.append(pygame.image.load(fpath).convert_alpha())
                except Exception as e:
                    print(f"加载帧失败 {fpath}: {e}")
        except Exception as e:
            print(f"加载目录失败 {dir_path}: {e}")
        return frames

    def _load_bianshen_frames(self):
        frames = []
        dir_path = "assets/characters/transform/bianshen"
        try:
            if not os.path.exists(dir_path):
                print(f"警告: 变身动画目录不存在 {dir_path}")
                return frames
            files = sorted([f for f in os.listdir(dir_path) if f.endswith('.png')])
            for file in files:
                fpath = os.path.join(dir_path, file)
                try:
                    frames.append(pygame.image.load(fpath).convert_alpha())
                except Exception as e:
                    print(f"加载变身动画帧失败 {fpath}: {e}")
        except Exception as e:
            print(f"加载变身动画目录失败 {dir_path}: {e}")
        return frames

    def _load_skill_frames(self):
        frames = []
        dir_path = "assets/characters/transform/skill"
        try:
            if not os.path.exists(dir_path):
                print(f"警告: 技能动画目录不存在 {dir_path}")
                return frames
            files = sorted([f for f in os.listdir(dir_path) if f.endswith('.png')])
            for file in files:
                fpath = os.path.join(dir_path, file)
                try:
                    frames.append(pygame.image.load(fpath).convert_alpha())
                except Exception as e:
                    print(f"加载技能动画帧失败 {fpath}: {e}")
        except Exception as e:
            print(f"加载技能动画目录失败 {dir_path}: {e}")
        return frames

    def _load_bullet_frames(self):
        frames = []
        dir_path = "assets/characters/transform/bullet"
        try:
            if not os.path.exists(dir_path):
                print(f"警告: 法术弹幕动画目录不存在 {dir_path}")
                return frames
            files = sorted([f for f in os.listdir(dir_path) if f.endswith('.png')])
            for file in files:
                fpath = os.path.join(dir_path, file)
                try:
                    frames.append(pygame.image.load(fpath).convert_alpha())
                except Exception as e:
                    print(f"加载法术弹幕动画帧失败 {fpath}: {e}")
        except Exception as e:
            print(f"加载法术弹幕动画目录失败 {dir_path}: {e}")
        return frames

    def move(self, keys, is_valid_position):
        if self.is_dead or self.is_transforming or self.is_using_skill:
            return  # 死亡、变身、技能期间不能移动
        if self.is_dashing:
            return  # 冲刺期间不能手动移动
        old_x, old_y = self.rect.topleft
        self.is_moving = False
        # 处理水平移动
        if keys[pygame.K_a]:
            self.rect.x -= self.move_speed
            self.facing_left = True
            self.direction = "left"
            self.is_moving = True
            if not all(is_valid_position(self.rect.left, y) for y in range(self.rect.top + 4, self.rect.bottom - 4, 4)):
                self.rect.x = old_x
        if keys[pygame.K_d]:
            self.rect.x += self.move_speed
            self.facing_left = False
            self.direction = "right"
            self.is_moving = True
            if not all(is_valid_position(self.rect.right - 1, y) for y in range(self.rect.top + 4, self.rect.bottom - 4, 4)):
                self.rect.x = old_x
        # 处理垂直移动
        if keys[pygame.K_w]:
            self.rect.y -= self.move_speed
            self.direction = "up"
            self.is_moving = True
            if not all(is_valid_position(x, self.rect.top) for x in range(self.rect.left + 4, self.rect.right - 4, 4)):
                self.rect.y = old_y
        if keys[pygame.K_s]:
            self.rect.y += self.move_speed
            self.direction = "down"
            self.is_moving = True
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
            try:
                channel = pygame.mixer.Channel(7)
                channel.stop()
                channel.set_volume(0.5)
                if self.transformed:
                    channel.play(self.firehit_sound)
                else:
                    channel.play(self.attack_none_sound)
            except Exception as e:
                print(f"播放空挥音效失败: {e}")
                if self.transformed:
                    self.firehit_sound.play()
                else:
                    self.attack_none_sound.play()
            return True
        return False

    def generate_attack_rect(self):
        # 生成一个更大范围的攻击判定区域（突刺方向）
        attack_distance = 30
        attack_width = self.tile_width * 1.5
        attack_height = self.tile_height * 1.5

        if self.direction == "left":
            self.attack_rect = pygame.Rect(
                self.rect.left - attack_distance,
                self.rect.centery - attack_height // 2,
                attack_distance,
                attack_height
            )
        elif self.direction == "right":
            self.attack_rect = pygame.Rect(
                self.rect.right,
                self.rect.centery - attack_height // 2,
                attack_distance,
                attack_height
            )
        elif self.direction == "up":
            self.attack_rect = pygame.Rect(
                self.rect.centerx - attack_width // 2,
                self.rect.top - attack_distance,
                attack_width,
                attack_distance
            )
        elif self.direction == "down":
            self.attack_rect = pygame.Rect(
                self.rect.centerx - attack_width // 2,
                self.rect.bottom,
                attack_width,
                attack_distance
            )

    def update(self):
        now = time.time()
        prev_action = self.action
        # 变身动画流程
        if self.is_transforming:
            self.action = "bianshen"
            if self.transform_anim_idx < len(self.transform_anim_frames) - 1:
                self.transform_anim_timer += 1/60
                if self.transform_anim_timer >= self.transform_anim_interval:
                    self.transform_anim_timer = 0
                    self.transform_anim_idx += 1
            else:
                # 动画播放完毕，切换到变身状态
                self.is_transforming = False
                self.transformed = not self.transformed
                self.set_transform_stats()
                self.frame_idx = 0
                # 变身解除时记录冷却
                if not self.transformed:
                    self.transform_last_time = now
                    self.transform_end_invincible = now + 1.0  # 解除变身后无敌1秒
            return
        if self.is_dead:
            self.action = "death"
            # 使用当前状态对应的帧集合
            frames_list = self.transform_frames.get("death") if self.transformed else self.frames.get("death")
            
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
            
        # 变身维持时间判定
        if self.transformed and now - self.transform_start_time >= self.transform_duration:
            self.transformed = False
            self.set_transform_stats()
            self.transform_last_time = now  # 解除变身时记录冷却
            self.transform_end_invincible = now + 1.0  # 解除变身后无敌1秒
        # 变身解除后无敌判定
        if hasattr(self, 'transform_end_invincible') and self.transform_end_invincible > 0:
            if now < self.transform_end_invincible:
                self.invincible = True
            else:
                self.invincible = False
                self.transform_end_invincible = 0
        # 冲刺逻辑
        if self.is_dashing:
            if self.walk_channel and self.walk_channel.get_busy():
                self.walk_channel.stop()
            speed = self.dash_speed
            dx, dy = 0, 0
            if self.direction == "left":
                dx = -1
            elif self.direction == "right":
                dx = 1
            elif self.direction == "up":
                dy = -1
            elif self.direction == "down":
                dy = 1
            for _ in range(int(speed)):
                old_x, old_y = self.rect.x, self.rect.y
                self.rect.x += dx
                self.rect.y += dy
                if not self.is_valid_position(self.rect.centerx, self.rect.centery):
                    self.rect.x, self.rect.y = old_x, old_y
                    break
                if not self.transformed:
                    self.dash_trail.append((self.rect.x, self.rect.y, time.time()))
            if not self.transformed:
                self.dash_trail = [t for t in self.dash_trail if now - t[2] < 0.2]
            if self.transformed and "dash" in self.transform_frames:
                self.action = "dash"
                dash_frames = self.transform_frames.get("dash", [])
                if dash_frames:
                    dash_progress = (now - self.dash_timer) / self.dash_duration
                    self.frame_idx = min(int(dash_progress * len(dash_frames)), len(dash_frames) - 1)
            else:
                self.action = "move"
            self.is_moving = True
            # 分离无敌和冲刺时长
            if now - self.dash_timer >= self.dash_invincible_duration:
                self.invincible = False
            if now - self.dash_timer >= self.dash_duration:
                self.is_dashing = False
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
            
        # 根据变身状态选择帧集合
        frames_dict = self.transform_frames if self.transformed else self.frames
        
        frames_list = frames_dict.get(action_key)
        if not frames_list and self.direction == "left" and self.action != "attack":
            frames_list = frames_dict.get(f"{self.action}_right")
        if not frames_list:
            frames_list = frames_dict.get("idle_down")
        if not frames_list:
            return
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
        # 技能动画流程
        if self.is_using_skill:
            self.action = "skill"
            if not hasattr(self, 'skill_bullet_fired'):
                self.skill_bullet_fired = False
            if not self.skill_bullet_fired and self.skill_idx == 2:
                direction = self.direction
                bullet_pos = self.rect.center
                self.skill_bullets.append(SkillBullet(bullet_pos, direction, self.bullet_frames, self.enemy_manager))
                self.skill_bullet_fired = True
            if self.skill_idx < len(self.skill_frames) - 1:
                self.skill_timer += 1/60
                if self.skill_timer >= self.skill_interval:
                    self.skill_timer = 0
                    self.skill_idx += 1
            else:
                self.is_using_skill = False
                self.frame_idx = 0
                self.skill_bullet_fired = False
        
        # 无论何种状态下都更新弹幕（移到外部）
        for bullet in self.skill_bullets:
            bullet.update(self.enemies, self.camera_x, self.camera_y)
        self.skill_bullets = [b for b in self.skill_bullets if b.alive]

    def take_damage(self, damage):
        if not self.is_dead and not self.invincible:
            self.current_health = max(0, self.current_health - damage)
            self.invincible = True
            self.invincible_timer = time.time()
            # 播放受伤音效，轮流播放
            try:
                channel = pygame.mixer.Channel(6)
                channel.stop()
                channel.set_volume(0.3)
                if self.hurt_sound_toggle:
                    channel.play(self.scream_sound)
                else:
                    channel.play(self.hurt_sound)
                self.hurt_sound_toggle = not self.hurt_sound_toggle
            except Exception as e:
                print(f"播放受伤音效失败: {e}")
                if self.hurt_sound_toggle:
                    self.scream_sound.play()
                else:
                    self.hurt_sound.play()
                self.hurt_sound_toggle = not self.hurt_sound_toggle
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
        # 先绘制弹幕，确保角色在弹幕上方
        for bullet in self.skill_bullets:
            bullet.draw(surface, camera_x, camera_y)

        # 变身动画优先播放
        if self.is_transforming and self.transform_anim_frames:
            frame = self.transform_anim_frames[self.transform_anim_idx]
            frame_width, frame_height = frame.get_size()
            draw_x = self.rect.centerx - frame_width // 2
            offset = 20
            draw_y = self.rect.bottom - frame_height + offset
            surface.blit(frame, (draw_x - camera_x, draw_y - camera_y))
            return
        # 技能动画优先播放
        if self.is_using_skill and self.skill_frames:
            frame = self.skill_frames[self.skill_idx]
            if self.direction == "left":
                frame = pygame.transform.flip(frame, True, False)
            frame_width, frame_height = frame.get_size()
            draw_x = self.rect.centerx - frame_width // 2
            offset = 20
            draw_y = self.rect.bottom - frame_height + offset
            surface.blit(frame, (draw_x - camera_x, draw_y - camera_y))
            return
        # 选择当前状态的帧集合
        frames_dict = self.transform_frames if self.transformed else self.frames
        # dash拖尾特效 - 只在非变身状态下显示
        if not self.transformed:
            for tx, ty, t in self.dash_trail:
                if self.action == "attack":
                    if self.direction == "left":
                        action_key = "attack_right"
                    else:
                        action_key = f"attack_{self.direction}"
                else:
                    action_key = f"move_{self.direction}"
                frames_list = frames_dict.get(action_key)
                if not frames_list and self.direction == "left" and self.action != "attack":
                    frames_list = frames_dict.get(f"move_right")
                if not frames_list:
                    frames_list = frames_dict.get("idle_down")
                if frames_list:
                    frame = frames_list[self.frame_idx % len(frames_list)]
                    alpha = int(120 * (1 - (time.time() - t) / 0.2))
                    trail_img = frame.copy()
                    trail_img.set_alpha(alpha)
                    draw_x = tx - (48 - self.rect.width) // 2
                    draw_y = ty - (48 - self.rect.height)
                    surface.blit(trail_img, (draw_x - camera_x, draw_y - camera_y))
        # 死亡时只用death动画帧
        if self.is_dead:
            frames_list = frames_dict.get("death")
            flip = False
        elif self.action == "dash" and self.transformed and "dash" in frames_dict:
            frames_list = frames_dict.get("dash")
            flip = self.direction == "left"
        else:
            if self.action == "attack":
                if self.direction == "left":
                    action_key = "attack_right"
                else:
                    action_key = f"attack_{self.direction}"
            else:
                action_key = f"{self.action}_{self.direction}"
            frames_list = frames_dict.get(action_key)
            flip = False
            if self.action == "attack" and self.direction == "left":
                flip = True
            elif not frames_list and self.direction == "left":
                frames_list = frames_dict.get(f"{self.action}_right")
                flip = True
        if not frames_list:
            frames_list = frames_dict.get("idle_down")
        if not frames_list:
            return
        idx = min(self.frame_idx, len(frames_list)-1)
        frame = frames_list[idx]
        if flip:
            frame = pygame.transform.flip(frame, True, False)
        frame_width, frame_height = frame.get_size()
        if self.transformed:
            draw_x = self.rect.centerx - frame_width // 2
            offset = 20
            draw_y = self.rect.bottom - frame_height + offset
        else:
            draw_x = self.rect.x - (frame_width - self.rect.width) // 2
            draw_y = self.rect.y - (frame_height - self.rect.height)
        # 保证变身解除后无敌1秒期间必定闪烁
        visible = True
        if (self.invincible or (hasattr(self, 'transform_end_invincible') and self.transform_end_invincible > time.time())) and not self.is_dashing:
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
            self.dash_trail.clear()  # dash开始时清空拖尾
            self.dash_trail.append((self.rect.x, self.rect.y, time.time()))  # 记录起点
            # 无论是否移动，都播放冲刺音效
            try:
                if self.transformed:
                    channel = pygame.mixer.Channel(4)
                    channel.stop()
                    channel.set_volume(0.3)
                    channel.play(self.firedash_sound)
                else:
                    channel = pygame.mixer.Channel(4)
                    channel.stop()
                    channel.set_volume(0.3)
                    channel.play(self.dash_sound)
            except Exception as e:
                print(f"播放冲刺音效失败: {e}")
                if self.transformed:
                    self.firedash_sound.play()
                else:
                    self.dash_sound.play()

    def equip_new_sword(self, img_path):
        """
        装备新武器，如果是耄耋之卵则获得变身能力
        """
        if img_path == "assets/weapon/maoluan.png":
            self.has_maoluan = True
            # 加载变身动画帧
            self.transform_frames = self._load_transform_frames()
            print("获得了耄耋之卵，按L键可以变身！")
    
    def toggle_transform(self):
        now = time.time()
        # 冷却判定
        if self.has_maoluan and not self.is_dead and not self.is_transforming:
            if not self.transformed and now - self.transform_last_time < self.transform_cooldown:
                return False
            self.is_transforming = True
            self.transform_anim_idx = 0
            self.transform_anim_timer = 0
            if not self.transformed:
                self.transform_start_time = now  # 记录变身开始时间
                try:
                    self.wuhu_sound.play()
                except Exception as e:
                    print(f"播放变身音效失败: {e}")
            return True
        return False 

    def set_transform_stats(self):
        if self.transformed:
            self.attack_damage = self.base_attack_damage *2   # 变身后攻击力
            self.dash_speed = self.base_dash_speed *2  # 变身后冲刺更远
        else:
            self.attack_damage = self.base_attack_damage
            self.dash_speed = self.base_dash_speed 

    def use_skill(self):
        now = time.time()
        if self.transformed and not self.is_using_skill and not self.is_transforming and not self.is_dead:
            # 技能冷却判定
            if now - self.skill_last_time < self.skill_cooldown:
                return False
            self.is_using_skill = True
            self.skill_idx = 0
            self.skill_timer = 0
            self.skill_bullet_fired = False
            self.skill_last_time = now  # 记录释放时间
            
            # 更稳定的音效播放逻辑
            print(f"[DEBUG] 技能释放，准备播放音效")
            try:
                # 使用专用频道播放技能音效，避免与其它音效冲突
                channel = pygame.mixer.Channel(3)
                channel.stop()  # 停止当前在频道3上播放的音效
                channel.set_volume(0.8)  # 稍微调高音量确保能听到
                # 优先使用audio_manager
                if hasattr(self, 'audio_manager') and self.audio_manager:
                    print(f"[DEBUG] 使用audio_manager播放fireskill音效")
                    self.audio_manager.play_sound(SoundCategory.COMBAT, "fireskill")
                    # 备用方案：同时使用频道直接播放
                    channel.play(self.fireskill_sound)
                else:
                    print(f"[DEBUG] 直接使用频道播放fireskill音效")
                    channel.play(self.fireskill_sound)
            except Exception as e:
                print(f"[ERROR] 播放技能音效失败: {e}")
                # 最后尝试：直接播放
                try:
                    self.fireskill_sound.play()
                    print("[DEBUG] 回退到直接播放fireskill_sound")
                except Exception as e2:
                    print(f"[ERROR] 直接播放也失败: {e2}")
            
            return True
        return False
   
    def set_enemies(self, enemies):
        """更新敌人列表"""
        self.enemies = enemies

    def set_camera_pos(self, x, y):
        """设置相机位置"""
        self.camera_x = x
        self.camera_y = y

    def get_dash_cooldown_info(self):
        """返回(剩余冷却时间, 总冷却时间)"""
        now = time.time()
        elapsed = now - self.dash_last_time
        remain = max(0, self.dash_cooldown - elapsed)
        return remain, self.dash_cooldown

    def get_attack_cooldown_info(self):
        """返回(剩余冷却时间, 总冷却时间)"""
        now = time.time()
        elapsed = now - self.attack_last_time
        remain = max(0, self.attack_cooldown - elapsed)
        return remain, self.attack_cooldown

    def get_skill_cooldown_info(self):
        """返回(剩余冷却时间, 总冷却时间)"""
        now = time.time()
        elapsed = now - self.skill_last_time
        remain = max(0, self.skill_cooldown - elapsed)
        return remain, self.skill_cooldown

    def get_transform_cooldown_info(self):
        """返回(剩余冷却时间, 总冷却时间)"""
        now = time.time()
        elapsed = now - self.transform_last_time
        remain = max(0, self.transform_cooldown - elapsed)
        return remain, self.transform_cooldown
