import pygame
import sys
import os

pygame.init()
screen = pygame.display.set_mode((320, 240))
pygame.display.set_caption("帧动画测试")
clock = pygame.time.Clock()

img_dir = "assets/characters/c_09/img"

def load_frames(prefix):
    return [pygame.image.load(os.path.join(img_dir, f)).convert_alpha()
            for f in sorted(os.listdir(img_dir)) if f.startswith(prefix) and f.endswith(".png")]

# 加载所有动作帧
frames = {
    "idle": load_frames("idle_"),
    "run": load_frames("run_"),
    "jump": load_frames("jump_"),
    "attack": load_frames("attack_n_"),
    "die": load_frames("die_"),
}

action = "idle"
frame_idx = 0
x, y = 120, 80
speed = 4
facing_left = False

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                action = "attack"
                frame_idx = 0
            elif event.key == pygame.K_j:
                action = "jump"
                frame_idx = 0
            elif event.key == pygame.K_d:
                action = "die"
                frame_idx = 0

    keys = pygame.key.get_pressed()
    if action not in ["attack", "jump", "die"]:
        if keys[pygame.K_LEFT]:
            x -= speed
            action = "run"
            facing_left = True
        elif keys[pygame.K_RIGHT]:
            x += speed
            action = "run"
            facing_left = False
        else:
            action = "idle"

    # 帧动画播放
    frame_idx = (frame_idx + 1) % len(frames[action])
    frame = frames[action][frame_idx]
    if facing_left:
        frame = pygame.transform.flip(frame, True, False)

    screen.fill((50, 50, 50))
    screen.blit(frame, (x, y))
    pygame.display.flip()
    clock.tick(10)

    # 动作播放完自动回到idle
    if action in ["attack", "jump", "die"] and frame_idx == len(frames[action]) - 1:
        action = "idle"
        frame_idx = 0