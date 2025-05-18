from PIL import Image
import os

sheet_path = "assets/characters/skeleton.png"  # 骷髅精灵表图片
output_dir = "assets/characters/skeleton_frames"  # 输出目录改为skeleton_frames
frame_w, frame_h = 48, 48

# 动作分布（行号从0开始）
# 每行代表一个方向：下、右、上
actions = [
    ("idle_down", 0, 0),     # 第0行是向下idle
    ("idle_right", 1, 1),    # 第1行是向右idle
    ("idle_up", 2, 2),       # 第2行是向上idle
    ("move_down", 3, 3),     # 第3行是向下move
    ("move_right", 4, 4),    # 第4行是向右move
    ("move_up", 5, 5),       # 第5行是向上move
    ("attack_down", 6, 6),   # 第6行是向下attack
    ("attack_right", 7, 7),  # 第7行是向右attack
    ("attack_up", 8, 8),     # 第8行是向上attack
    ("hurt_down", 9, 9),     # 第9行是向下hurt
    ("hurt_right", 10, 10),  # 第10行是向右hurt
    ("hurt_up", 11, 11),     # 第11行是向上hurt
    ("death", 12, 12),       # 第12行是death
]

# 需要生成向左动作的基础动作列表
left_actions = [
    "idle",
    "move",
    "attack",
    "hurt"
]

os.makedirs(output_dir, exist_ok=True)
sheet = Image.open(sheet_path)
sheet_w, sheet_h = sheet.size
frames_per_row = sheet_w // frame_w

# 存储向右动作的帧，用于生成向左动作
right_frames = {}

for action, row_start, row_end in actions:
    frame_idx = 0
    frames = []
    for row in range(row_start, row_end + 1):
        # 根据动作类型决定每行的帧数
        if action.startswith('attack'):
            frames_count = 4  # 攻击动作4帧
        elif action == 'death':
            frames_count = 6  # 死亡动作6帧
        else:
            frames_count = frames_per_row  # 其他动作使用完整行
            
        for col in range(frames_count):
            x = col * frame_w
            y = row * frame_h
            frame = sheet.crop((x, y, x+frame_w, y+frame_h))
            frame.save(os.path.join(output_dir, f"{action}_{frame_idx+1:02d}.png"))
            frames.append(frame)
            frame_idx += 1
    
    # 如果是向右的动作，保存帧用于生成向左动作
    if action.endswith('_right'):
        base_action = action.replace('_right', '')
        right_frames[base_action] = frames

# 生成向左动作的帧
for base_action in left_actions:
    if base_action in right_frames:
        frames = right_frames[base_action]
        for idx, frame in enumerate(frames):
            # 水平翻转帧
            flipped_frame = frame.transpose(Image.FLIP_LEFT_RIGHT)
            flipped_frame.save(os.path.join(output_dir, f"{base_action}_left_{idx+1:02d}.png"))

print(f"已完成拆分，所有帧已保存到 {output_dir}")
print("注意：向左的动作是通过水平翻转向右的动作生成的")