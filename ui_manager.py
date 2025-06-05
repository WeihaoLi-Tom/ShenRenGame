import pygame
import time
import math
import os
from game_state import GameStateManager

class UIManager:
    def __init__(self, window_width, window_height, game_state_manager=None):
        self.window_width = window_width
        self.window_height = window_height
        self.game_state_manager = game_state_manager
        self.fps = 0
        self.fps_timer = time.time()
        self.fps_counter = 0
        
        # 优先加载项目内的中文字体
        try:
            project_font_path = "assets/fonts/chinese.ttf"
            if os.path.exists(project_font_path):
                self.font = pygame.font.Font(project_font_path, 24)
                print(f"成功加载项目字体: {project_font_path}")
            else:
                self.font = pygame.font.Font(None, 24)
                print("警告: 未能加载中文字体，将使用默认字体")
        except Exception as e:
            print(f"加载字体时出错: {e}")
            self.font = pygame.font.Font(None, 24)
        
        # Boss警告相关
        self.boss_warning_img = None
        self.boss_warning_timer = 0
        self.boss_warning_duration = 2.0
        
        try:
            self.boss_warning_img = pygame.image.load("assets/title/Bosswarning.png").convert_alpha()
        except Exception as e:
            print(f"Boss提示图片加载失败: {e}")
        
    def draw_fps(self, surface):
        self.fps_counter += 1
        if time.time() - self.fps_timer >= 1:
            self.fps = self.fps_counter
            self.fps_counter = 0
            self.fps_timer = time.time()
        fps_text = self.font.render(f"FPS: {self.fps}", True, (255, 255, 255))
        surface.blit(fps_text, (10, 10))
        
    def draw_debug_info(self, surface, player_pos, zoom_level, show_collision, fps, game_state):
        debug_text = [
            f"位置: {player_pos}",
            f"缩放: {zoom_level:.1f}x",
            f"碰撞: {'开启' if show_collision else '关闭'}",
            f"FPS: {fps}",
            f"状态: {game_state}"
        ]
        for i, text in enumerate(debug_text):
            text_surface = self.font.render(text, True, (255, 255, 255))
            surface.blit(text_surface, (10, 10 + i * 25))
        
        # 绘制开发者控制台提示
        if self.game_state_manager and self.game_state_manager.console_tip and \
           time.time() - self.game_state_manager.console_tip_timer < 2.0:
            tip_text = self.font.render(self.game_state_manager.console_tip, True, (0, 255, 0))
            tip_rect = tip_text.get_rect(center=(self.window_width//2, 50))
            # 绘制半透明背景
            bg_surf = pygame.Surface((tip_rect.width + 20, tip_rect.height + 10), pygame.SRCALPHA)
            bg_surf.fill((0, 0, 0, 128))
            surface.blit(bg_surf, (tip_rect.x - 10, tip_rect.y - 5))
            surface.blit(tip_text, tip_rect)
        
    def draw_pause_screen(self, surface):
        pause_text = self.font.render("游戏暂停 - 按ESC继续", True, (255, 255, 255))
        text_rect = pause_text.get_rect(center=(self.window_width/2, self.window_height/2))
        surface.blit(pause_text, text_rect)
        
    def draw_boss_warning(self, surface):
        if self.boss_warning_img and self.boss_warning_timer > 0:
            elapsed = time.time() - self.boss_warning_timer
            if elapsed < self.boss_warning_duration:
                # 缩放图片
                scale = 0.6
                img_w = int(self.boss_warning_img.get_width() * scale)
                img_h = int(self.boss_warning_img.get_height() * scale)
                scaled_img = pygame.transform.scale(self.boss_warning_img, (img_w, img_h))
                
                # 跳跃动画
                jump_offset = int(18 * abs(math.sin(elapsed * 8)))
                
                # 闪烁效果
                if int(elapsed * 10) % 2 == 0:
                    img_rect = scaled_img.get_rect(center=(self.window_width//2, self.window_height//4 + jump_offset))
                    surface.blit(scaled_img, img_rect)
            else:
                self.boss_warning_timer = 0
        
    def trigger_boss_warning(self):
        self.boss_warning_timer = time.time() 