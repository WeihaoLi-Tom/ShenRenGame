import pygame
import os
import sys
import math
import time

class MenuItem:
    def __init__(self, text, font, pos, color=(255, 255, 255), hover_color=(255, 200, 0)):
        self.text = text
        self.font = font
        self.pos = pos
        self.color = color
        self.hover_color = hover_color
        self.hovered = False
        
        self.text_surface = self.font.render(text, True, color)
        self.text_rect = self.text_surface.get_rect(center=pos)
        
        # 添加边界以便更容易检测悬停
        padding = 20
        self.hover_rect = pygame.Rect(
            self.text_rect.left - padding,
            self.text_rect.top - padding,
            self.text_rect.width + padding * 2,
            self.text_rect.height + padding * 2
        )
        
    def update(self, mouse_pos):
        self.hovered = self.hover_rect.collidepoint(mouse_pos)
        
    def draw(self, surface):
        color = self.hover_color if self.hovered else self.color
        text_surface = self.font.render(self.text, True, color)
        
        # 绘制边框（仅在悬停时）
        if self.hovered:
            # 发光效果
            glow_size = 3
            for i in range(glow_size, 0, -1):
                alpha = 150 - i * 40
                glow_color = (*self.hover_color, alpha)
                glow_rect = pygame.Rect(
                    self.text_rect.left - i * 2,
                    self.text_rect.top - i * 2,
                    self.text_rect.width + i * 4,
                    self.text_rect.height + i * 4
                )
                pygame.draw.rect(surface, glow_color, glow_rect, border_radius=10)
            
            # 实际边框
            pygame.draw.rect(surface, color, self.text_rect.inflate(20, 10), 2, border_radius=5)
        
        surface.blit(text_surface, self.text_rect)

