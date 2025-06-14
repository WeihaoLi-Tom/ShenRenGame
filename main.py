import pygame
import sys
import time
import os
import math
from player import Player
from map_manager import MapManager
from enemy_manager import EnemyManager
from effects import EffectManager
from weapon_drop import WeaponDrop
from game_state import GameState, GameStateManager
from ui_manager import UIManager
from audio_manager import AudioManager, SoundCategory
from menu import GameMenu  # 导入新添加的菜单模块

# 初始化
pygame.init()
# 添加音频系统初始化，设置足够的声道数量
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=1024)
pygame.mixer.set_num_channels(32)  # 设置足够多的声道
print("音频系统初始化完成，声道数量:", pygame.mixer.get_num_channels())

WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Tom's Dungeon")
clock = pygame.time.Clock()

# 显示主菜单
menu = GameMenu(WINDOW_WIDTH, WINDOW_HEIGHT)
start_game = menu.run(screen)

# 如果玩家选择了退出，menu.run会调用sys.exit()
# 所以只有当玩家选择"开始游戏"时，才会继续下面的代码

# 初始化各个管理器
try:
    map_manager = MapManager("tiled/myMap.tmx", debug=True)
except Exception as e:
    print(f"加载地图时出错: {e}")
    sys.exit(1)

# 摄像机参数
ZOOM_LEVEL = 2.5
MIN_ZOOM = 1.0
MAX_ZOOM = 4.0
zoomed_width = int(WINDOW_WIDTH / ZOOM_LEVEL)
zoomed_height = int(WINDOW_HEIGHT / ZOOM_LEVEL)

# 初始化玩家
try:
    spawn_pos = map_manager.find_safe_spawn()
    player = Player(spawn_pos, (map_manager.tile_width, map_manager.tile_height), map_manager.is_valid_position)
except Exception as e:
    print(f"初始化玩家时出错: {e}")
    sys.exit(1)

# 初始化其他管理器
enemy_manager = EnemyManager(map_manager, player)
player.enemy_manager = enemy_manager
effect_manager = EffectManager()
game_state_manager = GameStateManager()
ui_manager = UIManager(WINDOW_WIDTH, WINDOW_HEIGHT, game_state_manager)
audio_manager = AudioManager()
player.audio_manager = audio_manager  # 设置player的audio_manager引用

# 全局变量
# weapon_drop = None  # 武器掉落物（改为使用enemy_manager.weapon_drop）
last_time = time.time()

# 新增：批量碰撞体编辑相关变量
selecting = False
select_start = None
select_end = None

# Boss出现回调机制
def merged_on_boss_spawn():
    ui_manager.trigger_boss_warning()
    audio_manager.trigger_boss_bgm()

# Boss死亡特效触发函数
def on_boss_dead(pos=None):
    if pos:
        bx, by = pos
    elif enemy_manager.boss:
        bx, by = enemy_manager.boss.rect.center
    else:
        print("警告: 无法获取Boss位置，爆炸特效未创建")
        return

    print(f"触发Boss死亡特效，位置：({bx}, {by})")
    effect_manager.create_explosion((bx, by))

# 小怪死亡特效触发函数
def on_enemy_dead(pos):
    effect_manager.create_small_explosion(pos)

# 注册回调
print("正在注册Boss相关回调...")
enemy_manager.on_boss_spawn = merged_on_boss_spawn
enemy_manager.on_boss_dead = on_boss_dead
enemy_manager.on_enemy_dead = on_enemy_dead
print("Boss相关回调注册完成")

show_debug_hitbox = False

try:
    gg_img = pygame.image.load("assets/title/gg.png").convert_alpha()
except Exception as e:
    gg_img = None
    print("死亡图片加载失败:", e)

gg_show_timer = 0  # 死亡动画结束后计时器

# 在初始化部分加载dashicon.png
try:
    dash_icon_path = os.path.join("assets", "icon", "dashicon.png")
    dash_icon = pygame.image.load(dash_icon_path).convert_alpha()
