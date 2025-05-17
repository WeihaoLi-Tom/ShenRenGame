import pygame
import sys
import random
import time
import math
from player import Player
from map_manager import MapManager
from enemy import Enemy, BossEnemy
from enemy_manager import EnemyManager

# 初始化
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Tom's Dungeon")
clock = pygame.time.Clock()

# 游戏状态
class GameState:
    RUNNING = "running"
    PAUSED = "paused"
    MENU = "menu"

# 初始化字体
try:
    font = pygame.font.Font(None, 24)
except:
    font = pygame.font.SysFont('arial', 24)

# 初始化地图管理器
try:
    map_manager = MapManager("tiled/sampleMap.tmx", debug=True)
except Exception as e:
    print(f"加载地图时出错: {e}")
    sys.exit(1)

# 摄像机参数
ZOOM_LEVEL = 2.5
MIN_ZOOM = 1.0
MAX_ZOOM = 4.0
zoomed_width = int(WINDOW_WIDTH / ZOOM_LEVEL)
zoomed_height = int(WINDOW_HEIGHT / ZOOM_LEVEL)

# 加载Boss出现提示图片
try:
    boss_warning_img = pygame.image.load("assets/title/Bosswarning.png").convert_alpha()
except Exception as e:
    boss_warning_img = None
    print(f"Boss提示图片加载失败: {e}")

boss_warning_timer = 0
boss_warning_duration = 2.0  # 秒

# 初始化玩家
try:
    spawn_pos = map_manager.find_safe_spawn()
    player = Player(spawn_pos, (map_manager.tile_width, map_manager.tile_height))
except Exception as e:
    print(f"初始化玩家时出错: {e}")
    sys.exit(1)

# 爆炸粒子类
class ExplosionParticle:
    def __init__(self, pos):
        self.x, self.y = pos
        self.radius = random.randint(4, 12)
        self.color = random.choice([
            (255, 200, 0), (255, 100, 0), (255, 255, 255),
            (255, 80, 80), (255, 255, 120), (255, 180, 80), (255, 80, 200)
        ])
        self.life = random.uniform(0.5, 1.0)
        self.birth = time.time()
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
    
    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
    
    def is_alive(self):
        return time.time() - self.birth < self.life
        
    def draw(self, surface, camera_x, camera_y, zoom=1.0):
        # 如果已过期，不绘制
        if not self.is_alive():
            return
            
        # 计算粒子在屏幕上的位置（考虑缩放）
        screen_x = int((self.x - camera_x) * zoom)
        screen_y = int((self.y - camera_y) * zoom)
        
        # 如果不在屏幕范围内，不绘制
        if (screen_x < -50 or screen_x > WINDOW_WIDTH + 50 or
            screen_y < -50 or screen_y > WINDOW_HEIGHT + 50):
            return
            
        # 计算当前透明度
        alpha = int(255 * (1 - (time.time() - self.birth) / self.life))
        radius = int(self.radius * zoom)
        
        # 创建临时表面并绘制
        temp_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(temp_surf, self.color + (alpha,), (radius, radius), radius)
        surface.blit(temp_surf, (screen_x - radius, screen_y - radius))

# 爆炸环
class ExplosionRing:
    def __init__(self, pos):
        self.x, self.y = pos
        self.birth = time.time()
        self.duration = 0.7
        self.max_radius = 120
    
    def is_alive(self):
        return time.time() - self.birth < self.duration
        
    def draw(self, surface, camera_x, camera_y, zoom=1.0):
        # 如果已过期，不绘制
        if not self.is_alive():
            return
            
        # 计算位置和当前状态
        screen_x = int((self.x - camera_x) * zoom)
        screen_y = int((self.y - camera_y) * zoom)
        
        # 如果不在屏幕范围内，不绘制
        if (screen_x < -150 or screen_x > WINDOW_WIDTH + 150 or
            screen_y < -150 or screen_y > WINDOW_HEIGHT + 150):
            return
            
        # 计算当前半径和透明度
        progress = (time.time() - self.birth) / self.duration
        radius = int(self.max_radius * progress * zoom)
        alpha = int(180 * (1 - progress))
        
        # 创建临时表面并绘制
        temp_surf = pygame.Surface((radius*2 + 20, radius*2 + 20), pygame.SRCALPHA)
        pygame.draw.circle(temp_surf, (255, 255, 180, alpha), (radius + 10, radius + 10), radius, max(2, int(6 * zoom)))
        surface.blit(temp_surf, (screen_x - radius - 10, screen_y - radius - 10))