class GameMenu:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.running = True
        self.start_game = False
        
        # 尝试加载字体
        try:
            font_path = os.path.join("assets", "fonts", "chinese.ttf")
            if os.path.exists(font_path):
                self.title_font = pygame.font.Font(font_path, 72)
                self.menu_font = pygame.font.Font(font_path, 36)
            else:
                # 尝试加载系统中文字体
                if os.name == 'nt':  # Windows
                    system_fonts = ["simhei.ttf", "msyh.ttc", "simsun.ttc"]
                    for font in system_fonts:
                        try:
                            path = os.path.join("C:/Windows/Fonts", font)
                            if os.path.exists(path):
                                self.title_font = pygame.font.Font(path, 72)
                                self.menu_font = pygame.font.Font(path, 36)
                                break
                        except:
                            pass
                    else:  # 如果for循环正常结束（没有找到中文字体）
                        self.title_font = pygame.font.Font(None, 72)
                        self.menu_font = pygame.font.Font(None, 36)
                else:  # 非Windows系统
                    self.title_font = pygame.font.Font(None, 72)
                    self.menu_font = pygame.font.Font(None, 36)
        except Exception as e:
            print(f"字体加载失败: {e}")
            self.title_font = pygame.font.Font(None, 72)
            self.menu_font = pygame.font.Font(None, 36)
        
        # 创建菜单项
        self.menu_items = [
            MenuItem("开始游戏", self.menu_font, (screen_width // 2, screen_height // 2)),
            MenuItem("退出游戏", self.menu_font, (screen_width // 2, screen_height // 2 + 80))
        ]
        
        # 加载背景图像
        try:
            self.bg_image = pygame.image.load(os.path.join("assets", "title", "menu_bg.png")).convert()
            self.bg_image = pygame.transform.scale(self.bg_image, (screen_width, screen_height))
        except:
            self.bg_image = None
            print("无法加载菜单背景图像")
        
        # 加载游戏标题图像
        try:
            self.title_image = pygame.image.load(os.path.join("assets", "title", "title.png")).convert_alpha()
            # 保持比例缩放标题
            width = min(screen_width * 0.8, self.title_image.get_width())
            height = (width / self.title_image.get_width()) * self.title_image.get_height()
            self.title_image = pygame.transform.smoothscale(self.title_image, (int(width), int(height)))
            self.title_rect = self.title_image.get_rect(midtop=(screen_width // 2, 50))
        except:
            self.title_image = None
            print("无法加载标题图像，将使用文字标题")
        
        # 初始化粒子系统
        self.particles = []
        self.last_particle_time = 0
        
        # 试玩加载音乐
        try:
            pygame.mixer.music.load(os.path.join("assets", "bgm", "menu_bgm.mp3"))
            pygame.mixer.music.set_volume(0.5)
            pygame.mixer.music.play(-1)
        except:
            print("无法加载菜单背景音乐")
    
    def add_particle(self, pos=None):
        """添加一个粒子到粒子系统"""
        if pos is None:
            x = pygame.math.Vector2(
                pygame.math.Vector2(self.screen_width // 2, self.screen_height // 2) + 
                pygame.math.Vector2(
                    (pygame.time.get_ticks() % 1000) / 1000.0 * self.screen_width - self.screen_width // 2,
                    (pygame.time.get_ticks() % 800) / 800.0 * self.screen_height - self.screen_height // 2
                )
            )
            y = pygame.math.Vector2(
                pygame.math.Vector2(self.screen_width // 2, self.screen_height // 2) + 
                pygame.math.Vector2(
                    (pygame.time.get_ticks() % 800 + 100) / 900.0 * self.screen_width - self.screen_width // 2,
                    (pygame.time.get_ticks() % 1000 + 100) / 1100.0 * self.screen_height - self.screen_height // 2
                )
            )
            pos = pygame.math.Vector2(x + (y - x) * (pygame.time.get_ticks() % 1000) / 1000.0)
        
        size = pygame.math.Vector2(3, 3)
        vel = pygame.math.Vector2(
            (pygame.time.get_ticks() % 200) / 100.0 - 1,
            (pygame.time.get_ticks() % 300) / 150.0 - 1
        ) * 0.5
        color = (
            150 + (pygame.time.get_ticks() % 100),
            100 + (pygame.time.get_ticks() % 155),
            50 + (pygame.time.get_ticks() % 150)
        )
        life = 2 + (pygame.time.get_ticks() % 1000) / 500.0
        self.particles.append({
            "pos": pos,
            "vel": vel,
            "size": size,
            "color": color,
            "life": life,
            "birth_time": time.time()
        })
    
    def update_particles(self):
        """更新粒子系统"""
        current_time = time.time()
        
        # 定期添加新粒子
        if current_time - self.last_particle_time > 0.1:
            self.add_particle()
            self.last_particle_time = current_time
        
        # 更新现有粒子
        for particle in self.particles[:]:
            age = current_time - particle["birth_time"]
            if age > particle["life"]:
                self.particles.remove(particle)
                continue
            
            # 更新位置
            particle["pos"] += particle["vel"]
            
            # 添加一些随机性和波动
            particle["vel"] += pygame.math.Vector2(
                math.sin(current_time * 5 + particle["birth_time"] * 10) * 0.02,
                math.cos(current_time * 3 + particle["birth_time"] * 8) * 0.02
            )
            
            # 边界检查
            if not (0 <= particle["pos"].x <= self.screen_width and 
                   0 <= particle["pos"].y <= self.screen_height):
                self.particles.remove(particle)
    
    def draw_particles(self, surface):
        """绘制所有粒子"""
        current_time = time.time()
        for particle in self.particles:
            age = current_time - particle["birth_time"]
            life_ratio = age / particle["life"]
            
            # 随着时间推移改变颜色和大小
            alpha = int(255 * (1 - life_ratio))
            color = (*particle["color"], alpha)
            size = particle["size"] * (1 - life_ratio * 0.5)
            
            # 绘制粒子
            pos = (int(particle["pos"].x), int(particle["pos"].y))
            pygame.draw.circle(surface, color, pos, max(1, int(size.x)))
    
    def run(self, screen):
        """运行菜单循环"""
        clock = pygame.time.Clock()
        
        while self.running:
            mouse_pos = pygame.mouse.get_pos()
            
            # 事件处理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                        pygame.quit()
                        sys.exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # 左键点击
                        for item in self.menu_items:
                            if item.hovered:
                                if item.text == "开始游戏":
                                    self.start_game = True
                                    self.running = False
                                elif item.text == "退出游戏":
                                    self.running = False
                                    pygame.quit()
                                    sys.exit()
            
            # 更新菜单项
            for item in self.menu_items:
                item.update(mouse_pos)
            
            # 更新粒子
            self.update_particles()
            
            # 绘制
            screen.fill((20, 20, 40))  # 深蓝色背景
            
            # 绘制背景图像（如果有）
            if self.bg_image:
                screen.blit(self.bg_image, (0, 0))
            
            # 绘制粒子
            self.draw_particles(screen)
            
            # 绘制标题
            if self.title_image:
                # 添加一些动画效果
                offset = math.sin(time.time() * 2) * 5
                title_pos = self.title_rect.copy()
                title_pos.y += offset
                screen.blit(self.title_image, title_pos)
            else:
                # 使用文字标题
                title_text = self.title_font.render("好汉大冒险", True, (255, 215, 0))
                title_rect = title_text.get_rect(center=(self.screen_width // 2, 100))
                screen.blit(title_text, title_rect)
            
            # 绘制菜单项
            for item in self.menu_items:
                item.draw(screen)
            
            # 绘制底部版权信息
            copyright_text = self.menu_font.render("2025 TGA最佳烂游", True, (100, 100, 100))
            copyright_rect = copyright_text.get_rect(midbottom=(self.screen_width // 2, self.screen_height - 20))
            screen.blit(copyright_text, copyright_rect)
            
            pygame.display.flip()
            clock.tick(60)
        
        # 停止菜单音乐
        try:
            pygame.mixer.music.fadeout(1000)
        except:
            pass
        
        return self.start_game

if __name__ == "__main__":
    # 测试代码
    pygame.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Menu Test")
    
    menu = GameMenu(800, 600)
    start_game = menu.run(screen)
    
    if start_game:
        print("Starting game...")
    else:
        print("Exiting...") 