import pygame
pygame.mixer.init()
sound = pygame.mixer.Sound("assets/sound/death.wav")
sound.play()
input("按回车退出")  # 保证声音有时间播放