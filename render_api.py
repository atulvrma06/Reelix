import shutil
import os
from fastapi import FastAPI
from importlib.metadata import version

app = FastAPI(title='Reelix backend diagnostics')

@app.get('/')
@app.get('/health')
def health():
    return {'status': 'ok', 'ffmpeg': bool(shutil.which('ffmpeg')), 'node': bool(shutil.which('node')), 'yt_dlp': version('yt-dlp'), 'provider_configured': bool(os.getenv('BGUTIL_BASE_URL'))}
