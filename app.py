import gradio as gr
import edge_tts
import asyncio
import uuid
import os
import re
import shutil
from typing import List, Tuple, Optional

from openai import OpenAI
from pydub import AudioSegment


# =========================
# 基本设置
# =========================

OUTPUT_DIR = "outputs"
API_KEY_FILE = "openai_api_key.txt"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================
# 普通语音设置
# =========================

VOICE_MAP = {
    "中文": "zh-CN-XiaoxiaoNeural",
    "日语": "ja-JP-NanamiNeural",
    "英语": "en-US-JennyNeural",
    "混合": "en-US-JennyNeural",
}


# =========================
# 双人对话语音设置
# =========================

DIALOGUE_VOICE_MAP = {
    # Speaker 1：女声
    "Speaker 1": "zh-CN-XiaoxiaoNeural",

    # Speaker 2：男声
    "Speaker 2": "zh-CN-YunxiNeural",
}


# 对话之间默认停顿时间，单位：毫秒
DIALOGUE_PAUSE_MS = 450


# =========================
# 读取 OpenAI API Key
# =========================

def read_openai_api_key() -> str:
    """
    从项目目录下的 openai_api_key.txt 读取 OpenAI API Key。
    """

    if not os.path.exists(API_KEY_FILE):
        raise gr.Error(
            "找不到 openai_api_key.txt。"
            "请在项目目录下创建该文件，并写入 OpenAI API Key。"
        )

    with open(API_KEY_FILE, "r", encoding="utf-8") as file:
        api_key = file.read().strip()

    if not api_key:
        raise gr.Error(
            "openai_api_key.txt 内容为空，请写入 OpenAI API Key。"
        )

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
    调用 OpenAI API，生成中日英混合朗读文本。
    """

    if not user_topic or not user_topic.strip():
        raise gr.Error("请输入主题或原始文本。")

    api_key = read_openai_api_key()
    client = OpenAI(api_key=api_key)

    prompt = f"""
请根据用户输入，生成一段适合语音朗读的中日英混合文本。

要求：
1. 使用中文、日语、英语三种语言自然混合。
2. 不要使用 Markdown。
3. 不要使用项目符号。
4. 句子适合 TTS 朗读。
5. 内容自然，有节奏感。
6. 不要输出解释，只输出最终朗读文本。
7. 中文、日语、英语之间可以自然切换。
8. 内容适合语言学习者反复收听。

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
            raise gr.Error(
                "OpenAI API 返回了空内容，请更换主题或模型后重试。"
            )

        return result

    except gr.Error:
        raise

    except Exception as error:
        raise gr.Error(f"调用 OpenAI API 失败：{error}")


# =========================
# ChatGPT 生成双人对话
# =========================

