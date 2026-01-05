function toggleSidebar() {
    const sidebar = document.querySelector('nav.sidebar');
    const toggleButton = document.querySelector('.toggle-sidebar');
    if (window.innerWidth <= 768) {
        sidebar.classList.toggle('hidden');
    }
    toggleButton.classList.toggle('active');
}

// 滚动位置管理
const scrollPositions = new Map(); // 存储每个页面的滚动位置（内存中）
let currentSection = null; // 当前页面标识
let isReturningFromSubpage = false; // 标记是否从子页面返回

// 更新底部导航栏的激活状态
function updateBottomNavActive(section) {
    const bottomNavLinks = document.querySelectorAll('.bottom-nav-link');
    bottomNavLinks.forEach(link => {
        if (link.getAttribute('data-section') === section) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

function changeContent(section, isInitialLoad = false) {
    const cacheBuster = Date.now();
    const url = `${section}.html?ts=${cacheBuster}`;
    const content = document.getElementById('content');
    const contentWrapper = document.querySelector('.content-wrapper');
    
    // 如果不是初始加载，保存当前页面的滚动位置
    if (!isInitialLoad && currentSection && contentWrapper) {
        scrollPositions.set(currentSection, contentWrapper.scrollTop);
    }
    
    // 如果不是初始加载，添加淡出动画
    if (!isInitialLoad && content.innerHTML.trim() !== '') {
        content.style.opacity = '0';
        content.style.transform = 'translateX(-30px)';
        content.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    } else if (isInitialLoad && content.innerHTML.trim() === '') {
        // 初始加载时，如果内容为空，设置初始状态
        content.style.opacity = '0';
        content.style.transform = 'translateX(50px)';
        content.style.transition = 'none';
    }
    
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
            let newSection = doc.querySelector('section');
            
            // 更新内容的函数
            const updateContent = () => {
                // 先清空内容
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
                    // 重置样式并显示错误内容
                    content.style.opacity = '1';
                    content.style.transform = 'translateX(0)';
                    content.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                    return;
                }
                
                // 添加滑入动画 - 使用内联样式确保所有浏览器兼容
                if (isInitialLoad) {
                    // 初始加载时：确保初始状态已设置（在函数开始时已设置）
                    // 使用 setTimeout 确保 DOM 已渲染
                    setTimeout(() => {
                        // 强制浏览器重排，确保初始样式已应用
                        void content.offsetHeight;
                        
                        // 触发滑入动画
                        content.style.transition = 'opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1), transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
                        content.style.opacity = '1';
                        content.style.transform = 'translateX(0)';
                        
                        // 动画完成后确保内容保持可见
                        setTimeout(() => {
                            content.style.opacity = '1';
                            content.style.transform = 'translateX(0)';
                        }, 600);
                    }, 50);
                } else {
                    // 切换页面时：使用内联样式实现动画
                    // 先移除可能存在的动画类
                    content.classList.remove('slide-in');
                    
                    // 设置初始状态（确保从右侧滑入）
                    content.style.opacity = '0';
                    content.style.transform = 'translateX(50px)';
                    content.style.transition = 'none';
                    
                    // 使用 setTimeout 确保浏览器已应用初始样式
                    setTimeout(() => {
                        // 强制浏览器重排，确保初始样式已应用
                        void content.offsetHeight;
                        
                        // 触发滑入动画（使用内联样式，不依赖 CSS 类）
                        content.style.transition = 'opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1), transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
                        content.style.opacity = '1';
                        content.style.transform = 'translateX(0)';
                        
                        // 动画完成后确保内容保持可见
                        setTimeout(() => {
                            content.style.opacity = '1';
                            content.style.transform = 'translateX(0)';
                        }, 600);
                    }, 10);
                }
                
                // 初始化内容并触发元素浮现动画
                initContent();
                
                // 更新当前页面标识
                currentSection = section;
                
                // 更新底部导航栏的激活状态
                updateBottomNavActive(section);
                
                // 检查是否从子页面返回（通过 sessionStorage 检测）
                const savedScrollPos = sessionStorage.getItem(`scroll_${section}`);
                if (savedScrollPos !== null && contentWrapper && isReturningFromSubpage) {
                    // 从子页面返回，恢复滚动位置
                    setTimeout(() => {
                        contentWrapper.scrollTop = parseInt(savedScrollPos, 10);
                        // 清除保存的位置和标记，以便下次切换页面时从顶部开始
                        sessionStorage.removeItem(`scroll_${section}`);
                        isReturningFromSubpage = false;
                    }, 300); // 延迟更久，确保内容已完全加载
                } else if (contentWrapper) {
                    // 正常切换页面，重置滚动位置到顶部
                    setTimeout(() => {
                        contentWrapper.scrollTop = 0;
                    }, 100);
                }
            };
            
            // 如果不是初始加载，等待淡出动画完成
            if (!isInitialLoad && content.innerHTML.trim() !== '') {
                setTimeout(updateContent, 300);
            } else {
                updateContent();
            }
        })
        .catch(error => {
            const content = document.getElementById('content');
            content.innerHTML = `
                <section class="section-error">
                    <h2>内容加载失败</h2>
                    <p>${error.message}</p>
                </section>`;
            content.style.opacity = '1';
            content.style.transform = 'translateX(0)';
            content.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
            console.error(error);
        });
    
    // 移动端：点击后自动收起菜单
    if (window.innerWidth <= 768) {
        const sidebar = document.querySelector('nav.sidebar');
        const toggleButton = document.querySelector('.toggle-sidebar');
        sidebar.classList.add('hidden');
        toggleButton.classList.remove('active');
    }
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
    
    // 处理 gallery-item 标题点击事件
    document.querySelectorAll('.gallery-item .update-title').forEach(item => {
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
    document.querySelectorAll('.update-item').forEach((item, index) => {
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
        
        // 添加逐个浮现动画
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
            item.style.transition = 'opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1), transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
        }, 100 + index * 100); // 每个元素延迟 100ms
    });

    // 处理 clickable 元素的点击事件
    document.querySelectorAll('.clickable').forEach(item => {
        item.addEventListener('click', function(event) {
            const link = this.getAttribute('data-link');
            if (link) {
                // 保存当前页面的滚动位置（进入子页面时）
                const contentWrapper = document.querySelector('.content-wrapper');
                if (contentWrapper && currentSection) {
                    scrollPositions.set(currentSection, contentWrapper.scrollTop);
                    // 使用 sessionStorage 持久化，以便从子页面返回时恢复
                    sessionStorage.setItem(`scroll_${currentSection}`, contentWrapper.scrollTop.toString());
                }
                window.open(link, '_blank', 'noopener');
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
    
    // 为画廊项目添加逐个浮现动画
    document.querySelectorAll('.gallery-item').forEach((item, index) => {
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
            item.style.transition = 'opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1), transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
        }, 150 + index * 80); // 每个元素延迟 80ms
    });
    
    // 为日志条目添加逐个浮现动画
    document.querySelectorAll('.journal-entry').forEach((item, index) => {
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
            item.style.transition = 'opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1), transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
        }, 100 + index * 100); // 每个元素延迟 100ms
    });
    
    // 为关于页面的列表项添加逐个浮现动画
    document.querySelectorAll('#about ul li').forEach((item, index) => {
        setTimeout(() => {
            item.style.opacity = '1';
            item.style.transform = 'translateX(0)';
            item.style.transition = 'opacity 0.6s cubic-bezier(0.4, 0, 0.2, 1), transform 0.6s cubic-bezier(0.4, 0, 0.2, 1)';
        }, 100 + index * 80); // 每个元素延迟 80ms
    });
    
    // 初始化时设置初始状态
    document.querySelectorAll('#about ul li').forEach(item => {
        item.style.opacity = '0';
        item.style.transform = 'translateX(-20px)';
    });
    
    // 重新初始化懒加载
    const lazyElements = document.querySelectorAll('.lazy');
    
    const lazyLoad = function(entries, observer) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                let element = entry.target;
                
                if (element.tagName === 'IMG') {
                    element.onload = () => {
                        element.classList.add('loaded');
                    };
                    element.src = element.dataset.src;
                    if (element.complete) {
                        element.classList.add('loaded');
                    }
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
    setTimeout(startSlideshow, 500);
    
    // 模态窗口点击事件，点击关闭模态窗口
    document.getElementById('modal').addEventListener('click', function() {
        this.style.display = 'none';
    });
    
    // 检测是否从子页面返回（使用 pageshow 事件）
    window.addEventListener('pageshow', function(event) {
        // 如果页面从缓存中恢复（比如从子页面返回）
        if (event.persisted) {
            // 设置标记，表示从子页面返回
            isReturningFromSubpage = true;
            // 延迟一下，确保页面已完全加载
            setTimeout(() => {
                const contentWrapper = document.querySelector('.content-wrapper');
                if (contentWrapper && currentSection) {
                    const savedScrollPos = sessionStorage.getItem(`scroll_${currentSection}`);
                    if (savedScrollPos !== null) {
                        contentWrapper.scrollTop = parseInt(savedScrollPos, 10);
                        // 清除保存的位置和标记
                        sessionStorage.removeItem(`scroll_${currentSection}`);
                        isReturningFromSubpage = false;
                    }
                }
            }, 300);
        }
    });
    
    // 也监听 popstate 事件（浏览器后退/前进）
    window.addEventListener('popstate', function(event) {
        // 设置标记，表示从子页面返回
        isReturningFromSubpage = true;
        // 延迟一下，确保页面已完全加载
        setTimeout(() => {
            const contentWrapper = document.querySelector('.content-wrapper');
            if (contentWrapper && currentSection) {
                const savedScrollPos = sessionStorage.getItem(`scroll_${currentSection}`);
                if (savedScrollPos !== null) {
                    contentWrapper.scrollTop = parseInt(savedScrollPos, 10);
                    // 清除保存的位置和标记
                    sessionStorage.removeItem(`scroll_${currentSection}`);
                    isReturningFromSubpage = false;
                }
            }
        }, 300);
    });
    
    // 初始加载内容，传入 isInitialLoad 参数
    changeContent('recent-updates', true);
    
    // 初始化底部导航栏激活状态
    updateBottomNavActive('recent-updates');

    // 懒加载
    const lazyElements = document.querySelectorAll('.lazy');
    
    const lazyLoad = function(entries, observer) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                let element = entry.target;
                
                if (element.tagName === 'IMG') {
                    element.onload = () => {
                        element.classList.add('loaded');
                    };
                    element.src = element.dataset.src;
                    if (element.complete) {
                        element.classList.add('loaded');
                    }
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