except Exception as e:
    dash_icon = None
    print("Dash图标加载失败:", e)

# 在初始化部分加载base.png
try:
    base_icon_path = os.path.join("assets", "icon", "base.png")
    base_icon = pygame.image.load(base_icon_path).convert_alpha()
except Exception as e:
    base_icon = None
    print("Base图标加载失败:", e)

# 在初始化部分加载attackicon.png
try:
    attack_icon_path = os.path.join("assets", "icon", "attackicon.png")
    attack_icon = pygame.image.load(attack_icon_path).convert_alpha()
except Exception as e:
    attack_icon = None
    print("Attack图标加载失败:", e)

# 在初始化部分加载bsicon.png
try:
    bs_icon_path = os.path.join("assets", "icon", "bsicon.png")
    bs_icon = pygame.image.load(bs_icon_path).convert_alpha()
except Exception as e:
    bs_icon = None
    print("变身图标加载失败:", e)

# 在初始化部分加载skillicon.png
try:
    skill_icon_path = os.path.join("assets", "icon", "skillicon1.png")
    skill_icon = pygame.image.load(skill_icon_path).convert_alpha()
except Exception as e:
    skill_icon = None
    print("技能图标加载失败:", e)

# 在初始化部分加载pickup.wav
try:
    pickup_sound_path = os.path.join("assets", "sound", "pickup.wav")
    pickup_sound = pygame.mixer.Sound(pickup_sound_path)
    pickup_sound.set_volume(0.5)
except Exception as e:
    pickup_sound = None
    print("拾取音效加载失败:", e)