def generate_dialogue_text(
    user_topic: str,
    style: str,
    length: str,
    model_name: str,
) -> str:
    """
    调用 OpenAI API，将用户输入转换成双人问答格式。
    """

    if not user_topic or not user_topic.strip():
        raise gr.Error("请输入对话主题或原始技术内容。")

    api_key = read_openai_api_key()
    client = OpenAI(api_key=api_key)

    prompt = f"""
请根据用户输入，生成一段适合双人语音播放的技术问答对话。

输出格式必须严格如下：

Speaker 1：问题内容
Speaker 2：参考答案内容
Speaker 1：下一个问题
Speaker 2：下一个参考答案

要求：
1. Speaker 1 是提问者。
2. Speaker 2 是回答者。
3. 每次发言单独占一行。
4. 每一行必须以“Speaker 1：”或“Speaker 2：”开头。
5. 不要输出 Markdown。
6. 不要使用星号、井号或代码块。
7. 不要输出标题、前言或额外说明。
8. 不要增加其他说话者。
9. 问题应该明确。
10. 答案应该准确、完整、容易理解。
11. 内容适合 TTS 自然朗读。
12. 可以包含中文、日语、英语和技术术语。
13. 每个问题后面紧接对应答案。
14. Speaker 1 和 Speaker 2 只用于识别人物，实际朗读时不会读出。

对话风格：{style}
对话长度：{length}

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
            raise gr.Error(
                "OpenAI API 返回了空内容，请更换主题或模型后重试。"
            )

        result = result.replace("```text", "")
        result = result.replace("```plaintext", "")
        result = result.replace("```", "")
        result = result.strip()

        return result

    except gr.Error:
        raise

    except Exception as error:
        raise gr.Error(f"调用 OpenAI API 失败：{error}")


# =========================
# 指定声音生成单段语音
# =========================

async def generate_tts_with_voice_async(
    text: str,
    voice: str,
    rate: int,
    output_path: Optional[str] = None,
) -> str:
    """
    使用指定声音生成 MP3。
    """

    if not text or not text.strip():
        raise gr.Error("需要朗读的文本不能为空。")

    if not voice:
        raise gr.Error("没有找到对应的语音设置。")

    if output_path is None:
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        output_path = os.path.join(OUTPUT_DIR, filename)

    rate_text = f"{int(rate):+d}%"

    communicate = edge_tts.Communicate(
        text=text.strip(),
        voice=voice,
        rate=rate_text,
        volume="+0%",
    )

    await communicate.save(output_path)

    return output_path


# =========================
# 普通文本生成语音
# =========================

async def generate_tts_async(
    text: str,
    language: str,
    rate: int,
) -> str:
    """
    根据语言选择声音并生成普通语音。
    """

    if not text or not text.strip():
        raise gr.Error("请输入文本。")

    voice = VOICE_MAP.get(language)

    if voice is None:
        raise gr.Error("请选择正确的输出语言。")

    return await generate_tts_with_voice_async(
        text=text,
        voice=voice,
        rate=rate,
    )


def text_to_speech(
    text: str,
    language: str,
    rate: int,
):
    """
    普通文本转语音。
    """

    try:
        output_path = asyncio.run(
            generate_tts_async(
                text=text,
                language=language,
                rate=rate,
            )
        )

        return output_path, output_path

    except gr.Error:
        raise

    except Exception as error:
        raise gr.Error(f"生成语音失败：{error}")


# =========================
# ChatGPT 混合文本转语音
# =========================

def chatgpt_to_mixed_speech(
    user_topic: str,
    style: str,
    length: str,
    model_name: str,
    rate: int,
):
    """
    先生成混合文本，再生成语音。
    """

    mixed_text = generate_mixed_text(
        user_topic=user_topic,
        style=style,
        length=length,
        model_name=model_name,
    )

    try:
        audio_path = asyncio.run(
            generate_tts_async(
                text=mixed_text,
                language="混合",
                rate=rate,
            )
        )

        return mixed_text, audio_path, audio_path

    except gr.Error:
        raise

    except Exception as error:
        raise gr.Error(f"生成混合语音失败：{error}")


# =========================
# 双人对话文本规范化
# =========================

def normalize_dialogue_text(text: str) -> str:
    """
    统一 Speaker 格式。

    支持：
    Speaker 1：
    Speaker 1:
    Speaker1：
    Speaker1:
    speaker 1:
    """

    normalized = text.replace("\r\n", "\n")
    normalized = normalized.replace("\r", "\n")
    normalized = normalized.replace("\u3000", " ")

    normalized = re.sub(
        r"(?i)speaker\s*1\s*[：:]",
        "Speaker 1：",
        normalized,
    )

    normalized = re.sub(
        r"(?i)speaker\s*2\s*[：:]",
        "Speaker 2：",
        normalized,
    )

    return normalized.strip()


# =========================
# 解析双人对话
# =========================

def parse_dialogue(text: str) -> List[Tuple[str, str]]:
    """
    将对话解析为：

    [
        ("Speaker 1", "问题正文"),
        ("Speaker 2", "答案正文"),
    ]

    Speaker 标签不会进入正文，所以不会被朗读。
    """

    if not text or not text.strip():
        raise gr.Error("请输入双人对话文本。")

    normalized_text = normalize_dialogue_text(text)

    pattern = re.compile(
        r"(Speaker\s*[12])\s*[：:]\s*"
        r"(.*?)"
        r"(?=(?:\n\s*)?Speaker\s*[12]\s*[：:]|\Z)",
        flags=re.IGNORECASE | re.DOTALL,
    )

    matches = pattern.findall(normalized_text)

    dialogue_items: List[Tuple[str, str]] = []

    for raw_speaker, raw_content in matches:
        speaker_number_match = re.search(r"[12]", raw_speaker)

        if speaker_number_match is None:
            continue

        speaker_number = speaker_number_match.group()
        speaker = f"Speaker {speaker_number}"

        content = re.sub(
            r"\s*\n+\s*",
            "，",
            raw_content,
        )

        content = re.sub(
            r"\s+",
            " ",
            content,
        )

        content = content.strip(" ，、")

        if content:
            dialogue_items.append(
                (
                    speaker,
                    content,
                )
            )

    if not dialogue_items:
        raise gr.Error(
            "没有识别到有效对话。"
            "请确保每段以“Speaker 1：”或“Speaker 2：”开头。"
        )

    return dialogue_items


# =========================
# 格式化对话预览
# =========================

def format_dialogue_preview(
    dialogue_items: List[Tuple[str, str]],
) -> str:
    """
    页面中继续显示 Speaker 标签。
    """

    lines = []

    for speaker, content in dialogue_items:
        lines.append(f"{speaker}：{content}")

    return "\n".join(lines)


# =========================
# 生成双人对话语音
# =========================

async def generate_dialogue_tts_async(
    dialogue_text: str,
    speaker_1_rate: int,
    speaker_2_rate: int,
    pause_ms: int,
) -> Tuple[str, str]:
    """
    Speaker 1 使用女声。
    Speaker 2 使用男声。

    注意：
    实际朗读时，只朗读冒号后面的正文。
    不会朗读 Speaker 1 和 Speaker 2。
    """

    dialogue_items = parse_dialogue(dialogue_text)

    session_id = uuid.uuid4().hex

    temp_dir = os.path.join(
        OUTPUT_DIR,
        f"dialogue_temp_{session_id}",
    )

    os.makedirs(
        temp_dir,
        exist_ok=True,
    )

    segment_paths: List[str] = []

    try:
        for index, (speaker, content) in enumerate(dialogue_items):
            voice = DIALOGUE_VOICE_MAP.get(speaker)

            if voice is None:
                raise gr.Error(
                    f"没有设置 {speaker} 对应的声音。"
                )

            if speaker == "Speaker 1":
                current_rate = int(speaker_1_rate)
            else:
                current_rate = int(speaker_2_rate)

            # 只朗读正文，不朗读 Speaker 标签
            speech_text = content

            segment_path = os.path.join(
                temp_dir,
                f"segment_{index:04d}.mp3",
            )

            await generate_tts_with_voice_async(
                text=speech_text,
                voice=voice,
                rate=current_rate,
                output_path=segment_path,
            )

            segment_paths.append(segment_path)

        if not segment_paths:
            raise gr.Error("没有生成任何对话语音。")

        combined_audio = AudioSegment.empty()

        safe_pause_ms = max(
            0,
            int(pause_ms),
        )

        pause_audio = AudioSegment.silent(
            duration=safe_pause_ms,
        )

        for index, segment_path in enumerate(segment_paths):
            segment_audio = AudioSegment.from_file(
                segment_path,
                format="mp3",
            )

            combined_audio += segment_audio

            if index < len(segment_paths) - 1:
                combined_audio += pause_audio

        final_filename = f"dialogue_{session_id}.mp3"

        final_output_path = os.path.join(
            OUTPUT_DIR,
            final_filename,
        )

        combined_audio.export(
            final_output_path,
            format="mp3",
            bitrate="192k",
        )

        preview_text = format_dialogue_preview(
            dialogue_items
        )

        return preview_text, final_output_path

    finally:
        shutil.rmtree(
            temp_dir,
            ignore_errors=True,
        )


# =========================
# 直接输入双人对话转语音
# =========================

def dialogue_to_speech(
    dialogue_text: str,
    speaker_1_rate: int,
    speaker_2_rate: int,
    pause_ms: int,
):
    """
    将已有双人对话转换成语音。
    """

    try:
        preview_text, audio_path = asyncio.run(
            generate_dialogue_tts_async(
                dialogue_text=dialogue_text,
                speaker_1_rate=speaker_1_rate,
                speaker_2_rate=speaker_2_rate,
                pause_ms=pause_ms,
            )
        )

        return preview_text, audio_path, audio_path

    except gr.Error:
        raise

    except Exception as error:
        raise gr.Error(f"生成双人对话语音失败：{error}")


# =========================
# ChatGPT 自动生成双人对话并转语音
# =========================

def chatgpt_to_dialogue_speech(
    user_topic: str,
    dialogue_style: str,
    dialogue_length: str,
    model_name: str,
    speaker_1_rate: int,
    speaker_2_rate: int,
    pause_ms: int,
):
    """
    先使用 ChatGPT 生成双人对话，
    再生成女声和男声交替的语音。
    """

    dialogue_text = generate_dialogue_text(
        user_topic=user_topic,
        style=dialogue_style,
        length=dialogue_length,
        model_name=model_name,
    )

    try:
        preview_text, audio_path = asyncio.run(
            generate_dialogue_tts_async(
                dialogue_text=dialogue_text,
                speaker_1_rate=speaker_1_rate,
                speaker_2_rate=speaker_2_rate,
                pause_ms=pause_ms,
            )
        )

        return preview_text, audio_path, audio_path

    except gr.Error:
        raise

    except Exception as error:
        raise gr.Error(f"生成双人对话语音失败：{error}")


# =========================
# 默认示例
# =========================

DEFAULT_DIALOGUE_EXAMPLE = """Speaker 1：问题 1 回顾：同一设备同时支持 Syslog 和 SNMP 时怎样分工？
Speaker 2：参考答案：Syslog 适合设备主动上报文本事件，SNMP 适合结构化指标查询和 Trap；两者可以互补，并通过时间和设备标识进行关联。
Speaker 1：为什么不能只使用 Syslog？
Speaker 2：因为 Syslog 主要提供设备主动发送的日志和事件信息，不适合持续、结构化地获取 CPU 使用率、内存使用率和接口流量等指标。
Speaker 1：SNMP Trap 和 SNMP GET 有什么区别？
Speaker 2：SNMP Trap 是设备主动发送异常通知，SNMP GET 是监控系统主动查询设备指标。两者结合后，可以同时获得实时告警和周期性状态数据。"""


# =========================
# Gradio 页面
# =========================

with gr.Blocks(
    title="文本转语音 / ChatGPT 混合语音 / 双人对话生成器"
) as demo:

    gr.Markdown(
        "# 文本转语音 / ChatGPT 混合语音 / 双人对话生成器"
    )

    gr.Markdown(
        """
