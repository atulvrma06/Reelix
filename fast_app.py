import io
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


# ==========================================
# DESIGN
# ==========================================

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background:
        radial-gradient(900px 500px at 15% -5%, rgba(124, 77, 255, .35), transparent 60%),
        radial-gradient(800px 500px at 90% 5%, rgba(236, 72, 153, .22), transparent 60%),
        radial-gradient(700px 600px at 50% 110%, rgba(56, 189, 248, .14), transparent 60%),
        #0a0c18;
    color: #f4f3ff;
}

#MainMenu, footer, [data-testid="stToolbar"] { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

.block-container {
    max-width: 980px;
    padding-top: 1.5rem;
    padding-bottom: 4rem;
}

/* ---------- Hero ---------- */
.hero { text-align: center; padding: 40px 8px 28px; }

.pill {
    display: inline-block;
    padding: 7px 18px;
    border-radius: 999px;
    background: rgba(167, 139, 250, .12);
    border: 1px solid rgba(167, 139, 250, .35);
    color: #d8ccff;
    font-size: .78rem;
    font-weight: 700;
    letter-spacing: .18em;
    backdrop-filter: blur(8px);
}

.hero h1 {
    font-size: clamp(2.4rem, 6vw, 4.4rem);
    line-height: 1.08;
    letter-spacing: -0.045em;
    font-weight: 800;
    color: #fff;
    margin: 22px 0 14px;
}

.grad {
    background: linear-gradient(100deg, #a78bfa 0%, #f472b6 55%, #38bdf8 100%);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero p {
    color: #aeb0cc;
    font-size: 1.08rem;
    max-width: 560px;
    margin: 0 auto;
}

.chips { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin-top: 26px; }
.chip {
    padding: 8px 16px;
    border-radius: 12px;
    background: rgba(255, 255, 255, .05);
    border: 1px solid rgba(255, 255, 255, .09);
    color: #cfd0e6;
    font-size: .86rem;
    font-weight: 500;
}

/* ---------- Cards ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(160deg, rgba(30, 27, 60, .72), rgba(15, 17, 36, .72));
    border: 1px solid rgba(167, 139, 250, .18);
    border-radius: 22px;
    box-shadow: 0 20px 60px -20px rgba(0, 0, 0, .6);
    backdrop-filter: blur(14px);
    padding: .6rem .8rem;
}

h2, h3 { letter-spacing: -0.02em; font-weight: 700; }

/* ---------- Inputs ---------- */
.stTextInput input {
    background: rgba(255, 255, 255, .05) !important;
    border: 1px solid rgba(255, 255, 255, .12) !important;
    border-radius: 12px !important;
    color: #fff !important;
    padding: 12px 14px !important;
}
.stTextInput input:focus {
    border-color: #a78bfa !important;
    box-shadow: 0 0 0 3px rgba(167, 139, 250, .25) !important;
}

[data-testid="stFileUploaderDropzone"] {
    background: rgba(255, 255, 255, .03);
    border: 1.5px dashed rgba(167, 139, 250, .45);
    border-radius: 16px;
}

/* ---------- Buttons ---------- */
.stButton button, .stDownloadButton button {
    border-radius: 14px;
    font-weight: 700;
    min-height: 50px;
    transition: transform .15s ease, box-shadow .2s ease;
}
.stButton button {
    background: linear-gradient(110deg, #7c4dff, #c04ee8 60%, #ec4899);
    color: #fff;
    border: 0;
    box-shadow: 0 10px 30px -8px rgba(168, 85, 247, .7);
}
.stButton button:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: 0 16px 38px -8px rgba(168, 85, 247, .9);
    color: #fff;
}
.stButton button:disabled { opacity: .4; }

.stDownloadButton button {
    background: rgba(255, 255, 255, .06);
    border: 1px solid rgba(167, 139, 250, .35);
    color: #e9e3ff;
}
.stDownloadButton button:hover {
    border-color: #a78bfa;
    background: rgba(167, 139, 250, .15);
    color: #fff;
}

/* ---------- Results ---------- */
.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 999px;
    font-size: .76rem;
    font-weight: 700;
    margin-right: 6px;
    background: rgba(167, 139, 250, .16);
    color: #d8ccff;
    border: 1px solid rgba(167, 139, 250, .3);
}
.badge.hot {
    background: rgba(244, 114, 182, .15);
    color: #fbcfe8;
    border-color: rgba(244, 114, 182, .35);
}

[data-testid="stVideo"] video {
    border-radius: 16px;
    max-height: 480px;
    background: #000;
}

hr { border-color: rgba(255, 255, 255, .08) !important; }

