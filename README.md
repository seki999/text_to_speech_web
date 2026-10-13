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

## 页面操作教程

### 选择语音引擎

页面顶部的设置对两个标签页均生效：

| 使用方式 | 设置 | 是否访问在线 TTS |
| --- | --- | --- |
| 在线朗读 | 语音引擎选“Edge 在线”，不勾选备用 | 是 |
| 在线优先、失败时离线 | 选“Edge 在线”，勾选“在线失败时自动使用 Windows 离线声音” | 会先尝试在线 |
| 完全本地合成 | 语音引擎选“Windows 离线” | 否 |

希望断网使用时，直接选择“Windows 离线”。语音包和依赖安装完成后，合成不需要外部 TTS 服务；网页仍通过本机地址打开。引擎选择不会自动保存到下次启动，下次打开默认仍为“Edge 在线”。

### 普通文本朗读

1. 打开“普通文本转语音”标签页。
2. 选择“输出语言”：中文、日语或英语。此选项决定声音，不会翻译输入文本，也不会自动切换混合语言声音。
3. 在文本框输入内容，例如 `你好，这是本地语音测试。`。
4. 调整“语速调整”：范围 -50 到 50，0 为正常，负数较慢、正数较快。初次试听可使用 -10。
5. 点击“生成语音”，等待播放器和下载文件出现。
6. 在“生成的语音”中播放；点击“下载 MP3 文件”区域的文件或下载图标保存。

日语示例：`こんにちは。今日は日本語の発音を練習します。`，输出语言选“日语”；英语示例：`Hello. Let's practice English together.`，输出语言选“英语”。普通文本中的方括号内容不会被程序过滤，方括号过滤仅用于双人对话。

### 双人对话朗读

打开“双人对话语音”，替换默认示例。中文练习可以直接粘贴：

```text
Speaker 1：今天我们练习什么？
Speaker 2：我们练习中文朗读和问答。
Speaker 1：可以把答案读慢一点吗？
Speaker 2：可以，两个说话者的语速可以分别调整。
```

将 Speaker 1 声音选为“中文男声”，Speaker 2 选为“中文女声”；Speaker 1 语速设为 0，Speaker 2 设为 -20，停顿设为 500 毫秒。点击“生成双人对话语音”，检查“解析后的对话内容”，然后试听或下载合并后的 MP3。离线模式缺少男声时会使用同语言已有声音，因此未必能区分两个角色。

英文提问、中文回答示例：

```text
Speaker 1: What does reliable [rɪˈlaɪəbl] mean?
Speaker 2：Reliable 的意思是可靠的。
Speaker 1: Can you give me an example?
Speaker 2：例如：This is a reliable tool. 这是一个可靠的工具。
```

Speaker 1 选“英文女声”，Speaker 2 选“中文女声”。每一段只使用该角色选择的声音，段内中英混合内容不会自动分别选声音。当前双人对话声音选项为中文/英文男声/女声，未提供日语选项。

输入规则：

- 支持 `Speaker 1：`、`Speaker 1:`、`Speaker1:` 以及大小写变化，Speaker 2 同理。建议每个带标签的语音段单独一行。
- 标签保留在预览中，不进入朗读正文。
- 对话中的英文方括号 `[...]` 及其中内容会被移除；只含这类内容的段落会跳过。
- 没有标签的行使用 Speaker 1，不会继承上一行的 Speaker 2；因此多行答案应在每行明确写出标签。
- 停顿范围为 0～2000 毫秒，默认 150 毫秒，添加在实际生成的语音段之间，结尾不额外添加停顿。

### 文件保存与退出

生成的普通语音和合并对话保存在项目的 `outputs/` 目录，文件名随机生成。对话中间片段会在任务结束时清理，最终 MP3 不会自动删除；需要时可手动清理旧文件。输出文件不会被 Git 提交。

关闭浏览器不会停止程序；在启动程序的 PowerShell 窗口按 `Ctrl+C` 退出。重新启动仍使用上面的 `app.py` 命令。若 7860 端口已被占用，先关闭之前启动的程序。

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

### 安装和检查 Windows 本地语音包

先在联网状态下安装所需语言，再进行断网朗读。Windows 版本和界面语言不同，按钮名称可能略有差异：

1. 打开 Windows“设置”→“时间和语言”→“语音”。在“管理语音”中选择“添加语音”，添加所需语言并等待下载完成。也可在“语言和区域”中添加语言，进入该语言的“语言选项”，下载“文本转语音”功能（如果提供）。不需要更改 Windows 显示语言。
2. 本项目要求的区域为“中文（简体，中国）”`zh-CN`、“日语（日本）”`ja-JP`、“英语（美国）”`en-US`。例如英语英国声音 `en-GB` 不满足当前英语选项的匹配条件。
3. 安装完成后重新启动应用，在 PowerShell 执行前面的声音列表命令。确认 `Culture` 出现所需区域，这是当前引擎能否使用该声音的判断依据。
4. 页面选择“Windows 离线”，先用对应语言的短句测试，再断网重复测试，并检查生成的 MP3 能播放、下载。

安装入口参考微软的[语言与声音说明](https://support.microsoft.com/en-us/accessibility/windows/narrator/appendix-a-supported-languages-and-voices)和[讲述人声音设置](https://support.microsoft.com/en-US/accessibility/windows/narrator/chapter-7-customizing-narrator)。当前项目以 [System.Speech 的 GetInstalledVoices](https://learn.microsoft.com/en-us/dotnet/api/system.speech.synthesis.speechsynthesizer.getinstalledvoices) 返回结果为准；在“讲述人”中可选的声音不一定能被此接口访问。

如果安装后仍未出现在列表中，不代表程序可以直接加载下载文件：当前实现不支持导入任意 `.onnx`、模型压缩包或讲述人自然声音，也未集成 Piper 等模型引擎。请确认声音支持 System.Speech/SAPI，并检查区域是否一致。不要通过修改注册表强行映射声音。

### 离线使用常见问题

| 现象 | 排查方法 |
| --- | --- |
| 提示 `No installed System.Speech voice for ...` | 安装相应区域的 TTS 声音，并通过声音列表命令确认可见；仅安装键盘或显示语言不等于安装 TTS 声音。 |
| 男声、女声听起来一样 | 同语言没有目标性别时会使用已有声音；检查本机声音列表中的 Gender。 |
| 语速变化不够细 | 本地引擎使用整数 Rate，滑块百分比经过映射，部分相邻值会得到相同速度。 |
| WAV 合成后 MP3 转换失败 | 检查 FFmpeg 和 ffprobe 是否安装，以及程序是否能定位它们。 |
| 勾选备用后仍等待网络 | 自动备用先尝试在线，并等待有限重试结束；想直接断网朗读请选择“Windows 离线”。 |

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
