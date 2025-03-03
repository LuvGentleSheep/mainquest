import os
import sys
import subprocess
from PIL import Image
from datetime import datetime
from tqdm import tqdm

def compress_images(project_name, target_size=(1800, 1200)):
    gallery_path = os.path.join('project', project_name, 'public', 'gallery')
    background_path = os.path.join('project', project_name, 'public', 'background')
    
    # 确保 background 目录存在
    os.makedirs(background_path, exist_ok=True)
    
    image_files = sorted([img for img in os.listdir(gallery_path) if img.lower().endswith(('png', 'jpg', 'jpeg'))])
    
    with tqdm(total=len(image_files), desc="Compressing images") as pbar:
        for img_name in image_files:
            img_path = os.path.join(gallery_path, img_name)
            img = Image.open(img_path)
            img = img.convert("RGB")  # 保证是RGB模式
            img.thumbnail(target_size)
            output_path = os.path.join(background_path, img_name)
            img.save(output_path, "JPEG", quality=70,icc_profile=img.info.get('icc_profile'))
#           print(f"Compressed {img_name} to {output_path}")
            pbar.update(1)

def generate_texts(project_name):
    gallery_path = os.path.join('project', project_name, 'public', 'gallery')
    background_path = os.path.join('project', project_name, 'public', 'background')

    # 获取 gallery 和 background 中的图片文件名，并按名称排序

    background_images = sorted([img for img in os.listdir(background_path) if img.lower().endswith(('png', 'jpg', 'jpeg'))])

    # 生成文本输出
    output1 = f"<title>{project_name}</title>"
    
    output2 = ''
    for i, img in enumerate(background_images):
        output2 += f'  <img class="lazy" data-src="./public/background/{img}" alt="背景图片{i+1}">\n'
    output2 += '</div>'
    output3 = f'<header>\n    <h1>{project_name}</h1>\n</header>\n<div class="gallery" id="gallery">\n'

    # 保存输出到文本文件
    with open(os.path.join('project', project_name, 'output1.txt'), 'w', encoding='utf-8') as f:
        f.write(output1)
    
    with open(os.path.join('project', project_name, 'output2.txt'), 'w', encoding='utf-8') as f:
        f.write(output2)
    
    with open(os.path.join('project', project_name, 'output3.txt'), 'w', encoding='utf-8') as f:
        f.write(output3)