# 添加武器掉落类
class WeaponDrop:
    def __init__(self, pos, img_path="assets/weapon/swd2.png"):
        self.pos = pos
        self.rect = pygame.Rect(pos[0]-16, pos[1]-16, 32, 32)  # 较大的拾取范围
        try:
            self.image = pygame.image.load(img_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (32, 32))
        except Exception as e:
            print(f"加载武器图片时出错: {e}")
            self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (255, 215, 0), (0, 0, 32, 32))
        self.hover_offset = 0
        self.hover_speed = 2
        self.hover_direction = 1
        self.glow_alpha = 0
        self.glow_direction = 5  # 透明度变化速度
        self.birth_time = time.time()
        
    def update(self):
        # 上下浮动动画
        self.hover_offset += self.hover_speed * self.hover_direction * 0.05
        if abs(self.hover_offset) >= 5:
            self.hover_direction *= -1
            
        # 光环透明度动画
        self.glow_alpha += self.glow_direction
        if self.glow_alpha >= 180 or self.glow_alpha <= 30:
            self.glow_direction *= -1
            
    def draw(self, surface, camera_x, camera_y):
        # 绘制光环
        glow_surf = pygame.Surface((48, 48), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 215, 0, self.glow_alpha), (24, 24), 20)
        surface.blit(glow_surf, (self.pos[0] - camera_x - 24, self.pos[1] - camera_y - 24 + self.hover_offset))
        
        # 只绘制旋转后的武器图像
        angle = (time.time() - self.birth_time) * 20 % 360
        rotated_img = pygame.transform.rotate(self.image, angle)
        rot_rect = rotated_img.get_rect(center=(self.pos[0] - camera_x, self.pos[1] - camera_y + self.hover_offset))
        surface.blit(rotated_img, rot_rect)

# 全局变量
explosion_particles = []
explosion_rings = []
boss_dead_timer = 0
weapon_drop = None  # 存储武器掉落实例

# 初始化敌人管理器
enemy_manager = EnemyManager(map_manager, player)

# 其他参数
game_state = GameState.RUNNING
running = True
show_collision = False
show_debug = False
collision_modified = False
auto_save_timer = 0
AUTO_SAVE_INTERVAL = 60 * 30
fps = 0
fps_timer = time.time()
fps_counter = 0
last_time = time.time()

# 渐进BGM相关
boss_bgm_fadein = False
boss_bgm_fadein_timer = 0
boss_bgm_fadein_duration = 5.0  # 渐变时长2秒
boss_bgm_max_volume = 0.2       # 最大音量上限

# Boss出现回调机制
def on_boss_spawn():
    global boss_warning_timer
    boss_warning_timer = time.time()

def boss_bgm_fadein_trigger():
    global boss_bgm_fadein, boss_bgm_fadein_timer
    boss_bgm_fadein = True
    boss_bgm_fadein_timer = 0
    pygame.mixer.music.set_volume(0)

# 合并回调，确保两者都能触发

def merged_on_boss_spawn():
    boss_bgm_fadein_trigger()
    on_boss_spawn()

# Boss死亡特效触发函数
def on_boss_dead(pos=None):
    global boss_dead_timer, explosion_particles, explosion_rings, weapon_drop
    boss_dead_timer = time.time()
    
    # 使用传入的正确死亡位置(如果有)，否则使用Boss当前位置
    if pos:
        bx, by = pos
    elif enemy_manager.boss:
        bx, by = enemy_manager.boss.rect.center
    else:
        print("警告: 无法获取Boss位置，爆炸特效未创建")
        return  # 没有位置信息则直接返回

    print(f"触发Boss死亡特效，位置：({bx}, {by})")
    
    # 生成粒子
    for _ in range(80):
        explosion_particles.append(ExplosionParticle((bx, by)))
    
    # 生成冲击波圆环
    explosion_rings.append(ExplosionRing((bx, by)))
    print(f"创建了{len(explosion_particles)}个爆炸粒子和{len(explosion_rings)}个冲击波圆环")
    
    # 生成武器掉落
    weapon_drop = WeaponDrop((bx, by))
    print("Boss掉落了一把武器: swd2.png")

# 小怪死亡特效触发函数
def on_enemy_dead(pos):
    # 只生成少量、单色粒子
    for _ in range(10):
        p = ExplosionParticle(pos)
        p.color = random.choice([(180, 220, 255), (120, 180, 255)])  # 幽灵蓝色系
        p.life = random.uniform(0.2, 0.4)
        explosion_particles.append(p)

