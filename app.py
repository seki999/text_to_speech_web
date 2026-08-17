import gradio as gr
import edge_tts
import asyncio
import uuid
import os
import re
import shutil
from typing import List, Tuple, Optional

from pydub import AudioSegment


# =========================
# 基本设置
# =========================

OUTPUT_DIR = "outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)


# =========================
# 普通语音设置
# =========================

VOICE_MAP = {
    "中文": "zh-CN-XiaoxiaoNeural",
    "日语": "ja-JP-NanamiNeural",
    "英语": "en-US-JennyNeural",
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

    规则：
    1. 带有 Speaker 1：或 Speaker 2：的句子，使用对应声音。
    2. 没有 Speaker 标签的句子，默认使用 Speaker 1 女声。
    3. Speaker 标签不会进入正文，所以不会被朗读。
    4. 没有标签的连续多行会合并为同一个 Speaker 1 语音段。
    """

    if not text or not text.strip():
        raise gr.Error("请输入双人对话文本。")

    normalized_text = normalize_dialogue_text(text)

    # 在每一个 Speaker 标签前强制换行，兼容多个说话者写在同一行的情况。
    normalized_text = re.sub(
        r"(?<!^)\s*(?=Speaker\s*[12]：)",
        "\n",
        normalized_text,
        flags=re.IGNORECASE,
    )

    dialogue_items: List[Tuple[str, str]] = []
    current_speaker = "Speaker 1"
    current_content_parts: List[str] = []

    speaker_line_pattern = re.compile(
        r"^\s*(Speaker\s*[12])\s*[：:]\s*(.*)$",
        flags=re.IGNORECASE,
    )

    def append_current_content() -> None:
        """保存当前累计的正文。"""
        if not current_content_parts:
            return

        content = "，".join(
            part.strip(" ，、")
            for part in current_content_parts
            if part and part.strip(" ，、")
        )
        content = re.sub(r"\s+", " ", content).strip(" ，、")

        if content:
            dialogue_items.append((current_speaker, content))

        current_content_parts.clear()

    for raw_line in normalized_text.split("\n"):
        line = raw_line.strip()

        if not line:
            continue

        match = speaker_line_pattern.match(line)

        if match:
            # 遇到新的 Speaker 标签前，先保存上一段内容。
            append_current_content()

            speaker_number_match = re.search(r"[12]", match.group(1))
            if speaker_number_match is None:
                current_speaker = "Speaker 1"
            else:
                current_speaker = f"Speaker {speaker_number_match.group()}"

            content = match.group(2).strip(" ，、")
            if content:
                current_content_parts.append(content)
        else:
            # 没有 Speaker 标签：默认按照 Speaker 1 女声朗读。
            # 如果上一段本身有明确标签，则先结束上一段，避免错误继承 Speaker 2。
            append_current_content()
            current_speaker = "Speaker 1"
            current_content_parts.append(line)

    append_current_content()

    if not dialogue_items:
        raise gr.Error("没有识别到可以朗读的文本。")

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
            # 同时忽略英文方括号 [] 及其中的内容，例如：[ˈwɑːloʊ]
            speech_text = re.sub(r"\[[^\]]*\]", "", content)
            # 清理删除方括号内容后可能产生的多余空格
            speech_text = re.sub(r"\s+", " ", speech_text).strip()

            if not speech_text:
                continue

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
    title="文本转语音 / 双人对话生成器"
) as demo:

    gr.Markdown(
        "# 文本转语音 / 双人对话生成器"
    )

    gr.Markdown(
        """
支持以下功能：

1. 普通文本转语音
2. Speaker 1 女声、Speaker 2 男声的双人对话语音

注意：双人对话中不会朗读 Speaker 1 和 Speaker 2；英文方括号 [ ] 及其中内容也不会朗读。
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
    # Tab 2：双人对话语音
    # =========================

    with gr.Tab("双人对话语音"):
        gr.Markdown(
            """
输入格式：

Speaker 1：问题内容  
Speaker 2：参考答案内容

Speaker 1 使用女声，Speaker 2 使用男声。  
实际朗读时不会读出 Speaker 1 和 Speaker 2。
没有 Speaker 标签的句子默认使用 Speaker 1 女声朗读。
"""
        )

        # 直接输入已有对话
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


# =========================
# 启动服务
# =========================

if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
    )