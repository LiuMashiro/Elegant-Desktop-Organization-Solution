import os
import shutil
import sys
import subprocess
from datetime import datetime

# ================= 路径配置 =================
TEMP_DESKTOP = r"C:\Users\[用户名]\Documents\temp_desktop"
TEMP_FOLD = r"C:\Users\[用户名]\Documents\temp_desktop_fold"
SHORTCUT_NAME = "折叠区.lnk"
TRIGGER_NAME = "强制整理.bat"
LOG_FILE = os.path.join(TEMP_FOLD, "整理日志.txt")
DATE_RECORD = os.path.join(TEMP_FOLD, "last_check_date.txt")
# ==========================================================

def ensure_folders():
    """确保目标文件夹存在"""
    if not os.path.exists(TEMP_FOLD):
        os.makedirs(TEMP_FOLD)

def check_date_interval():
    """检查是否距离上次整理超过7天"""
    today = datetime.now().date()
    if not os.path.exists(DATE_RECORD):
        with open(DATE_RECORD, 'w') as f:
            f.write(today.isoformat())
        return False
    try:
        with open(DATE_RECORD, 'r') as f:
            last_date = datetime.fromisoformat(f.read().strip()).date()
        return (today - last_date).days > 7
    except:
        return False

def check_file_count():
    """检查一级文件数量是否超过20"""
    count = 0
    for item in os.listdir(TEMP_DESKTOP):
        if item not in (SHORTCUT_NAME, TRIGGER_NAME):
            count += 1
    return count > 20

def get_folder_size(folder):
    """获取文件夹总大小（字节）"""
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
    """检查文件夹是否超过5GB"""
    return get_folder_size(TEMP_DESKTOP) > 5 * 1024**3

def move_files():
    """移动文件（排除指定项）"""
    moved = []
    for item in os.listdir(TEMP_DESKTOP):
        if item in (SHORTCUT_NAME, TRIGGER_NAME):
            continue
        src = os.path.join(TEMP_DESKTOP, item)
        dst = os.path.join(TEMP_FOLD, item)

        # 自动处理重名文件
        counter = 1
        base, ext = os.path.splitext(item)
        while os.path.exists(dst):
            dst = os.path.join(TEMP_FOLD, f"{base}_{counter}{ext}")
            counter += 1

        try:
            shutil.move(src, dst)
            moved.append(os.path.basename(dst))
        except Exception as e:
            print(f"移动失败 {item}: {e}")
    return moved

def send_notification(date_str):
    """发送Windows原生通知"""
    title = "临时桌面整理"
    message = f"已完成整理！日期：{date_str}"
    ps_script = f"""
    [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null;
    $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(1);
    $texts = $template.GetElementsByTagName("text");
    $texts[0].AppendChild($template.CreateTextNode("{title}"));
    $texts[1].AppendChild($template.CreateTextNode("{message}"));
    [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Python").Show($template);
    """
    try:
        subprocess.run(["powershell", "-Command", ps_script], capture_output=True)
    except:
        pass

def write_log(moved_items, reason):
    """写入日志"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log = f"=== 整理记录 ===\n时间：{now}\n触发原因：{reason}\n移动内容：\n"
    log += "\n".join(f"  - {i}" for i in moved_items) if moved_items else "  无文件移动"
    log += "\n\n"
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
        # 更新最后整理日期
        with open(DATE_RECORD, 'w') as f:
            f.write(datetime.now().date().isoformat())
        send_notification(datetime.now().strftime("%Y-%m-%d"))
        write_log(moved, " + ".join(reasons))

if __name__ == "__main__":
    main()
