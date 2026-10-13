"""Windows System.Speech 备用引擎，不需要 Python COM 包。"""
import json
import os
import subprocess
import tempfile
from pathlib import Path


def save_offline(text, voice, rate, output_path):
    if os.name != 'nt':
        raise RuntimeError('Windows 离线引擎仅支持 Windows。')
    from pydub import AudioSegment
    with tempfile.TemporaryDirectory(prefix='tts_offline_') as directory:
        directory = Path(directory)
        payload = directory / 'input.json'
        wav = directory / 'speech.wav'
        gender = 'Male' if any(name in voice for name in ('Yunxi', 'Guy')) else 'Female'
        payload.write_text(json.dumps(dict(text=text, locale=voice[:5], gender=gender,
            rate=max(-10, min(10, round(int(rate) / 10)))), ensure_ascii=False), encoding='utf-8')
        try:
            result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-File',
                str(Path(__file__).with_name('windows_tts.ps1')), str(payload), str(wav)],
                capture_output=True, timeout=120, creationflags=subprocess.CREATE_NO_WINDOW)
        except subprocess.TimeoutExpired as error:
            raise RuntimeError('Windows 离线合成超时，请缩短文本。') from error
        if result.returncode:
            raise RuntimeError('Windows 离线合成失败：' + result.stderr.decode('utf-8', errors='replace'))
        AudioSegment.from_wav(wav).export(output_path, format='mp3', bitrate='192k')
    return str(output_path)
