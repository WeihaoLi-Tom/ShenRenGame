from enum import Enum

class GameState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    MENU = "menu"

class GameStateManager:
    def __init__(self):
        self.current_state = GameState.RUNNING
        self.show_collision = False
        self.show_debug = False
        self.collision_modified = False
        self.auto_save_timer = 0
        self.AUTO_SAVE_INTERVAL = 60 * 30  # 30分钟自动保存一次
        
    def toggle_pause(self):
        if self.current_state == GameState.RUNNING:
            self.current_state = GameState.PAUSED
        else:
            self.current_state = GameState.RUNNING
            
    def toggle_collision_display(self):
        self.show_collision = not self.show_collision
        
    def toggle_debug_display(self):
        self.show_debug = not self.show_debug
        
    def mark_collision_modified(self):
        self.collision_modified = True
        self.auto_save_timer = 0
        
    def update_auto_save(self):
        if self.collision_modified:
            self.auto_save_timer += 1
            if self.auto_save_timer >= self.AUTO_SAVE_INTERVAL:
                return True
        return False
        
    def reset_auto_save(self):
        self.collision_modified = False
        self.auto_save_timer = 0 