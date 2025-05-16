import pygame
import os
from pathlib import Path

class Assets:
    def __init__(self):
        self.images = {}
        self.load_assets()

    def load_assets(self):
        assets_dir = Path('assets')
        if not assets_dir.exists():
            print("未找到资源目录，请先运行 download_assets.py 下载素材")
            return

        # 调试：打印 player_idle.png 路径和存在性
        player_path = assets_dir / 'characters' / 'player_idle.png'
        print(f"[调试] player_idle.png 路径: {player_path.resolve()} 存在: {player_path.exists()}")

        # 加载玩家和敌人静态图片
        self.load_image('characters/player.png', 'player_idle')
        self.load_image('characters/enemy_idle.png', 'enemy_idle')

        # 加载背景元素
        self.load_image('backgrounds/ground.png', 'ground')
        self.load_image('backgrounds/background.png', 'background')
        # 云朵占位图
        self.images['cloud'] = self.create_placeholder_sprite((60, 30), (255, 255, 255))

        # 加载特效
        self.load_image('effects/attack_effect.png', 'attack_effect')
        self.load_image('effects/hit_effect.png', 'hit_effect')

    def load_image(self, path, name):
        try:
            full_path = Path('assets') / path
            if full_path.exists():
                self.images[name] = pygame.image.load(str(full_path)).convert_alpha()
            else:
                print(f"警告: 未找到图片 {path}")
                self.images[name] = self.create_placeholder_sprite((32, 32), (255, 0, 255))
        except Exception as e:
            print(f"加载图片 {path} 时出错: {str(e)}")
            self.images[name] = self.create_placeholder_sprite((32, 32), (255, 0, 255))

    def create_placeholder_sprite(self, size, color):
        surface = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surface, color, (0, 0, size[0], size[1]), border_radius=5)
        return surface

    def get_image(self, name):
        img = self.images.get(name)
        if img is None:
            return self.create_placeholder_sprite((32, 32), (0, 255, 255))
        return img 