/* ---------- Footer ---------- */
.footer {
    text-align: center;
    padding: 36px 15px 10px;
    margin-top: 64px;
    border-top: 1px solid rgba(167, 139, 250, .2);
    color: #9a9bb5;
}
.footer h2 {
    letter-spacing: .5em;
    font-weight: 800;
    margin-bottom: 4px;
    background: linear-gradient(100deg, #a78bfa, #f472b6);
    -webkit-background-clip: text;
    background-clip: text;
    -webkit-text-fill-color: transparent;
}
.footer a { color: #c4b5fd; text-decoration: none; }
.footer a:hover { color: #fff; }
</style>
"""

HERO = """
<div class="hero">
<span class="pill">✂ REELIX · SHORTS STUDIO</span>
<h1>Long videos.<br><span class="grad">Shorts that stand out.</span></h1>
<p>Drop in a video, and Reelix finds the most energetic moments and turns them into polished vertical clips.</p>
<div class="chips">
<span class="chip">🎧 Audio-energy detection</span>
<span class="chip">📱 1080×1920 vertical</span>
<span class="chip">🌫️ Blurred backdrop</span>
<span class="chip">📦 One-click ZIP</span>
</div>
</div>
"""

st.markdown(CSS, unsafe_allow_html=True)
st.markdown(HERO, unsafe_allow_html=True)


# ==========================================
# HELPERS
# ==========================================

def get_secret(key, default=""):
    try:
        return st.secrets.get(key, default)
    except Exception:
        return os.getenv(key, default)


def run_command(args):
    result = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        timeout=900,
    )
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

def download_youtube(url, folder):
    parsed = urlparse(url)

    allowed_hosts = {
        "youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be",
    }

    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        raise ValueError("Please enter a valid HTTPS YouTube URL.")

    options = {
        "extractor_args": {
            "youtube": {"player_client": ["mweb", "tv", "web_safari"]}
        },
        "format": "bv*[height<=720]+ba/b[height<=720]/best",
        "merge_output_format": "mp4",
        "outtmpl": str(folder / "source.%(ext)s"),
        "noplaylist": True,
        "max_filesize": 1024 ** 3,
        "socket_timeout": 45,
        "retries": 5,
        "fragment_retries": 5,
        "quiet": True,
        "no_warnings": True,
    }

    node_path = find_node()
    if node_path:
        options["js_runtimes"] = {"node": {"path": node_path}}

    # Optional BGUtil HTTP provider.
    bgutil_url = get_secret("BGUTIL_BASE_URL")
    if bgutil_url:
        options["extractor_args"]["youtubepot-bgutilhttp"] = {
            "base_url": bgutil_url
        }

    # Optional BGUtil script provider.
    bgutil_home = get_secret("BGUTIL_SERVER_HOME")
    if bgutil_home:
        options["extractor_args"]["youtubepot-bgutilscript"] = {
            "server_home": bgutil_home
        }

    # Optional authorized YouTube cookies.
    cookies = get_secret("YOUTUBE_COOKIES")
    if cookies:
        cookie_file = folder / "cookies.txt"
        cookie_file.write_text(cookies, encoding="utf-8")
        options["cookiefile"] = str(cookie_file)
    options.setdefault("extractor_args", {})["youtubepot-bgutilhttp"] = {
    "base_url": [
        "https://bgutil-ytdlp-pot-provider-3r7r.onrender.com"
    ]
}
    with yt_dlp.YoutubeDL(options) as ydl:
        info = ydl.extract_info(url, download=False)

        if not info or info.get("is_live"):
            raise ValueError("Invalid or live video.")

        duration = float(info.get("duration") or 0)
        if not 0 < duration <= MAX_DURATION:
            raise ValueError("Video must be under 180 minutes.")

        ydl.download([url])

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
    if len(energy) < total_seconds + clip_length:
        energy = np.pad(energy, (0, total_seconds + clip_length - len(energy)))

    progress.progress(25, text="Finding interesting moments...")

    last_start = int(duration - clip_length)
    if last_start < 0:
        raise ValueError("Video is shorter than clip duration.")

    starts = list(range(0, last_start + 1, 5))
    if last_start not in starts:
        starts.append(last_start)

    # Rolling window means via prefix sums.
    prefix = np.concatenate(([0.0], np.cumsum(energy)))
    scores = [
        float((prefix[s + clip_length] - prefix[s]) / clip_length)
        for s in starts
    ]

    ranked = sorted(range(len(starts)), key=lambda i: scores[i], reverse=True)

    selected = []
    for index in ranked:
        start = starts[index]
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

    selected = sorted(selected)

    # Hype score: window loudness relative to the loudest window.
    peak = max(scores) if scores and max(scores) > 0 else 1.0
    score_by_start = dict(zip(starts, scores))
    hype = []
    for s in selected:
        window = float(
            (prefix[s + clip_length] - prefix[s]) / clip_length
        ) if s not in score_by_start else score_by_start[s]
        hype.append(int(round(100 * window / peak)))

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


def generate_clips(src, folder, count, length, progress):
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

        run_command([
            "ffmpeg", "-v", "error", "-y",
            "-ss", str(start),
            "-i", str(src),
            "-t", str(length),
            "-filter_complex", VERTICAL_FILTER,
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
        ])

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
        ["YouTube link", "Upload video"],
        horizontal=True,
    )

    url = ""
    upload = None

    if mode == "YouTube link":
        url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
        )
    else:
        upload = st.file_uploader(
            "Upload your video",
            type=["mp4", "mov", "mkv", "webm"],
        )

    col1, col2 = st.columns(2)

    count = col1.slider("Number of clips", 1, 5, 5)
    length = col2.slider("Clip duration (seconds)", 30, 60, 40, step=5)

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

            else:
                if not url.strip():
                    raise ValueError("Please enter a YouTube URL.")

                progress.progress(5, text="Downloading video...")
                src = download_youtube(url.strip(), folder)

            clips = generate_clips(src, folder, count, length, progress)

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

        if "403" in message:
            st.error(
                "YouTube returned HTTP 403. The hosting IP may be restricted. "
                "Try uploading the video instead."
            )
        else:
            st.error(f"Processing failed: {message}")


# ==========================================
# RESULTS
# ==========================================

if st.session_state.get("clips"):

    st.divider()
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
                    f'<span class="badge">⏱ {fmt_time(clip["start"])}</span>'
                    f'<span class="badge hot">🔥 Hype {clip["hype"]}%</span>',
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