#!/usr/bin/env python3
"""Rights-gated vertical Shorts renderer. Requires ffmpeg, ffprobe, yt-dlp and espeak-ng."""
import argparse, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path
from urllib.parse import urlsplit

def run(cmd):
    try:
        p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                         stdin=subprocess.DEVNULL,timeout=300)
    except subprocess.TimeoutExpired as e:
        output=e.stdout or ""
        if isinstance(output,bytes): output=output.decode("utf-8","replace")
        raise RuntimeError(f"Command timed out after 300 seconds: {cmd[0]}\n{output[-5000:]}") from e
    if p.returncode: raise RuntimeError(p.stdout[-5000:])
    return p.stdout

def clean(s): return " ".join((s or "").split())

def tts_executable():
    return shutil.which("espeak-ng") or shutil.which("espeak")

def validate_source_url(value):
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower().rstrip(".")
        return (
            parsed.scheme == "https"
            and parsed.username is None
            and parsed.password is None
            and parsed.port in (None, 443)
            and (host == "twitch.tv" or host.endswith(".twitch.tv"))
        )
    except ValueError:
        return False

def split_caption(text,limit=38):
    words=clean(text).split(); lines=[]; cur=""
    for word in words:
        nxt=(cur+" "+word).strip()
        if len(nxt)>limit and cur: lines.append(cur); cur=word
        else: cur=nxt
    if cur: lines.append(cur)
    return ["\n".join(lines[i:i+2]) for i in range(0,len(lines),2)]

def stamp(t):
    ms=int(t*1000); h=ms//3600000; m=(ms%3600000)//60000; s=(ms%60000)//1000
    return f"{h:02}:{m:02}:{s:02},{ms%1000:03}"
