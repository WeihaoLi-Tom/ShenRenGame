from PIL import Image
import os

sheet_path = "assets/characters/player_sheet.png"  # 你的精灵表图片名
output_dir = "assets/characters/player_frames"
frame_w, frame_h = 48, 48

# 动作分布（行号从0开始）
# 每行代表一个方向：下、右、上
actions = [
    ("idle_down", 0, 0),    # 第0行是向下idle
    ("idle_right", 1, 1),   # 第1行是向右idle
    ("idle_up", 2, 2),      # 第2行是向上idle
    ("move_down", 3, 3),    # 第3行是向下move
    ("move_right", 4, 4),   # 第4行是向右move
    ("move_up", 5, 5),      # 第5行是向上move
    ("attack_down", 6, 6),  # 第6行是向下attack
    ("attack_right", 7, 7), # 第7行是向右attack
    ("attack_up", 8, 8),    # 第8行是向上attack
    ("death", 9, 9),        # 第9行是death
]

os.makedirs(output_dir, exist_ok=True)
sheet = Image.open(sheet_path)
sheet_w, sheet_h = sheet.size
frames_per_row = sheet_w // frame_w

for action, row_start, row_end in actions:
    frame_idx = 0
    for row in range(row_start, row_end + 1):
        for col in range(4) if action.startswith('attack') else range(frames_per_row):
            x = col * frame_w
            y = row * frame_h
            frame = sheet.crop((x, y, x+frame_w, y+frame_h))
            frame.save(os.path.join(output_dir, f"{action}_{frame_idx+1:02d}.png"))
            frame_idx += 1

print(f"已完成拆分，所有帧已保存到 {output_dir}")