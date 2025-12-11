Set objShell = CreateObject("WScript.Shell")

' 获取当前目录
strCurrentDir = objShell.CurrentDirectory

' 设置工作目录为项目目录
strProjectPath = "C:\Users\ktphi\.gemini\antigravity\playground\canto-beats"

' 创建快捷方式
Set objShortcut = objShell.CreateShortcut(strProjectPath & "\Canto-beats (GPU).lnk")

' 设置目标：使用conda run来在canto-env中启动
objShortcut.TargetPath = "cmd.exe"
objShortcut.Arguments = "/k conda activate canto-env && python main.py && exit"
objShortcut.WorkingDirectory = strProjectPath
objShortcut.Description = "Canto-beats with GPU Acceleration"
objShortcut.IconLocation = "%SystemRoot%\System32\imageres.dll,109"

' 保存快捷方式
objShortcut.Save

WScript.Echo "快捷方式已创建: Canto-beats (GPU).lnk"
WScript.Echo "请双击该快捷方式启动GPU版本"
