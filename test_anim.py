import pygame
import os
import sys

# 初始化Pygame
pygame.init()

# 设置窗口
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption("角色动画测试")

# 加载动画帧
def load_animation_frames(folder_path):
    frames = []
    scale_factor = 2.0  # 放大2倍
    try:
        if not os.path.exists(folder_path):
            return frames
        files = sorted(os.listdir(folder_path))
        if not files:
            return frames
        for filename in files:
            if filename.endswith('.png'):
                image_path = os.path.join(folder_path, filename)
                try:
                    frame = pygame.image.load(image_path).convert_alpha()
                    original_size = frame.get_size()
                    new_size = (int(original_size[0] * scale_factor), int(original_size[1] * scale_factor))
                    frame = pygame.transform.scale(frame, new_size)
                    frames.append(frame)
                except Exception as e:
                    pass
    except Exception as e:
        pass
    return frames

# 加载动画
print("开始加载动画帧...")
idel_frames = load_animation_frames('assets/characters/test_frames/idel')
move_frames = load_animation_frames('assets/characters/test_frames/move')
attack_frames = load_animation_frames('assets/characters/test_frames/attack')
hurt_frames = load_animation_frames('assets/characters/test_frames/hurt')
death_frames = load_animation_frames('assets/characters/test_frames/die')
dash_frames = load_animation_frames('assets/characters/test_frames/dash')
skill_frames = load_animation_frames('assets/characters/test_frames/skill')  # 新增skill动画

# 检查是否成功加载了动画帧
if not idel_frames or not move_frames or not attack_frames or not hurt_frames or not death_frames or not dash_frames or not skill_frames:
    print("错误：某些动画帧未能成功加载，请检查文件路径和文件是否存在")
    pygame.quit()
    sys.exit(1)

print("动画帧加载完成")

# 动画状态
class AnimationState:
    IDLE = 0
    MOVING = 1
    ATTACK = 2
    HURT = 3
    DEATH = 4
    DASH = 5
    SKILL = 6  # 新增技能状态

