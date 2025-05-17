import pygame
import time
import math

class UIManager:
    def __init__(self, window_width, window_height):
        self.window_width = window_width
        self.window_height = window_height
        self.fps = 0
        self.fps_timer = time.time()
        self.fps_counter = 0
        
        # 初始化字体
        try:
            self.font = pygame.font.Font(None, 24)
        except:
            self.font = pygame.font.SysFont('arial', 24)
            
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
            f"Pos: {player_pos}",
            f"Zoom: {zoom_level:.1f}x",
            f"Collision: {'ON' if show_collision else 'OFF'}",
            f"FPS: {fps}",
            f"State: {game_state}"
        ]
        for i, text in enumerate(debug_text):
            text_surface = self.font.render(text, True, (255, 255, 255))
            surface.blit(text_surface, (10, 10 + i * 25))
            
    def draw_pause_screen(self, surface):
        pause_text = self.font.render("Game Pause - press ESC continue", True, (255, 255, 255))
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