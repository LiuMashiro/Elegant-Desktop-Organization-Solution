# 目标时间
$time = Get-Date "2099-12-31 00:00:00"

# 文件1
$file1 = "C:\Users\[用户名]\Documents\temp_desktop\强制整理.bat"
(Get-Item $file1).LastWriteTime = $time

# 文件2（快捷方式）
$file2 = "C:\Users\[用户名]\Documents\temp_desktop\折叠区.lnk"
(Get-Item $file2).LastWriteTime = $time

Write-Host "✅ 修改时间已设置为 2099 年！"