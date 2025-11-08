function toggleSidebar() {
    const sidebar = document.querySelector('nav.sidebar');
    const toggleButton = document.querySelector('.toggle-sidebar');
    sidebar.classList.toggle('hidden');
    // if (sidebar.classList.contains('hidden')) {
    //     toggleButton.style.left = '180px';
    // } else {
    //     toggleButton.style.left = '20px';
    // }
}

function changeContent(section) {
    const cacheBuster = Date.now();
    const url = `${section}.html?ts=${cacheBuster}`;
    
    fetch(url, { cache: "no-store" })
        .then(response => {
            if (!response.ok) {
                throw new Error(`加载 ${section}.html 失败（${response.status}）`);
            }
            return response.text();
        })
        .then(data => {
            const parser = new DOMParser();
            const doc = parser.parseFromString(data, 'text/html');
            const content = document.getElementById('content');
            let newSection = doc.querySelector('section');
            
            content.innerHTML = '';
            if (newSection) {
                content.appendChild(newSection);
            } else {
                content.innerHTML = data;
                newSection = content.querySelector('section');
            }
            
            if (!newSection) {
                content.innerHTML = `
                    <section class="section-error">
                        <h2>内容加载失败</h2>
                        <p>未在 ${section}.html 中找到 &lt;section&gt; 元素。</p>
                    </section>`;
                return;
            }
            
            initContent();
        })
        .catch(error => {
            const content = document.getElementById('content');
            content.innerHTML = `
                <section class="section-error">
                    <h2>内容加载失败</h2>
                    <p>${error.message}</p>
                </section>`;
            console.error(error);
        });
    // 隐藏 sidebar 并移动 toggle
    const sidebar = document.querySelector('nav.sidebar');
    const toggleButton = document.querySelector('.toggle-sidebar');
    sidebar.classList.remove('hidden');
    toggleButton.style.left = '20px';
}

function initContent() {
    // 初始化动态内容的事件监听器

    // 处理 update-main 点击事件
    document.querySelectorAll('.update-main').forEach(item => {
        item.addEventListener('click', function(event) {
            event.stopPropagation(); // 阻止事件冒泡
            const modal = document.getElementById('modal');
            const modalText = document.getElementById('modal-text');
            modalText.innerHTML = this.querySelector('p').innerHTML; // 使用 innerHTML 保留回车符
            modal.style.display = 'block';
        });
    });
    
    // 处理 gallery-item h3 点击事件
    document.querySelectorAll('.gallery-item h3').forEach(item => {
        item.addEventListener('click', function(event) {
            event.preventDefault(); // 阻止默认事件
            event.stopPropagation(); // 阻止事件冒泡
            const modal = document.getElementById('modal');
            const modalText = document.getElementById('modal-text');
            const galleryItem = this.closest('.gallery-item'); // 找到最近的 .gallery-item 元素
            const pText = galleryItem.querySelector('p').innerHTML; // 获取 .gallery-item 内 p 标签的文本内容
            modalText.textContent = pText; // 显示 p 标签的内容在模态窗口中
            modal.style.display = 'block';
        });
    });

    // 更新 update-item 的标题和添加点击事件
    document.querySelectorAll('.update-item').forEach(item => {
        const titleText = item.querySelector('.update-title').textContent;
        const imageTitle = item.querySelector('.image-title');
        const mainContent = item.querySelector('.update-main p').innerHTML;
        
        // 更新 image-title 的文本
        imageTitle.textContent = titleText; 
        
        // 添加点击事件监听
        imageTitle.addEventListener('click', function(event) {
            event.preventDefault(); // 阻止默认链接跳转
            event.stopPropagation(); // 阻止事件冒泡
            const modal = document.getElementById('modal');
            const modalText = document.getElementById('modal-text');
            modalText.innerHTML = mainContent; // 在模态视图中显示 main 内容
            modal.style.display = 'block';
        });
    });

    // 处理 clickable 元素的点击事件
    document.querySelectorAll('.clickable').forEach(item => {
        item.addEventListener('click', function(event) {
            const link = this.getAttribute('data-link');
            if (link) {
                window.location.href = link;
            } else {
                // 如果没有 data-link 属性，则不进行重定向
                event.preventDefault();
                const modal = document.getElementById('modal');
                const modalText = document.getElementById('modal-text');
                modalText.innerHTML = this.querySelector('p').innerHTML; // 使用 innerHTML 保留回车符
                modal.style.display = 'block';
            }
        });
    });
    // 重新初始化懒加载
    const lazyElements = document.querySelectorAll('.lazy, .gallery-item');
    
    const lazyLoad = function(entries, observer) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                let element = entry.target;
                
                if (element.tagName === 'IMG') {
                    element.src = element.dataset.src;
                    element.onload = () => {
                        element.classList.add('loaded');
                    }
                } else if (element.classList.contains('gallery-item')) {
                    element.style.backgroundImage = `url(${element.dataset.src})`;
                    element.classList.add('loaded');
                }
                
                observer.unobserve(element);
            }
        });
    }
    
    const observer = new IntersectionObserver(lazyLoad, {
        rootMargin: "0px 0px 200px 0px",
        threshold: 0.1
    });
    
    lazyElements.forEach(element => {
        observer.observe(element);
        console.log('Observing element:', element.dataset.src); // 调试输出
    });
}

document.addEventListener("DOMContentLoaded", function() {
    initContent();
    setTimeout(startSlideshow, 500);
    changeContent('recent-updates');
    // 模态窗口点击事件，点击关闭模态窗口
    document.getElementById('modal').addEventListener('click', function() {
        this.style.display = 'none';
    });

    // 懒加载
    const lazyElements = document.querySelectorAll('.lazy, .gallery-item');
    
    const lazyLoad = function(entries, observer) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                let element = entry.target;
                
                if (element.tagName === 'IMG') {
                    element.src = element.dataset.src;
                    element.onload = () => {
                        element.classList.add('loaded');
                    }
                } else if (element.classList.contains('gallery-item')) {
                    element.style.backgroundImage = `url(${element.dataset.src})`;
                    element.classList.add('loaded');
                }
                
                observer.unobserve(element);
            }
        });
    }
    
    const observer = new IntersectionObserver(lazyLoad, {
        rootMargin: "0px 0px 200px 0px",
        threshold: 0.1
    });
    
    lazyElements.forEach(element => {
        observer.observe(element);
        console.log('Observing element:', element.dataset.src); // 调试输出
    });
    
});

function startSlideshow() {
    let currentIndex = 0;
    const slides = document.querySelectorAll('.background-slideshow img');
    const totalSlides = slides.length;
    
    slides[currentIndex].classList.add('active');
    
    setInterval(() => {
        slides[currentIndex].classList.remove('active');
        currentIndex = (currentIndex + 1) % totalSlides;
        slides[currentIndex].classList.add('active');
    }, 12000); // 切换间隔时间为12秒，其中2秒用于渐变，10秒显示图片
}