支持以下功能：

1. 普通文本转语音
2. ChatGPT 自动生成中日英混合文本并转语音
3. Speaker 1 女声、Speaker 2 男声的双人对话语音

注意：双人对话中不会朗读 Speaker 1 和 Speaker 2。
"""
    )

    # =========================
    # Tab 1：普通文本转语音
    # =========================

    with gr.Tab("普通文本转语音"):
        language = gr.Dropdown(
            choices=[
                "中文",
                "日语",
                "英语",
            ],
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

        generate_btn = gr.Button(
            "生成语音",
            variant="primary",
        )

        audio_output = gr.Audio(
            label="生成的语音",
            type="filepath",
        )

        file_output = gr.File(
            label="下载 MP3 文件",
        )

        generate_btn.click(
            fn=text_to_speech,
            inputs=[
                text_input,
                language,
                rate,
            ],
            outputs=[
                audio_output,
                file_output,
            ],
        )

    # =========================
    # Tab 2：ChatGPT 生成混合语音
    # =========================

    with gr.Tab("ChatGPT 生成混合语音"):
        topic_input = gr.Textbox(
            label="请输入主题或原始文本",
            lines=6,
            placeholder=(
                "例如：帮我生成一段关于坚持学习英语、"
                "日语和 AI 技术的中日英混合朗读文本。"
            ),
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

        mixed_btn = gr.Button(
            "生成混合文本并生成语音",
            variant="primary",
        )

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
    # Tab 3：双人对话语音
    # =========================

    with gr.Tab("双人对话语音"):
        gr.Markdown(
            """
