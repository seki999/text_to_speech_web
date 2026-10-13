# 文本转语音 / 双人对话生成器

支持中文、日语、英语普通朗读；双人对话可独立选择声音与语速，设置段间停顿，合并 MP3 并播放、下载。Speaker 标签和对话中的方括号内容不会朗读。

## Windows / Python 3.13 安装

在项目目录执行 PowerShell 命令，无需修改执行策略或激活环境：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install --upgrade -r requirements-dev.txt
winget install --id Gyan.FFmpeg -e
.\.venv\Scripts\python.exe app.py
```

打开 http://127.0.0.1:7860 。FFmpeg 和 ffprobe 必须可用；程序会自动查找 winget 安装目录。仅运行时可安装 requirements.txt。已有环境如创建 venv 时报告文件无法复制，请先确认没有运行中的 Python；也可创建不同名称的新环境。

依赖限定 edge-tts>=7.2.8,<8，避免旧协议版本；Gradio 6.x、aiohttp 3.x 设置兼容范围。补齐 pydub，并在 Python 3.13 安装 audioop-lts（Python 3.13 删除了标准库 audioop）。当前代码不使用 OpenAI API，不需要 API Key。

## Edge TTS 调查与连接诊断

2026-10-13 核对 [PyPI](https://pypi.org/project/edge-tts/) 最新发布为 7.2.8，声明 Python >=3.7，提供通用 Python wheel；本项目已在 Windows Python 3.13.14 验证导入和离线测试。版本声明不保证微软在线服务可用。

按照 [上游 Communicate 公共接口](https://github.com/rany2/edge-tts/blob/master/src/edge_tts/communicate.py)，使用 `edge_tts.Communicate(text=..., voice=..., rate="+0%")`，随后 `await communicate.save(path)`；每次应用层重试创建新实例，避免复用只能流式消费一次的对象。设置连接 10 秒、接收 60 秒、每次合成总超时 120 秒。

独立连接测试不启动 Gradio、不要求 FFmpeg、不启用离线备用，也不做应用层重试：

```powershell
.\.venv\Scripts\python.exe check_edge_tts.py
.\.venv\Scripts\python.exe check_edge_tts.py --voice en-US-JennyNeural --text "Hello" --output english.mp3
```

失败退出码为 1，成功为 0。此命令会访问微软服务，并把文本发送到在线服务；自动 pytest 测试不会访问微软。

| 错误 | 处理 |
| --- | --- |
| 403 | 中文提示拒绝访问；不做应用层重试。更新依赖、检查系统时间与网络策略，或切换离线。升级不能保证解决服务端限制。 |
| 429 | 最多 3 次尝试；遵守 Retry-After（秒或 HTTP 日期）。要求等待超过 60 秒时停止并提示，不提前重试。 |
| 500/502/503/504 | 最多 3 次尝试，指数退避 1、2 秒加随机抖动；显示中文服务错误。 |
| 超时、断连、响应不完整、无音频 | 有限重试；失败后给出中文诊断。 |
| 证书验证失败、其他 HTTP 错误 | 不重试，提示检查证书、网络、DNS、防火墙及代理。 |

不修改 edge-tts 内部认证令牌、身份、请求头或服务地址，不绕过限制。上游库自身的协议行为由官方发行版维护。音频先保存到独立临时文件，成功后替换目标文件；失败和取消会清理临时文件。

## 可选 Windows 离线备用

页面可直接选择“Windows 离线”，或勾选“在线失败时自动使用 Windows 离线声音”（默认关闭）。备用发生时显示中文提示；普通文本和双人对话均支持，仍输出 MP3，保留独立语速、停顿与下载。

采用 Windows PowerShell 5.1 + [System.Speech SpeechSynthesizer](https://learn.microsoft.com/en-us/dotnet/api/system.speech.synthesis.speechsynthesizer?view=netframework-4.8.1)，使用已安装声音生成 WAV，再由 FFmpeg 转 MP3。无需下载模型或安装 Python COM 扩展，适合 Windows 本地备用；离线质量与在线神经声音不同。语言严格匹配 zh-CN、ja-JP、en-US；没有对应声音会明确失败，需在 Windows 安装语音语言包。部分 Windows 自然声音不能被 System.Speech 访问。

优先匹配性别，缺少该性别时使用同语言已有声音；两个说话者可能听起来相同。百分比语速映射为 System.Speech 的整数 Rate，非严格等效。离线每段最多等待 120 秒。

列出本机可用声音：

```powershell
powershell.exe -NoProfile -Command 'Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).GetInstalledVoices().VoiceInfo | Select-Object Name,Culture,Gender'
```

## 验证

```powershell
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -W error::SyntaxWarning -m py_compile app.py tts_service.py offline_tts.py check_edge_tts.py tests/test_tts.py
.\.venv\Scripts\python.exe -m pytest -q
```

pytest Mock 覆盖 403、429、503、超时、其他连接错误、退避、Retry-After、重试成功与临时文件清理、离线选择和自动备用。功能测试使用本地静音段及真实 FFmpeg，验证双人独立语速、标签/方括号过滤、停顿、MP3 合并和下载返回值。

仍需手动运行独立连接测试，并在网页检查在线中文/日语/英语音质、长文本、双人声音和浏览器下载。在线服务限制及可用性无法由 Mock 测试证明。

### 本次实际验证（2026-10-13）

Windows PowerShell / Python 3.13.14：依赖安装成功，pip check 无冲突；edge-tts 7.2.8、aiohttp 3.14.3、Gradio 6.30.0。语法检查将 SyntaxWarning 当作错误并通过。pytest：17 passed（全部无微软网络请求）。Gradio 本地启动 HTTP 200；System.Speech 英语离线实际生成 87,293 字节 MP3，FFmpeg 解码时长 4,260 毫秒。本机检测到中文 Huihui、日语 Haruka、英语 Zira/David 声音。在线连接未在此次验证中调用，需运行上面的独立测试；浏览器试听、实际下载和长文本在线朗读仍需人工确认。