running = True
while running:
    # 计算delta time
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time
    
    # 技能按钮通用参数（每帧都重新计算，防止窗口尺寸变化导致坐标错误）
    icon_size = 48
    gap = 18
    base_size = icon_size + 12
    base_offset = 6
    y_pos = WINDOW_HEIGHT - icon_size - 20

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            if game_state_manager.collision_modified:
                map_manager.save_collision_map()
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_state_manager.toggle_pause()
            elif game_state_manager.current_state == GameState.RUNNING:
                if event.key == pygame.K_f:  # F键只用于拾取武器
                    if enemy_manager.weapon_drop and enemy_manager.weapon_drop.rect.collidepoint(player.rect.center):
                        # 更稳定的拾取音效播放机制
                        print("[DEBUG] 触发拾取音效")
                        try:
                            # 使用专用频道2播放拾取音效
                            channel = pygame.mixer.Channel(2)
                            channel.stop()
                            channel.set_volume(0.6)
                            
                            # 双重保险：同时使用audio_manager和直接播放
                            audio_manager.play_sound(SoundCategory.UI, "pickup")
                            if pickup_sound:
                                channel.play(pickup_sound)
                                print("[DEBUG] 直接通过频道2播放pickup音效")
                        except Exception as e:
                            print(f"[ERROR] 拾取音效播放失败: {e}")
                            # 最后尝试直接播放
                            if pickup_sound:
                                try:
                                    pickup_sound.play()
                                    print("[DEBUG] 回退到直接播放pickup_sound")
                                except Exception as e2:
                                    print(f"[ERROR] 直接播放也失败: {e2}")
                        
                        if enemy_manager.weapon_drop.image_path == "assets/weapon/maoluan.png":
                            player.equip_new_sword("assets/weapon/maoluan.png")
                            print("玩家拾取了耄耋之卵!")
                        else:
                            player.equip_new_sword("assets/weapon/swd2.png")
                            print("玩家拾取了新武器!")
                        enemy_manager.weapon_drop = None
                elif event.key == pygame.K_TAB:
                    game_state_manager.toggle_debug_display()
                elif event.key == pygame.K_c:
                    game_state_manager.toggle_collision_display()
                elif event.key == pygame.K_k:
                    player.dash()
                elif event.key == pygame.K_l:
                    if player.toggle_transform():
                        game_state_manager.console_tip = "变身状态切换！"
                        game_state_manager.console_tip_timer = time.time()
                elif event.key == pygame.K_i:
                    if player.use_skill():
                        game_state_manager.console_tip = "技能释放！"
                        game_state_manager.console_tip_timer = time.time()
                # 开发者控制台按键
                elif game_state_manager.is_developer_mode():
                    if event.key == pygame.K_F1:  # 按F1生成耄耋之卵
                        enemy_manager.weapon_drop = WeaponDrop(player.rect.center, "assets/weapon/maoluan.png")
                        game_state_manager.console_tip = "已生成耄耋之卵"
                        game_state_manager.console_tip_timer = time.time()
                    elif event.key == pygame.K_o:
                        show_debug_hitbox = not show_debug_hitbox
                        print(f"碰撞体/攻击范围显示: {'开启' if show_debug_hitbox else '关闭'}")
                elif event.key == pygame.K_e and game_state_manager.show_collision:
                    if game_state_manager.is_developer_mode():
                        map_manager.toggle_collision_at_position(player.rect.centerx, player.rect.centery)
                        game_state_manager.mark_collision_modified()
                    else:
                        print("需要开启开发者模式才能修改碰撞体")
                elif event.key == pygame.K_s:
                    if game_state_manager.is_developer_mode():
                        if map_manager.save_collision_map():
                            game_state_manager.reset_auto_save()
                    else:
                        print("需要开启开发者模式才能保存碰撞地图")
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
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and game_state_manager.current_state == GameState.RUNNING and game_state_manager.show_collision:
            if game_state_manager.is_developer_mode():
                mouse_x, mouse_y = pygame.mouse.get_pos()
                unscaled_x = int(camera_x + (mouse_x / WINDOW_WIDTH) * zoomed_width)
                unscaled_y = int(camera_y + (mouse_y / WINDOW_HEIGHT) * zoomed_height)
                map_manager.toggle_collision_at_position(unscaled_x, unscaled_y)
                game_state_manager.mark_collision_modified()
            else:
                print("需要开启开发者模式才能修改碰撞体")
        # 开发者模式下右键批量切换碰撞体
        elif game_state_manager.is_developer_mode():
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
                selecting = True
                select_start = pygame.mouse.get_pos()
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 3 and selecting:
                selecting = False
                select_end = pygame.mouse.get_pos()
                # 计算选区范围（屏幕坐标转地图格子坐标）
                x1, y1 = select_start
                x2, y2 = select_end
                # 摄像机和缩放参数
                min_x = min(x1, x2)
                max_x = max(x1, x2)
                min_y = min(y1, y2)
                max_y = max(y1, y2)
                # 转为地图像素坐标
                map_x1 = int(camera_x + (min_x / WINDOW_WIDTH) * zoomed_width)
                map_x2 = int(camera_x + (max_x / WINDOW_WIDTH) * zoomed_width)
                map_y1 = int(camera_y + (min_y / WINDOW_HEIGHT) * zoomed_height)
                map_y2 = int(camera_y + (max_y / WINDOW_HEIGHT) * zoomed_height)
                # 转为tile坐标
                tile_x1 = max(0, map_x1 // map_manager.tile_width)
                tile_x2 = min(map_manager.width-1, map_x2 // map_manager.tile_width)
                tile_y1 = max(0, map_y1 // map_manager.tile_height)
                tile_y2 = min(map_manager.height-1, map_y2 // map_manager.tile_height)
                # 批量切换碰撞体
                for ty in range(tile_y1, tile_y2+1):
                    for tx in range(tile_x1, tile_x2+1):
                        map_manager.collision_map[ty][tx] = not map_manager.collision_map[ty][tx]
                game_state_manager.collision_modified = True
                print(f"批量切换碰撞体：({tile_x1},{tile_y1}) 到 ({tile_x2},{tile_y2})")

    if game_state_manager.current_state == GameState.RUNNING:
        # 玩家移动
        keys = pygame.key.get_pressed()
        player.move(keys, map_manager.is_valid_position)
        
        # 更新玩家状态
        player.update()
        
        # 环绕攻击模式下，动画期间每帧都判定一次
        if player.attack_mode == "orbit" and player.orbit_attack_anim:
            attack_rect = player.get_orbit_attack_rect()
            if attack_rect.width > 0 and not player.orbit_attack_hit:
                if enemy_manager.check_attacks(attack_rect):
                    player.orbit_attack_hit = True
        
        # 更新敌人管理器
        enemy_manager.update(map_manager.is_valid_position, delta_time)
        
        # 更新音频管理器
        audio_manager.update(delta_time)

        # 更新玩家的敌人列表
        player.set_enemies(enemy_manager.enemies)
        if enemy_manager.boss and enemy_manager.boss.alive:
            player.set_enemies(enemy_manager.enemies + [enemy_manager.boss])

        # 处理攻击按键
        if keys[pygame.K_j]:
            if player.attack():
                print("Player attacked!")
                if player.attack_mode == "orbit":
                    attack_rect = player.get_orbit_attack_rect()
                    if attack_rect.width > 0:
                        enemy_manager.check_attacks(attack_rect)
                else:
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
        if game_state_manager.show_collision:
            map_manager.draw_collision_overlay(visible_area, camera_x, camera_y, zoomed_width, zoomed_height)
        
        # 绘制敌人
        enemy_manager.draw(visible_area, camera_x, camera_y, ui_manager.font, show_debug_hitbox)
        
        # 绘制武器掉落物
        if enemy_manager.weapon_drop:
            enemy_manager.weapon_drop.update()
            enemy_manager.weapon_drop.draw(visible_area, camera_x, camera_y)
            enemy_manager.weapon_drop.draw_pickup_prompt(visible_area, camera_x, camera_y, player.rect.center, ui_manager.font)
        
        # 绘制玩家
        player.draw(visible_area, camera_x, camera_y, show_debug_hitbox)
        
        # 缩放并显示
        scaled_area = pygame.transform.scale(visible_area, (WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(scaled_area, (0, 0))

        # 更新和绘制特效
        effect_manager.update(delta_time)
        effect_manager.draw(screen, camera_x, camera_y, WINDOW_WIDTH / zoomed_width)

        # 绘制UI
        if game_state_manager.show_debug:
            ui_manager.draw_fps(screen)
            ui_manager.draw_debug_info(screen, player.position, ZOOM_LEVEL, 
                                     game_state_manager.show_collision, 
                                     ui_manager.fps, 
                                     game_state_manager.current_state)
        
        # 绘制Boss警告
        ui_manager.draw_boss_warning(screen)
        
        # 绘制玩家血条
        player.draw_health_bar(screen, 10, WINDOW_HEIGHT - 30, 200, 20)

        # L键（变身）
        if hasattr(player, 'has_maoluan') and player.has_maoluan and bs_icon:
            x_bs = WINDOW_WIDTH - icon_size*3 - gap*2 - 20
            if base_icon:
                scaled_base = pygame.transform.smoothscale(base_icon, (base_size, base_size))
                screen.blit(scaled_base, (x_bs - base_offset, y_pos - base_offset))
            scaled_icon = pygame.transform.smoothscale(bs_icon, (icon_size, icon_size))
            screen.blit(scaled_icon, (x_bs, y_pos))
            # 冷却扇形遮罩
            remain, total = player.get_transform_cooldown_info()
            if not player.transformed and remain > 0 and total > 0:
                ratio = remain / total
                mask_surf = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                center = (icon_size // 2, icon_size // 2)
                radius = icon_size // 2
                start_angle = -90
                end_angle = start_angle + int(360 * ratio)
                points = [center]
                steps = max(6, int(60 * ratio))
                for i in range(steps+1):
                    angle = math.radians(start_angle + (end_angle - start_angle) * i / steps)
                    x = center[0] + radius * math.cos(angle)
                    y = center[1] + radius * math.sin(angle)
                    points.append((x, y))
                pygame.draw.polygon(mask_surf, (0, 0, 0, 120), points)
                screen.blit(mask_surf, (x_bs, y_pos))
            font = pygame.font.Font(None, 28)
            l_text = font.render("L", True, (180, 255, 80))
            l_rect = l_text.get_rect(bottomright=(x_bs + icon_size - 4, y_pos + icon_size - 2))
            l_bg = pygame.Surface((l_rect.width+6, l_rect.height+2), pygame.SRCALPHA)
            l_bg.fill((0,0,0,120))
            screen.blit(l_bg, (l_rect.x-3, l_rect.y-1))
            screen.blit(l_text, l_rect)

        # J键（攻击）
        if attack_icon:
            x_j = WINDOW_WIDTH - icon_size*2 - gap - 20
            if base_icon:
                scaled_base = pygame.transform.smoothscale(base_icon, (base_size, base_size))
                screen.blit(scaled_base, (x_j - base_offset, y_pos - base_offset))
            scaled_icon = pygame.transform.smoothscale(attack_icon, (icon_size, icon_size))
            screen.blit(scaled_icon, (x_j, y_pos))
            remain, total = player.get_attack_cooldown_info()
            if remain > 0 and total > 0:
                ratio = remain / total
                mask_surf = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                center = (icon_size // 2, icon_size // 2)
                radius = icon_size // 2
                start_angle = -90
                end_angle = start_angle + int(360 * ratio)
                points = [center]
                steps = max(6, int(60 * ratio))
                for i in range(steps+1):
                    angle = math.radians(start_angle + (end_angle - start_angle) * i / steps)
                    x = center[0] + radius * math.cos(angle)
                    y = center[1] + radius * math.sin(angle)
                    points.append((x, y))
                pygame.draw.polygon(mask_surf, (0, 0, 0, 120), points)
                screen.blit(mask_surf, (x_j, y_pos))
            font = pygame.font.Font(None, 28)
            j_text = font.render("J", True, (255, 180, 80))
            j_rect = j_text.get_rect(bottomright=(x_j + icon_size - 4, y_pos + icon_size - 2))
            j_bg = pygame.Surface((j_rect.width+6, j_rect.height+2), pygame.SRCALPHA)
            j_bg.fill((0,0,0,120))
            screen.blit(j_bg, (j_rect.x-3, j_rect.y-1))
            screen.blit(j_text, j_rect)

        # K键（冲刺）
        if dash_icon:
            x_k = WINDOW_WIDTH - icon_size - 20
            if base_icon:
                scaled_base = pygame.transform.smoothscale(base_icon, (base_size, base_size))
                screen.blit(scaled_base, (x_k - base_offset, y_pos - base_offset))
            scaled_icon = pygame.transform.smoothscale(dash_icon, (icon_size, icon_size))
            screen.blit(scaled_icon, (x_k, y_pos))
            remain, total = player.get_dash_cooldown_info()
            if remain > 0 and total > 0:
                ratio = remain / total
                mask_surf = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                center = (icon_size // 2, icon_size // 2)
                radius = icon_size // 2
                start_angle = -90
                end_angle = start_angle + int(360 * ratio)
                points = [center]
                steps = max(6, int(60 * ratio))
                for i in range(steps+1):
                    angle = math.radians(start_angle + (end_angle - start_angle) * i / steps)
                    x = center[0] + radius * math.cos(angle)
                    y = center[1] + radius * math.sin(angle)
                    points.append((x, y))
                pygame.draw.polygon(mask_surf, (0, 0, 0, 120), points)
                screen.blit(mask_surf, (x_k, y_pos))
            font = pygame.font.Font(None, 28)
            k_text = font.render("K", True, (80, 180, 255))
            k_rect = k_text.get_rect(bottomright=(x_k + icon_size - 4, y_pos + icon_size - 2))
            k_bg = pygame.Surface((k_rect.width+6, k_rect.height+2), pygame.SRCALPHA)
            k_bg.fill((0,0,0,120))
            screen.blit(k_bg, (k_rect.x-3, k_rect.y-1))
            screen.blit(k_text, k_rect)

        # 死亡动画播放完后，渐变放大显示gg图片
        if player.is_dead and gg_img:
            if hasattr(player, 'death_anim_finished') and player.death_anim_finished:
                gg_show_timer += delta_time
                # 渐变参数
                duration = 3 # 渐变持续时间（秒）
                progress = min(gg_show_timer / duration, 1.0)
                scale = 0.3 + 0.7 * progress  # 从0.3倍放大到1倍
                alpha = int(255 * progress)   # 从0到255
                # 缩放图片，最大不超过半屏
                w, h = gg_img.get_size()
                max_w = WINDOW_WIDTH // 1.5
                max_h = WINDOW_HEIGHT // 1
                new_w = min(int(w * scale), max_w)
                new_h = min(int(h * scale), max_h)
                gg_scaled = pygame.transform.smoothscale(gg_img, (new_w, new_h))
                gg_scaled.set_alpha(alpha)
                rect = gg_scaled.get_rect(center=(WINDOW_WIDTH//2, WINDOW_HEIGHT//2))
                screen.blit(gg_scaled, rect)
            else:
                gg_show_timer = 0  # 死亡动画未播完，计时器归零

        # 自动保存逻辑
        if game_state_manager.update_auto_save():
            if map_manager.save_collision_map():
                game_state_manager.reset_auto_save()
                print("已自动保存碰撞地图")

        # 变身技能（I键），仅在变身状态下显示，且在所有技能按钮之后绘制
        if hasattr(player, 'transformed') and player.transformed and skill_icon:
            x_skill = WINDOW_WIDTH - icon_size*3 - gap*2 - 20
            y_skill = y_pos - icon_size - gap
            if base_icon:
                scaled_base = pygame.transform.smoothscale(base_icon, (base_size, base_size))
                screen.blit(scaled_base, (x_skill - base_offset, y_skill - base_offset))
            scaled_icon = pygame.transform.smoothscale(skill_icon, (icon_size, icon_size))
            screen.blit(scaled_icon, (x_skill, y_skill))
            # 冷却扇形遮罩
            remain, total = player.get_skill_cooldown_info()
            if remain > 0 and total > 0:
                ratio = remain / total
                mask_surf = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
                center = (icon_size // 2, icon_size // 2)
                radius = icon_size // 2
                start_angle = -90
                end_angle = start_angle + int(360 * ratio)
                points = [center]
                steps = max(6, int(60 * ratio))
                for i in range(steps+1):
                    angle = math.radians(start_angle + (end_angle - start_angle) * i / steps)
                    x = center[0] + radius * math.cos(angle)
                    y = center[1] + radius * math.sin(angle)
                    points.append((x, y))
                pygame.draw.polygon(mask_surf, (0, 0, 0, 120), points)
                screen.blit(mask_surf, (x_skill, y_skill))
            font = pygame.font.Font(None, 28)
            i_text = font.render("I", True, (255, 255, 120))
            i_rect = i_text.get_rect(bottomright=(x_skill + icon_size - 4, y_skill + icon_size - 2))
            i_bg = pygame.Surface((i_rect.width+6, i_rect.height+2), pygame.SRCALPHA)
            i_bg.fill((0,0,0,120))
            screen.blit(i_bg, (i_rect.x-3, i_rect.y-1))
            screen.blit(i_text, i_rect)
    else:
        # 暂停状态显示
        screen.fill((20, 20, 20))
        ui_manager.draw_pause_screen(screen)

    pygame.display.flip()
    clock.tick(60)

if game_state_manager.collision_modified:
    map_manager.save_collision_map()

pygame.quit()
sys.exit()
