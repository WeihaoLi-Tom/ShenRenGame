import pygame
from pathlib import Path
import time
import math
import random

class Player:
    def __init__(self, spawn_pos, tile_size):
        self.tile_width, self.tile_height = tile_size
        self.image = self.load_image()
        self.rect = self.image.get_rect()
        self.rect.topleft = spawn_pos
        self.move_speed = 1.8
        
        # 攻击相关属性
        self.attacking = False
        self.attack_timer = 0
        self.attack_duration = 0.3  # 攻击持续时间（秒）
        self.attack_cooldown = 1  # 攻击冷却时间（秒）
        self.attack_last_time = 0
        self.attack_range = self.tile_width  # 攻击范围
        self.attack_damage = 100
        self.facing = "right"  # 玩家朝向，用于决定攻击方向
        # 添加剑的攻击判定区域
        self.attack_rect = pygame.Rect(0, 0, 0, 0)
        
        # 剑图片
        self.sword_img = self.load_sword_image()
        
        # 生命值系统
        self.max_health = 1000
        self.current_health = 1000
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 1.0  # 受伤后无敌时间
        
        # 死亡相关
        self.is_dead = False
        self.death_timer = 0
        self.death_duration = 1.0  # 死亡动画持续时间
        self.death_angle = 0  # 死亡时的旋转角度
        self.gg_image = self.load_gg_image()
        self.gg_alpha = 0  # GG图片的透明度
        
        # 环绕攻击相关
        self.attack_mode = "stab"  # "stab"为突刺，"orbit"为环绕
        self.orbit_attack_anim = False
        self.orbit_attack_start_time = 0
        self.orbit_attack_duration = 0.5  # 环绕动画时长（秒）
        self.orbit_attack_angle = 0
        self.orbit_attack_hit = False  # 防止多次判定
        self.orbit_trail = []  # 剑影轨迹
        self.orbit_trail_length = 8  # 剑影数量
        self.orbit_particles = []  # 粒子特效
    
    def load_image(self):
        player_path = Path("assets/characters/player.png")
        if player_path.exists():
            img = pygame.image.load(str(player_path)).convert_alpha()
        else:
            img = pygame.Surface((self.tile_width, self.tile_height), pygame.SRCALPHA)
            pygame.draw.rect(img, (0, 128, 255), (0, 0, self.tile_width, self.tile_height))
        return pygame.transform.scale(img, (self.tile_width, self.tile_height))

    def load_sword_image(self):
        sword_path = Path("assets/weapon/tile_0106.png")
        if sword_path.exists():
            img = pygame.image.load(str(sword_path)).convert_alpha()
            # 恢复原始尺寸
            return pygame.transform.scale(img, (self.tile_width, self.tile_height))
        else:
            # 占位图
            img = pygame.Surface((self.tile_width, self.tile_height), pygame.SRCALPHA)
            pygame.draw.rect(img, (255, 255, 0), (0, 0, self.tile_width, self.tile_height), 2)
            return img

    def load_gg_image(self):
        """加载GG图片"""
        gg_path = Path("assets/title/gg.png")
        if gg_path.exists():
            try:
                img = pygame.image.load(str(gg_path)).convert_alpha()
                # 调整图片大小
                return pygame.transform.scale(img, (200, 200))
            except Exception as e:
                print(f"加载GG图片时出错: {e}")
                return None
        return None

    def move(self, keys, is_valid_position):
        old_x, old_y = self.rect.topleft
        # 水平移动
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.move_speed
            self.facing = "left"
            left_center = is_valid_position(self.rect.left, self.rect.centery)
            if not left_center:
                self.rect.x = old_x
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.move_speed
            self.facing = "right"
            right_center = is_valid_position(self.rect.right - 1, self.rect.centery)
            if not right_center:
                self.rect.x = old_x
        # 垂直移动
        if keys[pygame.K_UP]:
            self.rect.y -= self.move_speed
            self.facing = "up"
            top_center = is_valid_position(self.rect.centerx, self.rect.top)
            if not top_center:
                self.rect.y = old_y
        if keys[pygame.K_DOWN]:
            self.rect.y += self.move_speed
            self.facing = "down"
            bottom_center = is_valid_position(self.rect.centerx, self.rect.bottom - 1)
            if not bottom_center:
                self.rect.y = old_y
                
    def attack(self):
        current_time = time.time()
        if self.attack_mode == "orbit":
            if not self.orbit_attack_anim and current_time - self.attack_last_time >= self.attack_cooldown:
                self.orbit_attack_anim = True
                self.orbit_attack_start_time = current_time
                self.orbit_attack_angle = 0
                self.attack_last_time = current_time
                self.orbit_attack_hit = False
                # 记录环绕中心点
                self.orbit_center = (self.rect.x + self.rect.width / 2, self.rect.y + self.rect.height / 2)
                return True
            return False
        # 原有突刺逻辑
        if not self.attacking and current_time - self.attack_last_time >= self.attack_cooldown:
            self.attacking = True
            self.attack_timer = current_time
            self.attack_last_time = current_time
            self.generate_attack_rect()
            return True
        return False
    
    def generate_attack_rect(self):
        """生成一个更大范围的攻击判定区域"""
        # 攻击范围至少是角色的2倍
        attack_distance = 50  # 更远的攻击距离
        attack_width = self.tile_width * 2.0  # 更宽的攻击范围
        attack_height = self.tile_height * 2.0  # 更高的攻击范围
        
        if self.facing == "right":
            self.attack_rect = pygame.Rect(
                self.rect.right, 
                self.rect.centery - attack_height // 2,
                attack_distance,
                attack_height
            )
        elif self.facing == "left":
            self.attack_rect = pygame.Rect(
                self.rect.left - attack_distance, 
                self.rect.centery - attack_height // 2,
                attack_distance,
                attack_height
            )
        elif self.facing == "up":
            self.attack_rect = pygame.Rect(
                self.rect.centerx - attack_width // 2, 
                self.rect.top - attack_distance,
                attack_width,
                attack_distance
            )
        elif self.facing == "down":
            self.attack_rect = pygame.Rect(
                self.rect.centerx - attack_width // 2, 
                self.rect.bottom,
                attack_width,
                attack_distance
            )

    def get_orbit_attack_rect(self):
        if self.attack_mode == "orbit" and self.orbit_attack_anim:
            center = self.rect.center
            radius = 40
            angle_deg = self.orbit_attack_angle
            angle_rad = math.radians(angle_deg)
            sword_x = center[0] + radius * math.cos(angle_rad)
            sword_y = center[1] + radius * math.sin(angle_rad)
            # 剑柄始终朝向玩家
            sword_angle = angle_deg + 90
            rotated_sword = pygame.transform.rotate(self.sword_img, -sword_angle)
            sword_rect = rotated_sword.get_rect(center=(sword_x, sword_y))
            return sword_rect
        return pygame.Rect(0, 0, 0, 0)

    def update(self):
        # 更新死亡状态
        if self.is_dead:
            current_time = time.time()
            death_progress = (current_time - self.death_timer) / self.death_duration
            
            # 更新旋转角度（0到90度）
            self.death_angle = min(90, death_progress * 90)
            
            # 更新GG图片透明度（0到255）
            self.gg_alpha = min(255, int(death_progress * 255))
            return

        # 更新攻击状态
        if self.attacking:
            current_time = time.time()
            if current_time - self.attack_timer >= self.attack_duration:
                self.attacking = False
        
        # 更新环绕攻击状态
        if self.attack_mode == "orbit" and self.orbit_attack_anim:
            current_time = time.time()
            elapsed = current_time - self.orbit_attack_start_time
            t = min(elapsed / self.orbit_attack_duration, 1.0)
            self.orbit_attack_angle = 360 * t
            # 用固定的orbit_center
            center_x, center_y = getattr(self, 'orbit_center', (self.rect.x + self.rect.width / 2, self.rect.y + self.rect.height / 2))
            radius = 40
            angle_deg = self.orbit_attack_angle
            angle_rad = math.radians(angle_deg)
            sword_x = center_x + radius * math.cos(angle_rad)
            sword_y = center_y + radius * math.sin(angle_rad)
            sword_angle = angle_deg + 90
            # 生成线状粒子（切线方向）
            for _ in range(2):
                tangent_angle = angle_rad + math.pi/2  # 切线方向
                base_speed = random.uniform(1.2, 2.0)
                tangent_angle += random.uniform(-0.18, 0.18)
                vx = math.cos(tangent_angle) * base_speed
                vy = math.sin(tangent_angle) * base_speed
                self.orbit_particles.append({
                    'x': sword_x,
                    'y': sword_y,
                    'vx': vx,
                    'vy': vy,
                    'life': random.uniform(0.35, 0.55),
                    'age': 0,
                    'color': (255, 255, random.randint(120, 255)),
                    'size': random.randint(2, 4)
                })
            for p in self.orbit_particles:
                p['x'] += p['vx']
                p['y'] += p['vy']
                p['age'] += 1/60
            self.orbit_particles = [p for p in self.orbit_particles if p['age'] < p['life']]
            if t >= 1.0:
                self.orbit_attack_anim = False
                self.orbit_particles.clear()
        
        # 更新无敌状态
        if self.invincible:
            current_time = time.time()
            if current_time - self.invincible_timer >= self.invincible_duration:
                self.invincible = False
                
    def take_damage(self, damage):
        if not self.invincible and not self.is_dead:
            self.current_health = max(0, self.current_health - damage)
            self.invincible = True
            self.invincible_timer = time.time()
            
            # 检查是否死亡
            if self.current_health <= 0:
                self.die()
            return True
        return False
    
    def die(self):
        """处理玩家死亡"""
        if not self.is_dead:
            self.is_dead = True
            self.death_timer = time.time()
            self.death_angle = 0
            self.gg_alpha = 0
            # 停止所有移动
            self.move_speed = 0

    def heal(self, amount):
        self.current_health = min(self.max_health, self.current_health + amount)
            
    def get_attack_rect(self):
        """获取当前攻击判定区域"""
        if self.attacking:
            return self.attack_rect
        return pygame.Rect(0, 0, 0, 0)

    def draw(self, surface, camera_x, camera_y):
        if self.is_dead:
            # 绘制倒下的角色
            player_x = self.rect.x - camera_x
            player_y = self.rect.y - camera_y
            
            # 创建旋转后的图像
            rotated_image = pygame.transform.rotate(self.image, self.death_angle)
            # 获取旋转后的矩形
            rotated_rect = rotated_image.get_rect(center=self.rect.center)
            # 调整位置以保持中心点不变
            rotated_rect.x -= camera_x
            rotated_rect.y -= camera_y
            
            surface.blit(rotated_image, rotated_rect)
            
            # 绘制GG图片
            if self.gg_image:
                # 创建临时surface来设置透明度
                temp_surface = pygame.Surface(self.gg_image.get_size(), pygame.SRCALPHA)
                temp_surface.fill((255, 255, 255, self.gg_alpha))
                self.gg_image.set_alpha(self.gg_alpha)
                
                # 计算GG图片位置（屏幕中央）
                gg_x = (surface.get_width() - self.gg_image.get_width()) // 2
                gg_y = (surface.get_height() - self.gg_image.get_height()) // 2
                
                surface.blit(self.gg_image, (gg_x, gg_y))
            return

        # 正常状态下的绘制
        player_x = self.rect.x - camera_x
        player_y = self.rect.y - camera_y
        
        # 无敌状态时闪烁
        visible = True
        if self.invincible:
            visible = int(time.time() * 10) % 2 == 0
            
        if visible:
            surface.blit(self.image, (player_x, player_y))
        
        # 绘制剑
        if self.attack_mode == "orbit" and self.orbit_attack_anim:
            # 环绕攻击模式
            center_x, center_y = getattr(self, 'orbit_center', (player_x + self.rect.width/2, player_y + self.rect.height/2))
            radius = 40
            angle_deg = self.orbit_attack_angle
            angle_rad = math.radians(angle_deg)
            sword_x = center_x + radius * math.cos(angle_rad)
            sword_y = center_y + radius * math.sin(angle_rad)
            sword_angle = angle_deg + 90
            # 粒子特效
            for p in self.orbit_particles:
                alpha = int(255 * (1 - p['age']/p['life']))
                color = (*p['color'], alpha)
                pygame.draw.circle(surface, color, (int(p['x']-camera_x), int(p['y']-camera_y)), p['size'])
            # 主剑
            rotated_sword = pygame.transform.rotate(self.sword_img, -sword_angle)
            sword_rect = rotated_sword.get_rect(center=(sword_x - camera_x, sword_y - camera_y))
            surface.blit(rotated_sword, sword_rect.topleft)
        else:
            # 原有突刺模式
            sword_img = self.sword_img.copy()
            
            # 剑与角色的基础距离
            offset = 4
            
            # 根据朝向确定角度和基础位置
            if self.facing == "right":
                angle = -90  # 剑柄朝左（玩家），剑尖朝右
                base_x = player_x + self.rect.width + offset
                base_y = player_y + self.rect.height // 2 + 4  # 向下偏移4像素
            elif self.facing == "left":
                angle = 90   # 剑柄朝右（玩家），剑尖朝左
                base_x = player_x - offset
                base_y = player_y + self.rect.height // 2 + 4  # 向下偏移4像素
            elif self.facing == "up":
                angle = 0    # 剑柄朝下（玩家），剑尖朝上
                base_x = player_x + self.rect.width // 2
                base_y = player_y - offset
            elif self.facing == "down":
                angle = 180  # 剑柄朝上（玩家），剑尖朝下
                base_x = player_x + self.rect.width // 2
                base_y = player_y + self.rect.height + offset
            
            # 如果正在攻击，计算突刺偏移
            if self.attacking:
                elapsed = time.time() - self.attack_timer
                progress = min(elapsed / self.attack_duration, 1.0)
                thrust = 1.0 - 4 * (progress - 0.5) * (progress - 0.5)
                thrust_distance = int(35 * thrust)  # 保留增加的突刺距离
                if self.facing == "right":
                    base_x += thrust_distance
                elif self.facing == "left":
                    base_x -= thrust_distance
                elif self.facing == "up":
                    base_y -= thrust_distance
                elif self.facing == "down":
                    base_y += thrust_distance
            
            sword_img_rot = pygame.transform.rotate(sword_img, angle)
            sword_rect = sword_img_rot.get_rect(center=(base_x, base_y))
            surface.blit(sword_img_rot, sword_rect.topleft)
        
        # 调试：绘制攻击判定区域
        if self.attacking and False:  # 设为True可开启判定区域显示
            debug_rect = pygame.Rect(
                self.attack_rect.x - camera_x,
                self.attack_rect.y - camera_y,
                self.attack_rect.width,
                self.attack_rect.height
            )
            pygame.draw.rect(surface, (255, 0, 0, 128), debug_rect, 2)

    def draw_health_bar(self, surface, x, y, width=100, height=16):
        # 圆角参数
        radius = height // 2
        
        # 背景（带阴影）
        shadow_rect = pygame.Rect(x+2, y+2, width, height)
        pygame.draw.rect(surface, (30, 30, 30), shadow_rect, border_radius=radius)
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (64, 64, 64), bg_rect, border_radius=radius)
        
        # 渐变色计算
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
        
        # 血量条
        health_width = int(width * percent)
        health_rect = pygame.Rect(x, y, health_width, height)
        pygame.draw.rect(surface, health_color, health_rect, border_radius=radius)
        
        # 高光
        highlight_rect = pygame.Rect(x, y, health_width, height//2)
        highlight_color = (255, 255, 255, 60)
        highlight_surface = pygame.Surface((health_width, height//2), pygame.SRCALPHA)
        highlight_surface.fill(highlight_color)
        surface.blit(highlight_surface, (x, y))
        
        # 边框
        pygame.draw.rect(surface, (220, 220, 220), bg_rect, 2, border_radius=radius)
        
        # 血量数值
        font = pygame.font.Font(None, height)
        text = f"{self.current_health}/{self.max_health}"
        text_surf = font.render(text, True, (30, 30, 30))
        text_rect = text_surf.get_rect(center=(x+width//2, y+height//2))
        surface.blit(text_surf, text_rect)

    def set_position(self, pos):
        self.rect.topleft = pos

    @property
    def position(self):
        return self.rect.topleft
        
    @property
    def health_percent(self):
        return self.current_health / self.max_health 

    def equip_new_sword(self, sword_path):
        """更换玩家的武器"""
        try:
            img = pygame.image.load(sword_path).convert_alpha()
            self.sword_img = pygame.transform.scale(img, (self.tile_width, self.tile_height))
            # 提升攻击力
            self.attack_damage = 20  # 双倍攻击力
            # 切换到环绕攻击模式
            self.attack_mode = "orbit"
            print(f"武器更换成功! 攻击力提升到: {self.attack_damage}")
            print("切换到环绕攻击模式!")
            # 播放装备音效
            try:
                equip_sound = pygame.mixer.Sound("assets/sfx/item.wav")
                equip_sound.play()
            except Exception as e:
                print(f"播放装备音效失败: {e}")
            return True
        except Exception as e:
            print(f"加载新武器图片时出错: {e}")
            return False 