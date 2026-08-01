import os
import sys
import subprocess
import webbrowser
from PIL import Image
from datetime import datetime
from tqdm import tqdm
import socket


def get_lan_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"


def print_preview_urls(port, path=""):
    local_url = f"http://localhost:{port}{path}"
    lan_ip = get_lan_ip()
    lan_url = f"http://{lan_ip}:{port}{path}"
    print("本地服务器已启动，预览地址：")
    print(f"  - 本机: {local_url}")
    if lan_ip.startswith("127."):
        print("  - 局域网: 无法检测到有效的局域网 IP")
    else:
        print(f"  - 局域网: {lan_url}")

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
    output3 = f'<header class="banner">\n    <h1>{project_name}</h1>\n</header>\n<div class="gallery" id="gallery">\n'

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
        <link rel="apple-touch-icon" sizes="180x180" href="/homepage/favicon_io/apple-touch-icon.png">
        <link rel="icon" type="image/png" sizes="32x32" href="/homepage/favicon_io/favicon-32x32.png">
        <link rel="icon" type="image/png" sizes="16x16" href="/homepage/favicon_io/favicon-16x16.png">
        <link rel="icon" href="/homepage/favicon_io/favicon.ico">
        <link rel="manifest" href="/homepage/favicon_io/site.webmanifest">
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
                
                header.banner {
                        position: -webkit-sticky;
                        position: sticky;
                        top: 0;
                        height: 70px;
                        background: rgba(15, 15, 15, 0.8);
                        backdrop-filter: blur(20px) saturate(180%);
                        -webkit-backdrop-filter: blur(20px) saturate(180%);
                        border-bottom: 1px solid rgba(255, 255, 255, 0.12);
                        z-index: 1000; /* 确保header在最上层 */
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        padding: 0 32px;
                        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
                }

                header.banner h1 {
                        font-size: 22px;
                        font-weight: 700;
                        margin: 0;
                        background: linear-gradient(135deg, #ffffff 0%, rgba(255, 255, 255, 0.8) 100%);
                        -webkit-background-clip: text;
                        -webkit-text-fill-color: transparent;
                        background-clip: text;
                        letter-spacing: -0.5px;
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
    
            // 模态视图功能 - 使用与放映模式相同的加载逻辑
            const modal = document.getElementById("myModal");
            const span = document.getElementsByClassName("close")[0];
            let currentImageIndex = 0;
            let galleryImages = document.querySelectorAll('.gallery img');
            
            // 收集所有图片源（优先使用 data-src，如果没有则使用 src）- 与放映模式相同
            const srcList = [...galleryImages].map(img => img.dataset?.src || img.src);
            const cache = new Map();
            
            // 预加载函数 - 与放映模式相同
            const preload = (i) => {
                const src = srcList[i % srcList.length];
                if (cache.has(src)) return;
                const im = new Image();
                im.src = src;
                cache.set(src, im);
            };
    
            galleryImages.forEach((img, index) => {
                    img.onclick = function() {
                            showModal(img, index);
                    };
            });
    
        async function showModal(img, index) {
            currentImageIndex = index;
            const modalImg = document.getElementById("img01");
            const downloadLink = document.getElementById("downloadLink");
            
            // 获取图片源（优先使用 data-src）
            const currentSrc = img.dataset?.src || img.src;
            
            // 预加载当前图片
            preload(index);
            const imgObj = cache.get(currentSrc);
            
            // 等待图片加载完成（如果已加载则立即显示，否则等待）
            if (imgObj && imgObj.complete) {
                modalImg.src = currentSrc;
            } else if (imgObj) {
                await new Promise((resolve) => {
                    imgObj.onload = resolve;
                    imgObj.onerror = resolve; // 即使加载失败也继续
                });
                modalImg.src = currentSrc;
            } else {
                modalImg.src = currentSrc;
            }
            
            const highResSrc = currentSrc.replace('/background/', '/gallery/');
            modal.style.display = "flex";
            downloadLink.href = highResSrc;
            
            // 预加载前后各5张图片
            for (let i = index - 5; i <= index + 5; i++) {
                if (i >= 0 && i < srcList.length) {
                    preload(i);
                }
            }
        }
        
        async function updateModalImage() {
            const modalImg = document.getElementById("img01");
            const downloadLink = document.getElementById("downloadLink");
            const currentSrc = srcList[currentImageIndex];
            
            // 预加载当前图片
            preload(currentImageIndex);
            const imgObj = cache.get(currentSrc);
            
            // 等待图片加载完成
            if (imgObj && imgObj.complete) {
                modalImg.src = currentSrc;
            } else if (imgObj) {
                await new Promise((resolve) => {
                    imgObj.onload = resolve;
                    imgObj.onerror = resolve;
                });
                modalImg.src = currentSrc;
            } else {
                modalImg.src = currentSrc;
            }
            
            const highResSrc = currentSrc.replace('/background/', '/gallery/');
            downloadLink.href = highResSrc;
            
            // 预加载前后各3张图片（按需加载）
            for (let i = currentImageIndex - 3; i <= currentImageIndex + 3; i++) {
                const idx = (i + srcList.length) % srcList.length;
                preload(idx);
            }
        }
            document.querySelector('.prev').onclick = async () => {
                    currentImageIndex = (currentImageIndex - 1 + srcList.length) % srcList.length;
                    await updateModalImage();
            };
    
            document.querySelector('.next').onclick = async () => {
                    currentImageIndex = (currentImageIndex + 1) % srcList.length;
                    await updateModalImage();
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
    <!-- ========== 放映模式 MOD BEGIN (async-decode fixed) ========== -->
    <style>
    /* 按钮 */
    .slideshow-toggle{
        position:fixed;bottom:90px;left:50%;transform:translateX(-50%);
        padding:10px 24px;font-size:16px;border:2px solid #fff;border-radius:20px;
        background:rgba(0,0,0,.3);color:#fff;backdrop-filter:blur(10px);
        cursor:pointer;z-index:1200;transition:background .3s,color .3s;
    }
    .slideshow-toggle:hover{background:rgba(255,255,255,.25);}
    
    /* 模态整体：纯黑背景 + 淡入淡出 */
    .slideshow-modal{
        position:fixed;inset:0;z-index:4000;overflow:hidden;
        background:#000;opacity:0;visibility:hidden;pointer-events:none;
        transition:opacity .4s ease;
    }
    .slideshow-modal.open{
        opacity:1;visibility:visible;pointer-events:auto;
    }
    
    /* 高斯模糊背景：双层交叉淡切 */
    .slideshow-bg{
        position:absolute;inset:0;background-size:cover;background-position:center;
        filter:blur(30px);opacity:0;transition:opacity .75s ease-in-out;
    }
    .slideshow-bg.active{opacity:1;}
    
    /* 主图 */
    .slide-img{
        position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);
        max-width:90%;max-height:90%;object-fit:contain;border-radius:12px;
        box-shadow:0 0 25px rgba(0,0,0,.35);opacity:0;transition:opacity .75s ease-in-out;
    }
    .slide-img.active{opacity:1;}
    </style>
    
    <script>
    (function(){
        /* ——— 插入按钮 ——— */
        const btn=document.createElement('button');
        btn.className='slideshow-toggle';btn.textContent='放映模式';
        document.body.appendChild(btn);
    
        /* ——— 插入模态（双背景层） ——— */
        const modal=document.createElement('div');modal.className='slideshow-modal';
        modal.innerHTML=`<div id="bgA" class="slideshow-bg"></div>
                                            <div id="bgB" class="slideshow-bg"></div>
                                            <img id="imgA" class="slide-img" alt="">
                                            <img id="imgB" class="slide-img" alt="">`;
        document.body.appendChild(modal);
    
        /* ——— 收集数据 ——— */
        const srcList=[...document.querySelectorAll('#gallery img')].map(i=>i.dataset?.src||i.src);
        const cache=new Map();
        const preload=i=>{
                const src=srcList[i%srcList.length];
                if(cache.has(src)) return;
                const im=new Image(); im.src=src;
                cache.set(src,im);
        };
    
        /* ——— DOM 引用 / 状态 ——— */
        const bgA=document.getElementById('bgA'), bgB=document.getElementById('bgB');
        const imA=document.getElementById('imgA'), imB=document.getElementById('imgB');
        let cur=0,useA=true,useBgA=true,timer;
    
        /* ——— 异步切换函数：确保 decode 完成后再淡入 ——— */
        const crossfade = async nextIdx => {
            const newSrc = srcList[nextIdx];
            const newImg  = useA ? imB : imA;
            const oldImg  = useA ? imA : imB;
            const newBg   = useBgA ? bgB : bgA;
            const oldBg   = useBgA ? bgA : bgB;
    
            // 设置 src & 预解码
            newImg.src = newSrc;
            await (cache.get(newSrc)?.decode?.() ?? Promise.resolve());
    
            // 背景同理
            newBg.style.backgroundImage = `url('${newSrc}')`;
    
            // 交叉淡入淡出
            newImg.classList.add('active'); oldImg.classList.remove('active');
            newBg.classList.add('active');  oldBg.classList.remove('active');
    
            cur = nextIdx;
            useA = !useA; useBgA = !useBgA;
            preload(cur+1);                 // 继续预加载下一张
        };
    
        /* ——— 播放器节奏 ——— */
        const tick = async () => {
            const next=(cur+1)%srcList.length;
            const imgObj = cache.get(srcList[next]);
            if(imgObj && imgObj.complete){
                    await crossfade(next);
                    timer=setTimeout(tick,5000);
            }else{
                    timer=setTimeout(tick,300); // 等待资源完成
            }
        };
    
        /* ——— 全屏 ——— */
        const enterFullscreen = () => {
            const el = document.documentElement;
            const req = el.requestFullscreen?.() ?? el.webkitRequestFullscreen?.();
            if (req?.catch) req.catch(() => {});
        };
        const exitFullscreen = () => {
            if (!document.fullscreenElement && !document.webkitFullscreenElement) return;
            const ex = document.exitFullscreen?.() ?? document.webkitExitFullscreen?.();
            if (ex?.catch) ex.catch(() => {});
        };

        /* ——— 打开 / 关闭模态 ——— */
        const open = () => {
            if(!srcList.length) return;
            preload(0);
            const first = cache.get(srcList[0]);
            const start = async () => {
                await crossfade(0);
                modal.classList.add('open');
                document.body.style.overflow='hidden';
                enterFullscreen();
                timer=setTimeout(tick,5000);
            };
            first.complete ? start() : first.decode().then(start);
        };
        const close = () => {
            modal.classList.remove('open');
            document.body.style.overflow='auto';
            clearTimeout(timer);
            exitFullscreen();
        };

        document.addEventListener('fullscreenchange', () => {
            if (!document.fullscreenElement && modal.classList.contains('open')) close();
        });
        document.addEventListener('webkitfullscreenchange', () => {
            if (!document.webkitFullscreenElement && modal.classList.contains('open')) close();
        });
    
        /* ——— 事件绑定 ——— */
        btn.addEventListener('click',open);
        modal.addEventListener('click',close);
    })();
    </script>
    <!-- ========== 放映模式 MOD END (async-decode fixed) ========== -->
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
    safe_image_name = image_name.replace("\\ ", " ")
    safe_image_name = safe_image_name.replace(" ", "%20")
    # 获取本地时间并格式化
    local_tz = datetime.now().astimezone().tzinfo
    current_time = datetime.now().astimezone().strftime(f"%Y-%m-%d %H:%M:%S")
    
    # 生成 homepage_index.html 更新内容
    homepage_update = f"""
    <div class="update-item">
        <div class="update-image">
            <a href="../project/{project_name}/{project_name}_index.html" target="_blank" rel="noopener">
                <img class="lazy" data-src="../project/{project_name}/public/background/{safe_image_name}" loading="lazy" src="../project/{project_name}/public/background/{safe_image_name}" alt="更新图片">
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
    <div class="gallery-item clickable" data-link="../project/{project_name}/{project_name}_index.html" data-src="../project/{project_name}/public/background/{safe_image_name}">
        <a href="../project/{project_name}/{project_name}_index.html" target="_blank" rel="noopener">
            <div class="update-image">
                <img class="lazy" data-src="../project/{project_name}/public/background/{safe_image_name}" loading="lazy" src="../project/{project_name}/public/background/{safe_image_name}" alt="{title}">
            </div>
        </a>
        <div class="update-content">
            <div class="update-title">{title}</div>
        </div>
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
    # 获取并处理用户输入的项目路径
    raw_project_path = input("请拖拽项目文件夹到此终端并按回车键: ").strip()
    if os.name != 'nt':  # 针对 macOS/Linux
        processed_project_path = raw_project_path.replace("\\ ", " ")
    else:
        processed_project_path = raw_project_path
    project_path = os.path.normpath(processed_project_path)
    
    project_name = os.path.basename(project_path)
    compress_images(project_name)
    generate_texts(project_name)
    create_index_html(project_name)
    print(f"{project_name}_index.html 文件已生成。")
    
    title = input("请输入标题名称: ").strip()
    content = input("请输入正文内容: ").strip()
    
    # 构造 background 目录路径
    background_path = os.path.join(project_path, 'public', 'background')
    # 打开文件管理器并定位到指定目录
    if os.name == 'nt':  # Windows
        subprocess.Popen(f'explorer "{background_path}"')
    elif os.name == 'posix':  # macOS, Linux
        # macOS 上使用 'open'，Linux 可根据发行版改为 'xdg-open'
        subprocess.Popen(['open', background_path])
    
    image_path = input("请拖拽一张图片作为封面图: ").strip()
    image_name = os.path.basename(image_path)
    update_homepage_and_gallery(project_name, title, content, image_name)
    
    # 获取当前脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 端口
    port = "8000"
    
    # 检查端口是否被占用，如果是就杀掉占用该端口的进程
    def free_port(port):
        try:
            result = subprocess.run(["lsof", "-i", f":{port}"], capture_output=True, text=True)
            lines = result.stdout.strip().split("\n")
            if len(lines) > 1:
                for line in lines[1:]:
                    pid = line.split()[1]
                    print(f"关闭占用端口 {port} 的进程 PID: {pid}")
                    subprocess.run(["kill", "-9", pid])
        except Exception as e:
            print(f"释放端口失败: {e}")
            
    # 步骤 1：释放端口
    free_port(port)
    
    # 步骤 2：启动 HTTP 服务器
    server_process = subprocess.Popen([sys.executable, "-m", "http.server", port], cwd=script_dir)
    print_preview_urls(port)
    
    # 步骤 3：打开浏览器
    webbrowser.open(f"http://localhost:{port}")
    
