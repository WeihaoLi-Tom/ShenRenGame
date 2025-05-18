import pygame
import os
from enum import Enum

class SoundCategory(Enum):
    PLAYER = "player"
    COMBAT = "combat"
    UI = "ui"
    AMBIENT = "ambient"
    BOSS = "boss"

class AudioManager:
    def __init__(self):
        # 音效分类字典
        self.sounds = {category: {} for category in SoundCategory}
        
        # 音量控制
        self.volumes = {
            SoundCategory.PLAYER: 0.5,
            SoundCategory.COMBAT: 0.5,
            SoundCategory.UI: 0.3,
            SoundCategory.AMBIENT: 0.4,
            SoundCategory.BOSS: 0.5
        }
        
        # 音效状态
        self.is_muted = False
        self.current_bgm = None
        self.bgm_volume = 0.5
        
        # BOSS BGM 渐变控制
        self.boss_bgm_fadein = False
        self.boss_bgm_fadein_timer = 0
        self.boss_bgm_fadein_duration = 5.0
        self.boss_bgm_max_volume = 0.2
        
        # 加载所有音效
        self._load_sounds()
        
    def _load_sounds(self):
        def load(category, name, path, volume=0.5):
            try:
                sound = pygame.mixer.Sound(path)
                sound.set_volume(volume * self.volumes[category])
                self.sounds[category][name] = sound
            except Exception as e:
                print(f"音效 {name} 加载失败: {e}")

        # 玩家音效
        load(SoundCategory.PLAYER, "dash", "assets/sound/dash.wav", 0.3)
        load(SoundCategory.PLAYER, "firedash", "assets/sound/firedash.wav", 0.3)
        load(SoundCategory.PLAYER, "transform", "assets/sound/transform.wav", 0.5)
        
        # 战斗音效
        load(SoundCategory.COMBAT, "hitnone", "assets/sound/hitnone.wav", 0.5)
        load(SoundCategory.COMBAT, "firehit", "assets/sound/firehit.wav", 0.5)
        load(SoundCategory.COMBAT, "hurt", "assets/sound/hurt_out.wav", 0.1)
        load(SoundCategory.COMBAT, "scream", "assets/sound/Tom_Scream.wav", 1.0)
        load(SoundCategory.COMBAT, "fireskill", "assets/sound/fireskill.wav", 0.5)
        
        # UI音效
        load(SoundCategory.UI, "pickup", "assets/sound/pickup.wav", 0.5)
        load(SoundCategory.UI, "wuhu", "assets/sound/wuhu.wav", 0.5)
        
        # 环境音效
        load(SoundCategory.AMBIENT, "wind", "assets/sound/wind.wav", 0.3)
        
        # BOSS音效
        load(SoundCategory.BOSS, "boss_roar", "assets/sound/boss_roar.wav", 0.6)

    def play_sound(self, category: SoundCategory, name: str, channel=None, loop=0):
        """播放指定分类和名称的音效"""
        if self.is_muted:
            return
            
        sound = self.sounds[category].get(name)
        if not sound:
            print(f"音效 {category.value}/{name} 未加载")
            return
            
        try:
            if channel is not None:
                ch = pygame.mixer.Channel(channel)
                ch.stop()
                ch.play(sound, loops=loop)
            else:
                sound.play(loops=loop)
        except Exception as e:
            print(f"播放音效 {category.value}/{name} 失败: {e}")

    def set_category_volume(self, category: SoundCategory, volume: float):
        """设置指定分类的音量"""
        self.volumes[category] = max(0.0, min(1.0, volume))
        for sound in self.sounds[category].values():
            sound.set_volume(volume)

    def set_mute(self, mute: bool):
        """设置全局静音"""
        self.is_muted = mute
        pygame.mixer.music.set_volume(0 if mute else self.bgm_volume)

    def play_bgm(self, path: str, volume: float = 0.5, loop: int = -1):
        """播放背景音乐"""
        try:
            pygame.mixer.music.load(path)
            self.bgm_volume = volume
            pygame.mixer.music.set_volume(0 if self.is_muted else volume)
            pygame.mixer.music.play(loops=loop)
            self.current_bgm = path
        except Exception as e:
            print(f"播放背景音乐失败: {e}")

    def stop_bgm(self):
        """停止背景音乐"""
        pygame.mixer.music.stop()
        self.current_bgm = None

    def trigger_boss_bgm(self):
        """触发BOSS战BGM渐变"""
        self.boss_bgm_fadein = True
        self.boss_bgm_fadein_timer = 0
        pygame.mixer.music.set_volume(0)

    def update(self, dt):
        """更新音效状态"""
        if self.boss_bgm_fadein:
            self.boss_bgm_fadein_timer += dt
            vol = min(self.boss_bgm_fadein_timer / self.boss_bgm_fadein_duration, 1.0) * self.boss_bgm_max_volume
            pygame.mixer.music.set_volume(0 if self.is_muted else vol)
            if vol >= self.boss_bgm_max_volume:
                self.boss_bgm_fadein = False

    def load_font(self):
        """加载字体"""
        try:
            project_font_path = "assets/fonts/chinese.ttf"
            if os.path.exists(project_font_path):
                self.font = pygame.font.Font(project_font_path, 24)
                print(f"成功加载项目字体: {project_font_path}")
            else:
                font_loaded = False
                if os.name == 'nt':
                    font_paths = [
                        "C:/Windows/Fonts/msyh.ttc",
                        "C:/Windows/Fonts/simhei.ttf",
                        "C:/Windows/Fonts/simsun.ttc",
                    ]
                else:
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