# 角色类
class Character:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 5
        self.dash_speed = 12  # dash时的速度
        self.state = AnimationState.IDLE
        self.current_frame = 0
        self.animation_timer = 0
        self.animation_delay = 100  # 普通动画的延迟
        self.attack_animation_delay = 50  # 攻击动画的延迟（更快）
        self.dash_animation_delay = 50  # dash动画的延迟
        self.facing_right = True
        self.facing_dir = 'right'  # 新增，记录面朝方向
        self.idel_frames = idel_frames
        self.move_frames = move_frames
        self.attack_frames = attack_frames
        self.hurt_frames = hurt_frames
        self.death_frames = death_frames
        self.dash_frames = dash_frames
        self.skill_frames = skill_frames
        self.skill_animation_delay = 80  # 技能动画帧间隔
        self.is_attacking = False
        self.attack_cooldown = 0
        self.is_hurt = False
        self.is_dead = False
        self.is_dashing = False
        self.dash_duration = 300  # dash持续时间（毫秒）
        self.dash_timer = 0
        self.dash_cooldown = 800  # dash冷却时间（毫秒）
        self.dash_cooldown_timer = 0
        self.health = 100
        self.death_animation_complete = False
        self.death_animation_delay = 300
        self.dash_dir = None  # dash时的方向
        self.is_using_skill = False

    def take_damage(self, damage):
        if not self.is_dead:
            self.health -= damage
            if self.health <= 0:
                self.is_dead = True
                self.state = AnimationState.DEATH
                self.current_frame = 0
            else:
                self.is_hurt = True
                self.state = AnimationState.HURT
                self.current_frame = 0

    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_p] and not self.is_dead:
            self.take_damage(100)

        if self.is_dead:
            if not self.death_animation_complete and len(self.death_frames) > 0:
                self.animation_timer += dt
                if self.animation_timer >= self.death_animation_delay:
                    self.animation_timer = 0
                    if self.current_frame < len(self.death_frames) - 1:
                        self.current_frame += 1
                    else:
                        self.death_animation_complete = True
            if keys[pygame.K_r]:
                self.is_dead = False
                self.death_animation_complete = False
                self.current_frame = 0
                self.health = 100
                self.state = AnimationState.IDLE
            return

        if self.dash_cooldown_timer > 0:
            self.dash_cooldown_timer -= dt
        if self.is_dashing:
            self.dash_timer += dt
            if self.dash_timer >= self.dash_duration:
                self.is_dashing = False
                self.dash_cooldown_timer = self.dash_cooldown
                self.state = AnimationState.IDLE
                self.current_frame = 0

        # 技能释放逻辑（I键）
        if keys[pygame.K_i] and not self.is_using_skill and not self.is_attacking and not self.is_hurt and not self.is_dashing:
            self.is_using_skill = True
            self.state = AnimationState.SKILL
            self.current_frame = 0

        dx = dy = 0
        # dash控制（K键）
        if keys[pygame.K_k] and not self.is_dashing and self.dash_cooldown_timer <= 0 and not self.is_attacking and not self.is_hurt and not self.is_using_skill:
            self.is_dashing = True
            self.dash_timer = 0
            self.state = AnimationState.DASH
            self.current_frame = 0
            self.dash_dir = self.facing_dir
        if self.is_dashing:
            if self.dash_dir == 'left':
                dx = -self.dash_speed
                self.facing_right = False
            elif self.dash_dir == 'right':
                dx = self.dash_speed
                self.facing_right = True
            elif self.dash_dir == 'up':
                dy = -self.dash_speed
            elif self.dash_dir == 'down':
                dy = self.dash_speed
            self.x += dx
            self.y += dy
        elif self.is_using_skill:
            pass
        else:
            if keys[pygame.K_h] and not self.is_hurt and not self.is_dead:
                self.take_damage(20)
            if self.attack_cooldown > 0:
                self.attack_cooldown -= dt
            # 攻击控制（J键）
            if keys[pygame.K_j] and self.attack_cooldown <= 0 and not self.is_attacking and not self.is_hurt:
                self.is_attacking = True
                self.state = AnimationState.ATTACK
                self.current_frame = 0
                self.attack_cooldown = 100
            if not self.is_attacking and not self.is_hurt:
                if keys[pygame.K_a]:
                    dx = -self.speed
                    self.facing_right = False
                    self.facing_dir = 'left'
                if keys[pygame.K_d]:
                    dx = self.speed
                    self.facing_right = True
                    self.facing_dir = 'right'
                if keys[pygame.K_w]:
                    dy = -self.speed
                    self.facing_dir = 'up'
                if keys[pygame.K_s]:
                    dy = self.speed
                    self.facing_dir = 'down'
                self.x += dx
                self.y += dy
                if dx != 0 or dy != 0:
                    self.state = AnimationState.MOVING
                else:
                    self.state = AnimationState.IDLE

        # 更新动画帧
        if self.is_dashing:
            self.animation_timer += dt
            if self.animation_timer >= self.dash_animation_delay:
                self.animation_timer = 0
                self.current_frame = (self.current_frame + 1) % len(self.dash_frames)
        elif self.is_using_skill:
            self.animation_timer += dt
            if self.animation_timer >= self.skill_animation_delay:
                self.animation_timer = 0
                self.current_frame += 1
                if self.current_frame >= len(self.skill_frames):
                    self.current_frame = 0
                    self.is_using_skill = False
                    self.state = AnimationState.IDLE
        else:
            self.animation_timer += dt
            current_delay = self.attack_animation_delay if self.state == AnimationState.ATTACK else self.animation_delay
            if self.animation_timer >= current_delay:
                self.animation_timer = 0
                if self.state == AnimationState.IDLE:
                    self.current_frame = (self.current_frame + 1) % len(self.idel_frames)
                elif self.state == AnimationState.MOVING:
                    self.current_frame = (self.current_frame + 1) % len(self.move_frames)
                elif self.state == AnimationState.ATTACK:
                    self.current_frame += 1
                    if self.current_frame >= len(self.attack_frames):
                        self.current_frame = 0
                        self.is_attacking = False
                        self.state = AnimationState.IDLE
                elif self.state == AnimationState.HURT:
                    self.current_frame += 1
                    if self.current_frame >= len(self.hurt_frames):
                        self.current_frame = 0
                        self.is_hurt = False
                        self.state = AnimationState.IDLE

    def draw(self, screen):
        try:
            if self.state == AnimationState.IDLE:
                current_image = self.idel_frames[self.current_frame]
            elif self.state == AnimationState.MOVING:
                current_image = self.move_frames[self.current_frame]
            elif self.state == AnimationState.ATTACK:
                current_image = self.attack_frames[self.current_frame]
            elif self.state == AnimationState.HURT:
                current_image = self.hurt_frames[self.current_frame]
            elif self.state == AnimationState.DASH:
                current_image = self.dash_frames[self.current_frame]
            elif self.state == AnimationState.SKILL:
                current_image = self.skill_frames[self.current_frame]
            else:  # DEATH
                current_image = self.death_frames[self.current_frame]
            if not self.facing_right:
                current_image = pygame.transform.flip(current_image, True, False)
            screen.blit(current_image, (self.x, self.y))
            if self.is_dead and self.death_animation_complete:
                font = pygame.font.SysFont(None, 48)
                text = font.render("按R复活", True, (255, 0, 0))
                screen.blit(text, (300, 50))
        except IndexError:
            self.current_frame = 0

# 创建角色实例
character = Character(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2)

# 游戏主循环
clock = pygame.time.Clock()
running = True

while running:
    # 处理事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # 更新
    dt = clock.tick(60)
    character.update(dt)

    # 绘制
    screen.fill((0, 0, 0))  # 黑色背景
    character.draw(screen)
    pygame.display.flip()

pygame.quit()
sys.exit()
