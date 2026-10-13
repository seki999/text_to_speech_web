import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, Mock
import aiohttp
import pytest
import tts_service as service


def http_error(status, headers=None):
    return aiohttp.WSServerHandshakeError(Mock(real_url='https://example.invalid'), (),
        status=status, message='mock', headers=headers)


@pytest.mark.parametrize('error,count,word', [
    (http_error(403), 1, '403'), (http_error(429), 3, '429'),
    (http_error(503), 3, '503'), (http_error(400), 1, '400'),
    (TimeoutError(), 3, '超时'), (aiohttp.ClientConnectionError(), 3, '连接异常'),
    (ValueError('invalid'), 1, 'ValueError'),
])
def test_errors(monkeypatch, tmp_path, error, count, word):
    save = AsyncMock(side_effect=error)
    factory = Mock(return_value=Mock(save=save))
    sleep = AsyncMock()
    monkeypatch.setattr(service.edge_tts, 'Communicate', factory)
    monkeypatch.setattr(service.asyncio, 'sleep', sleep)
    with pytest.raises(service.TTSError, match=word):
        asyncio.run(service.save_edge('test', 'en-US-JennyNeural', 0, tmp_path / 'a.mp3'))
    assert factory.call_count == count
    assert sleep.await_count == count - 1
    assert not list(tmp_path.iterdir())


def test_retry_success_and_cleanup(monkeypatch, tmp_path):
    calls = []
    async def save(path):
        calls.append(path)
        Path(path).write_bytes(b'partial' if len(calls) == 1 else b'audio')
        if len(calls) == 1:
            raise http_error(503)
    factory = Mock(side_effect=lambda **kwargs: Mock(save=save))
    monkeypatch.setattr(service.edge_tts, 'Communicate', factory)
    monkeypatch.setattr(service.asyncio, 'sleep', AsyncMock())
    output = tmp_path / 'a.mp3'
    asyncio.run(service.save_edge('test', 'en-US-JennyNeural', -20, output))
    assert output.read_bytes() == b'audio'
    assert len(list(tmp_path.iterdir())) == 1
    assert factory.call_count == 2
    assert factory.call_args.kwargs['rate'] == '-20%'


def test_retry_after(monkeypatch):
    monkeypatch.setattr(service.random, 'uniform', lambda *args: 0)
    assert service.retry_delay(http_error(429, {'Retry-After': '12'}), 0) == 12
    assert service.retry_delay(http_error(503), 1) == 2


def test_long_retry_after(monkeypatch, tmp_path):
    save = AsyncMock(side_effect=http_error(429, {'Retry-After': '120'}))
    monkeypatch.setattr(service.edge_tts, 'Communicate', Mock(return_value=Mock(save=save)))
    with pytest.raises(service.TTSError, match='120'):
        asyncio.run(service.save_edge('test', 'en-US-JennyNeural', 0, tmp_path / 'a.mp3'))
    assert save.await_count == 1


def test_fallback(monkeypatch, tmp_path):
    import offline_tts
    monkeypatch.setattr(service, 'save_edge', AsyncMock(side_effect=service.TTSError('403')))
    offline = Mock(return_value='offline.mp3')
    monkeypatch.setattr(offline_tts, 'save_offline', offline)
    notify = Mock()
    assert asyncio.run(service.synthesize('test', 'en-US-JennyNeural', 20,
        tmp_path / 'a.mp3', fallback=True, notify=notify)) == 'offline.mp3'
    offline.assert_called_once()
    notify.assert_called_once()


def test_offline_direct(monkeypatch):
    import offline_tts
    online = AsyncMock()
    monkeypatch.setattr(service, 'save_edge', online)
    monkeypatch.setattr(offline_tts, 'save_offline', Mock(return_value='local.mp3'))
    assert asyncio.run(service.synthesize('test', 'en-US-JennyNeural', 0, 'a.mp3',
                                         engine='Windows 离线')) == 'local.mp3'
    online.assert_not_called()


def test_dialogue_merge(monkeypatch, tmp_path):
    import app
    from pydub import AudioSegment
    monkeypatch.setattr(app, 'OUTPUT_DIR', str(tmp_path))
    recorded = []
    async def fake(text, voice, rate, output_path=None, **kwargs):
        recorded.append((text, voice, rate))
        AudioSegment.silent(duration=100).export(output_path, format='mp3')
        return output_path
    monkeypatch.setattr(app, 'generate_tts_with_voice_async', fake)
    preview, path = asyncio.run(app.generate_dialogue_tts_async(
        'Speaker1: Hello [abc]\nSpeaker 2：你好', '英文女声', '中文男声', -20, 30, 200))
    assert recorded == [('Hello', 'en-US-JennyNeural', -20), ('你好', 'zh-CN-YunxiNeural', 30)]
    assert 'Speaker 2' in preview
    assert abs(len(AudioSegment.from_mp3(path)) - 400) < 30
    assert not list(tmp_path.glob('dialogue_temp_*'))


def test_plain_download(monkeypatch, tmp_path):
    import app
    monkeypatch.setattr(app, 'OUTPUT_DIR', str(tmp_path))
    fake = AsyncMock()
    monkeypatch.setattr(app, 'synthesize', fake)
    audio, download = app.text_to_speech('你好', '中文', 15)
    assert audio == download
    assert fake.call_args.args[:3] == ('你好', 'zh-CN-XiaoxiaoNeural', 15)


def test_empty_audio(monkeypatch, tmp_path):
    monkeypatch.setattr(service.edge_tts, 'Communicate', Mock(return_value=Mock(save=AsyncMock())))
    monkeypatch.setattr(service.asyncio, 'sleep', AsyncMock())
    with pytest.raises(service.TTSError, match='未返回音频'):
        asyncio.run(service.save_edge('test', 'en-US-JennyNeural', 0, tmp_path / 'a.mp3'))
    assert not list(tmp_path.iterdir())


def test_cancel_cleanup(monkeypatch, tmp_path):
    async def cancel(path):
        Path(path).write_bytes(b'partial')
        raise asyncio.CancelledError()
    monkeypatch.setattr(service.edge_tts, 'Communicate', Mock(return_value=Mock(save=cancel)))
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(service.save_edge('test', 'en-US-JennyNeural', 0, tmp_path / 'a.mp3'))
    assert not list(tmp_path.iterdir())


def test_fallback_failure(monkeypatch):
    import offline_tts
    monkeypatch.setattr(service, 'save_edge', AsyncMock(side_effect=service.TTSError('403')))
    monkeypatch.setattr(offline_tts, 'save_offline', Mock(side_effect=RuntimeError('missing voice')))
    with pytest.raises(service.TTSError, match='离线备用失败'):
        asyncio.run(service.synthesize('test', 'en-US-JennyNeural', 0, 'a.mp3', fallback=True))
