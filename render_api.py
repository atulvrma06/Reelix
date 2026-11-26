import shutil
import os
import tempfile
import threading
from fastapi import FastAPI
from importlib.metadata import version
import yt_dlp

app = FastAPI(title='Reelix backend diagnostics')
lock = threading.Lock()

@app.get('/')
@app.get('/health')
def health():
    return {'status': 'ok', 'ffmpeg': bool(shutil.which('ffmpeg')), 'node': bool(shutil.which('node')), 'yt_dlp': version('yt-dlp'), 'provider_configured': bool(os.getenv('BGUTIL_BASE_URL'))}

@app.get('/test-download')
def test_download():
    if not lock.acquire(blocking=False):
        return {'status': 'busy'}
    try:
        with tempfile.TemporaryDirectory() as folder:
            args = {'youtube': {'player_client': ['mweb', 'web_safari', 'tv']}}
            provider = os.getenv('BGUTIL_BASE_URL')
            if provider:
                args['youtubepot-bgutilhttp'] = {'base_url': [provider]}
            options = {'extractor_args': args, 'format': '18', 'outtmpl': folder + '/test.%(ext)s', 'test': True, 'noplaylist': True, 'socket_timeout': 20, 'retries': 0, 'fragment_retries': 0, 'extractor_retries': 0, 'js_runtimes': {'node': {'path': shutil.which('node')}}, 'quiet': False}
            with yt_dlp.YoutubeDL(options) as ydl:
                ydl.download(['https://www.youtube.com/watch?v=YE7VzlLtp-4'])
            size = sum(os.path.getsize(os.path.join(folder, f)) for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f)))
            return {'status': 'ok' if size else 'no_data', 'sample_bytes': size}
    except Exception as exc:
        message = str(exc)
        return {'status': 'failed', 'error': 'HTTP 403' if '403' in message else 'Download diagnostic failed; inspect Render logs'}
    finally:
        lock.release()
