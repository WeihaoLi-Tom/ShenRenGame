import random
from enemy import Enemy, BossEnemy
import pygame
from weapon_drop import WeaponDrop

class EnemyManager:
    def __init__(self, map_manager, player):
        self.map_manager = map_manager
        self.player = player
        self.enemies = []
        self.boss = None
        self.spawn_timer = 0
        self.spawn_interval = 7.0  # 每10秒生成一个新敌人
        self.max_enemies = 5  # 场上最多同时存在5个敌人
        self.killed_count = 0
        self.boss_spawn_threshold = 2  # 杀死5个小敌人后生成Boss
        self.boss_spawned = False
        self.on_boss_spawn = None  # Boss出现回调
        self.weapon_drop = None  # 添加武器掉落物属性
        
        # 初始生成2只幽灵
        self.spawn_initial_enemies()
    
    def spawn_initial_enemies(self):
        for _ in range(2):
            self.spawn_enemy()
    
    def spawn_enemy(self):
        """生成一个新的普通敌人"""
        # 如果Boss存在，不生成新敌人
        if self.boss and self.boss.alive:
            return
            
        if len(self.enemies) < self.max_enemies:
            pos = self.find_safe_enemy_spawn(100)
            if pos is not None:
                self.enemies.append(Enemy(pos))
                print(f"生成了一个新的幽灵敌人，当前敌人数: {len(self.enemies)}")
            else:
                print("未找到安全的敌人出生点，本次不生成敌人。")
    
    def spawn_boss(self):
        """生成Boss"""
        if not self.boss_spawned:
            pos = self.find_safe_enemy_spawn(200)
            if pos is not None:
                self.boss = BossEnemy(pos, size=(32, 32))
                self.boss.set_map_manager(self.map_manager)
                self.boss_spawned = True
                # 播放BGM
                try:
                    pygame.mixer.music.load("assets/bgm/mdam.mp3")
                    pygame.mixer.music.play(-1)
                    print("Boss BGM已播放: assets/bgm/mdam.mp3")
                except Exception as e:
                    print(f"播放Boss BGM失败: {e}")
                print("警告! Boss 猫碟已出现!")
                if self.on_boss_spawn:
                    self.on_boss_spawn()
            else:
                print("未找到安全的Boss出生点，Boss未生成。")
    
    def find_safe_enemy_spawn(self, min_distance_from_player=64):
        """查找安全的敌人出生点"""
        # 收集所有可行走区域
        valid_positions = []
        px, py = self.player.position
        for y in range(1, self.map_manager.height - 1):
            for x in range(1, self.map_manager.width - 1):
                if not self.map_manager.collision_map[y][x]:
                    pos_x = x * self.map_manager.tile_width
                    pos_y = y * self.map_manager.tile_height
                    # 确保离玩家有一定距离
                    if ((pos_x - px) ** 2 + (pos_y - py) ** 2) ** 0.5 > min_distance_from_player:
                        valid_positions.append((pos_x, pos_y))
        
        # 随机选择一个位置
        if valid_positions:
            return random.choice(valid_positions)
        # 如果找不到，返回None
        return None
    
    def update(self, is_valid_position, delta_time):
        # 更新敌人生成计时器（只有在Boss不存在时才生成新敌人）
        if not (self.boss and self.boss.alive):
            self.spawn_timer += delta_time
            if self.spawn_timer >= self.spawn_interval:
                self.spawn_timer = 0
                self.spawn_enemy()
        
        # 更新所有敌人
        for enemy in self.enemies[:]:  # 使用副本遍历，以便安全删除
            enemy.update(self.player, is_valid_position)
            enemy.try_attack(self.player)
            
            # 检查是否已死亡并需要清除
            if not enemy.alive:
                self.enemies.remove(enemy)
                self.killed_count += 1
                print(f"击败了一个敌人！已击败: {self.killed_count}/{self.boss_spawn_threshold}")
                
                # 检查是否达到生成Boss的条件
                if self.killed_count >= self.boss_spawn_threshold and not self.boss_spawned:
                    self.spawn_boss()
        
        # 更新Boss (如果存在)
        if self.boss and self.boss.alive:
            self.boss.update(self.player, is_valid_position)
            self.boss.try_attack(self.player)
    
    def check_attacks(self, attack_rect):
        """检查玩家攻击是否命中敌人或Boss"""
        hit = False
        # 检查是否命中普通敌人
        for enemy in self.enemies:
            if enemy.alive and attack_rect.colliderect(enemy.rect):
                enemy.take_damage(self.player.attack_damage)
                hit = True
                if hasattr(self.player, 'play_hit_sound'):
                    self.player.play_hit_sound()
                if not enemy.alive and hasattr(self, 'on_enemy_dead'):
                    self.on_enemy_dead(enemy.rect.center)
        # 检查是否命中Boss
        if self.boss and self.boss.alive and attack_rect.colliderect(self.boss.rect):
            self.boss.take_damage(self.player.attack_damage)
            hit = True
            if hasattr(self.player, 'play_hit_sound'):
                self.player.play_hit_sound()
            if not self.boss.alive:
                if hasattr(self, 'on_boss_dead') and self.on_boss_dead:
                    exact_pos = self.boss.death_position or self.boss.rect.center
                    self.on_boss_dead(exact_pos)
                    try:
                        self.weapon_drop = WeaponDrop(exact_pos, "assets/weapon/maoluan.png")
                    except Exception as e:
                        pass
                    try:
                        pygame.mixer.music.fadeout(2000)
                    except Exception as e:
                        pass
                    self.on_boss_dead = None
                    return hit
        if not hit and hasattr(self.player, 'attack_none_sound') and self.player.attack_none_sound:
            self.player.attack_none_sound.play()
        return hit
    
    def draw(self, surface, camera_x, camera_y, font=None, show_debug_hitbox=False):
        # 绘制所有敌人
        for enemy in self.enemies:
            enemy.draw(surface, camera_x, camera_y, show_debug_hitbox)
        
        # 绘制Boss (如果存在)
        if self.boss and self.boss.alive:
            self.boss.draw(surface, camera_x, camera_y, font, show_debug_hitbox) 