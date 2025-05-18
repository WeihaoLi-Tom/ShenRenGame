import pygame
import os
import time
from enemy import Enemy

class SkeletonEnemy(Enemy):
    def __init__(self, pos, size=(48, 48)):
        super().__init__(pos, size)
        # 基础属性调整
        self.max_health = 40
        self.current_health = 40
        self.move_speed = 0.6
        self.attack_range = 32  # 攻击范围再缩小
        self.attack_damage = 15
        self.attack_cooldown = 1.2
        self.vision_range = 150
        
        # 攻击判定相关
        self.attack_rect = pygame.Rect(0, 0, 0, 0)  # 攻击判定区域
        self.attack_offset = 0
        
        # 死亡动画最后一帧停留计时
        self.death_last_frame_hold = 0.5  # 最后一帧停留0.5秒
        self.death_last_frame_timer = 0
        
        # 动画相关
        print("开始加载骷髅动画帧...")
        self.frames = self._load_all_frames()
        print("骷髅动画帧加载完成")
        
        self.frame_idx = 0
        self.frame_timer = 0
        self.frame_interval = 0.18  # 动画播放速度减慢
        self.action = "idle"
        self.direction = "down"
        self.facing_left = False
        
        # 攻击动画相关
        self.attacking = False
        self.attack_anim_timer = 0
        self.attack_anim_duration = 0.4
        
        # 受伤动画相关
        self.hurt_anim_timer = 0
        self.hurt_anim_duration = 0.3
        self.is_hurt = False
        
        # 死亡动画相关
        self.death_anim_timer = 0
        self.death_anim_duration = 0.6
        self.is_dying = False
        
        # 设置初始图像
        if "idle" in self.frames and "down" in self.frames["idle"] and self.frames["idle"]["down"]:
            self.image = self.frames["idle"]["down"][0]
            self.rect = self.image.get_rect()
            self.rect.topleft = pos
        else:
            # 如果加载失败，使用一个默认的红色方块
            self.image = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.rect(self.image, (255, 0, 0), self.image.get_rect())
            self.rect = self.image.get_rect()
            self.rect.topleft = pos
            print("警告：无法加载骷髅动画帧，使用默认图像")

    def _load_frames(self, action):
        frames = {}
        base_dir = "assets/characters/skeleton_frames"
        if action == "death":
            # 死亡动画不分方向
            frames["none"] = []
            idx = 1
            while True:
                fname = f"death_{idx:02d}.png"
                fpath = os.path.join(base_dir, fname)
                if not os.path.exists(fpath):
                    break
                try:
                    frame = pygame.image.load(fpath).convert_alpha()
                    frames["none"].append(frame)
                except Exception as e:
                    print(f"加载帧失败 {fpath}: {e}")
                    break
                idx += 1
        else:
            directions = ["down", "right", "up", "left"]
            for direction in directions:
                frames[direction] = []
                idx = 1
                while True:
                    fname = f"{action}_{direction}_{idx:02d}.png"
                    fpath = os.path.join(base_dir, fname)
                    if not os.path.exists(fpath):
                        break
                    try:
                        frame = pygame.image.load(fpath).convert_alpha()
                        frames[direction].append(frame)
                    except Exception as e:
                        print(f"加载帧失败 {fpath}: {e}")
                        break
                    idx += 1
                if direction == "left" and not frames["left"] and frames["right"]:
                    frames["left"] = [pygame.transform.flip(frame, True, False) for frame in frames["right"]]
        return frames

    def _load_all_frames(self):
        """加载所有动作的动画帧"""
        frames = {}
        actions = ["idle", "move", "attack", "hurt", "death"]
        
        for action in actions:
            frames[action] = self._load_frames(action)
            # 打印加载的帧数，用于调试
            for direction in ["down", "right", "up", "left"]:
                if direction in frames[action]:
                    print(f"加载 {action}_{direction}: {len(frames[action][direction])} 帧")
            
        return frames

    def update(self, player, is_valid_position):
        if not self.alive:
            return
            
        # 更新动画计时器
        self.frame_timer += 0.016  # 假设60FPS
        
        # 如果正在死亡，只更新死亡动画
        if self.is_dying:
            self._update_death_animation()
            return
            
        # 如果正在受伤，只更新受伤动画
        if self.is_hurt:
            self._update_hurt_animation()
            return
            
        # 如果正在攻击，只更新攻击动画
        if self.attacking:
            self._update_attack_animation()
            return
            
        # 计算与玩家的距离和方向
        px, py = player.rect.center
        ex, ey = self.rect.center
        dx = px - ex
        dy = py - ey
        dist = (dx ** 2 + dy ** 2) ** 0.5
        
        # 更新朝向
        self._update_direction(dx, dy)
        
        # 状态切换
        if dist <= self.vision_range:
            self.state = 'chase'
            self.action = "move"
        else:
            self.state = 'patrol'
            self.action = "idle"
        
        # 行为
        if self.state == 'chase':
            if dist > self.attack_range:
                self.chase_player(dx, dy, dist, is_valid_position)
            else:
                self.try_attack(player)
        else:
            self.patrol(is_valid_position)
        
        # 更新动画帧
        if self.frame_timer >= self.frame_interval:
            self.frame_timer = 0
            self._update_animation_frame()
        
        # 更新图像
        self._update_image()
        
        # 更新位置
        self.rect.x = int(self.float_x)
        self.rect.y = int(self.float_y)

    def _update_direction(self, dx, dy):
        """根据移动方向更新朝向"""
        if abs(dx) > abs(dy):
            self.direction = "right" if dx > 0 else "left"
            self.facing_left = dx < 0
        else:
            self.direction = "down" if dy > 0 else "up"

    def _update_animation_frame(self):
        """更新动画帧索引"""
        if self.action == "death":
            frames = self.frames["death"]["none"]
        else:
            frames = self.frames[self.action][self.direction]
        if not frames:
            return
        # 攻击动作单独减慢动画速度
        if self.action == "attack":
            interval = 0.28
        else:
            interval = self.frame_interval
        self.frame_timer += 0.016
        if self.frame_timer >= interval:
            self.frame_timer = 0
            self.frame_idx = (self.frame_idx + 1) % len(frames)

    def _update_image(self):
        """更新当前显示的图像"""
        if self.action == "death":
            frames = self.frames["death"]["none"]
        else:
            frames = self.frames[self.action][self.direction]
        if not frames:
            return
        self.image = frames[self.frame_idx]
        if self.facing_left and self.direction == "right" and self.action != "death":
            self.image = pygame.transform.flip(self.image, True, False)

    def _update_attack_animation(self):
        frames = self.frames["attack"][self.direction]
        if not frames:
            self.attacking = False
            self.attack_anim_timer = 0
            self.action = "idle"
            return

        interval = 0.28
        is_last_frame = self.frame_idx == len(frames) - 1

        # 帧切换
        self.frame_timer += 0.016
        if self.frame_timer >= interval and not is_last_frame:
            self.frame_timer = 0
            self.frame_idx += 1
            if self.frame_idx >= len(frames):
                self.frame_idx = len(frames) - 1

        # 最后一帧停留
        if is_last_frame:
            self.attack_anim_timer += 0.016
            if not hasattr(self, '_attack_damage_applied'):
                self._attack_damage_applied = True
                if self.attack_rect.colliderect(self.target_player.rect):
                    self.target_player.take_damage(self.attack_damage)
            if self.attack_anim_timer >= 0.3:  # 最后一帧多停留0.3秒
                self.attacking = False
                self.attack_anim_timer = 0
                self.frame_idx = 0
                self.action = "idle"
                if hasattr(self, '_attack_damage_applied'):
                    del self._attack_damage_applied
        else:
            self._update_image()

    def _update_hurt_animation(self):
        """更新受伤动画"""
        self.hurt_anim_timer += 0.016
        if self.hurt_anim_timer >= self.hurt_anim_duration:
            self.is_hurt = False
            self.hurt_anim_timer = 0
            self.action = "idle"
        else:
            self._update_animation_frame()
            self._update_image()

    def _update_death_animation(self):
        """更新死亡动画"""
        frames = self.frames["death"]["none"]
        self.death_anim_timer += 0.016
        if not frames:
            self.alive = False
            return
        if self.frame_idx < len(frames) - 1:
            self._update_animation_frame()
            self._update_image()
        else:
            # 最后一帧停留
            self.death_last_frame_timer += 0.016
            if self.death_last_frame_timer >= self.death_last_frame_hold or self.death_anim_timer >= self.death_anim_duration:
                self.alive = False
            else:
                self._update_image()

    def generate_attack_rect(self):
        """生成攻击判定区域"""
        attack_rect = pygame.Rect(0, 0, 24, 24)  # 攻击判定区域更小
        # 让判定矩形更靠近骷髅本体
        offset = 4
        if self.direction == "right":
            attack_rect.midleft = self.rect.midright
            attack_rect.x -= offset
        elif self.direction == "left":
            attack_rect.midright = self.rect.midleft
            attack_rect.x += offset
        elif self.direction == "down":
            attack_rect.midtop = self.rect.midbottom
            attack_rect.y -= offset
        else:  # up
            attack_rect.midbottom = self.rect.midtop
            attack_rect.y += offset
        return attack_rect

    def try_attack(self, player):
        """尝试攻击玩家"""
        if not self.attacking and time.time() - self.last_attack_time >= self.attack_cooldown:
            # 生成攻击判定区域
            self.attack_rect = self.generate_attack_rect()
            self.attacking = True
            self.action = "attack"
            self.frame_idx = 0
            self.attack_anim_timer = 0
            self.last_attack_time = time.time()
            self.target_player = player  # 记录本次攻击的目标
        return False

    def take_damage(self, damage):
        """受到伤害"""
        if self.alive:
            self.current_health -= damage
            self.is_hurt = True
            self.action = "hurt"
            self.frame_idx = 0
            self.hurt_anim_timer = 0
            if self.current_health <= 0:
                self.current_health = 0
                self.is_dying = True
                self.action = "death"
                self.frame_idx = 0
                self.death_anim_timer = 0
                return True
            return True
        return False

    def draw(self, surface, camera_x, camera_y, show_debug_hitbox=False):
        """绘制骷髅"""
        if not self.alive:
            return
        x = self.rect.x - camera_x
        y = self.rect.y - camera_y
        visible = True
        if visible:
            surface.blit(self.image, (x, y))
        # 血条宽度24，居中
        bar_width = 24
        bar_x = x + (self.rect.width - bar_width) // 2
        self.draw_health_bar(surface, bar_x, y - 10, bar_width, 6)
        if show_debug_hitbox:
            debug_rect = pygame.Surface((self.rect.width - 12, self.rect.height - 12), pygame.SRCALPHA)
            pygame.draw.rect(debug_rect, (255, 0, 0, 128), debug_rect.get_rect())
            surface.blit(debug_rect, (x + 6, y + 6))
            if self.attacking:
                attack_rect = self.attack_rect.move(-camera_x, -camera_y)
                pygame.draw.rect(surface, (255, 0, 0, 128), attack_rect, 2)

    def chase_player(self, dx, dy, dist, is_valid_position):
        """追踪玩家的移动逻辑（只能上下左右单轴移动，有碰撞检测）"""
        if dist == 0:
            return
        # 优先移动距离更远的轴
        if abs(dx) > abs(dy):
            move_x = self.move_speed * (1 if dx > 0 else -1)
            next_x = self.float_x + move_x
            if is_valid_position(int(next_x + self.rect.width//2), int(self.float_y + self.rect.height//2)):
                self.float_x = next_x
        else:
            move_y = self.move_speed * (1 if dy > 0 else -1)
            next_y = self.float_y + move_y
            if is_valid_position(int(self.float_x + self.rect.width//2), int(next_y + self.rect.height//2)):
                self.float_y = next_y

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