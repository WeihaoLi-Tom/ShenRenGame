import pygame
import time

class WeaponDrop:
    def __init__(self, pos, img_path="assets/weapon/swd2.png"):
        self.pos = pos
        self.rect = pygame.Rect(pos[0]-16, pos[1]-16, 32, 32)
        self.image_path = img_path  # 保存图片路径
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
        draw_x = self.pos[0] - camera_x - 24
        draw_y = self.pos[1] - camera_y - 24 + self.hover_offset
        surface.blit(glow_surf, (draw_x, draw_y))
        
        # 绘制旋转后的武器图像
        angle = (time.time() - self.birth_time) * 20 % 360
        rotated_img = pygame.transform.rotate(self.image, angle)
        rot_rect = rotated_img.get_rect(center=(self.pos[0] - camera_x, self.pos[1] - camera_y + self.hover_offset))
        surface.blit(rotated_img, rot_rect)
        
    def draw_pickup_prompt(self, surface, camera_x, camera_y, player_pos, font):
        # 检查玩家是否靠近武器，显示拾取提示
        pickup_distance = 50
        px, py = player_pos
        wx, wy = self.pos
        if ((px - wx) ** 2 + (py - wy) ** 2) ** 0.5 < pickup_distance:
            # 用传入的小号font渲染中文
            small_font = pygame.font.Font(font.get_name(), 8) if hasattr(font, 'get_name') else font
            pickup_text = small_font.render("按F拾取耄耋之卵！", True, (255, 255, 255))
            scale = 0.7  # 比如70%
            pickup_text = pygame.transform.smoothscale(pickup_text, (int(pickup_text.get_width()*scale), int(pickup_text.get_height()*scale)))
            text_x = wx - camera_x - pickup_text.get_width() // 2
            text_y = wy - camera_y - 28  # 适当上移
            
            # 更紧凑的文字背景
            text_bg = pygame.Surface((pickup_text.get_width() + 4, pickup_text.get_height() + 2), pygame.SRCALPHA)
            pygame.draw.rect(text_bg, (0, 0, 0, 160), text_bg.get_rect(), 0, 2)
            surface.blit(text_bg, (text_x - 2, text_y - 1))
            surface.blit(pickup_text, (text_x, text_y)) 