def media_analysis(media):
    info=json.loads(run(["ffprobe","-v","error","-show_entries","format=duration:stream=index,codec_type,codec_name,width,height,r_frame_rate,channels,sample_rate","-of","json",str(media)]))
    streams=info.get("streams",[])
    video=next((s for s in streams if s.get("codec_type")=="video"),{})
    audio=next((s for s in streams if s.get("codec_type")=="audio"),{})
    duration=float(info.get("format",{}).get("duration") or 0)
    fps=video.get("r_frame_rate","0/1")
    try:
        n,d=(int(x) for x in fps.split("/",1)); fps_value=round(n/d,3) if d else 0
    except Exception: fps_value=0
    cmd=["ffmpeg","-nostdin","-hide_banner","-loglevel","info","-i",str(media),"-af","silencedetect=noise=-35dB:d=0.35","-f","null","-"]
    try:
        p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,timeout=120)
        log=p.stdout or ""
    except subprocess.TimeoutExpired:
        log=""
    silence_total=0.0
    for line in log.splitlines():
        if "silence_duration:" in line:
            try: silence_total+=float(line.rsplit("silence_duration:",1)[1].strip())
            except ValueError: pass
    scene_cmd=["ffmpeg","-nostdin","-hide_banner","-loglevel","info","-i",str(media),"-vf","select='gt(scene,0.30)',metadata=print","-an","-f","null","-"]
    try:
        scene_log=subprocess.run(scene_cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,timeout=120).stdout or ""
        scene_changes=sum(1 for line in scene_log.splitlines() if "pts_time:" in line)
    except (subprocess.TimeoutExpired, OSError):
        scene_changes=None
    mean_volume_db=None
    if audio:
        try:
            vol_log=run(["ffmpeg","-nostdin","-hide_banner","-i",str(media),"-vn","-af","volumedetect","-f","null","-"])
            for line in vol_log.splitlines():
                if "mean_volume:" in line:
                    mean_volume_db=float(line.split("mean_volume:",1)[1].split("dB",1)[0].strip())
        except Exception:
            mean_volume_db=None
    return {
        "duration":round(duration,3),
        "video":{"width":video.get("width"),"height":video.get("height"),"fps":fps_value,"codec":video.get("codec_name")},
        "audio":{"present":bool(audio),"codec":audio.get("codec_name"),"channels":audio.get("channels"),"sample_rate":audio.get("sample_rate")},
        "silence_ratio":round(min(1.0,silence_total/duration),3) if duration else 1.0,
        "scene_change_count":scene_changes,
        "mean_volume_db":mean_volume_db,
        "usable_for_shorts":bool(video and duration>0 and duration<=59.9)
    }


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-url",required=True)
    ap.add_argument("--title",required=True)
    ap.add_argument("--narration",required=True)
    ap.add_argument("--output",default="short.mp4")
    ap.add_argument("--rights-approved",required=True)
    ap.add_argument("--test-local-source", help=argparse.SUPPRESS)
    a=ap.parse_args()
    if a.rights_approved.lower()!="true": raise SystemExit("BLOCKED: rights approval is not true.")
    if a.test_local_source:
        if os.environ.get("RENDER_TEST_MODE") != "1":
            raise SystemExit("Local test input is disabled outside the isolated CI test mode.")
        if not Path(a.test_local_source).is_file():
            raise SystemExit("Test source file does not exist.")
    elif not validate_source_url(a.source_url):
        raise SystemExit("Invalid source URL: use an HTTPS Twitch clip URL only.")
    title=clean(a.title)[:90]; narration=clean(a.narration)
    if len(narration)<20: raise SystemExit("Narration is too short.")
    out=Path(a.output).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        w=Path(td); media=w/"source.mp4"; voice=w/"voice.wav"; srt=w/"captions.srt"; titlefile=w/"title.txt"
        if a.test_local_source:
            shutil.copyfile(a.test_local_source, media)
        else:
            run(["yt-dlp","--no-playlist","--merge-output-format","mp4","-o",str(media),a.source_url])
            if not media.exists():
                found=list(w.glob("source.*"))
                if not found: raise RuntimeError("Source download produced no media file.")
                media=found[0]
        tts=tts_executable()
        if not tts: raise RuntimeError("No offline TTS engine found; install espeak-ng or espeak.")
        run([tts,"-v","en-us","-s","165","-w",str(voice),narration])
        voice_info=json.loads(run(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(voice)]))
        voice_duration=float(voice_info["format"]["duration"])
        if voice_duration > 59.9:
            raise RuntimeError("Narration exceeds the 59.9-second Shorts limit; shorten the voiceover.")
        source_info=json.loads(run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type","-of","json",str(media)]))
        source_duration=float(source_info["format"].get("duration") or 0)
        analysis=media_analysis(media)
        analysis_path=out.parent/"render-analysis.json"
        analysis_path.write_text(json.dumps(analysis,indent=2),encoding="utf-8")
        if source_duration<=0: raise RuntimeError("Could not determine source clip duration.")
        duration=min(59.9,max(source_duration,voice_duration))
        has_source_audio=any(stream.get("codec_type")=="audio" for stream in source_info.get("streams",[]))
        chunks=split_caption(narration)
        with srt.open("w",encoding="utf-8") as f:
            for i,chunk in enumerate(chunks):
                f.write(f"{i+1}\n{stamp(voice_duration*i/len(chunks))} --> {stamp(voice_duration*(i+1)/len(chunks))}\n{chunk}\n\n")
        titlefile.write_text(title,encoding="utf-8")
        caption_files=[]
        for i,chunk in enumerate(chunks):
            cf=w/f"caption_{i}.txt"
            cf.write_text(chunk,encoding="utf-8")
            caption_files.append(cf)
        video_pad=max(0.0,duration-source_duration)
        vf=("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,"
            + (f"tpad=stop_mode=clone:stop_duration={video_pad}," if video_pad > 0 else "")
            + "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            "textfile="+str(titlefile)+":fontcolor=white:fontsize=58:borderw=4:bordercolor=black:"
            "x=(w-text_w)/2:y=120")
        for i,cf in enumerate(caption_files):
            start=voice_duration*i/len(chunks); end=voice_duration*(i+1)/len(chunks)
            vf += (",drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
                   "textfile="+str(cf)+":fontcolor=white:fontsize=64:borderw=4:bordercolor=black:"
                   "line_spacing=12:x=(w-text_w)/2:y=h-430:"
                   f"enable='between(t,{start:.3f},{end:.3f})'")
        if has_source_audio:
            audio_filter=(f"[0:a:0]atrim=duration={duration},asetpts=PTS-STARTPTS,volume=0.22[bg];"
                          f"[1:a:0]atrim=duration={duration},asetpts=PTS-STARTPTS,apad=whole_dur={duration}[vo];"
                          "[bg][vo]amix=inputs=2:duration=longest:dropout_transition=2,"
                          f"atrim=duration={duration}[aout]")
        else:
            audio_filter=f"[1:a:0]apad=whole_dur={duration},atrim=duration={duration}[aout]"
        run(["ffmpeg","-nostdin","-hide_banner","-loglevel","warning","-filter_threads","1","-filter_complex_threads","1","-threads","2","-y","-i",str(media),"-i",str(voice),
             "-vf",vf,"-filter_complex",audio_filter,"-map","0:v:0","-map","[aout]","-t",str(duration),
             "-r","30","-c:v","libx264","-preset","veryfast","-crf","22",
             "-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",str(out)])
    check=json.loads(run(["ffprobe","-v","error","-show_entries","stream=codec_type,codec_name,width,height",
                          "-show_entries","format=duration","-of","json",str(out)]))
    video=next((x for x in check["streams"] if x["codec_type"]=="video"),{})
    if video.get("width")!=1080 or video.get("height")!=1920 or video.get("codec_name")!="h264":
        raise RuntimeError("Output validation failed: expected 1080x1920 H.264.")
    if not any(x.get("codec_type")=="audio" and x.get("codec_name")=="aac" for x in check["streams"]):
        raise RuntimeError("Output validation failed: AAC audio missing.")
    print(json.dumps({"ok":True,"output":str(out),"duration":check["format"]["duration"],
                      "width":1080,"height":1920,"video":"h264","audio":"aac",
                      "source_audio_mixed":has_source_audio,"voiceover_duration":round(voice_duration,2),
                      "analysis":analysis}))

if __name__=="__main__":
    try: main()
    except Exception as e: print(f"RENDER_FAILED: {e}",file=sys.stderr); sys.exit(1)
