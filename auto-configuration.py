import os
import sys
import subprocess
from datetime import datetime
import ctypes
from ctypes import wintypes, windll, c_wchar_p, HRESULT

# ------------------------------------------------------------------------------
# 1. 自动安装依赖 (pywin32)
# ------------------------------------------------------------------------------
try:
    import win32com.client
except ImportError:
    print("正在安装必要组件 (pywin32)，请稍候...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pywin32'])
        import win32com.client
    except Exception as e:
        print(f"安装失败，请手动运行: pip install pywin32\n错误: {e}")
        input("按回车退出...")
        sys.exit(1)

# ------------------------------------------------------------------------------
# 2. 系统API调用 - 获取用户名文件夹名字的文档路径
# ------------------------------------------------------------------------------
class GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", wintypes.BYTE * 8)]

FOLDERID_Documents = GUID(0xFDD39AD0, 0x238F, 0x46AF, (0xAD, 0xB4, 0x6C, 0x85, 0x48, 0x03, 0x69, 0xC7))
SHGetKnownFolderPath = windll.shell32.SHGetKnownFolderPath
SHGetKnownFolderPath.argtypes = [ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE, ctypes.POINTER(c_wchar_p)]
SHGetKnownFolderPath.restype = HRESULT

def get_documents_path():
    path_ptr = c_wchar_p()
    result = SHGetKnownFolderPath(ctypes.byref(FOLDERID_Documents), 0, None, ctypes.byref(path_ptr))
    if result != 0:
        raise Exception("无法获取Documents路径")
    path = path_ptr.value
    windll.ole32.CoTaskMemFree(path_ptr)
    return path

# ------------------------------------------------------------------------------
# 3. 创建快捷方式
# ------------------------------------------------------------------------------
def create_shortcut(target_path, shortcut_location, arguments="", working_dir=""):
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(shortcut_location)
    shortcut.TargetPath = target_path
    shortcut.Arguments = arguments
    shortcut.WorkingDirectory = working_dir
    shortcut.save()

# ------------------------------------------------------------------------------
# 4. 主配置逻辑
# ------------------------------------------------------------------------------
def main():
    print("="*40)
    print("   桌面整理工具 - 一键配置")
    print("="*40)

    # --- 步骤 1: 确定路径 ---
    try:
        docs_path = get_documents_path()
    except:
        docs_path = os.path.expanduser("~\\Documents") # 备用方案
    
    python_exe = sys.executable
    pythonw_exe = os.path.join(os.path.dirname(python_exe), "pythonw.exe")
    
    # 定义所有标准路径
    cleaner_script_path = os.path.join(docs_path, "temp_desktop_cleaner.py")
    temp_desktop_path = os.path.join(docs_path, "temp_desktop")
    temp_fold_path = os.path.join(docs_path, "temp_desktop_fold")
    bat_path = os.path.join(temp_desktop_path, "强制整理.bat")
    lnk_path = os.path.join(temp_desktop_path, "折叠区.lnk")
    
    # 启动文件夹路径
    startup_folder = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
    startup_lnk_path = os.path.join(startup_folder, "TempDesktopAutoStart.lnk")

    print(f"[1/7] 检测路径...")
    print(f"      文档目录: {docs_path}")
    print(f"      Python路径: {python_exe}")

    # --- 步骤 2: 创建文件夹 ---
    print(f"[2/7] 创建文件夹结构...")
    os.makedirs(temp_desktop_path, exist_ok=True)
    os.makedirs(temp_fold_path, exist_ok=True)

    # --- 步骤 3: 生成主程序脚本 (temp_desktop_cleaner.py) ---
    print(f"[3/7] 生成整理脚本...")
    

    cleaner_code = f'''import os
import shutil
import sys
import subprocess
from datetime import datetime

# ================= 路径配置 (自动生成) =================
TEMP_DESKTOP = r"{temp_desktop_path}"
TEMP_FOLD = r"{temp_fold_path}"
SHORTCUT_NAME = "折叠区.lnk"
TRIGGER_NAME = "强制整理.bat"
LOG_FILE = os.path.join(TEMP_FOLD, "整理日志.txt")
DATE_RECORD = os.path.join(TEMP_FOLD, "last_check_date.txt")
# =======================================================

def ensure_folders():
    if not os.path.exists(TEMP_FOLD):
        os.makedirs(TEMP_FOLD)

def check_date_interval():
    today = datetime.now().date()
    if not os.path.exists(DATE_RECORD):
        with open(DATE_RECORD, 'w') as f:
            f.write(today.isoformat())
        return False
    try:
        with open(DATE_RECORD, 'r') as f:
            last_date = datetime.fromisoformat(f.read().strip()).date()
        if (today - last_date).days > 7:
            with open(DATE_RECORD, 'w') as f:
                f.write(today.isoformat())
            return True
        return False
    except:
        return False

def check_file_count():
    count = 0
    for item in os.listdir(TEMP_DESKTOP):
        if item not in (SHORTCUT_NAME, TRIGGER_NAME):
            count += 1
    return count > 20

def get_folder_size(folder):
    total = 0
    for dirpath, _, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            try:
                total += os.path.getsize(fp)
            except:
                pass
    return total

def check_folder_size():
    return get_folder_size(TEMP_DESKTOP) > 5 * 1024**3

def move_files():
    moved = []
    for item in os.listdir(TEMP_DESKTOP):
        if item in (SHORTCUT_NAME, TRIGGER_NAME):
            continue
        src = os.path.join(TEMP_DESKTOP, item)
        dst = os.path.join(TEMP_FOLD, item)
        
        counter = 1
        base_name, ext = os.path.splitext(item)
        while os.path.exists(dst):
            dst = os.path.join(TEMP_FOLD, f"{{base_name}}_{{counter}}{{ext}}")
            counter += 1
            
        try:
            shutil.move(src, dst)
            moved.append(os.path.basename(dst))
        except Exception as e:
            print(f"移动失败 {{item}}: {{e}}")
    return moved

def send_notification(date_str):
    title = "临时桌面整理"
    message = f"已完成整理！日期：{{date_str}}"
    ps_script = f"""
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;
    [Windows.UI.Notifications.ToastNotification, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;
    [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null;
    
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02);
    $textNodes = $template.GetElementsByTagName("text");
    $textNodes.Item(0).AppendChild($template.CreateTextNode("{{title}}")) | Out-Null;
    $textNodes.Item(1).AppendChild($template.CreateTextNode("{{message}}")) | Out-Null;
    
    $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Python Script");
    $notifier.Show($template);
    """
    try:
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
    except:
        pass

def write_log(moved_items, reason):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = f"=== 整理记录 ===\\n时间：{{now}}\\n触发原因：{{reason}}\\n移动内容：\\n"
    log += "\\n".join([f"  - {{i}}" for i in moved_items]) if moved_items else "  无文件移动"
    log += "\\n\\n"
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(log)

def main():
    ensure_folders()
    force_mode = '--force' in sys.argv
    reasons = []

    if force_mode:
        reasons.append("手动强制触发")
    else:
        if check_date_interval():
            reasons.append("超过7天未整理")
        if check_file_count():
            reasons.append("文件数超20个")
        if check_folder_size():
            reasons.append("大小超5GB")

    if reasons:
        moved = move_files()
        with open(DATE_RECORD, 'w') as f:
            f.write(datetime.now().date().isoformat())
        send_notification(datetime.now().strftime("%Y-%m-%d"))
        write_log(moved, " + ".join(reasons))

if __name__ == "__main__":
    main()
'''
    
    with open(cleaner_script_path, 'w', encoding='utf-8') as f:
        f.write(cleaner_code)

    # --- 步骤 4: 配置开机自启动 ---
    print(f"[4/7] 配置开机自启动...")
    if os.path.exists(pythonw_exe):
        create_shortcut(pythonw_exe, startup_lnk_path, arguments=f'"{cleaner_script_path}"')
    else:
        print("      警告: 未找到 pythonw.exe，跳过自启动配置")

    # --- 步骤 5: 生成强制整理.bat ---
    print(f"[5/7] 生成强制整理脚本...")
    bat_content = f'@echo off\n"{python_exe}" "{cleaner_script_path}" --force\nexit'
    with open(bat_path, 'w', encoding='gbk') as f: # Bat文件默认GBK编码防止乱码
        f.write(bat_content)

    # --- 步骤 6: 创建“折叠区”快捷方式 ---
    print(f"[6/7] 创建快捷方式...")
    create_shortcut(temp_fold_path, lnk_path)

    # --- 步骤 7: 修改时间戳为2099年 (置顶) ---
    print(f"[7/7] 设置文件置顶属性...")
    year_2099 = datetime(2099, 1, 1).timestamp()
    
    try:
        os.utime(bat_path, (year_2099, year_2099))
        os.utime(lnk_path, (year_2099, year_2099))
    except:
        pass # 权限不足时忽略，不影响主要功能

    print("\n✅ 配置全部完成！")
    print(f"请前往: {temp_desktop_path} 查看")
    input("\n按回车键退出...")

if __name__ == "__main__":
    main()
