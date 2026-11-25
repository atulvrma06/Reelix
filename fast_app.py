
import os
import io
import re
import shutil
import zipfile
import tempfile
import subprocess

from pathlib import Path
from urllib.parse import urlparse

import numpy as np
import streamlit as st
import yt_dlp


# ==========================================
# REELIX CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Reelix AI | Shorts Studio",
    page_icon="✂️",
    layout="wide"
)

APP_NAME = "REELIX"
DEVELOPER = "Atul Verma"
PHONE = "+91 6005090551"
EMAIL = "vermaatul2946@gmail.com"


# ==========================================
# DESIGN
# ==========================================

st.markdown("""
<style>
.stApp {
    background:
    radial-gradient(ellipse at 50% 0%,
    #30205b 0%, #101225 42%, #080b17 85%);
    color: #f4f3ff;
}

.block-container {
    max-width: 1050px;
    padding-top: 2rem;
    padding-bottom: 4rem;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.hero {
    text-align: center;
    padding: 35px 8px 45px;
}

.hero h1 {
    font-size: clamp(2.5rem, 6vw, 4.5rem);
    line-height: 1.1;
    letter-spacing: -0.05em;
    color: white;
    margin: 15px 0;
    font-weight: 850;
}

.hero span {
    color: #b69aff;
}

.hero p {
    color: #b9b9d0;
    font-size: 1.1rem;
}

.brand {
    letter-spacing: .2em;
    color: #c4b5fd;
    font-weight: 800;
}

.stButton button {
    background: linear-gradient(110deg,#7440e8,#a34ee8);
    color: white;
    border: 0;
    border-radius: 12px;
    font-weight: 700;
    min-height: 48px;
}

.stDownloadButton button {
    border-radius: 10px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #14172b99;
    border-radius: 18px;
    border: 1px solid #34304e;
}

.stTextInput input {
    border-radius: 10px;
}

.footer {
    text-align: center;
    padding: 35px 15px;
    margin-top: 60px;
    border-top: 1px solid #49316d;
    color: #a1a1aa;
}

.footer h2 {
    color: #b69aff;
    letter-spacing: 5px;
}

.footer a {
    color: #c4b5fd;
    text-decoration: none;
}

footer {
    visibility: hidden;
}
</style>

<div class="hero">
    <div class="brand">✂ REELIX / SHORTS STUDIO</div>
    <h1>
        Long videos.<br>
        <span>Shorts that stand out.</span>
    </h1>
    <p>
        Find energetic moments and turn them into vertical clips.
    </p>
</div>
""", unsafe_allow_html=True)


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
        timeout=900
    )
    return result.stdout


def get_video_duration(src):
    output = run_command([
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(src)
    ])

    return float(output.decode().strip())


# ==========================================
# YOUTUBE DOWNLOAD
# ==========================================

def download_youtube(url, folder):

    parsed = urlparse(url)

    allowed_hosts = {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be"
    }

    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        raise ValueError("Please enter a valid HTTPS YouTube URL.")

    node_path = shutil.which("node")

    if not node_path:
        raise RuntimeError(
            "Node.js runtime is unavailable on this server."
        )

    options = {
        "js_runtimes": {
            "node": {"path": node_path}
        },

        "extractor_args": {
            "youtube": {
                "player_client": ["mweb", "tv", "web_safari"]
            }
        },

        "format":
            "bv*[height<=720]+ba/b[height<=720]/best",

        "merge_output_format": "mp4",

        "outtmpl": str(folder / "source.%(ext)s"),

        "noplaylist": True,
        "max_filesize": 1024**3,
        "socket_timeout": 45,
        "retries": 5,
        "fragment_retries": 5,
        "quiet": True,
        "no_warnings": False
    }

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

    with yt_dlp.YoutubeDL(options) as ydl:

        info = ydl.extract_info(url, download=False)

        if not info:
            raise RuntimeError("Unable to read video information.")

        if info.get("is_live"):
            raise ValueError("Live videos are not supported.")

        duration = float(info.get("duration") or 0)

        if not 0 < duration <= 10800:
            raise ValueError(
                "Video must be recorded and under 180 minutes."
            )

        ydl.download([url])

    files = [
        f for f in folder.glob("source.*")
        if f.suffix.lower() in {".mp4", ".webm", ".mkv", ".mov"}
    ]

    if not files:
        raise RuntimeError("Downloaded video file was not found.")

    return files[0]


# ==========================================
# AUDIO HIGHLIGHT DETECTION
# ==========================================

def analyze_audio(src, duration, clip_length, count, progress):

    progress.progress(15, text="Analyzing video audio...")

    try:
        raw_audio = run_command([
            "ffmpeg",
            "-v", "error",
            "-i", str(src),
            "-vn",
            "-ac", "1",
            "-ar", "2000",
            "-f", "s16le",
            "-"
        ])

        audio = (
            np.frombuffer(raw_audio, dtype="<i2")
            .astype(np.float32) / 32768.0
        )

        if len(audio) == 0:
            raise ValueError("No audio found.")

        samples_per_second = 2000

        energy = []

        for i in range(0, len(audio), samples_per_second):
            chunk = audio[i:i + samples_per_second]

            if len(chunk):
                energy.append(
                    float(np.sqrt(np.mean(chunk ** 2)))
                )

        energy = np.array(energy)

    except Exception:
        energy = np.zeros(int(duration) + 1)

    progress.progress(25, text="Finding interesting moments...")

    last_start = int(duration - clip_length)

    if last_start < 0:
        raise ValueError("Video is shorter than clip duration.")

    starts = list(range(0, last_start + 1, 5))

    if last_start not in starts:
        starts.append(last_start)

    scores = []

    for start in starts:

        segment = energy[start:start + clip_length]

        score = (
            float(np.mean(segment))
            if len(segment)
            else 0
        )

        scores.append(score)

    selected = []

    ranked = sorted(
        range(len(starts)),
        key=lambda i: scores[i],
        reverse=True
    )

    for index in ranked:

        start = starts[index]

        if all(
            abs(start - previous) >= clip_length
            for previous in selected
        ):
            selected.append(start)

        if len(selected) == count:
            break

    # Fallback if audio analysis cannot identify enough moments.
    if len(selected) < count:
        selected = [
            int(i * (duration - clip_length) / count)
            for i in range(count)
        ]

    return sorted(selected)


