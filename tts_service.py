"""统一在线连接处理；不修改身份、认证或请求头。"""
import asyncio
import random
import uuid
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import aiohttp
import edge_tts


class TTSError(RuntimeError):
    pass


def describe_error(error):
    status = getattr(error, 'status', None)
    if status == 403:
        return 'Edge TTS 拒绝连接（403）。请更新依赖、检查系统时间及网络策略；服务可能限制访问。不会自动重试或绕过限制，可使用离线引擎。'
    if status == 429:
        return 'Edge TTS 请求过多（429）。请稍后再试，减少请求频率。'
    if status == 503:
        return 'Edge TTS 服务暂时不可用（503）。请稍后再试或使用离线引擎。'
    if isinstance(error, TimeoutError):
        return 'Edge TTS 连接或接收超时。请检查网络或使用离线引擎。'
    if isinstance(error, aiohttp.ClientSSLError):
        return 'Edge TTS TLS 证书验证失败。请检查系统时间、证书和代理。'
    if isinstance(error, edge_tts.exceptions.NoAudioReceived):
        return 'Edge TTS 未返回音频。请检查文本、声音和服务状态。'
    if isinstance(error, aiohttp.ClientError):
        return f'Edge TTS 连接异常（{status or type(error).__name__}）。请检查网络、DNS、防火墙和代理。'
    return f'语音生成失败（{type(error).__name__}）：{error}'


def retryable(error):
    status = getattr(error, 'status', None)
    if status is not None:
        return status in (429, 500, 502, 503, 504)
    if isinstance(error, aiohttp.ClientSSLError):
        return False
    return isinstance(error, (TimeoutError, aiohttp.ClientConnectionError,
                              aiohttp.ClientPayloadError, edge_tts.exceptions.NoAudioReceived))


def retry_delay(error, attempt):
    delay = min(8, 2 ** attempt) + random.uniform(0, 0.5)
    value = (getattr(error, 'headers', None) or {}).get('Retry-After')
    if value:
        try:
            delay = max(delay, float(value))
        except ValueError:
            try:
                delay = max(delay, (parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())
            except (ValueError, TypeError, OverflowError):
                pass
    return delay


async def save_edge(text, voice, rate, output_path, *, attempts=3, timeout=120):
    if attempts < 1:
        raise ValueError('attempts 必须至少为 1')
    target = Path(output_path)
    partial = target.with_name(target.name + f'.{uuid.uuid4().hex}.part')
    try:
        for attempt in range(attempts):
            try:
                communicate = edge_tts.Communicate(text=text, voice=voice,
                    rate=f'{int(rate):+d}%', volume='+0%', connect_timeout=10, receive_timeout=60)
                await asyncio.wait_for(communicate.save(str(partial)), timeout=timeout)
                if not partial.exists() or not partial.stat().st_size:
                    raise edge_tts.exceptions.NoAudioReceived('empty audio')
                partial.replace(target)
                return str(target)
            except Exception as error:
                partial.unlink(missing_ok=True)
                if not retryable(error) or attempt == attempts - 1:
                    raise TTSError(describe_error(error)) from error
                delay = retry_delay(error, attempt)
                if delay > 60:
                    raise TTSError(describe_error(error) + f' 服务要求等待约 {delay:.0f} 秒。') from error
                await asyncio.sleep(delay)
    finally:
        partial.unlink(missing_ok=True)


async def synthesize(text, voice, rate, output_path, engine='Edge 在线', fallback=False, notify=None):
    from offline_tts import save_offline
    if engine == 'Windows 离线':
        return await asyncio.to_thread(save_offline, text, voice, rate, output_path)
    try:
        return await save_edge(text, voice, rate, output_path)
    except TTSError as error:
        if not fallback:
            raise
        if notify:
            notify(str(error) + ' 正在使用 Windows 离线声音。')
        try:
            return await asyncio.to_thread(save_offline, text, voice, rate, output_path)
        except Exception as offline_error:
            raise TTSError(f'{error}\n离线备用失败：{offline_error}') from offline_error
