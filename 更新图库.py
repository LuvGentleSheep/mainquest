import os
import sys
import subprocess
import webbrowser
from PIL import Image
import re

def compress_image(input_path, output_path, target_size=(1800, 1200), quality=70):
    with Image.open(input_path) as img:
        img = img.convert("RGB")
        img.thumbnail(target_size)
        img.save(output_path, "JPEG", quality=quality)

def update_gallery(project_path):
    public_path = os.path.join(project_path, 'public')
    gallery_path = os.path.join(public_path, 'gallery')
    background_path = os.path.join(public_path, 'background')
    html_path = os.path.join(project_path, f"{os.path.basename(project_path)}_index.html")

    # 确保 background 目录存在
    os.makedirs(background_path, exist_ok=True)

    # 获取 gallery 和 background 中的图片文件名
    gallery_images = set(img for img in os.listdir(gallery_path) if img.lower().endswith(('png', 'jpg', 'jpeg')))
    background_images = set(img for img in os.listdir(background_path) if img.lower().endswith(('png', 'jpg', 'jpeg')))

    # 添加新的压缩图像到 background
    for img_name in gallery_images - background_images:
        input_img_path = os.path.join(gallery_path, img_name)
        output_img_path = os.path.join(background_path, img_name)
        compress_image(input_img_path, output_img_path)
        print(f"Compressed and added: {img_name}")

    # 删除 background 中多余的图像
    for img_name in background_images - gallery_images:
        os.remove(os.path.join(background_path, img_name))
        print(f"Deleted from background: {img_name}")

    # 更新 HTML 文件
    with open(html_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # 正则表达式来查找并替换背景幻灯片和图库部分
    background_slideshow_code = '<div class="background-slideshow" id="background-slideshow">\n'
    for i, img_name in enumerate(sorted(gallery_images)):
        background_slideshow_code += f'  <img class="lazy" data-src="./public/background/{img_name}" alt="背景图片{i + 1}">\n'
    background_slideshow_code += '</div>'

    gallery_code = '<div class="gallery" id="gallery">\n'
    for i, img_name in enumerate(sorted(gallery_images)):
        gallery_code += f'  <img class="lazy" data-src="./public/background/{img_name}" alt="背景图片{i + 1}">\n'
    gallery_code += '</div>'

    # 使用正则表达式替换 HTML 中的内容
    html_content = re.sub(
        r'<div class="background-slideshow" id="background-slideshow">.*?</div>',
        background_slideshow_code,
        html_content,
        flags=re.DOTALL
    )
    html_content = re.sub(
        r'<div class="gallery" id="gallery">.*?</div>',
        gallery_code,
        html_content,
        flags=re.DOTALL
    )

    # 将修改后的内容写回 HTML 文件
    with open(html_path, 'w', encoding='utf-8') as file:
        file.write(html_content)

    print(f"HTML updated in {html_path}")

if __name__ == "__main__":
    # 自动打开与脚本同目录下的 project 文件夹
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_folder = os.path.join(current_dir, "project")
    
    if os.path.isdir(project_folder):
        if sys.platform.startswith("darwin"):  # macOS
            subprocess.Popen(["open", project_folder])
        elif sys.platform.startswith("win"):
            os.startfile(project_folder)
        elif sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", project_folder])
        else:
            print("当前系统不支持自动打开文件夹功能。")
    else:
        print("没有找到 'project' 文件夹，请检查文件目录。")
    
    # 获取用户输入，并对路径进行预处理（针对非 Windows 系统去除用于转义空格的反斜杠）
    raw_input_path = input("请拖拽项目文件夹到此终端并按回车键: ").strip()
    if not sys.platform.startswith("win"):
        # 将 "\ " 替换为空格，去除不必要的反斜杠
        processed_path = raw_input_path.replace("\\ ", " ")
    else:
        processed_path = raw_input_path
    project_path = os.path.normpath(processed_path)
    
    update_gallery(project_path)
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 启动本地 HTTP 服务器，并在默认浏览器中打开 http://localhost:8000
    # 这里设置工作目录为脚本所在目录，即包含 index.html 的目录
    server_process = subprocess.Popen([sys.executable, "-m", "http.server", "8000"], cwd=script_dir)
    print("HTTP 服务器已启动，访问地址： http://localhost:8000")
    
    # 打开默认浏览器访问本地服务器
    webbrowser.open("http://localhost:8000")