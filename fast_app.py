import os, tempfile, subprocess, zipfile, io, re
from pathlib import Path
from urllib.parse import urlparse
import numpy as np
import streamlit as st
import yt_dlp

st.set_page_config(page_title='Reelix AI | Shorts Studio',page_icon='✂️',layout='wide')
st.markdown('''<style>
.stApp{background:radial-gradient(ellipse at 50% 0%,#30205b 0%,#101225 42%,#080b17 80%);color:#f4f3ff}.block-container{max-width:1000px;padding-top:3rem;padding-bottom:4rem}header[data-testid="stHeader"]{background:transparent}.hero{text-align:center;padding:32px 8px 40px}.hero h1{font-size:clamp(2.3rem,6vw,4.5rem);line-height:1.1;letter-spacing:-.05em;margin:15px 0;color:white}.hero span{color:#b69aff}.hero p{color:#b9b9d0;font-size:1.1rem}.brand{letter-spacing:.18em;color:#c4b5fd;font-weight:700;font-size:.85rem}.stButton button{background:linear-gradient(110deg,#7440e8,#a34ee8);color:white;border:0;border-radius:12px;font-weight:700;min-height:48px}.stDownloadButton button{border-radius:10px}.stTextInput input{border-radius:10px}div[data-testid="stVerticalBlockBorderWrapper"]{background:#14172b99;border-radius:20px}footer{visibility:hidden}
</style><div class="hero"><div class="brand">✂ Reelix / SHORTS STUDIO</div><h1>Long videos.<br><span>Shorts that stand out.</span></h1><p>Find energetic moments and turn them into vertical clips.</p></div>''',unsafe_allow_html=True)

def run(args):
    p=subprocess.run(args,capture_output=True,check=True)
    return p.stdout

def process(src,folder,n,length,progress):
    duration=float(run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(src)]))
    if not 0<duration<=10800: raise ValueError('Video must be at most 180 minutes.')
    if duration<length*n: raise ValueError('Video is too short for this many non-overlapping clips.')
    progress.progress(30,text='Analyzing audio activity…')
    try:
        raw=run(['ffmpeg','-v','error','-i',str(src),'-vn','-ac','1','-ar','2000','-f','s16le','-'])
        a=np.frombuffer(raw,dtype='<i2').astype(np.float32)/32768
        sec=np.array([np.sqrt(np.mean(a[i:i+2000]**2)) for i in range(0,len(a),2000)])
    except subprocess.CalledProcessError: sec=np.zeros(int(duration))
    starts=list(range(0,int(duration-length)+1,5)); starts.append(int(duration-length))
    scores=[float(np.mean(sec[s:s+length])) if len(sec[s:s+length]) else 0 for s in starts]
    chosen=[]
    for i in sorted(range(len(starts)),key=lambda i:scores[i],reverse=True):
        s=starts[i]
        if all(abs(s-t)>=length for t in chosen): chosen.append(s)
        if len(chosen)==n: break
    if len(chosen)<n: chosen=[int(i*duration/n) for i in range(n)]
    results=[]
    for i,s in enumerate(sorted(chosen)):
        out=folder/f'short_{i+1:02d}.mp4'
        run([
            'ffmpeg', '-v', 'error', '-y',
            '-ss', str(s),
            '-i', str(src),
            '-t', str(length),
            '-map', '0:v:0',
            '-map', '0:a:0?',
            '-vf',
            'scale=1080:1920:force_original_aspect_ratio=decrease:force_divisible_by=2,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,setsar=1',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '18',
            '-threads', '2',
            '-pix_fmt', 'yuv420p',
            '-c:a', 'aac',
            '-b:a', '192k',
            '-movflags', '+faststart',
            str(out)
        ])
        results.append((out.name,out.read_bytes(),s)); progress.progress(35+int(65*(i+1)/n),text=f'Rendered {i+1}/{n} clips')
    return results

