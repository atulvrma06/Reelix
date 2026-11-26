import io
import http.client
import ipaddress
import socket
import ssl
import time
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import streamlit as st
import yt_dlp


# ==========================================
# CONFIG
# ==========================================

st.set_page_config(
    page_title="Reelix AI | Shorts Studio",
    page_icon="✂️",
    layout="wide",
)

APP_NAME = "REELIX"
DEVELOPER = "Atul Verma"
PHONE = "+91 6005090551"
PHONE_LINK = "+916005090551"
EMAIL = "vermaatul2946@gmail.com"

MAX_DURATION = 10800  # 180 minutes
VIDEO_EXTS = {".mp4", ".webm", ".mkv", ".mov"}
DEFAULT_BGUTIL_URL = "https://bgutil-ytdlp-pot-provider-3r7r.onrender.com"


# ==========================================
# DESIGN
# ==========================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #07080f;
    --card: rgba(20, 20, 40, .62);
    --line: rgba(255, 255, 255, .08);
    --violet: #8b5cf6;
    --pink: #ec4899;
    --cyan: #22d3ee;
    --text: #f5f4ff;
    --muted: #9b9dbd;
}

html, body, [class*="css"], .stApp {
    font-family: 'Plus Jakarta Sans', sans-serif;
}

.stApp {
    background:
        radial-gradient(1000px 520px at 12% -8%, rgba(139, 92, 246, .38), transparent 60%),
        radial-gradient(800px 520px at 95% 0%, rgba(236, 72, 153, .24), transparent 60%),
        radial-gradient(900px 600px at 50% 115%, rgba(34, 211, 238, .14), transparent 60%),
        var(--bg);
    color: var(--text);
}

/* subtle grid texture */
.stApp::before {
    content: "";
    position: fixed; inset: 0;
    background-image:
        linear-gradient(rgba(255,255,255,.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,.025) 1px, transparent 1px);
    background-size: 46px 46px;
    mask-image: radial-gradient(ellipse at 50% 0%, #000 20%, transparent 75%);
    -webkit-mask-image: radial-gradient(ellipse at 50% 0%, #000 20%, transparent 75%);
    pointer-events: none;
    z-index: 0;
}

#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

.block-container {
    max-width: 1000px;
    padding-top: 1.2rem;
    padding-bottom: 4rem;
    position: relative;
    z-index: 1;
}

/* ---------- Nav ---------- */
.nav {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 4px 0;
}
.logo {
    display: flex; align-items: center; gap: 10px;
    font-weight: 800; letter-spacing: .32em; font-size: .95rem; color: #fff;
}
.logo-mark {
    width: 34px; height: 34px; border-radius: 11px;
    display: grid; place-items: center; font-size: 1rem;
    background: linear-gradient(135deg, var(--violet), var(--pink));
    box-shadow: 0 8px 24px -6px rgba(168, 85, 247, .8);
}
.nav-tag {
    font-size: .74rem; color: var(--muted); font-weight: 600;
    padding: 6px 12px; border-radius: 999px;
    border: 1px solid var(--line); background: rgba(255,255,255,.03);
}

/* ---------- Hero ---------- */
.hero { text-align: center; padding: 48px 8px 12px; }

.pill {
    display: inline-flex; align-items: center; gap: 8px;
    padding: 7px 16px; border-radius: 999px;
    background: rgba(139, 92, 246, .12);
    border: 1px solid rgba(139, 92, 246, .35);
    color: #ddd2ff; font-size: .74rem; font-weight: 700; letter-spacing: .16em;
}
.dot {
    width: 7px; height: 7px; border-radius: 50%; background: #34d399;
    box-shadow: 0 0 0 0 rgba(52, 211, 153, .7);
    animation: pulse 2s infinite;
}
@keyframes pulse {
    70% { box-shadow: 0 0 0 9px rgba(52, 211, 153, 0); }
    100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0); }
}