def create_index_html(project_name):
    file1_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    """
    file2_content = """
        <style>
                body, html {
                        margin: 0;
                        padding: 0;
                        height: 100%;
                        font-family: Arial, sans-serif;
                        background-color: #f5f5f5;
                        color: #333;
                        overflow: auto;
                }
                
                /* 背景图片幻灯片效果 */
                .background-slideshow {
                        position: fixed;
                        top: 0;
                        left: 0;
                        width: 100%;
                        height: 100%;
                        overflow: hidden;
                        z-index: 0;
                }
                
                .background-slideshow img {
                        position: absolute;
                        width: 100%;
                        height: 100%;
                        object-fit: cover; /* 保持背景图片比例裁切 */
                        filter: blur(50px);
                        opacity: 0; /* 初始状态下图片是透明的 */
                        transition: opacity 2s ease-in-out; /* 平滑过渡效果 */
                }
                
                .background-slideshow img.active {
                        opacity: 1; /* 将当前显示的图片的透明度设置为1，使其可见 */
                }
                
                header {
                        position: -webkit-sticky;
                        position: sticky;
                        top: 0;
                        background-color: rgba(0, 0, 0, 0.7); /* 半透明黑色背景 */
                        color: #fff; /* 白色字体 */
                        padding: 1rem;
                        text-align: center;
                        z-index: 1000; /* 确保header在最上层 */
                        -webkit-backdrop-filter: blur(10px); /* 高斯模糊效果 */
                        backdrop-filter: blur(10px);
                }
                
                .gallery {
                        display: flex;
                        flex-wrap: wrap; /* 允许换行 */
                        justify-content: center;
                        gap: 1rem; /* 默认间距 */
                        padding: 1rem;
                        padding-bottom: 3rem; /* 设置与 footer 的距离 */
                        position: relative;
                        z-index: 1;
                        max-width: 1000px; /* 固定瀑布流宽度 */
                        margin: 1rem auto 3rem auto; /* 居中对齐，并设置顶部底部边距 */
                }
                
                /* 当页面宽度大于1000px时，设置gap为1.5rem */
                @media (min-width: 1000px) {
                        .gallery {
                                gap: 1.5rem;
                        }
                }        
                .gallery img {
                        flex: 1 1 calc(50% - 1rem); /* 每个图片占据两列中的一列 */
                        max-width: calc(50% - 1rem);
                        aspect-ratio: 4 / 3;
                        height: auto;
                        object-fit: cover; /* 保持比例裁剪 */
                        margin-bottom: 0rem;
                        transition: transform 0.3s, box-shadow 0.3s;
                        box-shadow: 0 0 15px rgba(0,0,0,0.1);
                        cursor: pointer;
                        border-radius: 15px; /* 圆角矩形效果 */
                }
                
                .gallery img:hover {
                        transform: scale(1.05);
                        box-shadow: 0 0 30px 10px rgba(255, 255, 255, 0.8);
                }
                
                footer {
                        background-color: rgba(0, 0, 0, 0.7);
                        color: #fff;
                        text-align: center;
                        padding: 1rem;
                        position: fixed;
                        bottom: 0;
                        width: 100%;
                        z-index: 1000; /* 确保footer在最上层 */
                        -webkit-backdrop-filter: blur(10px); /* 高斯模糊效果 */
                        backdrop-filter: blur(10px);
                }
                
                .social-links a {
                        margin: 0 0.5rem;
                        color: #fff;
                        text-decoration: none;
                }
                
                .social-links a:hover {
                        text-decoration: underline;
                }
                
                /* 模态视图 */
                .modal {
                        display: none;
                        position: fixed;
                        z-index: 2000; /* 确保模态视图在最上层 */
                        left: 0;
                        top: 0;
                        width: 100%;
                        height: 100%;
                        overflow: auto;
                        background-color: rgba(0, 0, 0, 0.9);
                        backdrop-filter: blur(5px);
                        justify-content: center;
                        align-items: center; /* 上下居中对齐 */
                }
                
                .modal-content {
                        margin: auto;
                        display: block;
                        width: auto;
                        height: auto;
                        max-width: 100%;
                        max-height: 100%;
                }
                
                .modal-content.zoomed {
                        transform: scale(2); /* 调整缩放比例 */
                        cursor: zoom-out;
                }
                
                .close {
                        position: absolute;
                        bottom: 30px;
                        right: 35px;
                        color: #f1f1f1;
                        font-size: 40px;
                        font-weight: bold;
                        transition: 0.3s;
                }
                
                .close:hover,
                .close:focus {
                        color: #bbb;
                        text-decoration: none;
                        cursor: pointer;
                }
                .prev {
                        position: absolute;
                        bottom: 30px;
                        left: 50%; /* 水平居中 */
                        transform: translateX(-50%) translateX(-30px);
                        color: #f1f1f1;
                        font-size: 40px;
                        font-weight: bold;
                        transition: 0.3s;
                }
                .prev:hover,
                .prev:focus {
                        color: #bbb;
                        text-decoration: none;
                        cursor: pointer;
                }
                .next {
                        position: absolute;
                        bottom: 30px;
                        left: 50%; /* 水平居中 */
                        transform: translateX(-50%) translateX(30px); /* 水平居中后向右偏移 20px */
                        color: #f1f1f1;
                        font-size: 40px;
                        font-weight: bold;
                        transition: 0.3s;
                }
                .next:hover,
                .next:focus {
                        color: #bbb;
                        text-decoration: none;
                        cursor: pointer;
                }
                .download-btn {
                    position: absolute;
                    bottom: 90px;
                    right: 35px;
                    background-color: rgba(0, 0, 0, 0.3); /* 半透明黑色背景 */
                    -webkit-backdrop-filter: blur(10px); /* 高斯模糊效果 */
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    font-size: 15px;
                    font-weight: bold;
                    cursor: pointer;
                    border-radius: 15px;
                    transition: background-color 0.3s ease;
                    text-decoration: none;
                }
                
                .download-btn:hover {
                    background-color: #45a049;
                }
            
                
        </style>
