# Elegant-Desktop-Organization-Solution
一种支持Wallpaper Engine动态壁纸、高斯模糊和定期清理临时文件区的优雅整洁桌面整理方案

<img width="3839" height="2062" alt="屏幕截图 2026-04-18 212710" src="https://github.com/user-attachments/assets/b809c580-788b-4e83-beb8-64955ba3288e" />
效果预览

---

临时文件区：对于短期内需要高频处理的文件，可以置入临时文件区。满足闲时条件时，临时文件区中的文件将被折叠进入折叠区（也可手动触发折叠）。折叠区将创建折叠日志。

- 闲时条件（满足任一）：
  - 被手动触发
  - 启动时检查（满足任一）：
    - 本次日期与上次日期记录间隔＞7天
    - 文件数量超过20个。只计算一级单位。
    - 所有文件大小超过5GB。

---
工作目录：

```
📁 我的文档/
├─ 📄 temp_desktop_cleaner.py    # 工具主程序（后台自动运行）
├─ 📁 temp_desktop               # 【临时桌面】存放所有临时文件
│  ├─ 📄 强制整理.bat            # 手动触发整理脚本
│  └─ 🔗 折叠区.lnk              # 归档文件夹快捷方式
└─ 📁 temp_desktop_fold          # 【折叠区】自动归档的文件存放地
   ├─ 📄 整理日志.txt            # 整理记录日志
   └─ 📄 last_check_date.txt     # 自动整理时间记录
```

### 配置

环境：Python

**自动化一键配置（推荐）：**

运行auto-configuration.py

**手动配置【不推荐】（手动编辑程序，替换[用户名]为用户文件夹名字，并注意Python路径）：**

  1.准备工作：在文档中创建temp_desktop和temp_desktop_fold文件夹。

  2.创建脚本运行主体：将temp_desktop_cleaner.py置入在C:\Users\[用户名]\Documents\

  3.创建脚本触发器：将“强制整理.bat”置入C:\Users\[用户名]\Documents\temp_desktop

  4.将折叠文件夹的快捷方式放入临时区，命名为“折叠区”。

  5.自启动：Win+R输入shell:startup，创建快捷方式（注意Python路径）：

  ```
  C:\Users\[用户名]\AppData\Local\Microsoft\WindowsApps\pythonw.exe "C:\Users\[用户名]\Documents\temp_desktop_cleaner.py"
  ```

  6.置顶强制触发bat和折叠区：Powershell运行time_set.ps1


**配置Fences**

仿照示例图片创造分区。其中，临时文件区使用Folder Portals链接到临时文件夹。

按照此方式配置外观和功能：

<img width="878" height="899" alt="屏幕截图 2026-04-18 215139" src="https://github.com/user-attachments/assets/b12bc903-3590-405b-bc54-1c5dc0fd802a" />
<img width="851" height="814" alt="屏幕截图 2026-04-18 215107" src="https://github.com/user-attachments/assets/b2c6e2a2-c9ff-421e-a62e-18d990f10fbd" />


**配置Wallpaper Engine**

要实现动态壁纸的模糊需要如此配置：

<img width="483" height="354" alt="屏幕截图 2026-04-18 220151" src="https://github.com/user-attachments/assets/de930929-86d1-405e-82ed-6491d8f80c0f" />


### 已知问题

如果Wallpaper还设置了自动切换壁纸，则往往切换满一定时间后Fences才会刷新背景。