.hero h1 {
    font-size: clamp(2.5rem, 6.4vw, 4.8rem);
    line-height: 1.04; letter-spacing: -0.05em; font-weight: 800;
    color: #fff; margin: 24px 0 16px;
}
.grad {
    background: linear-gradient(100deg, #a78bfa 0%, #f472b6 50%, #22d3ee 100%);
    background-size: 200% auto;
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shine 6s linear infinite;
}
@keyframes shine { to { background-position: 200% center; } }

.hero p {
    color: var(--muted); font-size: 1.08rem; line-height: 1.65;
    max-width: 580px; margin: 0 auto;
}

/* ---------- Feature cards ---------- */
.features {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 14px; margin: 34px 0 30px;
}
.feature {
    padding: 18px 16px; border-radius: 18px;
    background: var(--card); border: 1px solid var(--line);
    backdrop-filter: blur(12px);
    transition: transform .25s ease, border-color .25s ease;
}
.feature:hover { transform: translateY(-4px); border-color: rgba(139, 92, 246, .5); }
.feature .ic {
    width: 38px; height: 38px; border-radius: 12px; display: grid; place-items: center;
    font-size: 1.1rem; margin-bottom: 12px;
    background: linear-gradient(135deg, rgba(139,92,246,.3), rgba(236,72,153,.22));
}
.feature b { display: block; font-size: .9rem; color: #fff; margin-bottom: 3px; }
.feature span { font-size: .78rem; color: var(--muted); line-height: 1.45; }
@media (max-width: 800px) { .features { grid-template-columns: repeat(2, 1fr); } }

/* ---------- Main cards ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(160deg, rgba(30, 27, 62, .72), rgba(12, 14, 32, .72));
    border: 1px solid rgba(139, 92, 246, .2);
    border-radius: 24px;
    box-shadow: 0 30px 80px -30px rgba(0, 0, 0, .8), inset 0 1px 0 rgba(255,255,255,.05);
    backdrop-filter: blur(16px);
    padding: .9rem 1rem;
}

h2, h3 { letter-spacing: -0.03em; font-weight: 800; color: #fff; }
label, .stRadio label p, .stSlider label p, .stCheckbox label p {
    color: #cfd0ea !important; font-weight: 600 !important; font-size: .88rem !important;
}

/* ---------- Segmented radio ---------- */
div[role="radiogroup"] {
    background: rgba(255,255,255,.04);
    border: 1px solid var(--line);
    border-radius: 14px; padding: 5px; gap: 4px; width: fit-content;
}
div[role="radiogroup"] > label {
    padding: 8px 18px; border-radius: 10px; margin: 0 !important;
    cursor: pointer; transition: background .2s ease;
}
div[role="radiogroup"] > label > div:first-child { display: none; }
div[role="radiogroup"] > label:has(input:checked) {
    background: linear-gradient(110deg, #7c4dff, #c04ee8 60%, #ec4899);
    box-shadow: 0 6px 20px -6px rgba(168, 85, 247, .8);
}
div[role="radiogroup"] > label:has(input:checked) p { color: #fff !important; }

/* ---------- Inputs ---------- */
.stTextInput input {
    background: rgba(255, 255, 255, .05) !important;
    border: 1px solid rgba(255, 255, 255, .12) !important;
    border-radius: 14px !important;
    color: #fff !important;
    padding: 14px 16px !important;
}
.stTextInput input:focus {
    border-color: var(--violet) !important;
    box-shadow: 0 0 0 4px rgba(139, 92, 246, .22) !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: rgba(139, 92, 246, .05);
    border: 1.5px dashed rgba(139, 92, 246, .5);
    border-radius: 18px;
    padding: 28px;
    transition: background .2s ease, border-color .2s ease;
}
[data-testid="stFileUploaderDropzone"]:hover {
    background: rgba(139, 92, 246, .1);
    border-color: var(--pink);
}

[data-testid="stSlider"] [role="slider"] {
    background: #fff !important;
    box-shadow: 0 0 0 5px rgba(139, 92, 246, .35);
}

/* ---------- Buttons ---------- */
.stButton button, .stDownloadButton button {
    border-radius: 16px;
    font-weight: 700;
    min-height: 54px;
    letter-spacing: .01em;
    transition: transform .15s ease, box-shadow .2s ease, background .2s ease;
}
.stButton button {
    background: linear-gradient(110deg, #7c4dff, #c04ee8 60%, #ec4899);
    color: #fff; border: 0;
    box-shadow: 0 12px 34px -10px rgba(168, 85, 247, .8);
}
.stButton button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 18px 42px -10px rgba(168, 85, 247, 1);
    color: #fff;
}
.stButton button:disabled { opacity: .35; }

.stDownloadButton button {
    background: rgba(255, 255, 255, .05);
    border: 1px solid rgba(139, 92, 246, .4);
    color: #ebe6ff;
}
.stDownloadButton button:hover {
    border-color: var(--violet);
    background: rgba(139, 92, 246, .18);
    color: #fff;
}

/* ---------- Progress ---------- */
.stProgress > div > div > div > div {
    background: linear-gradient(90deg, #7c4dff, #ec4899, #22d3ee);
    border-radius: 999px;
}

/* ---------- Results ---------- */
.badge {
    display: inline-block; padding: 5px 13px; border-radius: 999px;
    font-size: .76rem; font-weight: 700; margin: 0 6px 6px 0;
    background: rgba(139, 92, 246, .16); color: #ddd2ff;
    border: 1px solid rgba(139, 92, 246, .32);
}
.badge.hot {
    background: rgba(244, 114, 182, .14); color: #fcd3e8;
    border-color: rgba(244, 114, 182, .38);
}
.meter {
    height: 8px; border-radius: 999px; background: rgba(255,255,255,.07);
    overflow: hidden; margin: 8px 0 14px;
}
.meter > div {
    height: 100%; border-radius: 999px;
    background: linear-gradient(90deg, #7c4dff, #ec4899, #fbbf24);
}

[data-testid="stVideo"] video {
    border-radius: 18px; max-height: 480px; background: #000;
    box-shadow: 0 20px 50px -20px rgba(0,0,0,.9);
}

hr { border-color: rgba(255, 255, 255, .08) !important; }

/* ---------- Footer ---------- */
.footer {
    text-align: center; padding: 38px 15px 10px; margin-top: 64px;
    border-top: 1px solid rgba(139, 92, 246, .2); color: var(--muted);
}
.footer h2 {
    letter-spacing: .5em; font-weight: 800; margin-bottom: 4px;
    background: linear-gradient(100deg, #a78bfa, #f472b6);
    -webkit-background-clip: text; background-clip: text;
    -webkit-text-fill-color: transparent;
}
.footer p { margin: 4px 0; }
.footer a { color: #c4b5fd; text-decoration: none; }
.footer a:hover { color: #fff; }
</style>
"""

HERO = """
<div class="nav">
  <div class="logo"><span class="logo-mark">✂</span>REELIX</div>
  <span class="nav-tag">Shorts Studio · v2</span>
</div>

<div class="hero">
  <span class="pill"><span class="dot"></span>AI SHORTS STUDIO</span>
  <h1>Long videos.<br><span class="grad">Shorts that stand out.</span></h1>
  <p>Drop in a video and Reelix finds the most energetic moments,
     then turns them into polished vertical clips, ready to post.</p>
</div>

<div class="features">
  <div class="feature"><div class="ic">🎧</div><b>Energy detection</b><span>Finds the loudest, most exciting moments</span></div>
  <div class="feature"><div class="ic">📱</div><b>1080×1920</b><span>True vertical for Shorts, Reels &amp; TikTok</span></div>
  <div class="feature"><div class="ic">🌫️</div><b>Blurred backdrop</b><span>No ugly black bars, ever</span></div>
  <div class="feature"><div class="ic">📦</div><b>One-click ZIP</b><span>Download every clip in one go</span></div>
</div>
"""

st.markdown(CSS, unsafe_allow_html=True)
st.markdown(HERO, unsafe_allow_html=True)


# ==========================================
# HELPERS
# ==========================================

def get_secret(key, default=""):
    """Read from Streamlit secrets, then environment variables."""
    try:
        value = st.secrets.get(key)
        if value:
            return value
    except Exception:
        pass
    return os.getenv(key, default)


def run_command(args, cwd=None):
    try:
        result = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            timeout=900,
            cwd=cwd,
        )
    except subprocess.CalledProcessError as error:
        details = (error.stderr or b"").decode(errors="ignore").strip()
        raise RuntimeError(details[-400:] or f"{args[0]} failed.") from error
    return result.stdout


def get_video_duration(src):
    output = run_command([
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(src),
    ])
    return float(output.decode().strip())


def fmt_time(seconds):
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def find_node():
    node_path = shutil.which("node")
    if node_path:
        return node_path
    try:
        import nodejs_wheel  # provided by the nodejs-wheel package
        nodejs_wheel.node(["--version"])
        return shutil.which("node")
    except Exception:
        return None


# ==========================================
# YOUTUBE DOWNLOAD
# ==========================================

def download_direct(url, folder):
    """Fetch a bounded HTTPS MP4 from a public IP, without redirects."""
    parsed = urlparse(url)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.port not in (None, 443)
            or not parsed.path.lower().endswith(".mp4")):
        raise ValueError("Enter a public HTTPS URL ending in .mp4.")
    host = parsed.hostname
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    ips = [entry[4][0] for entry in addresses]
    if not ips or any(not ipaddress.ip_address(ip).is_global for ip in ips):
        raise ValueError("Only public video servers are allowed.")
    class PinnedHTTPS(http.client.HTTPSConnection):
        def connect(self):
            raw = socket.create_connection((ips[0], 443), timeout=20)
            try:
                self.sock = self._context.wrap_socket(raw, server_hostname=host)
            except Exception:
                raw.close()
                raise
    conn = PinnedHTTPS(host, timeout=20, context=ssl.create_default_context())
    limit = 200 * 1024 * 1024
    target = folder / "source.mp4"
    deadline = time.monotonic() + 180
    try:
        path = parsed.path + ("?" + parsed.query if parsed.query else "")
        conn.request("GET", path, headers={"Accept": "video/mp4, application/octet-stream"})
        response = conn.getresponse()
        if response.status != 200:
            raise ValueError(f"Video server returned HTTP {response.status}. Redirects are not supported.")
        mime = response.getheader("Content-Type", "").split(";")[0].strip().lower()
        if mime not in {"video/mp4", "application/octet-stream"}:
            raise ValueError("The URL did not return an MP4 video.")
        declared = response.getheader("Content-Length")
        if declared and int(declared) > limit:
            raise ValueError("Direct video limit is 200 MB.")
        total = 0
        with target.open("wb") as output:
            while True:
                if time.monotonic() > deadline:
                    raise ValueError("Direct download timed out.")
                chunk = response.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > limit:
                    raise ValueError("Direct video limit is 200 MB.")
                output.write(chunk)
        if not total:
            raise ValueError("Empty video response.")
        return target
    finally:
        conn.close()


def download_youtube(url, folder):
    parsed = urlparse(url)

    allowed_hosts = {
        "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
    }

    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        raise ValueError("Please enter a valid HTTPS YouTube URL.")

    extractor_args = {
        "youtube": {"player_client": ["mweb", "web_safari", "tv"]},
    }

    options = {
        # Prefer IPv4: some hosted environments resolve YouTube media to IPv6
        # addresses that can fail with HTTP 403 during the media download.
        "source_address": "0.0.0.0",
        "extractor_args": extractor_args,
        "format": "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720]/best[height<=720]",
        "merge_output_format": "mp4",
        "outtmpl": str(folder / "source.%(ext)s"),
        "noplaylist": True,
        "max_filesize": 1024 ** 3,
        "socket_timeout": 45,
        "retries": 8,
        "fragment_retries": 8,
        "extractor_retries": 5,
        "file_access_retries": 3,
        "quiet": False,
        "no_warnings": False,
        "verbose": False,
    }

    node_path = find_node()
    if node_path:
        options["js_runtimes"] = {"node": {"path": node_path}}

    # BGUtil PO-token provider (HTTP). Secret/env var overrides the default.
    bgutil_url = get_secret("BGUTIL_BASE_URL", DEFAULT_BGUTIL_URL)
    if bgutil_url:
        extractor_args["youtubepot-bgutilhttp"] = {"base_url": [bgutil_url]}

    # Optional BGUtil script provider.
    bgutil_home = get_secret("BGUTIL_SERVER_HOME")
    if bgutil_home:
        extractor_args["youtubepot-bgutilscript"] = {"server_home": [bgutil_home]}

    # Optional authorized YouTube cookies.
    cookies = get_secret("YOUTUBE_COOKIES")
    if cookies:
        cookie_file = folder / "cookies.txt"
        cookie_file.write_text(cookies, encoding="utf-8")
        options["cookiefile"] = str(cookie_file)

    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info or info.get("is_live"):
            raise ValueError("Invalid or live video.")

        duration = float(info.get("duration") or 0)
        if not 0 < duration <= MAX_DURATION:
            raise ValueError("Video must be under 180 minutes.")

        # Reuse the freshly extracted metadata and signed media URLs rather than
        # extracting the video a second time before download.
        ydl.process_ie_result(info, download=True)

    files = [
        f for f in folder.glob("source.*")
        if f.suffix.lower() in VIDEO_EXTS
    ]

    if not files:
        raise RuntimeError("Downloaded video not found.")

    return files[0]


# ==========================================
# AUDIO HIGHLIGHT DETECTION
# ==========================================

def analyze_audio(src, duration, clip_length, count, progress):
    """Return (start_times, hype_scores 0-100) for the loudest moments."""

    progress.progress(15, text="Analyzing video audio...")

    sample_rate = 2000
    total_seconds = int(duration) + 1

    try:
        raw_audio = run_command([
            "ffmpeg", "-v", "error",
            "-i", str(src),
            "-vn", "-ac", "1", "-ar", str(sample_rate),
            "-f", "s16le", "-",
        ])

        audio = np.frombuffer(raw_audio, dtype="<i2").astype(np.float32) / 32768.0

        if len(audio) < sample_rate:
            raise ValueError("No audio found.")

        usable = (len(audio) // sample_rate) * sample_rate
        per_second = audio[:usable].reshape(-1, sample_rate)
        energy = np.sqrt(np.mean(per_second ** 2, axis=1))

    except Exception:
        energy = np.zeros(total_seconds, dtype=np.float32)

    # Pad so every window slice is full length.
    needed = total_seconds + clip_length
    if len(energy) < needed:
        energy = np.pad(energy, (0, needed - len(energy)))

    progress.progress(25, text="Finding interesting moments...")

    last_start = int(duration - clip_length)
    if last_start < 0:
        raise ValueError("Video is shorter than clip duration.")

    starts = list(range(0, last_start + 1, 5))
    if last_start not in starts:
        starts.append(last_start)

    # Rolling window means via prefix sums.
    prefix = np.concatenate(([0.0], np.cumsum(energy)))
    scores = {
        s: float((prefix[s + clip_length] - prefix[s]) / clip_length)
        for s in starts
    }

    ranked = sorted(starts, key=lambda s: scores[s], reverse=True)

    selected = []
    for start in ranked:
        if all(abs(start - prev) >= clip_length for prev in selected):
            selected.append(start)
        if len(selected) == count:
            break

    # Fallback (silent video / not enough separate windows): spread evenly.
    if len(selected) < count:
        selected = [
            int(i * (duration - clip_length) / max(count - 1, 1))
            for i in range(count)
        ]
        for s in selected:
            if s not in scores:
                scores[s] = float((prefix[s + clip_length] - prefix[s]) / clip_length)

    selected = sorted(selected)

    # Hype score: window loudness relative to the loudest window.
    peak = max(scores.values())
    peak = peak if peak > 0 else 1.0
    hype = [int(round(100 * scores[s] / peak)) for s in selected]

    return selected, hype


# ==========================================
# GENERATE VERTICAL SHORTS
# ==========================================

# Sharp video centred over a blurred, zoomed copy of itself (no black bars).
VERTICAL_FILTER = (
    "[0:v]split=2[bg][fg];"
    "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
    "crop=1080:1920,boxblur=28:6,eq=brightness=-0.06[bgb];"
    "[fg]scale=1080:1920:force_original_aspect_ratio=decrease:"
    "force_divisible_by=2[fgs];"
    "[bgb][fgs]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[v]"
)


@st.cache_resource
def caption_model():
    from faster_whisper import WhisperModel
    return WhisperModel("tiny", device="cpu", compute_type="int8", cpu_threads=2, num_workers=1)


def make_captions(src, folder, start, length, settings):
    audio = folder / "caption_audio.wav"
    run_command(["ffmpeg", "-v", "error", "-y", "-ss", str(start),
                 "-i", str(src), "-t", str(length), "-vn", "-ac", "1",
                 "-ar", "16000", str(audio)])
    model = caption_model()
    segments, _ = model.transcribe(str(audio), language=settings["language"],
                                   beam_size=1, word_timestamps=True)
    def stamp(t):
        cs = max(0, round(t * 100))
        return f"{cs//360000}:{cs//6000%60:02d}:{cs//100%60:02d}.{cs%100:02d}"
    def clean(t):
        return t.replace("\\", " ").replace("{", "(").replace("}", ")").replace("\n", " ").strip()
    color = "&H00" + settings["color"][5:7] + settings["color"][3:5] + settings["color"][1:3]
    alignment = {"Bottom": 2, "Center": 5, "Top": 8}[settings["position"]]
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{settings['font']},{settings['size']},{color},&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,1,4,1,{alignment},80,80,240,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    events = []
    for segment in segments:
        if settings["animated"]:
            for word in segment.words or []:
                t = clean(word.word)
                if t and word.start < length and word.end > word.start:
                    events.append(f"Dialogue: 0,{stamp(word.start)},{stamp(min(length, word.end))},Default,,0,0,0,,{t}")
        else:
            t = clean(segment.text)
            if t and segment.start < length and segment.end > segment.start:
                events.append(f"Dialogue: 0,{stamp(segment.start)},{stamp(min(length, segment.end))},Default,,0,0,0,,{t}")
    if not events:
        return False
    (folder / "captions.ass").write_text(header + "\n".join(events), encoding="utf-8")
    return True


def generate_clips(src, folder, count, length, progress, captions=None):
    duration = get_video_duration(src)

    if not 0 < duration <= MAX_DURATION:
        raise ValueError("Maximum supported video duration is 180 minutes.")

    if duration < count * length:
        raise ValueError("Video is too short for the selected number of clips.")

    starts, hype = analyze_audio(src, duration, length, count, progress)

    results = []

    for index, start in enumerate(starts):
        output = folder / f"Reelix_Short_{index + 1:02d}.mp4"

        progress.progress(
            30 + int(70 * index / len(starts)),
            text=f"Rendering clip {index + 1}/{len(starts)}...",
        )

        video_filter = VERTICAL_FILTER
        if captions:
            try:
                progress.progress(30 + int(70 * index / len(starts)), text=f"Transcribing clip {index + 1}...")
                if make_captions(src, folder, start, length, captions):
                    video_filter = VERTICAL_FILTER[:-3] + "[base];[base]ass=captions.ass[v]"
                else:
                    st.warning(f"Clip {index + 1}: no speech detected; exporting without captions.")
            except Exception:
                st.warning(f"Clip {index + 1}: transcription unavailable; exporting without captions.")
        run_command([
            "ffmpeg", "-v", "error", "-y",
            "-ss", str(start),
            "-i", str(src),
            "-t", str(length),
            "-filter_complex", video_filter,
            "-map", "[v]",
            "-map", "0:a:0?",
            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-threads", "2",
            "-c:a", "aac",
            "-b:a", "128k",
            "-movflags", "+faststart",
            str(output),
        ], cwd=str(folder))

        if not output.exists() or output.stat().st_size == 0:
            raise RuntimeError("A clip could not be rendered.")

        results.append({
            "name": output.name,
            "data": output.read_bytes(),
            "start": start,
            "hype": hype[index],
        })

    progress.progress(100, text="All clips are ready!")
    return results


# ==========================================
# MAIN USER INTERFACE
# ==========================================

with st.container(border=True):

    st.subheader("✦ Create your shorts")

    mode = st.radio(
        "Source",
        ["Upload video", "Direct MP4 link", "YouTube link"],
        horizontal=True,
    )

    url = ""
    upload = None

    if mode == "YouTube link":
        url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
        )
        st.caption("YouTube may restrict cloud downloads. Upload or use an authorized direct MP4 link if this fails.")
    elif mode == "Direct MP4 link":
        url = st.text_input("Direct HTTPS MP4 URL", placeholder="https://example.com/video.mp4")
        st.caption("Public MP4 file, up to 200 MB; redirects are not supported.")
    else:
        upload = st.file_uploader(
            "Upload your video",
            type=["mp4", "mov", "mkv", "webm"],
        )

    col1, col2 = st.columns(2, gap="large")

    count = col1.slider("Number of clips", 1, 5, 5)
    length = col2.slider("Clip duration (seconds)", 30, 60, 40, step=5)

    captions = None
    if st.checkbox("AI subtitles (experimental, slower on free hosting)"):
        language = st.selectbox("Speech language", ["Auto detect", "English", "Hindi"])
        captions = {
            "language": {"Auto detect": None, "English": "en", "Hindi": "hi"}[language],
            "animated": st.checkbox("Word-by-word captions", value=True),
            "font": st.selectbox("Caption font", ["Noto Sans", "Noto Sans Devanagari", "DejaVu Sans"]),
            "size": st.slider("Caption size", 40, 100, 72),
            "color": st.color_picker("Caption colour", "#FFFF00"),
            "position": st.selectbox("Caption position", ["Bottom", "Center", "Top"]),
        }
        st.caption("First use downloads a small speech model. Try one clip first. Hindi uses Devanagari script.")
    allowed = st.checkbox("I own this video or have permission to process it.")

    generate = st.button(
        "✦ Generate shorts",
        use_container_width=True,
        disabled=not allowed,
    )


# ==========================================
# PROCESSING
# ==========================================

if generate:

    st.session_state.pop("clips", None)
    st.session_state.pop("zip", None)

    progress = st.progress(0, text="Preparing video...")

    try:
        with tempfile.TemporaryDirectory(prefix="Reelix_") as temporary:

            folder = Path(temporary)

            if mode == "Upload video":
                if upload is None:
                    raise ValueError("Please upload a video first.")

                src = folder / ("source" + Path(upload.name).suffix.lower())
                src.write_bytes(upload.getbuffer())

            elif mode == "Direct MP4 link":
                progress.progress(5, text="Downloading MP4...")
                src = download_direct(url.strip(), folder)
            else:
                if not url.strip():
                    raise ValueError("Please enter a YouTube URL.")

                progress.progress(5, text="Downloading video...")
                src = download_youtube(url.strip(), folder)

            clips = generate_clips(src, folder, count, length, progress, captions)

        # Build the ZIP once, not on every rerun.
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            for clip in clips:
                archive.writestr(clip["name"], clip["data"])

        st.session_state["clips"] = clips
        st.session_state["zip"] = buffer.getvalue()

        st.success("Your clips are ready! 🎉")

    except subprocess.TimeoutExpired:
        st.error("Processing timed out. Try a shorter video.")

    except Exception as error:
        message = str(error)

        if mode == "YouTube link" and any(term in message.lower() for term in ("403", "429", "not a bot", "sign in")):
            st.error("YouTube restricted this cloud server. Upload an authorized video file or use a direct MP4 link instead.")
        else:
            st.error(f"Processing failed: {message}")


# ==========================================
# RESULTS
# ==========================================

if st.session_state.get("clips"):

    st.markdown("<br>", unsafe_allow_html=True)
    st.subheader("✦ Your shorts")

    clips = st.session_state["clips"]

    for index, clip in enumerate(clips):

        with st.container(border=True):

            left, right = st.columns([1, 1], gap="large")

            with left:
                st.video(clip["data"])

            with right:
                st.markdown(f"### Short {index + 1:02d}")

                st.markdown(
                    f'<span class="badge">⏱ Starts at {fmt_time(clip["start"])}</span>'
                    f'<span class="badge hot">🔥 Hype {clip["hype"]}%</span>',
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f'<div class="meter"><div style="width:{clip["hype"]}%"></div></div>',
                    unsafe_allow_html=True,
                )

                st.caption("1080×1920 · MP4 · ready for Shorts, Reels & TikTok")

                st.download_button(
                    "⬇ Download MP4",
                    data=clip["data"],
                    file_name=clip["name"],
                    mime="video/mp4",
                    key=f"download_{index}",
                    use_container_width=True,
                )

    st.download_button(
        "⬇ Download all clips (ZIP)",
        data=st.session_state["zip"],
        file_name="Reelix_shorts.zip",
        mime="application/zip",
        use_container_width=True,
    )


# ==========================================
# FOOTER
# ==========================================

st.markdown(f"""
<div class="footer">
<h2>{APP_NAME}</h2>
<p>Long Videos. Viral Shorts.</p>
<p>Designed &amp; Developed by <strong style="color:white;">{DEVELOPER}</strong></p>
<p>📞 <a href="tel:{PHONE_LINK}">{PHONE}</a></p>
<p>✉️ <a href="mailto:{EMAIL}">{EMAIL}</a></p>
<p style="font-size:12px;">© 2026 Reelix AI. All Rights Reserved.</p>
</div>
""", unsafe_allow_html=True)
