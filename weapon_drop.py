import pygame
import time

class WeaponDrop:
    def __init__(self, pos, img_path="assets/weapon/swd2.png"):
        self.pos = pos
        self.rect = pygame.Rect(pos[0]-16, pos[1]-16, 32, 32)
        try:
            self.image = pygame.image.load(img_path).convert_alpha()
            self.image = pygame.transform.scale(self.image, (32, 32))
        except Exception as e:
            print(f"加载武器图片时出错: {e}")
            self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (255, 215, 0), (0, 0, 32, 32))
        self.hover_offset = 0
        self.hover_speed = 2
        self.hover_direction = 1
        self.glow_alpha = 0
        self.glow_direction = 5
        self.birth_time = time.time()
        
    def update(self):
        # 上下浮动动画
        self.hover_offset += self.hover_speed * self.hover_direction * 0.05
        if abs(self.hover_offset) >= 5:
            self.hover_direction *= -1
            
        # 光环透明度动画
        self.glow_alpha += self.glow_direction
        if self.glow_alpha >= 180 or self.glow_alpha <= 30:
            self.glow_direction *= -1
            
    def draw(self, surface, camera_x, camera_y):
        # 绘制光环
        glow_surf = pygame.Surface((48, 48), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 215, 0, self.glow_alpha), (24, 24), 20)
        surface.blit(glow_surf, (self.pos[0] - camera_x - 24, self.pos[1] - camera_y - 24 + self.hover_offset))
        
        # 绘制旋转后的武器图像
        angle = (time.time() - self.birth_time) * 20 % 360
        rotated_img = pygame.transform.rotate(self.image, angle)
        rot_rect = rotated_img.get_rect(center=(self.pos[0] - camera_x, self.pos[1] - camera_y + self.hover_offset))
        surface.blit(rotated_img, rot_rect)
        
    def draw_pickup_prompt(self, surface, camera_x, camera_y, player_pos):
        # 检查玩家是否靠近武器，显示拾取提示
        pickup_distance = 50
        px, py = player_pos
        wx, wy = self.pos
        if ((px - wx) ** 2 + (py - wy) ** 2) ** 0.5 < pickup_distance:
            # 绘制提示文本
            pickup_font = pygame.font.Font(None, 20)
            pickup_text = pickup_font.render("Press F to Pick Up !", True, (255, 255, 255))
            text_x = wx - camera_x - pickup_text.get_width() // 2
            text_y = wy - camera_y - 40
            
            # 添加文字背景
            text_bg = pygame.Surface((pickup_text.get_width() + 10, pickup_text.get_height() + 6), pygame.SRCALPHA)
            pygame.draw.rect(text_bg, (0, 0, 0, 150), text_bg.get_rect(), 0, 3)
            surface.blit(text_bg, (text_x - 5, text_y - 3))
            surface.blit(pickup_text, (text_x, text_y)) 