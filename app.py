import gradio as gr
import edge_tts
import asyncio
import uuid
import os
from openai import OpenAI


# =========================
# 基本设置
# =========================

OUTPUT_DIR = "outputs"
API_KEY_FILE = "openai_api_key.txt"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================
# 语音设置
# =========================

VOICE_MAP = {
    "中文": "zh-CN-XiaoxiaoNeural",
    "日语": "ja-JP-NanamiNeural",
    "英语": "en-US-JennyNeural",

    # 混合语音暂时使用英文声音
    # 如果你更重视中文自然度，可以改成 zh-CN-XiaoxiaoNeural
    # 如果你更重视日语自然度，可以改成 ja-JP-NanamiNeural
    "混合": "en-US-JennyNeural",
}


# =========================
# OpenAI API Key 读取
# =========================

def read_openai_api_key() -> str:
    """
    从本地 openai_api_key.txt 读取 OpenAI API Key。
    文件内容只需要一行 API Key。
    """
    if not os.path.exists(API_KEY_FILE):
        raise gr.Error(
            "找不到 openai_api_key.txt。请在项目目录下创建这个文件，并写入你的 OpenAI API Key。"
        )

    with open(API_KEY_FILE, "r", encoding="utf-8") as f:
        api_key = f.read().strip()

    if not api_key:
        raise gr.Error("openai_api_key.txt 是空的，请写入你的 OpenAI API Key。")

    return api_key


# =========================
# ChatGPT 生成混合文本
# =========================

def generate_mixed_text(
    user_topic: str,
    style: str,
    length: str,
    model_name: str,
) -> str:
    """
    调用 OpenAI API，生成中日英混合文本。
    """
    if not user_topic or not user_topic.strip():
        raise gr.Error("请输入主题或原始文本。")

    api_key = read_openai_api_key()
    client = OpenAI(api_key=api_key)

    prompt = f"""
请根据用户输入，生成一段适合朗读成语音的中日英混合文本。

要求：
1. 使用中文、日语、英语三种语言自然混合。
2. 不要使用 Markdown。
3. 不要使用项目符号。
4. 句子要适合 TTS 朗读。
5. 内容要自然、有节奏感。
6. 不要输出解释，只输出最终朗读文本。
7. 中文、日语、英语之间可以自然切换。
8. 内容要适合学习语言的人反复听。

风格：{style}
长度：{length}

用户输入：
{user_topic}
"""

    try:
        response = client.responses.create(
            model=model_name,
            input=prompt,
        )

        result = response.output_text.strip()

        if not result:
            raise gr.Error("OpenAI API 返回了空内容，请换一个主题或模型再试。")

        return result

    except Exception as e:
        raise gr.Error(f"调用 OpenAI API 失败：{e}")


# =========================
# edge-tts 生成语音
# =========================

async def generate_tts_async(text: str, language: str, rate: int):
    """
    使用 edge-tts 生成 MP3 语音。
    """
    if not text or not text.strip():
        raise gr.Error("请输入文本。")

    voice = VOICE_MAP.get(language)

    if voice is None:
        raise gr.Error("请选择正确的语言。")

    filename = f"tts_{uuid.uuid4().hex}.mp3"
    output_path = os.path.join(OUTPUT_DIR, filename)

    rate_text = f"{rate:+d}%"

    communicate = edge_tts.Communicate(
        text=text,
        voice=voice,
        rate=rate_text,
        volume="+0%",
    )

    await communicate.save(output_path)

    return output_path


# =========================
# 普通文本转语音
# =========================

def text_to_speech(text: str, language: str, rate: int):
    """
    普通文本转语音。
    注意：
    Gradio 页面有两个输出：
    1. audio_output
    2. file_output

    所以这里必须返回两个值。
    """
    output_path = asyncio.run(
        generate_tts_async(
            text=text,
            language=language,
            rate=rate,
        )
    )

    return output_path, output_path


