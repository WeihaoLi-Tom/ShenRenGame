import pygame
import os

class AudioManager:
    def __init__(self):
        self.boss_bgm_fadein = False
        self.boss_bgm_fadein_timer = 0
        self.boss_bgm_fadein_duration = 5.0  # 渐变时长5秒
        self.boss_bgm_max_volume = 0.2       # 最大音量上限
        
    def trigger_boss_bgm(self):
        self.boss_bgm_fadein = True
        self.boss_bgm_fadein_timer = 0
        pygame.mixer.music.set_volume(0)
        
    def update(self, dt):
        if self.boss_bgm_fadein:
            self.boss_bgm_fadein_timer += dt
            vol = min(self.boss_bgm_fadein_timer / self.boss_bgm_fadein_duration, 1.0) * self.boss_bgm_max_volume
            pygame.mixer.music.set_volume(vol)
            if vol >= self.boss_bgm_max_volume:
                self.boss_bgm_fadein = False

    def load_font(self):
        try:
            # 优先加载你自己的字体
            project_font_path = "assets/fonts/chinese.ttf"
            if os.path.exists(project_font_path):
                self.font = pygame.font.Font(project_font_path, 24)
                print(f"成功加载项目字体: {project_font_path}")
            else:
                # 下面是原有的系统字体尝试
                font_loaded = False
                if os.name == 'nt':  # Windows系统
                    font_paths = [
                        "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                        "C:/Windows/Fonts/simhei.ttf",  # 黑体
                        "C:/Windows/Fonts/simsun.ttc",  # 宋体
                    ]
                else:  # Linux/Mac系统
                    font_paths = [
                        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
                        "/System/Library/Fonts/PingFang.ttc",
                    ]
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        self.font = pygame.font.Font(font_path, 24)
                        font_loaded = True
                        print(f"成功加载字体: {font_path}")
                        break
                if not font_loaded:
                    self.font = pygame.font.Font(None, 24)
                    print("警告: 未能加载中文字体，将使用默认字体")
        except Exception as e:
            print(f"加载字体时出错: {e}")
            self.font = pygame.font.Font(None, 24) 