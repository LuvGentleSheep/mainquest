import os
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
    project_path = input("请拖拽项目文件夹到此终端并按回车键: ").strip()
    update_gallery(project_path)