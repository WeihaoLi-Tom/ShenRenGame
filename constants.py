import pygame

# 窗口设置
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
SKY_BLUE = (135, 206, 235)
GROUND_COLOR = (34, 139, 34)
PLAYER_COLOR = (70, 130, 180)
ENEMY_COLOR = (220, 20, 60)

# 玩家设置
PLAYER_SPEED = 5
PLAYER_WIDTH = 30
PLAYER_HEIGHT = 50
PLAYER_JUMP_POWER = -15
PLAYER_GRAVITY = 0.8
PLAYER_MAX_HEALTH = 100
PLAYER_INVINCIBLE_TIME = 60

# 敌人设置
ENEMY_WIDTH = 30
ENEMY_HEIGHT = 30
ENEMY_SPEED = 2
ENEMY_HEALTH = 50
ENEMY_MOVE_DELAY = 60
ENEMY_DAMAGE = 10

# 攻击设置
ATTACK_RADIUS = 40
ATTACK_DURATION = 20
ATTACK_DAMAGE = 25
ATTACK_PARTICLE_COUNT = 8
ATTACK_PARTICLE_LIFE = 30 