# 保证所有回调注册在主循环前
enemy_manager.on_boss_spawn = merged_on_boss_spawn
enemy_manager.on_boss_dead = on_boss_dead
enemy_manager.on_enemy_dead = on_enemy_dead

def draw_fps():
    global fps, fps_timer, fps_counter
    fps_counter += 1
    if time.time() - fps_timer >= 1:
        fps = fps_counter
        fps_counter = 0
        fps_timer = time.time()
    fps_text = font.render(f"FPS: {fps}", True, (255, 255, 255))
    screen.blit(fps_text, (10, 10))

def draw_debug_info():
    debug_text = [
        f"Pos: {player.position}",
        f"Zoom: {ZOOM_LEVEL:.1f}x",
        f"Collision: {'ON' if show_collision else 'OFF'}",
        f"FPS: {fps}",
        f"State: {game_state}"
    ]
    for i, text in enumerate(debug_text):
        text_surface = font.render(text, True, (255, 255, 255))
        screen.blit(text_surface, (10, 10 + i * 25))

while running:
    # 计算delta time
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if collision_modified:
                map_manager.save_collision_map()
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_state = GameState.PAUSED if game_state == GameState.RUNNING else GameState.RUNNING
            elif game_state == GameState.RUNNING:
                if event.key == pygame.K_f:  # F键只用于拾取武器
                    # 检查是否在武器掉落物附近
                    if weapon_drop and weapon_drop.rect.collidepoint(player.rect.center):
                        # 更换玩家武器
                        player.equip_new_sword("assets/weapon/swd2.png")
                        print("玩家拾取了新武器!")
                        weapon_drop = None  # 移除掉落物
                elif event.key == pygame.K_TAB:  # Tab键用于切换调试信息
                    show_debug = not show_debug
                    print(f"Debug info: {'ON' if show_debug else 'OFF'}")
                elif event.key == pygame.K_c:
                    show_collision = not show_collision
                    print(f"碰撞区域显示: {'开启' if show_collision else '关闭'}")
                elif event.key == pygame.K_e and show_collision:
                    map_manager.toggle_collision_at_position(player.rect.centerx, player.rect.centery)
                    collision_modified = True
                elif event.key == pygame.K_s:
                    if map_manager.save_collision_map():
                        collision_modified = False
                        auto_save_timer = 0
                elif event.key == pygame.K_d:
                    tile_x = player.rect.centerx // map_manager.tile_width
                    tile_y = player.rect.centery // map_manager.tile_height
                    print(f"玩家当前位置: 像素({player.position}) 瓦片({tile_x},{tile_y})")
                    print(f"该位置是否为墙壁: {map_manager.collision_map[tile_y][tile_x]}")
                elif event.key == pygame.K_h:
                    player.take_damage(10)
                    print(f"Player took damage! Health: {player.current_health}/{player.max_health}")
                elif event.key == pygame.K_r:
                    player.heal(10)
                    print(f"Player healed! Health: {player.current_health}/{player.max_health}")
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_state == GameState.RUNNING and show_collision:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            unscaled_x = int(camera_x + (mouse_x / WINDOW_WIDTH) * zoomed_width)
            unscaled_y = int(camera_y + (mouse_y / WINDOW_HEIGHT) * zoomed_height)
            map_manager.toggle_collision_at_position(unscaled_x, unscaled_y)
            collision_modified = True

    if game_state == GameState.RUNNING:
        # 玩家移动
        keys = pygame.key.get_pressed()
        player.move(keys, map_manager.is_valid_position)
        
        # 更新玩家状态
        player.update()
        
        # 更新敌人管理器
        enemy_manager.update(map_manager.is_valid_position, delta_time)

        # 处理攻击按键
        if keys[pygame.K_SPACE]:
            if player.attack():
                print("Player attacked!")
                # 攻击判定
                attack_rect = player.attack_rect
                enemy_manager.check_attacks(attack_rect)
                
        # 摄像机跟随逻辑
        camera_x = player.rect.centerx - zoomed_width // 2
        camera_y = player.rect.centery - zoomed_height // 2
        camera_x = max(0, min(camera_x, map_manager.map_width - zoomed_width))
        camera_y = max(0, min(camera_y, map_manager.map_height - zoomed_height))

        # 清空屏幕
        screen.fill((20, 20, 20))
        visible_area = pygame.Surface((zoomed_width, zoomed_height), pygame.SRCALPHA)

        # 绘制地图
        map_manager.draw_map(visible_area, camera_x, camera_y, zoomed_width, zoomed_height)
        if show_collision:
            map_manager.draw_collision_overlay(visible_area, camera_x, camera_y, zoomed_width, zoomed_height)
        
        # 绘制敌人
        enemy_manager.draw(visible_area, camera_x, camera_y)
        
        # 绘制武器掉落物
        if weapon_drop:
            weapon_drop.update()
            weapon_drop.draw(visible_area, camera_x, camera_y)
            
            # 检查玩家是否靠近武器，显示拾取提示
            pickup_distance = 50  # 提示显示距离
            px, py = player.rect.center
            wx, wy = weapon_drop.pos
            if ((px - wx) ** 2 + (py - wy) ** 2) ** 0.5 < pickup_distance:
                # 绘制提示文本
                pickup_font = pygame.font.Font(None, 20)
                pickup_text = pickup_font.render("Press F to Pick Up !", True, (255, 255, 255))
                text_x = wx - camera_x - pickup_text.get_width() // 2
                text_y = wy - camera_y - 40  # 在武器上方显示
                # 添加文字背景
                text_bg = pygame.Surface((pickup_text.get_width() + 10, pickup_text.get_height() + 6), pygame.SRCALPHA)
                pygame.draw.rect(text_bg, (0, 0, 0, 150), text_bg.get_rect(), 0, 3)
                visible_area.blit(text_bg, (text_x - 5, text_y - 3))
                visible_area.blit(pickup_text, (text_x, text_y))
        
        # 绘制玩家
        player.draw(visible_area, camera_x, camera_y)
        
        # 缩放并显示
        scaled_area = pygame.transform.scale(visible_area, (WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(scaled_area, (0, 0))

        # 更新和绘制爆炸粒子
        for p in explosion_particles[:]:
            p.update(delta_time)
            if not p.is_alive():
                explosion_particles.remove(p)
        
        # 清理过期冲击波
        for ring in explosion_rings[:]:
            if not ring.is_alive():
                explosion_rings.remove(ring)
                
        # 计算缩放比例
        zoom = WINDOW_WIDTH / zoomed_width
        
        # 在屏幕上绘制爆炸特效
        for p in explosion_particles:
            p.draw(screen, camera_x, camera_y, zoom)
        for ring in explosion_rings:
            ring.draw(screen, camera_x, camera_y, zoom)

        # 绘制调试信息
        if show_debug:
            draw_fps()
            draw_debug_info()
        
        # Boss出现提示
        if boss_warning_img and boss_warning_timer > 0:
            elapsed = time.time() - boss_warning_timer
            if elapsed < boss_warning_duration:
                # 缩放图片
                scale = 0.6
                img_w = int(boss_warning_img.get_width() * scale)
                img_h = int(boss_warning_img.get_height() * scale)
                scaled_img = pygame.transform.scale(boss_warning_img, (img_w, img_h))
                # 跳跃动画（正弦波上下浮动）
                jump_offset = int(18 * abs(math.sin(elapsed * 8)))  # 跳跃频率和幅度可调
                # 闪烁效果（每0.1秒闪一次）
                if int(elapsed * 10) % 2 == 0:
                    img_rect = scaled_img.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//4 + jump_offset))
                    screen.blit(scaled_img, img_rect)
            else:
                boss_warning_timer = 0
        
        # 始终绘制玩家血条
        player.draw_health_bar(screen, 10, WINDOW_HEIGHT - 30, 200, 20)

        # 自动保存逻辑
        if collision_modified:
            auto_save_timer += 1
            if auto_save_timer >= AUTO_SAVE_INTERVAL:
                if map_manager.save_collision_map():
                    collision_modified = False
                    auto_save_timer = 0
                    print("已自动保存碰撞地图")

        if boss_bgm_fadein:
            boss_bgm_fadein_timer += clock.get_time() / 1000.0
            vol = min(boss_bgm_fadein_timer / boss_bgm_fadein_duration, 1.0) * boss_bgm_max_volume
            pygame.mixer.music.set_volume(vol)
            if vol >= boss_bgm_max_volume:
                boss_bgm_fadein = False
    else:
        # 暂停状态显示
        screen.fill((20, 20, 20))
        pause_text = font.render("Game Pause - press ESC continue", True, (255, 255, 255))
        text_rect = pause_text.get_rect(center=(WINDOW_WIDTH/2, WINDOW_HEIGHT/2))
        screen.blit(pause_text, text_rect)

    pygame.display.flip()
    clock.tick(60)

if collision_modified:
    map_manager.save_collision_map()

pygame.quit()
sys.exit()
