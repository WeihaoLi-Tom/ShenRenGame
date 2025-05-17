import pygame
from pathlib import Path
import time
import random
import heapq
import math

class Enemy:
    def __init__(self, pos, size=(24, 24)):
        self.image = self.load_image(size)
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.float_x = float(self.rect.x)
        self.float_y = float(self.rect.y)
        self.max_health = 30
        self.current_health = 30
        self.move_speed = 0.5
        self.alive = True
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 0.5
        # 攻击相关
        self.attack_range = 20
        self.attack_damage = 10
        self.attack_cooldown = 1.0
        self.last_attack_time = 0
        # AI相关
        self.vision_range = 120  # 感知范围
        self.patrol_range = 64   # 巡逻半径
        self.patrol_center = pos
        self.patrol_dir = 1      # 1/-1，左右或上下巡逻
        self.patrol_axis = 'x'   # 'x'或'y'，巡逻方向
        self.patrol_timer = time.time()  # 初始化为当前时间
        self.patrol_interval = 2.0  # 每隔2秒换方向
        self.state = 'patrol'    # 'patrol' or 'chase'
        # 防卡墙参数
        self.stuck_time = 0
        self.stuck_threshold = 1.0  # 1秒不动判定为卡住
        self.last_position = pos
        self.random_dir_timer = 0
        self.random_dir_interval = 0.5
        self.random_direction = (0, 0)
        self.attack_mode = "stab"  # "stab"为突刺，"orbit"为环绕
        self.orbit_attack_anim = False
        self.orbit_attack_start_time = 0
        self.orbit_attack_duration = 0.5  # 环绕动画时长（秒）
        self.orbit_attack_angle = 0
        self.orbit_attack_hit = False  # 防止多次判定

    def load_image(self, size):
        ghost_path = Path("assets/characters/ghost.png")
        if ghost_path.exists():
            img = pygame.image.load(str(ghost_path)).convert_alpha()
            return pygame.transform.scale(img, size)
        else:
            img = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.circle(img, (200, 200, 255), (size[0]//2, size[1]//2), size[0]//2)
            return img

    def update(self, player, is_valid_position):
        if not self.alive:
            return
        
        px, py = player.rect.center
        ex, ey = self.rect.center
        dx = px - ex
        dy = py - ey
        dist = (dx ** 2 + dy ** 2) ** 0.5
        
        # 检测是否卡住(位置长时间不变)
        if (abs(self.rect.x - self.last_position[0]) < 0.1 and 
            abs(self.rect.y - self.last_position[1]) < 0.1):
            self.stuck_time += 0.016  # 假设每帧约16ms
        else:
            self.stuck_time = 0
            self.last_position = (self.rect.x, self.rect.y)
        
        # 状态切换
        if dist <= self.vision_range:
            self.state = 'chase'
        elif self.state == 'chase' and dist > self.vision_range * 1.2:
            self.state = 'patrol'
        
        # 行为
        if self.state == 'chase':
            if dist > self.attack_range:
                self.chase_player(dx, dy, dist)
        elif self.state == 'patrol':
            self.patrol()
        
        # 如果卡住了，尝试脱困
        if self.stuck_time >= self.stuck_threshold:
            self.unstuck()
        
        # 更新rect位置
        self.rect.x = int(self.float_x)
        self.rect.y = int(self.float_y)
        
        # 更新无敌状态
        if self.invincible:
            if time.time() - self.invincible_timer > self.invincible_duration:
                self.invincible = False
        
        # 环绕攻击逻辑
        if self.attack_mode == "orbit" and self.orbit_attack_anim:
            elapsed = time.time() - self.orbit_attack_start_time
            t = min(elapsed / self.orbit_attack_duration, 1.0)
            self.orbit_attack_angle = 360 * t
            if t >= 1.0:
                self.orbit_attack_anim = False

    def chase_player(self, dx, dy, dist):
        """追踪玩家的移动逻辑（只能上下左右单轴移动）"""
        if dist == 0:
            return
        # 优先移动距离更远的轴
        if abs(dx) > abs(dy):
            move_x = self.move_speed * (1 if dx > 0 else -1)
            next_x = self.float_x + move_x
            self.float_x = next_x
        else:
            move_y = self.move_speed * (1 if dy > 0 else -1)
            next_y = self.float_y + move_y
            self.float_y = next_y
    
    def patrol(self):
        """巡逻行为的移动逻辑（只能单轴移动）"""
        now = time.time()
        if now - self.patrol_timer > self.patrol_interval:
            self.patrol_dir *= -1
            self.patrol_axis = 'y' if self.patrol_axis == 'x' else 'x'
            self.patrol_timer = now
        move_x, move_y = 0, 0
        if self.patrol_axis == 'x':
            move_x = self.move_speed * self.patrol_dir
        else:
            move_y = self.move_speed * self.patrol_dir
        patrol_cx, patrol_cy = self.patrol_center
        if abs((self.float_x + move_x + self.rect.width//2) - patrol_cx) > self.patrol_range:
            move_x = 0
            self.patrol_dir *= -1
        if abs((self.float_y + move_y + self.rect.height//2) - patrol_cy) > self.patrol_range:
            move_y = 0
            self.patrol_dir *= -1
        self.float_x += move_x
        self.float_y += move_y
    
    def unstuck(self):
        """当幽灵卡住时尝试脱困（无视碰撞）"""
        now = time.time()
        if now - self.random_dir_timer > self.random_dir_interval:
            self.random_direction = (random.uniform(-1, 1), random.uniform(-1, 1))
            self.random_dir_timer = now
        dir_x, dir_y = self.random_direction
        length = (dir_x**2 + dir_y**2)**0.5
        if length > 0:
            dir_x /= length
            dir_y /= length
        escape_speed = self.move_speed * 1.5
        self.float_x += dir_x * escape_speed
        self.float_y += dir_y * escape_speed
        if (abs(self.float_x - self.last_position[0]) > 0.5 or 
            abs(self.float_y - self.last_position[1]) > 0.5):
            self.stuck_time = 0

    def take_damage(self, damage):
        if not self.invincible and self.alive:
            self.current_health -= damage
            self.invincible = True
            self.invincible_timer = time.time()
            if self.current_health <= 0:
                self.current_health = 0
                self.alive = False

    def draw(self, surface, camera_x, camera_y, show_debug_hitbox=False):
        if not self.alive:
            return
        x = self.rect.x - camera_x
        y = self.rect.y - camera_y
        # 受伤时闪烁
        visible = True
        if self.invincible:
            visible = int(time.time() * 10) % 2 == 0
        if visible:
            surface.blit(self.image, (x, y))
        # 绘制血条
        self.draw_health_bar(surface, x, y - 10, self.rect.width, 6)
        # 调试：绘制碰撞体和攻击范围
        if show_debug_hitbox:
            # 敌人碰撞体
            debug_rect = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            pygame.draw.rect(debug_rect, (255, 0, 0, 128), debug_rect.get_rect())
            surface.blit(debug_rect, (self.rect.x - camera_x, self.rect.y - camera_y))
            # 攻击范围（假设攻击时有attack_rect属性）
            if hasattr(self, 'attacking') and self.attacking and hasattr(self, 'attack_rect'):
                pygame.draw.rect(surface, (0, 0, 255, 120), self.attack_rect.move(-camera_x, -camera_y), 2)

    def draw_health_bar(self, surface, x, y, width, height):
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (64, 64, 64), bg_rect)
        percent = self.current_health / self.max_health
        health_width = int(width * percent)
        health_color = (0, 255, 0) if percent > 0.5 else (255, 0, 0)
        health_rect = pygame.Rect(x, y, health_width, height)
        pygame.draw.rect(surface, health_color, health_rect)
        pygame.draw.rect(surface, (200, 200, 200), bg_rect, 1)

    def try_attack(self, player):
        if not self.alive:
            return
        now = time.time()
        px, py = player.rect.center
        ex, ey = self.rect.center
        dist = ((px - ex) ** 2 + (py - ey) ** 2) ** 0.5
        if now - self.last_attack_time >= self.attack_cooldown:
            if dist <= self.attack_range:
                if player.take_damage(self.attack_damage):
                    self.last_attack_time = now

class BossEnemy:
    def __init__(self, pos, size=(32, 32)):
        self.image = self.load_image(size)
        self.normal_image = self.image.copy()
        self.attack_image = self.load_attack_image(size)
        self.rect = self.image.get_rect()
        self.rect.topleft = pos
        self.float_x = float(self.rect.x)
        self.float_y = float(self.rect.y)
        self.max_health = 200
        self.current_health = 200
        self.move_speed = 0.4  # 基础速度
        self.alive = True
        self.invincible = False
        self.invincible_timer = 0
        self.invincible_duration = 0.3
        # 攻击相关
        self.attack_range = 30
        self.attack_damage = 20
        self.attack_cooldown = 1.5
        self.last_attack_time = 0
        # AI相关
        self.vision_range = 150  # 感知范围
        self.patrol_range = 80   # 巡逻半径
        self.patrol_center = pos
        self.patrol_dir = 1
        self.patrol_axis = 'x'
        self.patrol_timer = time.time()
        self.patrol_interval = 3.0
        self.state = 'patrol'
        # 防卡墙参数
        self.stuck_time = 0
        self.stuck_threshold = 1.0
        self.last_position = pos
        self.random_dir_timer = 0
        self.random_dir_interval = 0.5
        self.random_direction = (0, 0)
        # 攻击动画
        self.is_attacking = False
        self.attack_anim_timer = 0
        self.attack_anim_duration = 0.3
        # 死亡位置
        self.death_position = None
        # 加速能力相关
        self.dash_speed = 7.0
        self.dash_duration = 1.0  # 加速持续时间
        self.dash_cooldown = 6.0  # 加速冷却时间
        self.is_dashing = False
        self.dash_timer = 0
        self.last_dash_time = 0
        self.dash_trail_particles = []  # 加速时的粒子效果
        # A*寻路相关
        self.path = []  # 当前A*路径（节点列表）
        self.astar_timer = 0
        self.astar_interval = 0.3  # 每0.3秒寻路一次
        self.last_astar_target = None
        self.map_manager = None  # 需要在创建Boss时传入map_manager
        # 脱困相关
        self.stuck_time = 0
        self.stuck_threshold = 1.0  # 1秒未大幅移动判定为卡住
        self.last_position = (self.float_x, self.float_y)
        self.unstuck_mode = False
        self.unstuck_dir = (0, 0)
        self.unstuck_timer = 0
        self.phase = 1
        self.phase2_triggered = False
        self.ha_bullets = []  # 存储弹幕
        self.ha_img = None
        self.load_ha_image((24, 24))  # 弹幕缩小一点更美观
        self.phase2_particles = []  # 二阶段粒子特效
        self.phase2_particle_timer = 0
        self.phase2_tip = None  # (显示时间戳, alpha)
        self.attack_mode = "stab"  # "stab"为突刺，"orbit"为环绕
        self.orbit_attack_anim = False
        self.orbit_attack_start_time = 0
        self.orbit_attack_duration = 0.5  # 环绕动画时长（秒）
        self.orbit_attack_angle = 0
        self.orbit_attack_hit = False  # 防止多次判定

    def set_map_manager(self, map_manager):
        self.map_manager = map_manager

    def load_image(self, size):
        boss_path = Path("assets/characters/maodie.png")
        if boss_path.exists():
            try:
                img = pygame.image.load(str(boss_path)).convert_alpha()
                rect = img.get_bounding_rect()
                cropped_img = img.subsurface(rect)
                return pygame.transform.scale(cropped_img, size)
            except Exception as e:
                print(f"加载Boss图片时出错: {e}，使用默认图形")
                img = pygame.Surface(size, pygame.SRCALPHA)
                pygame.draw.circle(img, (255, 200, 0), (size[0]//2, size[1]//2), size[0]//2)
                return img
        else:
            img = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.circle(img, (255, 200, 0), (size[0]//2, size[1]//2), size[0]//2)
            return img

    def load_attack_image(self, size):
        haqi_path = Path("assets/characters/haqi.png")
        if haqi_path.exists():
            try:
                img = pygame.image.load(str(haqi_path)).convert_alpha()
                rect = img.get_bounding_rect()
                cropped_img = img.subsurface(rect)
                return pygame.transform.scale(cropped_img, size)
            except Exception as e:
                print(f"加载haqi图片时出错: {e}，使用默认图形")
                img = pygame.Surface(size, pygame.SRCALPHA)
                pygame.draw.circle(img, (255, 0, 0), (size[0]//2, size[1]//2), size[0]//2)
                return img
        else:
            img = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.circle(img, (255, 0, 0), (size[0]//2, size[1]//2), size[0]//2)
            return img

    def load_ha_image(self, size):
        try:
            img = pygame.image.load("assets/characters/ha.png").convert_alpha()
            self.ha_img = pygame.transform.scale(img, size)
        except Exception as e:
            print(f"加载ha弹幕图片失败: {e}")
            self.ha_img = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.circle(self.ha_img, (255, 0, 0), (size[0]//2, size[1]//2), size[0]//2)

    def update(self, player, is_valid_position):
        if not self.alive:
            return
        # 二阶段切换
        if self.phase == 1 and self.current_health <= self.max_health // 2:
            self.phase = 2
            self.phase2_triggered = True
            print("Boss进入二阶段！无视碰撞")
            self.phase2_tip = (time.time(), 255)  # 进入二阶段时触发提示
        # 更新加速状态
        current_time = time.time()
        if self.is_dashing:
            if current_time - self.dash_timer >= self.dash_duration:
                self.is_dashing = False
                self.move_speed = 0.4  # 恢复基础速度
                self.image = self.normal_image  # 恢复普通状态图片
        elif current_time - self.last_dash_time >= self.dash_cooldown:
            # 在追踪状态下且玩家在视野范围内时触发加速
            if self.state == 'chase':
                self.trigger_dash()
            
        # 更新加速粒子效果
        if self.is_dashing:
            self.update_dash_particles()
            
        # 攻击动画计时
        if self.is_attacking:
            if time.time() - self.attack_anim_timer > self.attack_anim_duration:
                self.is_attacking = False
                self.image = self.normal_image
            
        px, py = player.rect.center
        ex, ey = self.rect.center
        dx = px - ex
        dy = py - ey
        dist = (dx ** 2 + dy ** 2) ** 0.5
        
        # --- 卡住检测 ---
        move_dist = ((self.float_x - self.last_position[0]) ** 2 + (self.float_y - self.last_position[1]) ** 2) ** 0.5
        if move_dist < 1.0:
            self.stuck_time += 0.016
        else:
            self.stuck_time = 0
            self.last_position = (self.float_x, self.float_y)
        # 如果卡住，进入脱困模式
        if self.stuck_time > self.stuck_threshold:
            if not self.unstuck_mode:
                self.unstuck_mode = True
                self.unstuck_timer = 0
                # 记录卡住时的格子
                self.stuck_tile = self.get_tile_pos(self.rect.center)
        # 脱困模式
        if self.unstuck_mode:
            self.unstuck_timer += 0.016
            # 重新A*寻路，临时把卡住格子设为障碍
            player_tile = self.get_tile_pos(player.rect.center)
            my_tile = self.get_tile_pos(self.rect.center)
            neighbor_tiles = []
            if self.map_manager:
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    nx, ny = player_tile[0]+dx, player_tile[1]+dy
                    if 0<=nx<self.map_manager.width and 0<=ny<self.map_manager.height:
                        if not self.map_manager.collision_map[ny][nx]:
                            neighbor_tiles.append((nx, ny))
            if not neighbor_tiles:
                neighbor_tiles = [player_tile]
            # 临时障碍
            avoid_tiles = {self.stuck_tile}
            path = self.astar_multi_goal(my_tile, neighbor_tiles, avoid_tiles)
            if path and len(path) > 1:
                next_tile = path[1]
                self.move_to_tile(next_tile, is_valid_position)
                # 如果移动距离大于2像素或脱困时间超过1秒，恢复A*寻路
                if ((self.float_x - self.last_position[0]) ** 2 + (self.float_y - self.last_position[1]) ** 2) ** 0.5 > 2.0 or self.unstuck_timer > 1.0:
                    self.unstuck_mode = False
                    self.stuck_time = 0
                    self.last_position = (self.float_x, self.float_y)
                return  # 脱困时不执行普通A*寻路
            else:
                # 没有新路径，等待或尝试原地小幅移动
                pass
        
        # 状态切换
        if dist <= self.vision_range:
            self.state = 'chase'
        elif self.state == 'chase' and dist > self.vision_range * 1.2:
            self.state = 'patrol'
        
        # 行为
        if self.state == 'chase':
            if dist > self.attack_range:
                self.chase_player(dx, dy, dist, is_valid_position)
        elif self.state == 'patrol':
            self.patrol(is_valid_position)
        
        # 更新rect位置
        self.rect.x = int(self.float_x)
        self.rect.y = int(self.float_y)
        
        # 更新无敌状态
        if self.invincible:
            if time.time() - self.invincible_timer > self.invincible_duration:
                self.invincible = False
        
        # --- A*寻路 ---
        self.astar_timer += 0.016  # 假设每帧16ms
        player_tile = self.get_tile_pos(player.rect.center)
        my_tile = self.get_tile_pos(self.rect.center)
        # 计算玩家周围一圈可通行格子
        neighbor_tiles = []
        if self.map_manager:
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                nx, ny = player_tile[0]+dx, player_tile[1]+dy
                if 0<=nx<self.map_manager.width and 0<=ny<self.map_manager.height:
                    if not self.map_manager.collision_map[ny][nx]:
                        neighbor_tiles.append((nx, ny))
        # 如果没有可通行邻居，仍以玩家格子为目标
        if not neighbor_tiles:
            neighbor_tiles = [player_tile]
        if self.map_manager and self.astar_timer >= self.astar_interval:
            self.astar_timer = 0
            # 只有目标或自身格子变化时才重新寻路
            if self.last_astar_target != (my_tile, tuple(neighbor_tiles)):
                self.path = self.astar_multi_goal(my_tile, neighbor_tiles)
                self.last_astar_target = (my_tile, tuple(neighbor_tiles))
        # 跟随A*路径
        if self.path and len(self.path) > 1:
            next_tile = self.path[1]  # path[0]是自己当前位置
            self.move_to_tile(next_tile, is_valid_position)
        # 更新弹幕
        self.update_ha_bullets(player)
        # 更新二阶段粒子特效
        if self.phase == 2:
            self.update_phase2_particles()
        # 发射ha后形象切回
        if hasattr(self, 'haqi_switch_time') and self.image == self.attack_image:
            if time.time() - self.haqi_switch_time > 0.2:
                self.image = self.normal_image
        
        # 环绕攻击逻辑
        if self.attack_mode == "orbit" and self.orbit_attack_anim:
            elapsed = time.time() - self.orbit_attack_start_time
            t = min(elapsed / self.orbit_attack_duration, 1.0)
            self.orbit_attack_angle = 360 * t
            if t >= 1.0:
                self.orbit_attack_anim = False
    
    def chase_player(self, dx, dy, dist, is_valid_position):
        """追踪玩家的移动逻辑（只能上下左右单轴移动，有碰撞检测）"""
        if dist == 0:
            return
        # 二阶段无视碰撞直接移动
        if self.phase == 2:
            move_x = self.move_speed * (dx / dist)
            move_y = self.move_speed * (dy / dist)
            self.float_x += move_x
            self.float_y += move_y
            return
            
        # 优先移动距离更远的轴
        if abs(dx) > abs(dy):
            move_x = self.move_speed * (1 if dx > 0 else -1)
            next_x = self.float_x + move_x
            if is_valid_position(int(next_x + self.rect.width//2), int(self.float_y + self.rect.height//2)):
                self.float_x = next_x
            else:
                # X方向被阻挡，尝试Y方向
                move_y = self.move_speed * (1 if dy > 0 else -1)
                next_y = self.float_y + move_y
                if is_valid_position(int(self.float_x + self.rect.width//2), int(next_y + self.rect.height//2)):
                    self.float_y = next_y
        else:
            move_y = self.move_speed * (1 if dy > 0 else -1)
            next_y = self.float_y + move_y
            if is_valid_position(int(self.float_x + self.rect.width//2), int(next_y + self.rect.height//2)):
                self.float_y = next_y
            else:
                # Y方向被阻挡，尝试X方向
                move_x = self.move_speed * (1 if dx > 0 else -1)
                next_x = self.float_x + move_x
                if is_valid_position(int(next_x + self.rect.width//2), int(self.float_y + self.rect.height//2)):
                    self.float_x = next_x
    
    def patrol(self, is_valid_position):
        """巡逻行为的移动逻辑（只能单轴移动，有碰撞检测）"""
        now = time.time()
        if now - self.patrol_timer > self.patrol_interval:
            self.patrol_dir *= -1
            self.patrol_axis = 'y' if self.patrol_axis == 'x' else 'x'
            self.patrol_timer = now
        move_x, move_y = 0, 0
        if self.patrol_axis == 'x':
            move_x = self.move_speed * self.patrol_dir
        else:
            move_y = self.move_speed * self.patrol_dir
        patrol_cx, patrol_cy = self.patrol_center
        if abs((self.float_x + move_x + self.rect.width//2) - patrol_cx) > self.patrol_range:
            move_x = 0
            self.patrol_dir *= -1
        if abs((self.float_y + move_y + self.rect.height//2) - patrol_cy) > self.patrol_range:
            move_y = 0
            self.patrol_dir *= -1
        # 只允许单轴移动并检测碰撞
        if move_x != 0:
            next_x = self.float_x + move_x
            if is_valid_position(int(next_x + self.rect.width//2), int(self.float_y + self.rect.height//2)):
                self.float_x = next_x
        elif move_y != 0:
            next_y = self.float_y + move_y
            if is_valid_position(int(self.float_x + self.rect.width//2), int(next_y + self.rect.height//2)):
                self.float_y = next_y
    
    def unstuck(self, is_valid_position):
        """当Boss卡住时尝试脱困 (有碰撞检测)"""
        now = time.time()
        
        if now - self.random_dir_timer > self.random_dir_interval:
            self.random_direction = (random.uniform(-1, 1), random.uniform(-1, 1))
            self.random_dir_timer = now
            
        dir_x, dir_y = self.random_direction
        length = (dir_x**2 + dir_y**2)**0.5
        if length > 0:
            dir_x /= length
            dir_y /= length
            
        escape_speed = self.move_speed * 1.5
        
        next_x = self.float_x + dir_x * escape_speed
        if is_valid_position(int(next_x + self.rect.width//2), int(self.float_y + self.rect.height//2)):
            self.float_x = next_x
            
        next_y = self.float_y + dir_y * escape_speed
        if is_valid_position(int(self.float_x + self.rect.width//2), int(next_y + self.rect.height//2)):
            self.float_y = next_y
            
        if is_valid_position(int(self.float_x + self.rect.width//2), int(self.float_y + self.rect.height//2)):
            if (abs(self.float_x - self.last_position[0]) > 0.5 or 
                abs(self.float_y - self.last_position[1]) > 0.5):
                self.stuck_time = 0

    def take_damage(self, damage):
        if not self.invincible and self.alive:
            self.current_health -= damage
            self.invincible = True
            self.invincible_timer = time.time()
            if self.current_health <= 0:
                self.current_health = 0
                self.alive = False
                # 记录死亡位置
                self.death_position = self.rect.center
                # 只有Boss才记录位置
                print(f"Boss死亡，位置：{self.death_position}")

    def try_attack(self, player):
        if not self.alive:
            return
        now = time.time()
        px, py = player.rect.center
        ex, ey = self.rect.center
        dist = ((px - ex) ** 2 + (py - ey) ** 2) ** 0.5
        if now - self.last_attack_time >= self.attack_cooldown:
            if self.phase == 1:
                if dist <= self.attack_range:
                    if player.take_damage(self.attack_damage):
                        self.last_attack_time = now
                        # 攻击动画切换
                        self.is_attacking = True
                        self.attack_anim_timer = time.time()
                        self.image = self.attack_image
            else:
                # 二阶段无视距离直接发射弹幕
                self.last_attack_time = now
                self.shoot_ha_bullet(player)

    def shoot_ha_bullet(self, player):
        # 发射时切换Boss形象为haqi.png
        self.image = self.attack_image
        # ...原有发射逻辑...
        ex, ey = self.rect.center
        px, py = player.rect.center
        dx, dy = px - ex, py - ey
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist == 0:
            dist = 1
        speed = 3.0
        vx = speed * dx / dist
        vy = speed * dy / dist
        bullet = {
            'x': ex,
            'y': ey,
            'vx': vx,
            'vy': vy,
            'img': self.ha_img,
            'rect': pygame.Rect(ex, ey, self.ha_img.get_width(), self.ha_img.get_height()),
            'alive': True,
            'age': 0
        }
        self.ha_bullets.append(bullet)
        # 发射后0.2秒切回普通形象
        self.haqi_switch_time = time.time()

    def update_ha_bullets(self, player):
        for bullet in self.ha_bullets:
            if not bullet['alive']:
                continue
            bullet['x'] += bullet['vx']
            bullet['y'] += bullet['vy']
            bullet['age'] += 1  # 每帧自增
            bullet['rect'].x = int(bullet['x'] - bullet['img'].get_width()//2)
            bullet['rect'].y = int(bullet['y'] - bullet['img'].get_height()//2)
            # 碰撞检测
            if bullet['rect'].colliderect(player.rect):
                player.take_damage(self.attack_damage)
                bullet['alive'] = False
            # 超出屏幕或地图范围
            if bullet['x'] < 0 or bullet['y'] < 0 or bullet['x'] > 2000 or bullet['y'] > 2000:
                bullet['alive'] = False
        # 移除死亡弹幕
        self.ha_bullets = [b for b in self.ha_bullets if b['alive']]

    def update_phase2_particles(self):
        # 每帧生成一些粒子，围绕Boss旋转
        import random, math
        self.phase2_particle_timer += 1
        if self.phase2_particle_timer % 3 == 0:
            angle = random.uniform(0, 2*math.pi)
            radius = random.randint(self.rect.width//2+8, self.rect.width)
            speed = random.uniform(0.05, 0.1)
            color = random.choice([(255,255,100,180),(255,180,50,160),(255,80,0,120)])
            self.phase2_particles.append({
                'angle': angle,
                'radius': radius,
                'speed': speed,
                'color': color,
                'life': random.randint(20, 40)
            })
        # 更新粒子
        for p in self.phase2_particles:
            p['angle'] += p['speed']
            p['life'] -= 1
        self.phase2_particles = [p for p in self.phase2_particles if p['life'] > 0]

    def draw(self, surface, camera_x, camera_y, font=None, show_debug_hitbox=False):
        if not self.alive:
            return
        x = self.rect.x - camera_x
        y = self.rect.y - camera_y
        # 二阶段特效：动态光环和粒子
        if self.phase == 2:
            cx = x + self.rect.width//2
            cy = y + self.rect.height//2
            # 绘制旋转粒子
            for p in self.phase2_particles:
                px = int(cx + math.cos(p['angle']) * p['radius'])
                py = int(cy + math.sin(p['angle']) * p['radius'])
                color = p['color']
                # 检查surface是否支持alpha
                if surface.get_flags() & pygame.SRCALPHA:
                    draw_color = color
                else:
                    draw_color = color[:3]
                pygame.draw.circle(surface, draw_color, (px, py), 4)
            # 绘制动态光环
            t = pygame.time.get_ticks() / 1000.0
            for r in range(self.rect.width//2+8, self.rect.width+8, 6):
                alpha = int(80 + 40*math.sin(t*2 + r))
                color = (255, 200, 50, alpha)
                halo = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
                pygame.draw.circle(halo, color, (r, r), r, 2)
                surface.blit(halo, (cx-r, cy-r), special_flags=pygame.BLEND_RGBA_ADD)
        # 绘制加速粒子效果
        if self.is_dashing:
            for particle in self.dash_trail_particles:
                alpha = int(255 * (1 - (time.time() - particle['birth']) / particle['life']))
                color = (*particle['color'][:3], alpha)
                pygame.draw.circle(surface, color, 
                                 (int(particle['x'] - camera_x), 
                                  int(particle['y'] - camera_y)), 3)
        
        # 受伤时闪烁
        visible = True
        if self.invincible:
            visible = int(time.time() * 10) % 2 == 0
        if visible:
            surface.blit(self.image, (x, y))
        # 绘制血条
        self.draw_health_bar(surface, x, y - 15, self.rect.width, 8)
        # 绘制弹幕（越飞越大）
        for bullet in self.ha_bullets:
            bx = bullet['x'] - camera_x - bullet['img'].get_width()//2
            by = bullet['y'] - camera_y - bullet['img'].get_height()//2
            # 计算缩放比例，最大2.5倍
            scale = min(1.0 + bullet['age'] * 0.02, 2.5)
            img = pygame.transform.rotozoom(bullet['img'], 0, scale)
            img_rect = img.get_rect(center=(bullet['x']-camera_x, bullet['y']-camera_y))
            surface.blit(img, img_rect)
        # ====== 新增：绘制"飞升喵星！"浮动提示 ======
        if self.phase2_tip and font is not None:
            start_time, _ = self.phase2_tip
            elapsed = time.time() - start_time
            duration = 2  # 总显示时长（秒）
            fade_duration = 0.8  # 渐隐时长
            if elapsed < duration:
                if elapsed > (duration - fade_duration):
                    alpha = int(255 * (1 - (elapsed - (duration - fade_duration)) / fade_duration))
                else:
                    alpha = 255
                small_font = pygame.font.Font(font.get_name(), 10) if hasattr(font, 'get_name') else font
                tip_text = small_font.render("飞升喵星！", True, (255, 255, 0))
                scale = 0.5
                tip_text = pygame.transform.smoothscale(tip_text, (int(tip_text.get_width()*scale), int(tip_text.get_height()*scale)))
                tip_text.set_alpha(alpha)

                # ---- 美化：添加圆角半透明背景 ----
                padding = 8
                bg_w = tip_text.get_width() + padding
                bg_h = tip_text.get_height() + padding
                bg_surf = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
                # 画圆角矩形
                pygame.draw.rect(bg_surf, (0, 0, 0, int(alpha*0.6)), (0, 0, bg_w, bg_h), border_radius=bg_h//2)
                # ---- 美化：伪描边 ----
                for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                    outline = small_font.render("飞升喵星！", True, (0,0,0))
                    outline = pygame.transform.smoothscale(outline, (int(outline.get_width()*scale), int(outline.get_height()*scale)))
                    outline.set_alpha(alpha)
                    bg_surf.blit(outline, (padding//2+dx, padding//2+dy))
                # 正常文字
                bg_surf.blit(tip_text, (padding//2, padding//2))

                tip_x = self.rect.centerx - camera_x - bg_w // 2
                tip_y = self.rect.top - camera_y - 38  # 适当上移
                surface.blit(bg_surf, (tip_x, tip_y))
            else:
                self.phase2_tip = None
        # ====== 新增结束 ======
        # 调试：绘制碰撞体和攻击范围
        if show_debug_hitbox:
            debug_rect = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
            pygame.draw.rect(debug_rect, (255, 0, 0, 128), debug_rect.get_rect())
            surface.blit(debug_rect, (self.rect.x - camera_x, self.rect.y - camera_y))
            # 攻击范围（假设攻击时有attack_rect属性）
            if hasattr(self, 'attacking') and self.attacking and hasattr(self, 'attack_rect'):
                pygame.draw.rect(surface, (0, 0, 255, 120), self.attack_rect.move(-camera_x, -camera_y), 2)

    def draw_health_bar(self, surface, x, y, width, height):
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(surface, (64, 64, 64), bg_rect)
        percent = self.current_health / self.max_health
        health_width = int(width * percent)
        health_color = (255, 50, 50) if percent > 0.3 else (200, 0, 0)
        health_rect = pygame.Rect(x, y, health_width, height)
        pygame.draw.rect(surface, health_color, health_rect)
        pygame.draw.rect(surface, (200, 200, 200), bg_rect, 1)

    def trigger_dash(self):
        """触发加速能力"""
        self.is_dashing = True
        self.dash_timer = time.time()
        self.last_dash_time = time.time()
        self.move_speed = 3.0  # 提升速度
        # 切换到加速状态图片
        self.image = self.attack_image
        # 生成初始粒子效果
        self.generate_dash_particles()

    def generate_dash_particles(self):
        """生成加速时的粒子效果"""
        for _ in range(5):  # 每次生成5个粒子
            self.dash_trail_particles.append({
                'x': self.rect.centerx,
                'y': self.rect.centery,
                'life': 0.5,  # 粒子生命周期
                'birth': time.time(),
                'color': (255, 200, 0, 128)  # 半透明的金色
            })

    def update_dash_particles(self):
        """更新加速粒子效果"""
        current_time = time.time()
        # 生成新的粒子
        if random.random() < 0.3:  # 30%的概率生成新粒子
            self.generate_dash_particles()
        
        # 更新现有粒子
        self.dash_trail_particles = [p for p in self.dash_trail_particles 
                                   if current_time - p['birth'] < p['life']]

    def get_tile_pos(self, pos):
        # pos为像素坐标，返回(tile_x, tile_y)
        tile_x = int(pos[0] // self.rect.width)
        tile_y = int(pos[1] // self.rect.height)
        return (tile_x, tile_y)

    def move_to_tile(self, tile, is_valid_position):
        # 让Boss朝目标格子移动
        target_x = tile[0] * self.rect.width
        target_y = tile[1] * self.rect.height
        dx = target_x - self.float_x
        dy = target_y - self.float_y
        dist = (dx ** 2 + dy ** 2) ** 0.5
        if dist == 0:
            return
        move_x = self.move_speed * dx / dist
        move_y = self.move_speed * dy / dist
        next_x = self.float_x + move_x
        next_y = self.float_y + move_y
        
        # 二阶段无视碰撞直接移动
        if self.phase == 2:
            self.float_x = next_x
            self.float_y = next_y
            return
            
        if is_valid_position(int(next_x + self.rect.width//2), int(next_y + self.rect.height//2)):
            self.float_x = next_x
            self.float_y = next_y

    def astar_multi_goal(self, start, goals, avoid_tiles=None):
        # A*算法，目标为goals中的任意一个，avoid_tiles为临时障碍集合
        width = self.map_manager.width
        height = self.map_manager.height
        collision = self.map_manager.collision_map
        if avoid_tiles is None:
            avoid_tiles = set()
            
        # 二阶段无视碰撞，直接返回目标路径
        if self.phase == 2:
            # 如果有多个目标，选择最近的
            if len(goals) > 1:
                nearest_goal = min(goals, key=lambda g: abs(g[0] - start[0]) + abs(g[1] - start[1]))
                return [start, nearest_goal]
            elif len(goals) == 1:
                return [start, goals[0]]
            else:
                return [start]
                
        def heuristic(a, b):
            return abs(a[0] - b[0]) + abs(a[1] - b[1])
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: min(heuristic(start, g) for g in goals)}
        goal_set = set(goals)
        while open_set:
            _, current = heapq.heappop(open_set)
            if current in goal_set:
                # 回溯路径
                path = [current]
                while current in came_from:
                    current = came_from[current]
                    path.append(current)
                path.reverse()
                return path
            for dx, dy in [(-1,0),(1,0),(0,-1),(0,1)]:
                neighbor = (current[0]+dx, current[1]+dy)
                if 0<=neighbor[0]<width and 0<=neighbor[1]<height:
                    if collision[neighbor[1]][neighbor[0]] or neighbor in avoid_tiles:
                        continue
                    tentative_g = g_score[current] + 1
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g
                        f_score[neighbor] = tentative_g + min(heuristic(neighbor, g) for g in goals)
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))
        return [start]  # 找不到路径时只返回起点 

    def attack(self):
        current_time = time.time()
        if self.attack_mode == "orbit":
            if not self.orbit_attack_anim and current_time - self.attack_last_time >= self.attack_cooldown:
                self.orbit_attack_anim = True
                self.orbit_attack_start_time = current_time
                self.orbit_attack_angle = 0
                self.attack_last_time = current_time
                self.orbit_attack_hit = False
            return False  # 不走原有突刺逻辑
        # 原有突刺逻辑
        if not self.is_attacking and current_time - self.last_attack_time >= self.attack_cooldown:
            self.is_attacking = True
            self.attack_anim_timer = current_time
            self.last_attack_time = current_time
            self.generate_attack_rect()
            return True
        return False 

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