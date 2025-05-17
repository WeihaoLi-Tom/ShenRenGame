import pygame
import sys
import time
from player import Player
from map_manager import MapManager
from enemy_manager import EnemyManager
from effects import EffectManager
from weapon_drop import WeaponDrop
from game_state import GameState, GameStateManager
from ui_manager import UIManager

# 初始化
pygame.init()
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 600
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("Tom's Dungeon")
clock = pygame.time.Clock()

# 初始化各个管理器
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

# 初始化玩家
try:
    spawn_pos = map_manager.find_safe_spawn()
    player = Player(spawn_pos, (map_manager.tile_width, map_manager.tile_height))
except Exception as e:
    print(f"初始化玩家时出错: {e}")
    sys.exit(1)

# 初始化其他管理器
enemy_manager = EnemyManager(map_manager, player)
effect_manager = EffectManager()
game_state_manager = GameStateManager()
ui_manager = UIManager(WINDOW_WIDTH, WINDOW_HEIGHT)

# 全局变量
weapon_drop = None
last_time = time.time()

# Boss出现回调机制
def merged_on_boss_spawn():
    ui_manager.trigger_boss_warning()

# Boss死亡特效触发函数
def on_boss_dead(pos=None):
    global weapon_drop
    if pos:
        bx, by = pos
    elif enemy_manager.boss:
        bx, by = enemy_manager.boss.rect.center
    else:
        print("警告: 无法获取Boss位置，爆炸特效未创建")
        return

    print(f"触发Boss死亡特效，位置：({bx}, {by})")
    effect_manager.create_explosion((bx, by))
    weapon_drop = WeaponDrop((bx, by))
    print("Boss掉落了一把武器: swd2.png")

# 小怪死亡特效触发函数
def on_enemy_dead(pos):
    effect_manager.create_small_explosion(pos)

# 注册回调
enemy_manager.on_boss_spawn = merged_on_boss_spawn
enemy_manager.on_boss_dead = on_boss_dead
enemy_manager.on_enemy_dead = on_enemy_dead

running = True
while running:
    # 计算delta time
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time
    
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
                    if weapon_drop and weapon_drop.rect.collidepoint(player.rect.center):
                        player.equip_new_sword("assets/weapon/swd2.png")
                        print("玩家拾取了新武器!")
                        weapon_drop = None
                elif event.key == pygame.K_TAB:
                    game_state_manager.toggle_debug_display()
                elif event.key == pygame.K_c:
                    game_state_manager.toggle_collision_display()
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

    if game_state_manager.current_state == GameState.RUNNING:
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
        enemy_manager.draw(visible_area, camera_x, camera_y)
        
        # 绘制武器掉落物
        if weapon_drop:
            weapon_drop.update()
            weapon_drop.draw(visible_area, camera_x, camera_y)
            weapon_drop.draw_pickup_prompt(visible_area, camera_x, camera_y, player.rect.center)
        
        # 绘制玩家
        player.draw(visible_area, camera_x, camera_y)
        
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

        # 自动保存逻辑
        if game_state_manager.update_auto_save():
            if map_manager.save_collision_map():
                game_state_manager.reset_auto_save()
                print("已自动保存碰撞地图")
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