# =========================
# ChatGPT 生成混合文本 + 转语音
# =========================

def chatgpt_to_mixed_speech(
    user_topic: str,
    style: str,
    length: str,
    model_name: str,
    rate: int,
):
    """
    先用 ChatGPT 生成中日英混合文本，
    再用 edge-tts 生成 MP3。
    """
    mixed_text = generate_mixed_text(
        user_topic=user_topic,
        style=style,
        length=length,
        model_name=model_name,
    )

    audio_path = asyncio.run(
        generate_tts_async(
            text=mixed_text,
            language="混合",
            rate=rate,
        )
    )

    # 这里有三个输出：
    # 1. mixed_text_output
    # 2. mixed_audio_output
    # 3. mixed_file_output
    return mixed_text, audio_path, audio_path


# =========================
# Gradio 网页界面
# =========================

with gr.Blocks(title="文本转语音 / ChatGPT 混合语音生成器") as demo:
    gr.Markdown("# 文本转语音 / ChatGPT 混合语音生成器")
    gr.Markdown(
        "可以直接输入文本生成语音，也可以调用 ChatGPT 先生成中日英混合文本，再生成 MP3。"
    )

    # -------------------------
    # Tab 1: 普通文本转语音
    # -------------------------

    with gr.Tab("普通文本转语音"):
        language = gr.Dropdown(
            choices=["中文", "日语", "英语"],
            value="中文",
            label="输出语言",
        )

        text_input = gr.Textbox(
            label="请输入文本",
            lines=8,
            placeholder="例如：你好，这是一个文本转语音测试。",
        )

        rate = gr.Slider(
            minimum=-50,
            maximum=50,
            value=0,
            step=5,
            label="语速调整",
        )

        generate_btn = gr.Button("生成语音")

        audio_output = gr.Audio(
            label="生成的语音",
            type="filepath",
        )

        file_output = gr.File(
            label="下载 MP3 文件",
        )

        generate_btn.click(
            fn=text_to_speech,
            inputs=[text_input, language, rate],
            outputs=[audio_output, file_output],
        )

    # -------------------------
    # Tab 2: ChatGPT 生成混合语音
    # -------------------------

    with gr.Tab("ChatGPT 生成混合语音"):
        topic_input = gr.Textbox(
            label="请输入主题或原始文本",
            lines=6,
            placeholder="例如：帮我生成一段关于坚持学习英语、日语和AI技术的中日英混合朗读文本。",
        )

        with gr.Row():
            style_input = gr.Dropdown(
                choices=[
                    "自然口语",
                    "英语学习",
                    "日语面试练习",
                    "鼓励型演讲",
                    "轻松幽默",
                    "商务表达",
                ],
                value="英语学习",
                label="生成风格",
            )

            length_input = gr.Dropdown(
                choices=[
                    "短一点，约100字",
                    "中等长度，约200字",
                    "长一点，约400字",
                ],
                value="中等长度，约200字",
                label="长度",
            )

        with gr.Row():
            model_input = gr.Textbox(
                label="OpenAI 模型名",
                value="gpt-4o-mini",
            )

            mixed_rate = gr.Slider(
                minimum=-50,
                maximum=50,
                value=0,
                step=5,
                label="语速调整",
            )

        mixed_btn = gr.Button("生成混合文本并生成语音")

        mixed_text_output = gr.Textbox(
            label="ChatGPT 生成的混合文本",
            lines=10,
        )

        mixed_audio_output = gr.Audio(
            label="生成的混合语音",
            type="filepath",
        )

        mixed_file_output = gr.File(
            label="下载 MP3 文件",
        )

        mixed_btn.click(
            fn=chatgpt_to_mixed_speech,
            inputs=[
                topic_input,
                style_input,
                length_input,
                model_input,
                mixed_rate,
            ],
            outputs=[
                mixed_text_output,
                mixed_audio_output,
                mixed_file_output,
            ],
        )


# =========================
# 启动服务
# =========================

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
    )