# 文本转语音 / ChatGPT 混合语音生成器

这是一个基于 Python + Gradio + edge-tts + OpenAI API 的本地网页小程序。

你可以在浏览器中输入文本，然后生成 MP3 语音文件。  
也可以调用 ChatGPT API，先自动生成中文、日语、英语混合文本，再把生成的内容转换成语音。

---

## 1. 功能介绍

本项目目前支持两个主要功能：

### 1.1 普通文本转语音

你可以手动输入一段文本，然后选择输出语言：

- 中文
- 日语
- 英语

点击按钮后，会生成 MP3 文件，可以在线试听，也可以下载。

### 1.2 ChatGPT 生成混合语音

你可以输入一个主题，例如：

```text
帮我生成一段关于每天坚持学习英语、日语和AI技术的中日英混合朗读文本。
```

程序会先调用 OpenAI API 生成一段适合朗读的中日英混合文本，然后自动生成 MP3 语音文件。

---

## 2. 项目目录结构

建议目录结构如下：

```text
text_to_speech_web/
├── .venv/
├── app.py
├── requirements.txt
├── openai_api_key.txt
├── outputs/
└── README.md
```

说明：

```text
app.py                 主程序文件
requirements.txt       Python 依赖列表
openai_api_key.txt     保存 OpenAI API Key 的本地文件
outputs/               生成的 MP3 文件保存目录
README.md              项目说明文件
```

---

## 3. 环境要求

建议使用：

```text
Python 3.10 / 3.11 / 3.12
```

Windows 用户建议使用官网版 Python，不太建议使用 Microsoft Store 版 Python。

---

## 4. 创建本地 Python 虚拟环境

进入项目目录：

```powershell
cd C:\Users\sekine\Documents\text_to_speech_web
```

创建虚拟环境：

```powershell
python -m venv .venv
```

激活虚拟环境：

```powershell
.venv\Scripts\Activate.ps1
```

如果 PowerShell 提示执行策略错误，可以先执行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

然后再次激活：

```powershell
.venv\Scripts\Activate.ps1
```

激活成功后，命令行前面一般会显示：

```text
(.venv)
```

---

## 5. 安装依赖

确认已经进入虚拟环境后，执行：

```powershell
pip install -r requirements.txt
```

`requirements.txt` 内容如下：

```txt
gradio
edge-tts
openai
```

如果你还没有 `requirements.txt`，可以自己新建一个，写入上面三行。

---

## 6. 设置 OpenAI API Key

在项目目录下创建文件：

```text
openai_api_key.txt
```

里面只写一行你的 OpenAI API Key：

```text
sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

注意：

- 不要加引号
- 不要加空格
- 不要把这个文件上传到 GitHub
- 不要把 API Key 发给别人

如果你只使用“普通文本转语音”功能，可以暂时不配置这个文件。  
但是如果要使用“ChatGPT 生成混合语音”功能，就必须配置。

---

## 7. 运行程序

在项目目录下执行：

```powershell
python .\app.py
```

正常启动后，命令行会显示类似：

```text
Running on local URL:  http://127.0.0.1:7860
```

然后在浏览器打开：

```text
http://127.0.0.1:7860
```

---

## 8. 使用方法

### 8.1 普通文本转语音

打开网页后，进入：

```text
普通文本转语音
```

输入文本，例如：

```text
你好，这是一个文本转语音测试。
```

选择语言：

```text
中文
```

点击：

```text
生成语音
```

页面下方会出现：

- 语音播放器
- MP3 下载按钮

---

### 8.2 日语文本转语音

输入：

```text
今日はいい天気ですね。明日も一緒に頑張りましょう。
```

选择：

```text
日语
```

点击生成即可。

---

### 8.3 英语文本转语音

输入：

```text
Learning English every day is a powerful habit. Keep going, and you will become better.
```

选择：

```text
英语
```

点击生成即可。

---

### 8.4 ChatGPT 生成混合语音

进入：

```text
ChatGPT 生成混合语音
```

输入主题：

```text
帮我生成一段关于每天坚持学习英语、日语和AI技术的中日英混合朗读文本。
```

选择风格，例如：

```text
英语学习
```

选择长度，例如：

```text
中等长度，约200字
```

模型名可以使用默认值：

```text
gpt-4o-mini
```

点击：

```text
生成混合文本并生成语音
```

程序会输出：

- ChatGPT 生成的混合文本
- 混合语音播放器
- MP3 下载文件

---

## 9. 语速调整

页面上有“语速调整”滑块。

范围：

```text
-50 到 50
```

含义：

```text
0     正常速度
-20   慢一点
+20   快一点
```

如果你是做英语、日语听力练习，建议先使用：

```text
-10 或 -20
```

等熟悉之后再调回正常速度。

---

## 10. 常见问题

### 10.1 MP3 已经生成，但网页报错：needed 2, returned 1

原因是 Gradio 页面设置了两个输出组件：

```python
outputs=[audio_output, file_output]
```

但是函数只返回了一个值。

正确写法是返回两个值：

```python
return output_path, output_path
```

本项目当前版本已经修正了这个问题。

---

### 10.2 找不到 openai_api_key.txt

如果出现：

```text
找不到 openai_api_key.txt
```

请确认这个文件在 `app.py` 同一个目录下。

正确结构：

```text
text_to_speech_web/
├── app.py
├── openai_api_key.txt
└── requirements.txt
```

---

### 10.3 openai_api_key.txt 是空的

请打开文件，确认里面写了 API Key，例如：

```text
sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