</head>
<body>

<!-- 背景图片幻灯片 -->
<div class="background-slideshow" id="background-slideshow">

    """
    file3_content = """
    <!-- 模态视图 -->
    <div id="myModal" class="modal">
            <span class="close">&times;</span>
            <span class="prev">&#10094;</span>
            <span class="next">&#10095;</span>
            <img class="modal-content" id="img01">
            <a id="downloadLink" class="download-btn" href="#" target="_blank" download>下载原图</a>
    </div>
    
    <footer>
            <div class="social-links">
                    <a href="https://weibo.com/5707972729" target="_blank">欢迎来看我的微博 🎉</a>
                    <a href="https://space.bilibili.com/7684674" target="_blank">以及B站 📺</a>
            </div>
    </footer>
    
    <script>
            // 幻灯片切换功能
            function startSlideshow() {
                    let currentIndex = 0;
                    const slides = document.querySelectorAll('.background-slideshow img');
                    const totalSlides = slides.length;
    
                    slides[currentIndex].classList.add('active');
    
                    setInterval(() => {
                            slides[currentIndex].classList.remove('active');
                            currentIndex = (currentIndex + 1) % totalSlides;
                            slides[currentIndex].classList.add('active');
                    }, 7000); // 切换间隔时间为7秒，其中2秒用于渐变，5秒显示图片
            }
    
            startSlideshow();
    
            // 模态视图功能
            const modal = document.getElementById("myModal");
            const span = document.getElementsByClassName("close")[0];
            let currentImageIndex = 0;
            let galleryImages = document.querySelectorAll('.gallery img');
    
            galleryImages.forEach((img, index) => {
                    img.onclick = function() {
                            showModal(img, index);
                    };
            });
    
        function showModal(img, index) {
            currentImageIndex = index;
            const modalImg = document.getElementById("img01");
            const downloadLink = document.getElementById("downloadLink");
            const highResSrc = img.src.replace('/background/', '/gallery/');
            modal.style.display = "flex";
            modalImg.src = img.src;
            downloadLink.href = highResSrc;
        }
        
        function updateModalImage() {
            const modalImg = document.getElementById("img01");
            const downloadLink = document.getElementById("downloadLink");
            const currentImg = galleryImages[currentImageIndex];
            const highResSrc = currentImg.src.replace('/background/', '/gallery/');
            modalImg.src = currentImg.src;
            downloadLink.href = highResSrc;
        }
            document.querySelector('.prev').onclick = () => {
                    currentImageIndex = (currentImageIndex - 1 + galleryImages.length) % galleryImages.length;
                    updateModalImage();
            };
    
            document.querySelector('.next').onclick = () => {
                    currentImageIndex = (currentImageIndex + 1) % galleryImages.length;
                    updateModalImage();
            };
    
            span.onclick = function() {
                    modal.style.display = "none";
            };
    
            window.onclick = function(event) {
                    if (event.target === modal) {
                            modal.style.display = "none";
                    }
            };
        document.addEventListener("DOMContentLoaded", function() {
            const lazyImages = document.querySelectorAll('img.lazy');
        
            const lazyLoad = function(entries, observer) {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        let img = entry.target;
                        img.src = img.dataset.src;
                        img.onload = () => {
                            img.classList.add('loaded');
                        }
                        observer.unobserve(img);
                    }
                });
            }
        
            const observer = new IntersectionObserver(lazyLoad);
        
            lazyImages.forEach(img => {
                observer.observe(img);
            });
        });
    </script>
    </body>
    </html>
    """
    output1_path = os.path.join('project', project_name, 'output1.txt')
    output2_path = os.path.join('project', project_name, 'output2.txt')
    output3_path = os.path.join('project', project_name, 'output3.txt')
    index_html_path = os.path.join(f"./project/{project_name}/{project_name}_index.html")
    
    # 读取所有文件的内容

    with open(output1_path, 'r', encoding='utf-8') as f:
        output1_content = f.read()
    with open(output2_path, 'r', encoding='utf-8') as f:
        output2_content = f.read()
    with open(output3_path, 'r', encoding='utf-8') as f:
        output3_content = f.read()

    
    # 按照指定顺序组合内容
    combined_content = (
        file1_content + '\n' +
        output1_content + '\n' +
        file2_content + '\n' +
        output2_content + '\n' +
        output3_content + '\n' +
        output2_content + '\n' +
        file3_content
    )
    
    # 写入 index.html 文件
    with open(index_html_path, 'w', encoding='utf-8') as f:
        f.write(combined_content)
        
    # 删除临时文件
        os.remove(output1_path)
        os.remove(output2_path)
        os.remove(output3_path)
        print("临时文件已删除。")
        
def update_homepage_and_gallery(project_name, title, content, image_name):
    # 获取本地时间并格式化
    local_tz = datetime.now().astimezone().tzinfo
    current_time = datetime.now().astimezone().strftime(f"%Y-%m-%d %H:%M:%S")
    
    # 生成 homepage_index.html 更新内容
    homepage_update = f"""
    <div class="update-item">
        <div class="update-image">
            <a href="../project/{project_name}/{project_name}_index.html">
                <img class="lazy" data-src="../project/{project_name}/public/background/{image_name}" alt="更新图片">
                <div class="image-title"></div>
            </a>
        </div>
        <div class="update-content">
            <div class="update-title">{title}</div>
            <div class="update-main clickable">
                <p>{content}</p>
            </div>
            <div class="update-time">{current_time}</div>
        </div>
    </div>
    """
    
    # 生成 gallery.html 更新内容
    gallery_update = f"""
    <div class="gallery-item clickable" data-link="../project/{project_name}/{project_name}_index.html" data-src="../project/{project_name}/public/background/{image_name}">
        <h3>{title}</h3>
        <p>{content}</p>
    </div>
    """
    
    # 更新 homepage_index.html
    homepage_index_path = './homepage/recent-updates.html'
    with open(homepage_index_path, 'r+', encoding='utf-8') as file:
        content = file.read()
        insert_position = content.find('<div class="update-container">') + len('<div class="update-container">')
        updated_content = content[:insert_position] + homepage_update + content[insert_position:]
        file.seek(0)
        file.write(updated_content)
        file.truncate()
        
    # 更新 gallery.html
    gallery_path = './homepage/gallery.html'
    with open(gallery_path, 'r+', encoding='utf-8') as file:
        content = file.read()
        insert_position = content.find('<div class="gallery-row">') + len('<div class="gallery-row">')
        updated_content = content[:insert_position] + gallery_update + content[insert_position:]
        file.seek(0)
        file.write(updated_content)
        file.truncate()
        
    print("recent-updates.html 和 gallery.html 已更新。")
    
if __name__ == "__main__":
    project_path = input("请拖拽项目文件夹到此终端并按回车键: ").strip()
    project_name = os.path.basename(os.path.normpath(project_path))
    compress_images(project_name)
    generate_texts(project_name)
    create_index_html(project_name)
    print(f"{project_name}_index.html 文件已生成。")
    
    title = input("请输入标题名称: ").strip()
    content = input("请输入正文内容: ").strip()
    
    # 打开文件管理器并定位到指定目录
    background_path = os.path.join(project_path, 'public', 'background')
    if os.name == 'nt':  # Windows
        subprocess.Popen(f'explorer "{background_path}"')
    elif os.name == 'posix':  # macOS, Linux
        subprocess.Popen(['open', background_path])
    
    image_path = input("请拖拽一张图片作为封面图: ").strip()
    image_name = os.path.basename(image_path)
    update_homepage_and_gallery(project_name, title, content, image_name)