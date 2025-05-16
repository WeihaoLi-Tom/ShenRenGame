import os
import requests
import zipfile
import shutil
from pathlib import Path
import webbrowser

def download_file(url, filename):
    """下载文件"""
    print(f"正在下载 {filename}...")
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as f:
        if total_size == 0:
            f.write(response.content)
        else:
            downloaded = 0
            total_size = int(total_size)
            for data in response.iter_content(chunk_size=4096):
                downloaded += len(data)
                f.write(data)
                done = int(50 * downloaded / total_size)
                print(f"\r下载进度: [{'=' * done}{' ' * (50-done)}] {downloaded}/{total_size} bytes", end='')
    print("\n下载完成！")

def setup_assets():
    """设置游戏素材"""
    # 创建资源目录
    assets_dir = Path('assets')
    if not assets_dir.exists():
        assets_dir.mkdir()
        (assets_dir / 'characters').mkdir()
        (assets_dir / 'backgrounds').mkdir()
        (assets_dir / 'effects').mkdir()

    print("请按照以下步骤操作：")
    print("1. 浏览器将自动打开 Kenney.nl 的 Pixel Adventure 素材包页面")
    print("2. 点击 'Download' 按钮下载素材包")
    print("3. 将下载的 zip 文件重命名为 'pixel_adventure.zip' 并移动到游戏目录")
    print("4. 按回车键继续...")
    
    # 打开下载页面
    webbrowser.open("https://kenney.nl/assets/pixel-adventure")
    
    input()
    
    # 检查文件是否存在
    zip_file = "pixel_adventure.zip"
    if not os.path.exists(zip_file):
        print(f"错误: 未找到 {zip_file} 文件")
        return
    
    try:
        # 解压文件
        print("正在解压文件...")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall("temp_assets")
        
        # 移动需要的文件
        print("正在整理文件...")
        
        # 移动角色精灵图
        character_files = [
            "Main Characters/Ninja Frog/Idle (32x32).png",
            "Main Characters/Ninja Frog/Run (32x32).png",
            "Main Characters/Ninja Frog/Jump (32x32).png",
            "Main Characters/Ninja Frog/Attack (32x32).png"
        ]
        
        for file in character_files:
            src = Path("temp_assets") / "Pixel Adventure" / "Main Characters" / "Ninja Frog" / file
            dst = assets_dir / "characters" / f"player_{file.split('(')[0].strip().lower()}.png"
            if src.exists():
                shutil.copy2(src, dst)
        
        # 移动敌人精灵图
        enemy_files = [
            "Enemies/Rocks/Idle (32x32).png",
            "Enemies/Rocks/Run (32x32).png"
        ]
        
        for file in enemy_files:
            src = Path("temp_assets") / "Pixel Adventure" / file
            dst = assets_dir / "characters" / f"enemy_{file.split('(')[0].strip().lower()}.png"
            if src.exists():
                shutil.copy2(src, dst)
        
        # 移动背景元素
        background_files = [
            "Terrain/Terrain.png",
            "Background/Green.png"
        ]
        
        for file in background_files:
            src = Path("temp_assets") / "Pixel Adventure" / file
            dst = assets_dir / "backgrounds" / file.split('/')[-1]
            if src.exists():
                shutil.copy2(src, dst)
        
        # 移动特效
        effect_files = [
            "Effects/Hit Effect.png",
            "Effects/Attack Effect.png"
        ]
        
        for file in effect_files:
            src = Path("temp_assets") / "Pixel Adventure" / file
            dst = assets_dir / "effects" / file.split('/')[-1]
            if src.exists():
                shutil.copy2(src, dst)
        
        # 清理临时文件
        print("正在清理临时文件...")
        shutil.rmtree("temp_assets")
        os.remove(zip_file)
        
        print("素材设置完成！")
        
    except Exception as e:
        print(f"发生错误: {str(e)}")
        # 清理临时文件
        if os.path.exists("temp_assets"):
            shutil.rmtree("temp_assets")
        if os.path.exists(zip_file):
            os.remove(zip_file)

if __name__ == "__main__":
    setup_assets() 