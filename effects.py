import pygame
import random
import time
import math

class ExplosionParticle:
    def __init__(self, pos):
        self.x, self.y = pos
        self.radius = random.randint(4, 12)
        self.color = random.choice([
            (255, 200, 0), (255, 100, 0), (255, 255, 255),
            (255, 80, 80), (255, 255, 120), (255, 180, 80), (255, 80, 200)
        ])
        self.life = random.uniform(0.5, 1.0)
        self.birth = time.time()
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(2, 5)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
    
    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
    
    def is_alive(self):
        return time.time() - self.birth < self.life
        
    def draw(self, surface, camera_x, camera_y, zoom=1.0):
        if not self.is_alive():
            return
            
        screen_x = int((self.x - camera_x) * zoom)
        screen_y = int((self.y - camera_y) * zoom)
        
        if (screen_x < -50 or screen_x > surface.get_width() + 50 or
            screen_y < -50 or screen_y > surface.get_height() + 50):
            return
            
        alpha = int(255 * (1 - (time.time() - self.birth) / self.life))
        radius = int(self.radius * zoom)
        
        temp_surf = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
        pygame.draw.circle(temp_surf, self.color + (alpha,), (radius, radius), radius)
        surface.blit(temp_surf, (screen_x - radius, screen_y - radius))

class ExplosionRing:
    def __init__(self, pos):
        self.x, self.y = pos
        self.birth = time.time()
        self.duration = 0.7
        self.max_radius = 120
    
    def is_alive(self):
        return time.time() - self.birth < self.duration
        
    def draw(self, surface, camera_x, camera_y, zoom=1.0):
        if not self.is_alive():
            return
            
        screen_x = int((self.x - camera_x) * zoom)
        screen_y = int((self.y - camera_y) * zoom)
        
        if (screen_x < -150 or screen_x > surface.get_width() + 150 or
            screen_y < -150 or screen_y > surface.get_height() + 150):
            return
            
        progress = (time.time() - self.birth) / self.duration
        radius = int(self.max_radius * progress * zoom)
        alpha = int(180 * (1 - progress))
        
        temp_surf = pygame.Surface((radius*2 + 20, radius*2 + 20), pygame.SRCALPHA)
        pygame.draw.circle(temp_surf, (255, 255, 180, alpha), (radius + 10, radius + 10), radius, max(2, int(6 * zoom)))
        surface.blit(temp_surf, (screen_x - radius - 10, screen_y - radius - 10))

class EffectManager:
    def __init__(self):
        self.particles = []
        self.rings = []
    
    def create_explosion(self, pos, particle_count=80):
        for _ in range(particle_count):
            self.particles.append(ExplosionParticle(pos))
        self.rings.append(ExplosionRing(pos))
    
    def create_small_explosion(self, pos, particle_count=10):
        for _ in range(particle_count):
            p = ExplosionParticle(pos)
            p.color = random.choice([(180, 220, 255), (120, 180, 255)])
            p.life = random.uniform(0.2, 0.4)
            self.particles.append(p)
    
    def update(self, dt):
        # 更新粒子
        for p in self.particles[:]:
            p.update(dt)
            if not p.is_alive():
                self.particles.remove(p)
        
        # 更新冲击波
        for ring in self.rings[:]:
            if not ring.is_alive():
                self.rings.remove(ring)
    
    def draw(self, surface, camera_x, camera_y, zoom=1.0):
        for p in self.particles:
            p.draw(surface, camera_x, camera_y, zoom)
        for ring in self.rings:
            ring.draw(surface, camera_x, camera_y, zoom) 