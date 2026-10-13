"""手动连接测试；不导入 Gradio、不调用 FFmpeg、无离线兜底。"""
import argparse
import asyncio
import sys
from importlib.metadata import version
from tts_service import save_edge, TTSError


def main():
    # 日文 Windows 的 cp932 无法输出全部中文诊断。
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Edge TTS 独立在线连接测试')
    parser.add_argument('--text', default='你好，这是语音连接测试。')
    parser.add_argument('--voice', default='zh-CN-XiaoxiaoNeural')
    parser.add_argument('--output', default='edge_connection_test.mp3')
    args = parser.parse_args()
    print(f"edge-tts {version('edge-tts')} / aiohttp {version('aiohttp')}")
    try:
        path = asyncio.run(save_edge(args.text, args.voice, 0, args.output, attempts=1))
    except TTSError as error:
        print(str(error))
        return 1
    print(f'连接成功，音频已保存：{path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
