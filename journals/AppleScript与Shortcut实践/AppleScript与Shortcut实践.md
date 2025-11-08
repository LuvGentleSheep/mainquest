banner:: "../assets/image_1718227246155_0.png"
icon:: 🛠️

- # 聚集窗口（在菜单栏中固定）
  #macOS #AppleScript #多显示器 #窗口管理 #优化 #生产力工具 #权限设置
  ```javascript
  on run {input, parameters}
  tell application "System Events"
  set allWindows to {}
  repeat with appProc in (application processes where background only is false)
  	set allWindows to allWindows & windows of appProc
  end repeat
  
  repeat with win in allWindows
  	try
  		set position of win to {50, 50}
  	on error
  		-- 忽略错误，继续移动下一个窗口
  	end try
  end repeat
  end tell
  return input
  end run
  ```
-
- # 筛选横屏壁纸（作为访达快速操作使用）
  #脚本 #自动化 #文件管理 #AppleScript
  ```javascript
  on run {input, parameters}
  	-- 获取选中的文件夹路径
  	set selectedFolder to POSIX path of (input as string)
  	
  	-- 设置新文件夹路径
  	set landscapeFolder to selectedFolder & "landscape/"
  	
  	-- 创建新文件夹
  	do shell script "mkdir -p " & quoted form of landscapeFolder
  	
  	-- 获取文件夹中的所有文件
  	set imageFiles to paragraphs of (do shell script "find " & quoted form of selectedFolder & " -type f \\( -iname \\*.jpg -o -iname \\*.jpeg -o -iname \\*.png -o -iname \\*.gif \\)")
  	
  	repeat with eachFile in imageFiles
  		-- 获取图片尺寸
  		set imageDimensions to (do shell script "sips -g pixelHeight -g pixelWidth " & quoted form of eachFile)
  		set dimensionsList to paragraphs of imageDimensions
  		
  		-- 提取高度和宽度
  		set width to word 2 of item 3 of dimensionsList
  		set height to word 2 of item 2 of dimensionsList
  		
  		-- 如果宽度大于高度，则为横版图片
  		if width > height then
  			-- 复制横版图片到新文件夹
  			do shell script "cp " & quoted form of eachFile & " " & quoted form of landscapeFolder
  		end if
  	end repeat
  end run
  ```
- # 同时跳转多个搜索引擎（配合popclip）
  [[Jun 8th, 2024]] 
  #AppleScript #PopClip #快捷指令 #搜索自动化
  ```javascript
  on run {input}
  	-- 将输入转换为字符串
  	set searchTerm to input as string
  	
  	-- 对搜索词进行URL编码
  	set encodedSearchTerm to do shell script "python3 -c 'import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))' " & quoted form of searchTerm
  	
  	-- 定义搜索引擎的URL模板
  	set twitterSearchURL to "https://twitter.com/search?q="
  	set instagramSearchURL to "https://www.instagram.com/explore/tags/"
  	set googleSearchURL to "https://www.google.com/search?q="
  	set bilibiliSearchURL to "https://search.bilibili.com/all?keyword="
  	set xiaohongshuSearchURL to "https://www.xiaohongshu.com/search_result/?keyword="
  	
  	-- 将所有搜索引擎的URL模板放入一个列表
  	set searchURLs to {twitterSearchURL, instagramSearchURL, googleSearchURL, bilibiliSearchURL, xiaohongshuSearchURL}
  	
  	-- 遍历每个搜索引擎URL，生成完整的搜索链接并在默认浏览器中打开
  	repeat with baseURL in searchURLs
  		-- 对于Instagram，需要在URL末尾加上斜杠
  		if baseURL is instagramSearchURL then
  			set searchURL to baseURL & encodedSearchTerm & "/"
  		else
  			set searchURL to baseURL & encodedSearchTerm
  		end if
  		do shell script "open " & quoted form of searchURL
        delay 0.5 -- 添加一个0.5秒的延迟
  	end repeat
  end run
  ```
  
  ```
  #popclip shortcut example
  name: 搜
  shortcut name: 搜索Free
  ```
-
- # 在Logseq转换Markdown链接到横幅格式（配合popclip）
  [[Jun 13th, 2024]]
  #AppleScript #logseq #PopClip #快捷指令 
  ```javascript
  -- #popclip
  -- name: 转banner
  -- icon: 🚥
  -- language: applescript
  tell application "System Events"
  	tell process "Logseq" -- 将 "TextEdit" 替换为你的文本编辑器的名称
  		set frontmost to true
  		keystroke "c" using {command down} -- 复制选中的文本
  		delay 0.1 -- 等待复制完成
  		set selectedText to the clipboard
  		if selectedText starts with "!" then
  			set AppleScript's text item delimiters to {"]("}
  			set fileAddress to text item 2 of selectedText
  			set AppleScript's text item delimiters to {")"}
  			set fileAddress to text item 1 of fileAddress
  			set newText to "banner:: \"" & fileAddress & "\"" & return & "icon:: "
  			set the clipboard to newText
  			keystroke "v" using {command down} -- 粘贴新文本
  		end if
  	end tell
  end tell
  ```
- # 在 Logseq 转换日期为跳转日志日期
  [[2025/09/11]] GMT+8 06:38:01
  
  ```javascript
  -- #popclip
  -- name: 转Logseq日期链接
  -- icon: 🗓️
  -- language: applescript
  -- requirements: [text]
  -- regex: '^\s*\d{4}(?:\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日|\s*[-/]\s*\d{1,2}\s*[-/]\s*\d{1,2})\s*$'
  tell application "System Events"
  	tell process "Logseq"
  		set frontmost to true
  		keystroke "c" using {command down}
  		delay 0.05
  		set selectedText to (the clipboard as text)
  
  		-- 支持：
  		-- 1) 2025年9月11日
  		-- 2) 2025 年 9 月 11 日（含半角/全角空格 U+3000）
  		-- 3) 2025-09-11 / 2025/9/1
  		set sh to "printf %s " & quoted form of selectedText & " | /usr/bin/perl -CSD -ne 'use utf8; chomp; " & ¬
  			"if(/^\\s*(\\d{4})[\\h\\x{3000}]*年[\\h\\x{3000}]*(\\d{1,2})[\\h\\x{3000}]*月[\\h\\x{3000}]*(\\d{1,2})[\\h\\x{3000}]*日\\s*$/u " & ¬
  			" || /^\\s*(\\d{4})[\\h\\x{3000}]*(?:-|\\/)[\\h\\x{3000}]*(\\d{1,2})[\\h\\x{3000}]*(?:-|\\/)[\\h\\x{3000}]*(\\d{1,2})\\s*$/u){" & ¬
  			"$y=$1//$4;$m=$2//$5;$d=$3//$6; printf \"[[%04d/%02d/%02d]]\", $y,$m,$d; " & ¬
  			"} else { print $_ }'"
  
  		try
  			set newText to do shell script sh
  		on error
  			set newText to selectedText
  		end try
  
  		set the clipboard to newText
  		keystroke "v" using {command down}
  	end tell
  end tell
  ```
-
-