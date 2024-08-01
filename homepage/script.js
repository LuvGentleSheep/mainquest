function toggleSidebar() {
    const sidebar = document.querySelector('nav.sidebar');
    const toggleButton = document.querySelector('.toggle-sidebar');
    sidebar.classList.toggle('hidden');
//  if (sidebar.classList.contains('hidden')) {
//      toggleButton.style.left = '180px';
//  } else {
//      toggleButton.style.left = '20px';
//  }
}

document.querySelectorAll('.clickable').forEach(item => {
    item.addEventListener('click', function(event) {
        const link = this.getAttribute('data-link');
        if (link) {
            window.location.href = link;
        } else {
            // 如果没有data-link属性，则不进行重定向
            event.preventDefault();
            const modal = document.getElementById('modal');
            const modalText = document.getElementById('modal-text');
            modalText.innerHTML = this.querySelector('p').innerHTML; // 使用 innerHTML 保留回车符
            modal.style.display = 'block';
        }
    });
});

function changeContent(section, image) {
        // 切换内容
    fetch(`${section}.html`).then(response => {
        return response.text();
    }).then(data => {
        const content = document.getElementById('content');
        content.innerHTML = data;
        // 隐藏 sidebar 并移动 toggle
        const sidebar = document.querySelector('nav.sidebar');
        const toggleButton = document.querySelector('.toggle-sidebar');
        sidebar.classList.remove('hidden');
        toggleButton.style.left = '20px';
        startSlideshow();
    });
}

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
startSlideshow();

// 实现多行文本截断并显示省略号
//document.addEventListener('DOMContentLoaded', function() {
//  const elements = document.querySelectorAll('.update-text p');
//  elements.forEach(element => {
//      const lineHeight = parseInt(window.getComputedStyle(element).lineHeight);
//      const maxLines = 3; // 最大显示行数
//      const maxHeight = lineHeight * maxLines;
//      element.style.maxHeight = maxHeight + 'px';
//      element.style.overflow = 'hidden';
//      element.style.textOverflow = 'ellipsis';
//      element.style.display = '-webkit-box';
//      element.style.webkitLineClamp = maxLines;
//      element.style.webkitBoxOrient = 'vertical';
//  });
//});

document.addEventListener("DOMContentLoaded", function() {
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
    
    // 模态窗口点击事件，点击关闭模态窗口
    document.getElementById('modal').addEventListener('click', function() {
        this.style.display = 'none';
    });
    // 处理点击图片的重定向
    document.querySelectorAll('.clickable').forEach(item => {
        item.addEventListener('click', function(event) {
            const link = this.getAttribute('data-link');
            if (link) {
                window.location.href = link;
            } else {
                event.preventDefault();
                event.stopPropagation();
            }
        });
    });
});

document.addEventListener("DOMContentLoaded", function() {
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