# ==========================================
# GENERATE VERTICAL SHORTS
# ==========================================

def generate_clips(src, folder, count, length, progress):

    duration = get_video_duration(src)

    if not 0 < duration <= 10800:
        raise ValueError("Maximum supported video duration is 180 minutes.")

    if duration < count * length:
        raise ValueError(
            "Video is too short for the selected number of clips."
        )

    starts = analyze_audio(
        src,
        duration,
        length,
        count,
        progress
    )

    results = []

    for index, start in enumerate(starts):

        output = folder / f"Reelix_Short_{index + 1:02d}.mp4"

        progress.progress(
            30 + int(70 * index / count),
            text=f"Rendering clip {index + 1}/{count}..."
        )

        run_command([
            "ffmpeg",
            "-v", "error",
            "-y",

            "-ss", str(start),
            "-i", str(src),

            "-t", str(length),

            "-map", "0:v:0",
            "-map", "0:a:0?",

            "-vf",
            "scale=1080:1920:force_original_aspect_ratio=decrease:force_divisible_by=2,"
            "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,"
            "setsar=1",

            "-c:v", "libx264",
            "-preset", "veryfast",
            "-crf", "20",
            "-threads", "2",
            "-pix_fmt", "yuv420p",

            "-c:a", "aac",
            "-b:a", "128k",

            "-movflags", "+faststart",

            str(output)
        ])

        if not output.exists() or output.stat().st_size == 0:
            raise RuntimeError("A clip could not be rendered.")

        results.append({
            "name": output.name,
            "data": output.read_bytes(),
            "start": start
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
        horizontal=True
    )

    url = ""
    upload = None

    if mode == "YouTube link":

        url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=..."
        )

    else:

        upload = st.file_uploader(
            "Upload your video",
            type=["mp4", "mov", "mkv", "webm"]
        )

    col1, col2 = st.columns(2)

    count = col1.slider(
        "Number of clips",
        min_value=1,
        max_value=5,
        value=5
    )

    length = col2.slider(
        "Clip duration (seconds)",
        min_value=30,
        max_value=60,
        value=40,
        step=5
    )

    allowed = st.checkbox(
        "I own this video or have permission to process it."
    )

    generate = st.button(
        "✦ Generate shorts",
        use_container_width=True,
        disabled=not allowed
    )


# ==========================================
# PROCESSING
# ==========================================

if generate:

    st.session_state.pop("clips", None)

    progress = st.progress(0, text="Preparing video...")

    try:

        with tempfile.TemporaryDirectory(
            prefix="Reelix_"
        ) as temporary:

            folder = Path(temporary)

            if mode == "Upload video":

                if upload is None:
                    raise ValueError("Please upload a video first.")

                src = folder / (
                    "source" + Path(upload.name).suffix.lower()
                )

                src.write_bytes(upload.getbuffer())

            else:

                if not url.strip():
                    raise ValueError("Please enter a YouTube URL.")

                progress.progress(
                    5,
                    text="Downloading authorized video..."
                )

                src = download_youtube(url.strip(), folder)

            clips = generate_clips(
                src,
                folder,
                count,
                length,
                progress
            )

            st.session_state["clips"] = clips

        st.success("Your clips are ready!")

    except subprocess.TimeoutExpired:
        st.error("Processing timed out. Try a shorter video.")

    except Exception as error:

        message = str(error)

        if "403" in message:
            st.error(
                "YouTube returned HTTP 403. "
                "The hosting IP may be restricted. "
                "Try an authorized uploaded video instead."
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

    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(
        zip_buffer,
        "w",
        zipfile.ZIP_DEFLATED
    ) as archive:

        for clip in clips:
            archive.writestr(
                clip["name"],
                clip["data"]
            )

    for index, clip in enumerate(clips):

        with st.container(border=True):

            left, right = st.columns([1, 1])

            with left:
                st.video(clip["data"])

            with right:

                st.markdown(
                    f"### Short {index + 1:02d}"
                )

                start = clip["start"]

                st.caption(
                    f"Source timestamp: "
                    f"{start // 60}:{start % 60:02d}"
                )

                st.download_button(
                    "⬇ Download MP4",
                    data=clip["data"],
                    file_name=clip["name"],
                    mime="video/mp4",
                    key=f"download_{index}"
                )

    st.download_button(
        "⬇ Download all clips (ZIP)",
        data=zip_buffer.getvalue(),
        file_name="Reelix_shorts.zip",
        mime="application/zip",
        use_container_width=True
    )


# ==========================================
# FOOTER
# ==========================================

st.markdown("""
<div class="footer">

<h2>REELIX</h2>

<p>Long Videos. Viral Shorts.</p>

<p>
Designed & Developed by
<strong style="color:white;">Atul Verma</strong>
</p>

<p>
📞
<a href="tel:+916005090551">
+91 6005090551
</a>
</p>

<p>
✉️
<a href="mailto:vermaatul2946@gmail.com">
vermaatul2946@gmail.com
</a>
</p>

<p style="font-size:12px;">
© 2026 Reelix AI. All Rights Reserved.
</p>

</div>
""", unsafe_allow_html=True)
