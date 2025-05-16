import pygame
import os
import json
from pathlib import Path
from pytmx.util_pygame import load_pygame

class MapManager:
    def __init__(self, tmx_path, collision_file="collision_map.json", debug=True):
        self.debug = debug
        self.tmx_data = load_pygame(tmx_path)
        self.tile_width = self.tmx_data.tilewidth
        self.tile_height = self.tmx_data.tileheight
        self.width = self.tmx_data.width
        self.height = self.tmx_data.height
        self.map_width = self.width * self.tile_width
        self.map_height = self.height * self.tile_height
        self.collision_file = collision_file
        self.wall_gids = [
            30, 31, 41, 14, 16, 17, 18, 19, 26, 28, 49, 51, 52,
            1, 2, 3, 4, 5, 6, 7, 27,
            1610612787, 1610612789, 3221225485, 2684354573, 2684354610, 2147483698,
        ]
        self.data = list(list(self.tmx_data.visible_layers)[0].data)
        self.collision_map = [[False for _ in range(self.width)] for _ in range(self.height)]
        
        # 打印TMX文件信息
        if self.debug:
            print("TMX文件信息:")
            print(f"图块集数量: {len(self.tmx_data.tilesets)}")
            for i, tileset in enumerate(self.tmx_data.tilesets):
                print(f"图块集 {i+1}:")
                print(f"  名称: {tileset.name}")
                print(f"  首GID: {tileset.firstgid}")
                print(f"  图块数量: {tileset.tilecount}")
                print(f"  图块大小: {tileset.tilewidth}x{tileset.tileheight}")
        
        # 装饰物相关 - 直接加载PNG图片
        self.decoration_images = []
        decoration_paths = [
            "assets/backgrounds/tile_0063.png",
            "assets/backgrounds/tile_0064.png",
            "assets/backgrounds/tile_0065.png",
            "assets/backgrounds/tile_0072.png",
            "assets/backgrounds/tile_0082.png",
        ]
        for path in decoration_paths:
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (self.tile_width, self.tile_height))
                self.decoration_images.append(img)
                if self.debug:
                    print(f"成功加载装饰物图片: {path}")
            except Exception as e:
                print(f"加载装饰物图片失败 {path}: {e}")
        
        self.decoration_map = [[None for _ in range(self.width)] for _ in range(self.height)]
        self._load_or_generate_collision()
        self._generate_decorations()

    def _load_or_generate_collision(self):
        loaded = False
        if os.path.exists(self.collision_file):
            try:
                with open(self.collision_file, 'r') as f:
                    loaded_map = json.load(f)
                    if len(loaded_map) == self.height and len(loaded_map[0]) == self.width:
                        self.collision_map = loaded_map
                        loaded = True
                        if self.debug:
                            print(f"已从{self.collision_file}加载碰撞地图")
            except Exception as e:
                print(f"加载碰撞地图时出错: {e}")
        if not loaded:
            self._generate_collision_map()

    def _generate_collision_map(self):
        wall_count = 0
        collision_layer = None
        for layer in self.tmx_data.visible_layers:
            if hasattr(layer, 'name') and (layer.name.lower() == "collision" or layer.name.lower() == "walls"):
                collision_layer = layer
                if self.debug:
                    print(f"找到专用碰撞层: {layer.name}")
                break
        if collision_layer:
            for y, row in enumerate(collision_layer.data):
                for x, gid in enumerate(row):
                    if gid != 0:
                        self.collision_map[y][x] = True
                        wall_count += 1
        else:
            for y, row in enumerate(self.data):
                for x, gid in enumerate(row):
                    if x == 0 or y == 0 or x == self.width - 1 or y == self.height - 1:
                        self.collision_map[y][x] = True
                        wall_count += 1
                    elif gid != 0:
                        is_wall = False
                        if gid in self.wall_gids:
                            is_wall = True
                        tile_props = self.tmx_data.get_tile_properties_by_gid(gid)
                        if tile_props and ('wall' in tile_props or 'collision' in tile_props):
                            is_wall = True
                        if is_wall:
                            self.collision_map[y][x] = True
                            wall_count += 1
        if self.debug:
            print(f"已创建碰撞地图，识别到 {wall_count} 个障碍物瓦片")

    def save_collision_map(self):
        try:
            with open(self.collision_file, 'w') as f:
                json.dump(self.collision_map, f)
            if self.debug:
                print(f"碰撞地图已保存到 {self.collision_file}")
            return True
        except Exception as e:
            print(f"保存碰撞地图时出错: {e}")
            return False

    def is_valid_position(self, x, y):
        if x < 0 or y < 0 or x >= self.map_width or y >= self.map_height:
            return False
        tile_x = x // self.tile_width
        tile_y = y // self.tile_height
        if tile_x < 0 or tile_y < 0 or tile_x >= self.width or tile_y >= self.height:
            return False
        return not self.collision_map[int(tile_y)][int(tile_x)]

    def find_safe_spawn(self):
        good_spawn_points = [
            (10, 3), (10, 10), (20, 10), (15, 15)
        ]
        for tile_x, tile_y in good_spawn_points:
            if (0 <= tile_x < self.width and 0 <= tile_y < self.height and not self.collision_map[tile_y][tile_x]):
                return tile_x * self.tile_width, tile_y * self.tile_height
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if not self.collision_map[y][x]:
                    return x * self.tile_width, y * self.tile_height
        return self.map_width // 2, self.map_height // 2

    def toggle_collision_at_position(self, x, y):
        tile_x = int(x // self.tile_width)
        tile_y = int(y // self.tile_height)
        if 0 <= tile_x < self.width and 0 <= tile_y < self.height:
            self.collision_map[tile_y][tile_x] = not self.collision_map[tile_y][tile_x]
            print(f"位置 ({tile_x},{tile_y}) 的碰撞状态: {'墙壁' if self.collision_map[tile_y][tile_x] else '可通行'}")
            print("按S键保存当前碰撞地图")

    def _generate_decorations(self):
        """在非碰撞区域随机生成装饰物"""
        import random
        # 遍历所有非碰撞区域
        for y in range(1, self.height - 1):
            for x in range(1, self.width - 1):
                if not self.collision_map[y][x]:
                    # 5%的概率放置装饰物
                    if random.random() < 0.02:
                        # 随机选择一个装饰物图片
                        decoration_img = random.choice(self.decoration_images)
                        self.decoration_map[y][x] = decoration_img
                        if self.debug:
                            print(f"在位置 ({x}, {y}) 放置装饰物")

    def draw_map(self, surface, camera_x, camera_y, zoomed_width, zoomed_height):
        # 绘制基础地图
        for y, row in enumerate(self.data):
            for x, gid in enumerate(row):
                tile_x = x * self.tile_width
                tile_y = y * self.tile_height
                if (camera_x <= tile_x <= camera_x + zoomed_width and 
                    camera_y <= tile_y <= camera_y + zoomed_height):
                    if gid != 0:
                        tile_img = self.tmx_data.get_tile_image_by_gid(gid)
                        if tile_img:
                            surface.blit(tile_img, (tile_x - camera_x, tile_y - camera_y))
        
        # 绘制装饰物
        for y in range(self.height):
            for x in range(self.width):
                decoration_img = self.decoration_map[y][x]
                if decoration_img is not None:
                    tile_x = x * self.tile_width
                    tile_y = y * self.tile_height
                    if (camera_x <= tile_x <= camera_x + zoomed_width and 
                        camera_y <= tile_y <= camera_y + zoomed_height):
                        surface.blit(decoration_img, (tile_x - camera_x, tile_y - camera_y))

    def draw_collision_overlay(self, surface, camera_x, camera_y, zoomed_width, zoomed_height):
        if not self.debug:
            return
        for y in range(self.height):
            for x in range(self.width):
                tile_x = x * self.tile_width
                tile_y = y * self.tile_height
                if (camera_x <= tile_x <= camera_x + zoomed_width and 
                    camera_y <= tile_y <= camera_y + zoomed_height):
                    if self.collision_map[y][x]:
                        rect = pygame.Rect(tile_x - camera_x, tile_y - camera_y, self.tile_width, self.tile_height)
                        overlay = pygame.Surface((self.tile_width, self.tile_height), pygame.SRCALPHA)
                        overlay.fill((255, 0, 0, 128))
                        surface.blit(overlay, rect) 