文件里不要只写空行。

---

### 10.4 PowerShell 无法激活虚拟环境

如果执行：

```powershell
.venv\Scripts\Activate.ps1
```

出现执行策略错误，可以执行：

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

然后重新执行：

```powershell
.venv\Scripts\Activate.ps1
```

---

### 10.5 python -m venv .venv 创建虚拟环境卡住

如果你使用的是 Microsoft Store 版 Python，路径可能类似：

```text
C:\Program Files\WindowsApps\PythonSoftwareFoundation.Python...
```

这种情况有时会出现虚拟环境或 pip 问题。

建议安装官网版 Python 3.12，然后使用：

```powershell
py -3.12 -m venv .venv
```

---

### 10.6 edge-tts 生成失败

可能原因：

- 网络暂时不稳定
- 文本太长
- 语音服务暂时不可用

可以先测试一段短文本：

```text
你好，这是测试。
```

如果短文本可以生成，说明程序本身没问题。

---

## 11. 当前使用的主要技术

```text
Python
Gradio
edge-tts
OpenAI API
```

说明：

- Gradio 用来创建本地网页界面
- edge-tts 用来生成 MP3 语音
- OpenAI API 用来生成混合语言文本

---

## 12. 安全注意事项

请不要把下面这个文件上传到公开仓库：

```text
openai_api_key.txt
```

如果你使用 Git，建议创建 `.gitignore` 文件，并写入：

```gitignore
.venv/
outputs/
openai_api_key.txt
__pycache__/
*.mp3
```

---

## 13. 推荐启动流程

每次重新打开项目时，可以按这个顺序：

```powershell
cd C:\Users\sekine\Documents\text_to_speech_web
.venv\Scripts\Activate.ps1
python .\app.py
```

然后打开浏览器：

```text
http://127.0.0.1:7860
```

---

## 14. 后续可以扩展的功能

以后可以继续增加：

- 多角色对话语音
- 中日英自动分段，不同语言使用不同声音
- 批量生成多个 MP3
- 自动保存生成历史
- 把生成文本导出为 TXT
- 给英语学习添加单词解释
- 给日语面试练习添加固定模板
- 支持 OpenAI TTS
- 支持本地大模型 LM Studio
- 支持上传文本文件后批量生成语音

---

## 15. 简单总结

这个小程序适合用来做：

```text
文本转语音
英语听力材料生成
日语面试朗读练习
中日英混合语言学习
AI 自动生成学习材料
```

你已经可以把它作为一个本地学习工具继续扩展。  
后面如果继续加入单词解释、听写、跟读、录音评分，它就会慢慢变成一个完整的语言学习助手。
