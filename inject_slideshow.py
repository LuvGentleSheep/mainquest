#!/usr/bin/env python3
# inject_slideshow.py
"""
批量向 HTML 文件中插入放映模式模块
----------------------------------
使用方法（终端示例）：
    python3 inject_slideshow.py /path/to/folder1 /path/to/folder2 ...
"""

import sys
from pathlib import Path

# === 放映模式代码块（全文保持原样） ===
MODULE_TEXT = r"""
<!-- ========== 放映模式 MOD BEGIN (fixed Map usage) ========== -->
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
  /* ——插入按钮—— */
  const btn=document.createElement('button');
  btn.className='slideshow-toggle';btn.textContent='放映模式';
  document.body.appendChild(btn);

  /* ——插入模态结构（双背景层）—— */
  const modal=document.createElement('div');modal.className='slideshow-modal';
  modal.innerHTML=`<div id="bgA" class="slideshow-bg"></div>
                   <div id="bgB" class="slideshow-bg"></div>
                   <img id="slideA" class="slide-img" alt="">
                   <img id="slideB" class="slide-img" alt="">`;
  document.body.appendChild(modal);

  /* ——数据准备—— */
  const galleryImgs=[...document.querySelectorAll('#gallery img')];
  const sources=galleryImgs.map(i=>i.dataset?.src||i.src);
  const cache=new Map();                              // 正确使用 Map
  const preload=i=>{
      const src=sources[i%sources.length];
      if(cache.has(src)) return;
      const im=new Image();
      im.src=src;
      cache.set(src,im);                              // ★ 修复：使用 Map.set
  };

  /* ——引用 & 状态—— */
  const bgA=document.getElementById('bgA'), bgB=document.getElementById('bgB');
  const imgA=document.getElementById('slideA'), imgB=document.getElementById('slideB');
  let cur=0,useA=true,useBgA=true,timer;

  /* ——工具函数—— */
  const swap=(incoming,outgoing,src)=>{
      outgoing.src=src; outgoing.classList.add('active');
      incoming.classList.remove('active');
  };
  const swapBg=(incoming,outgoing,src)=>{
      outgoing.style.backgroundImage=`url('${src}')`;
      outgoing.classList.add('active');
      incoming.classList.remove('active');
  };

  /* ——显示指定索引—— */
  const show=i=>{
    const src=sources[i];
    swap(useA?imgB:imgA,useA?imgA:imgB,src);
    swapBg(useBgA?bgB:bgA,useBgA?bgA:bgB,src);
    cur=i; useA=!useA; useBgA=!useBgA;
    preload(cur+1);                                   // 继续预载下一张
  };

  /* ——边播边载—— */
  const tick=()=>{
    const next=(cur+1)%sources.length;
    const nextImg=cache.get(sources[next]);
    if(nextImg && nextImg.complete){
        show(next);
        timer=setTimeout(tick,5000);
    }else{
        timer=setTimeout(tick,300);
    }
  };

  /* ——打开 / 关闭模态—— */
  const open=()=>{
    if(!sources.length) return;
    preload(0);
    const first=cache.get(sources[0]);
    const start=()=>{show(0);modal.classList.add('open');document.body.style.overflow='hidden';timer=setTimeout(tick,5000);};
    first.complete ? start() : (first.onload=start);
  };
  const close=()=>{modal.classList.remove('open');document.body.style.overflow='auto';clearTimeout(timer);};

  btn.addEventListener('click',open);
  modal.addEventListener('click',close);
})();
</script>
<!-- ========== 放映模式 MOD END (fixed Map usage) ========== -->
"""

def inject(html_path: Path) -> None:
    """在 </body> 之前插入模块；若已存在标记则跳过"""
    text = html_path.read_text(encoding="utf-8", errors="ignore")
    if "放映模式 MOD BEGIN" in text:
        print(f"[跳过] {html_path} 已注入过")
        return

    lower = text.lower()
    index = lower.rfind("</body>")
    if index == -1:
        print(f"[警告] {html_path} 未找到 </body> 标签")
        return

    new_text = text[:index] + MODULE_TEXT + text[index:]
    backup = html_path.with_suffix(html_path.suffix + ".bak")
    html_path.rename(backup)               # 备份原文件
    html_path.write_text(new_text, encoding="utf-8")
    print(f"[完成] {html_path} 已更新（备份为 {backup.name}）")

def main():
    if len(sys.argv) == 1:
        print("请拖动包含 HTML 文件的文件夹到终端，再运行脚本")
        sys.exit(1)

    for folder in sys.argv[1:]:
        p = Path(folder)
        if not p.exists():
            print(f"[错误] 路径不存在: {p}")
            continue
        html_files = list(p.rglob("*.html"))
        if not html_files:
            print(f"[提示] {p} 内未发现 HTML 文件")
            continue
        for html in html_files:
            inject(html)

if __name__ == "__main__":
    main()