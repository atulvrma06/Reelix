
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

MAX_VIDEO_DURATION = 10800
MAX_VIDEO_SIZE = 1024**3
PROVIDER_VERSION = "2.0.2"


# ==========================================
# BACKGROUND DESIGN
# ==========================================

st.markdown("""
<style>

.stApp {
    background:
    radial-gradient(
        ellipse at 50% 0%,
        #30205b 0%,
        #101225 42%,
        #080b17 80%
    );
    color: #f4f3ff;
}

.block-container {
    max-width: 1000px;
    padding-top: 3rem;
    padding-bottom: 4rem;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.hero {
    text-align: center;
    padding: 32px 8px 40px;
}

.hero h1 {
    font-size: clamp(2.3rem, 6vw, 4.5rem);
    line-height: 1.1;
    letter-spacing: -.05em;
    margin: 15px 0;
    color: white;
}

.hero span {
    color: #b69aff;
}

.hero p {
    color: #b9b9d0;
    font-size: 1.1rem;
}

.brand {
    letter-spacing: .18em;
    color: #c4b5fd;
    font-weight: 700;
    font-size: .85rem;
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

.stTextInput input {
    border-radius: 10px;
}

div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #14172b99;
    border-radius: 20px;
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
# COMMAND EXECUTION
# ==========================================

def run(args, cwd=None):

    result = subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        raise RuntimeError(
            result.stderr[-3000:] or
            result.stdout[-3000:] or
            "Command failed."
        )

    return result.stdout


# ==========================================
# BGUTIL PO TOKEN PROVIDER
# ==========================================

@st.cache_resource(show_spinner=False)
def ensure_bgutil_provider():

    home = Path.home()

    repo = home / "bgutil-ytdlp-pot-provider"

    server = repo / "server"

    build_file = server / "build" / "generate_once.js"

    node_path = shutil.which("node")
    npm_path = shutil.which("npm")
    npx_path = shutil.which("npx")

    if not node_path:
        raise RuntimeError("Node.js 22+ is not installed.")

    if not npm_path or not npx_path:
        raise RuntimeError(
            "npm/npx not found. Check Node.js installation."
        )

    node_version = run([node_path, "--version"]).strip()

    st.info(f"Node.js detected: {node_version}")

    if not repo.exists() or not (server / "package.json").exists():

        if repo.exists():
            shutil.rmtree(repo)

        st.write("Downloading bgutil provider...")

        run([
            "git",
            "clone",
            "--single-branch",
            "--branch",
            PROVIDER_VERSION,
            "https://github.com/Brainicism/bgutil-ytdlp-pot-provider.git",
            str(repo)
        ])

    if not build_file.exists():

        st.write("Installing provider dependencies...")

        run(
            [npm_path, "ci"],
            cwd=str(server)
        )

        st.write("Building PO Token generation script...")

        run(
            [npx_path, "tsc"],
            cwd=str(server)
        )

    if not build_file.exists():
        raise RuntimeError(
            "PO Token script build file was not created."
        )

    return str(server)


# ==========================================
# YOUTUBE URL VALIDATION
# ==========================================

def validate_youtube_url(url):

    u = urlparse(url)

    host = (u.hostname or "").lower()

    allowed_hosts = {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
        "youtu.be"
    }

    if u.scheme != "https" or host not in allowed_hosts:
        raise ValueError("Enter a valid HTTPS YouTube URL.")

    return True


# ==========================================
# AUDIO ACTIVITY ANALYSIS
# ==========================================

def analyze_audio(src, duration, length):

    try:

        raw = run([
            "ffmpeg",
            "-v", "error",
            "-i", str(src),
            "-vn",
            "-ac", "1",
            "-ar", "2000",
            "-f", "s16le",
            "-"
        ])

        audio = np.frombuffer(
            raw.encode() if isinstance(raw, str) else raw,
            dtype="<i2"
        ).astype(np.float32) / 32768

        if len(audio) == 0:
            raise ValueError("No audio detected.")

        seconds = np.array([
            np.sqrt(np.mean(audio[i:i+2000] ** 2))
            for i in range(0, len(audio), 2000)
        ])

    except Exception:
        seconds = np.zeros(int(duration))

    starts = list(
        range(0, int(duration - length) + 1, 5)
    )

    starts.append(int(duration - length))

    scores = [
        float(np.mean(seconds[s:s+length]))
        if len(seconds[s:s+length])
        else 0
        for s in starts
    ]

    return starts, scores


# ==========================================
# SHORTS GENERATION
# ==========================================

def process(src, folder, n, length, progress):

    duration = float(run([
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1",
        str(src)
    ]).strip())

    if not 0 < duration <= MAX_VIDEO_DURATION:

        raise ValueError(
            "Video must be at most 180 minutes."
        )

    if duration < length * n:

        raise ValueError(
            "Video is too short for the selected clips."
        )

    progress.progress(
        30,
        text="Analyzing audio activity..."
    )

    starts, scores = analyze_audio(
        src,
        duration,
        length
    )

    chosen = []

    for i in sorted(
        range(len(starts)),
        key=lambda i: scores[i],
        reverse=True
    ):

        s = starts[i]

        if all(
            abs(s - t) >= length
            for t in chosen
        ):
            chosen.append(s)

        if len(chosen) == n:
            break

    if len(chosen) < n:

        chosen = [
            int(i * (duration - length) / n)
            for i in range(n)
        ]

    results = []

    for i, start in enumerate(sorted(chosen)):

        output = folder / f"short_{i+1:02d}.mp4"

        run([
            "ffmpeg",
            "-v", "error",
            "-y",

            "-ss", str(start),
            "-i", str(src),

            "-t", str(length),

            "-map", "0:v:0",
            "-map", "0:a:0?",

            "-vf",
            (
                "scale=1080:1920:"
                "force_original_aspect_ratio=decrease:"
                "force_divisible_by=2,"
                "pad=1080:1920:(ow-iw)/2:(oh-ih)/2,"
                "setsar=1"
            ),

            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "18",
            "-threads", "2",
            "-pix_fmt", "yuv420p",

            "-c:a", "aac",
            "-b:a", "192k",

            "-movflags", "+faststart",

            str(output)
        ])

        results.append((
            output.name,
            output.read_bytes(),
            start
        ))

        progress.progress(
            35 + int(65 * (i + 1) / n),
            text=f"Rendered {i+1}/{n} clips..."
        )

    return results


# ==========================================
# MAIN INTERFACE
# ==========================================

with st.container(border=True):

    st.subheader("Create your shorts")

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
            "Upload video",
            type=["mp4", "mov", "mkv", "webm"]
        )

    c1, c2 = st.columns(2)

    n = c1.slider(
        "Number of clips",
        1, 5, 5
    )

    length = c2.slider(
        "Clip duration (seconds)",
        30, 60, 40, 5
    )

    allowed = st.checkbox(
        "I own this video or have permission to process it."
    )

    go = st.button(
        "✦ Generate shorts",
        use_container_width=True,
        disabled=not allowed
    )


# ==========================================
# GENERATE BUTTON
# ==========================================

if go:

    st.session_state.pop("clips", None)

    progress = st.progress(
        0,
        text="Preparing video..."
    )

    try:

        with tempfile.TemporaryDirectory(
            prefix="Reelix-"
        ) as tmp:

            folder = Path(tmp)

            # ------------------------------
            # LOCAL UPLOAD
            # ------------------------------

            if mode == "Upload video":

                if upload is None:
                    raise ValueError("Upload a video first.")

                if upload.size > MAX_VIDEO_SIZE:
                    raise ValueError(
                        "Video size exceeds 1 GB."
                    )

                src = folder / (
                    "source" +
                    Path(upload.name).suffix.lower()
                )

                src.write_bytes(upload.getbuffer())

            # ------------------------------
            # YOUTUBE DOWNLOAD
            # ------------------------------

            else:

                validate_youtube_url(url)

                st.info(
                    "Preparing YouTube PO Token provider..."
                )

                server_home = ensure_bgutil_provider()

                node_path = shutil.which("node")

                ydl_options = {

                    "js_runtimes": {
                        "node": {
                            "path": node_path
                        }
                    },

                    "extractor_args": {

                        "youtubepot-bgutilscript": {
                            "server_home": [server_home]
                        },

                        "youtube": {
                            "player_client": [
                                "mweb",
                                "tv",
                                "web_safari"
                            ]
                        }
                    },

                    "format": (
                        "bv*[height<=1080][ext=mp4]+ba[ext=m4a]"
                        "/b[height<=720]"
                        "/b[height<=480]"
                    ),

                    "merge_output_format": "mp4",

                    "outtmpl": str(
                        folder / "source.%(ext)s"
                    ),

                    "noplaylist": True,

                    "max_filesize": MAX_VIDEO_SIZE,

                    "quiet": False,

                    "verbose": True,

                    "socket_timeout": 30,

                    "retries": 3,

                    "fragment_retries": 3
                }

                progress.progress(
                    10,
                    text="Checking YouTube video..."
                )

                with yt_dlp.YoutubeDL(ydl_options) as y:

                    info = y.extract_info(
                        url,
                        download=False
                    )

                    if not info:
                        raise ValueError(
                            "Unable to read YouTube video."
                        )

                    if info.get("is_live"):
                        raise ValueError(
                            "Live streams are not supported."
                        )

                    video_duration = float(
                        info.get("duration") or 0
                    )

                    if not 0 < video_duration <= MAX_VIDEO_DURATION:

                        raise ValueError(
                            "Choose a recorded video under 180 minutes."
                        )

                    if info.get("filesize", 0) > MAX_VIDEO_SIZE:
                        raise ValueError(
                            "Video exceeds 1 GB."
                        )

                    progress.progress(
                        20,
                        text="Downloading authorized video..."
                    )

                    y.download([url])

                src_files = [
                    f for f in folder.glob("source.*")
                    if f.suffix.lower() in [
                        ".mp4",
                        ".webm",
                        ".mkv",
                        ".mov"
                    ]
                ]

                if not src_files:
                    raise ValueError(
                        "Downloaded video file not found."
                    )

                src = src_files[0]

            # ------------------------------
            # PROCESS CLIPS
            # ------------------------------

            st.session_state.clips = process(
                src,
                folder,
                n,
                length,
                progress
            )

        st.success("Your clips are ready!")

    except Exception as e:

        st.error(
            f"Processing failed: {str(e)}"
        )

        st.info(
            "If YouTube blocks downloading, "
            "try an authorized MP4 upload."
        )


# ==========================================
# DISPLAY GENERATED SHORTS
# ==========================================

if st.session_state.get("clips"):

    st.subheader("Your shorts")

    clips = st.session_state.clips

    for i, (name, data, start) in enumerate(clips):

        with st.container(border=True):

            a, b = st.columns([1, 2])

            a.video(data)

            b.markdown(
                f"**Short {i+1:02d}**"
            )

            b.caption(
                f"Source timestamp: "
                f"{start//60}:{start%60:02d}"
            )

            b.download_button(
                "Download MP4",
                data=data,
                file_name=name,
                mime="video/mp4",
                key=name
            )

    # ------------------------------
    # DOWNLOAD ALL AS ZIP
    # ------------------------------

    buffer = io.BytesIO()

    with zipfile.ZipFile(
        buffer,
        "w",
        zipfile.ZIP_DEFLATED
    ) as archive:

        for name, data, _ in clips:

            archive.writestr(
                name,
                data
            )

    st.download_button(
        "⬇ Download all clips (ZIP)",
        data=buffer.getvalue(),
        file_name="Reelix_shorts.zip",
        mime="application/zip",
        use_container_width=True
    )


# ==========================================
# FOOTER
# ==========================================

st.caption(
    "Reelix AI • Audio-activity highlights • No paid AI API"
)

st.markdown("""
<hr style="
    border: 0;
    border-top: 1px solid #302040;
">

<div style="
    text-align:center;
    padding:25px;
    color:#a1a1aa;
">

<h2 style="color:#a855f7;">
REELIX
</h2>

<p>Long Videos. Viral Shorts.</p>

<p>
Designed & Developed by
<b style="color:white;">Atul Verma</b>
</p>

<p>
📞
<a style="color:#c084fc;"
href="tel:+916005090551">
+91 6005090551
</a>
</p>

<p>
✉️
<a style="color:#c084fc;"
href="mailto:vermaatul2946@gmail.com">
vermaatul2946@gmail.com
</a>
</p>

<p style="
    font-size:12px;
    color:#71717a;
">
© 2026 Reelix. All Rights Reserved.
</p>

</div>
""", unsafe_allow_html=True)