with st.container(border=True):
    st.subheader('Create your shorts')
    mode=st.radio('Source',['YouTube link','Upload video'],horizontal=True)
    url=st.text_input('YouTube URL',placeholder='https://www.youtube.com/watch?v=…') if mode=='YouTube link' else ''
    upload=st.file_uploader('Video file',type=['mp4','mov','mkv','webm']) if mode=='Upload video' else None
    c1,c2=st.columns(2)
    n=c1.slider('Number of clips',1,5,5); length=c2.slider('Clip duration (seconds)',30,60,40,5)
    allowed=st.checkbox('I own this video or have permission to process it.')
    go=st.button('✦ Generate shorts',use_container_width=True,disabled=not allowed)
if go:
    st.session_state.pop('clips',None)
    p=st.progress(0,text='Preparing video…')
    try:
        with tempfile.TemporaryDirectory(prefix='Reelix-') as tmp:
            folder=Path(tmp)
            if mode=='Upload video':
                if upload is None: raise ValueError('Upload a video first.')
                src=folder/('source'+Path(upload.name).suffix.lower()); src.write_bytes(upload.getbuffer())
            else:
                u=urlparse(url); host=u.hostname or ''
                if u.scheme!='https' or host not in {'youtube.com','www.youtube.com','m.youtube.com','youtu.be'}: raise ValueError('Enter a valid HTTPS YouTube link.')
                with yt_dlp.YoutubeDL({'format':'bv*[height<=1080][ext=mp4]+ba[ext=m4a]/b[height<=480]/bv*[height<=480]+ba','merge_output_format':'mp4','outtmpl':str(folder/'source.%(ext)s'),'noplaylist':True,'max_filesize':1024**3,'quiet':True,'socket_timeout':30}) as y:
                    info=y.extract_info(url,download=False)
                    if not info or info.get('is_live') or not 0<(info.get('duration') or 0)<=10800: raise ValueError('Choose a recorded video under 180 minutes.')
                    y.download([url])
                src=next(f for f in folder.glob('source.*') if f.suffix in {'.mp4','.webm','.mkv'})
            st.session_state.clips=process(src,folder,n,length,p)
        st.success('Your clips are ready!')
    except Exception as e: st.error(f'Processing failed: {e}. If YouTube blocks downloading, upload your authorized video instead.')
if st.session_state.get('clips'):
    st.subheader('Your shorts')
    clips=st.session_state.clips
    for i,(name,data,start) in enumerate(clips):
        with st.container(border=True):
            a,b=st.columns([1,2]); a.video(data); b.markdown(f'**Short {i+1:02d}**'); b.caption(f'Source timestamp: {start//60}:{start%60:02d}'); b.download_button('Download MP4',data,name,'video/mp4',key=name)
    buf=io.BytesIO()
    with zipfile.ZipFile(buf,'w') as z:
        for name,data,_ in clips: z.writestr(name,data)
    st.download_button('Download all clips (ZIP)',buf.getvalue(),'Reelix_shorts.zip','application/zip')
st.caption('Reelix AI • Audio-activity highlights • No paid AI API • Processing time varies')
st.markdown("""
<hr style="border: 0; border-top: 1px solid #302040;">

<div style="text-align:center; padding:25px; color:#a1a1aa;">
<h2 style="color:#a855f7;">REELIX</h2>
<p>Long Videos. Viral Shorts.</p>
<p>Designed & Developed by <b style="color:white;">Atul Verma</b></p>
<p>📞 <a style="color:#c084fc;" href="tel:+916005090551">+91 6005090551</a></p>
<p>✉️ <a style="color:#c084fc;" href="mailto:vermaatul2946@gmail.com">vermaatul2946@gmail.com</a></p>
<p style="font-size:12px; color:#71717a;">© 2026 Reelix. All Rights Reserved.</p>
</div>
""", unsafe_allow_html=True)