输入格式：

Speaker 1：问题内容  
Speaker 2：参考答案内容

Speaker 1 使用女声，Speaker 2 使用男声。  
实际朗读时不会读出 Speaker 1 和 Speaker 2。
"""
        )

        with gr.Tabs():

            # -------------------------
            # 直接输入已有对话
            # -------------------------

            with gr.Tab("直接输入对话"):
                dialogue_input = gr.Textbox(
                    label="请输入 Speaker 1 / Speaker 2 对话",
                    lines=16,
                    value=DEFAULT_DIALOGUE_EXAMPLE,
                    placeholder=(
                        "Speaker 1：这里填写问题。\n"
                        "Speaker 2：这里填写参考答案。"
                    ),
                )

                with gr.Row():
                    speaker_1_rate = gr.Slider(
                        minimum=-50,
                        maximum=50,
                        value=0,
                        step=5,
                        label="Speaker 1 女声语速",
                    )

                    speaker_2_rate = gr.Slider(
                        minimum=-50,
                        maximum=50,
                        value=0,
                        step=5,
                        label="Speaker 2 男声语速",
                    )

                dialogue_pause = gr.Slider(
                    minimum=0,
                    maximum=2000,
                    value=DIALOGUE_PAUSE_MS,
                    step=50,
                    label="每段对话之间的停顿时间（毫秒）",
                )

                dialogue_generate_btn = gr.Button(
                    "生成双人对话语音",
                    variant="primary",
                )

                dialogue_preview_output = gr.Textbox(
                    label="解析后的对话内容",
                    lines=14,
                )

                dialogue_audio_output = gr.Audio(
                    label="双人对话语音",
                    type="filepath",
                )

                dialogue_file_output = gr.File(
                    label="下载双人对话 MP3",
                )

                dialogue_generate_btn.click(
                    fn=dialogue_to_speech,
                    inputs=[
                        dialogue_input,
                        speaker_1_rate,
                        speaker_2_rate,
                        dialogue_pause,
                    ],
                    outputs=[
                        dialogue_preview_output,
                        dialogue_audio_output,
                        dialogue_file_output,
                    ],
                )

            # -------------------------
            # ChatGPT 自动生成双人对话
            # -------------------------

            with gr.Tab("ChatGPT 自动生成对话"):
                dialogue_topic_input = gr.Textbox(
                    label="请输入对话主题或原始技术内容",
                    lines=8,
                    placeholder=(
                        "例如：根据 Syslog、SNMP GET、SNMP Trap、"
                        "TCP Ping 的区别，生成详细复习问答。"
                    ),
                )

                with gr.Row():
                    dialogue_style_input = gr.Dropdown(
                        choices=[
                            "技术复习问答",
                            "初学者讲解",
                            "深入技术面试",
                            "轻松自然对话",
                            "教师与学生问答",
                            "面试官与应聘者",
                        ],
                        value="技术复习问答",
                        label="对话风格",
                    )

                    dialogue_length_input = gr.Dropdown(
                        choices=[
                            "简短，生成3组问答",
                            "中等，生成6组问答",
                            "详细，生成10组问答",
                            "非常详细，生成15组问答",
                        ],
                        value="中等，生成6组问答",
                        label="对话长度",
                    )

                dialogue_model_input = gr.Textbox(
                    label="OpenAI 模型名",
                    value="gpt-4o-mini",
                )

                with gr.Row():
                    generated_speaker_1_rate = gr.Slider(
                        minimum=-50,
                        maximum=50,
                        value=0,
                        step=5,
                        label="Speaker 1 女声语速",
                    )

                    generated_speaker_2_rate = gr.Slider(
                        minimum=-50,
                        maximum=50,
                        value=0,
                        step=5,
                        label="Speaker 2 男声语速",
                    )

                generated_dialogue_pause = gr.Slider(
                    minimum=0,
                    maximum=2000,
                    value=DIALOGUE_PAUSE_MS,
                    step=50,
                    label="每段对话之间的停顿时间（毫秒）",
                )

                chatgpt_dialogue_btn = gr.Button(
                    "生成双人对话文本并生成语音",
                    variant="primary",
                )

                generated_dialogue_output = gr.Textbox(
                    label="ChatGPT 生成的双人对话",
                    lines=16,
                )

                generated_dialogue_audio_output = gr.Audio(
                    label="生成的双人对话语音",
                    type="filepath",
                )

                generated_dialogue_file_output = gr.File(
                    label="下载双人对话 MP3",
                )

                chatgpt_dialogue_btn.click(
                    fn=chatgpt_to_dialogue_speech,
                    inputs=[
                        dialogue_topic_input,
                        dialogue_style_input,
                        dialogue_length_input,
                        dialogue_model_input,
                        generated_speaker_1_rate,
                        generated_speaker_2_rate,
                        generated_dialogue_pause,
                    ],
                    outputs=[
                        generated_dialogue_output,
                        generated_dialogue_audio_output,
                        generated_dialogue_file_output,
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