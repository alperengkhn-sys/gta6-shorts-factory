#!/usr/bin/env python3
"""Vertical Shorts renderer. Preserves original Twitch video and audio; no TTS or added overlays."""
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
        parts = [part for part in parsed.path.split("/") if part]
        is_clip = (
            (host in ("twitch.tv", "www.twitch.tv")
             and ((len(parts) == 2 and parts[0].lower() == "clip")
                  or (len(parts) == 3 and parts[1].lower() == "clip")))
            or (host == "clips.twitch.tv" and len(parts) == 1)
        )
        return (
            parsed.scheme == "https"
            and parsed.username is None
            and parsed.password is None
            and parsed.port in (None, 443)
            and is_clip
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
    ap.add_argument("--output",default="short.mp4")
    ap.add_argument("--test-local-source", help=argparse.SUPPRESS)
    a=ap.parse_args()
    if a.test_local_source:
        if os.environ.get("RENDER_TEST_MODE") != "1":
            raise SystemExit("Local test input is disabled outside the isolated CI test mode.")
        if not Path(a.test_local_source).is_file():
            raise SystemExit("Test source file does not exist.")
    elif not validate_source_url(a.source_url):
        raise SystemExit("Invalid source URL: use an HTTPS Twitch clip URL only.")
    title=clean(a.title)[:90]
    out=Path(a.output).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        w=Path(td); media=w/"source.mp4"
        if a.test_local_source:
            shutil.copyfile(a.test_local_source, media)
        else:
            run(["yt-dlp","--no-playlist","--merge-output-format","mp4","-o",str(media),a.source_url])
            if not media.exists():
                found=list(w.glob("source.*"))
                if not found: raise RuntimeError("Source download produced no media file.")
                media=found[0]
        source_info=json.loads(run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type","-of","json",str(media)]))
        source_duration=float(source_info.get("format",{}).get("duration") or 0)
        streams=source_info.get("streams",[])
        has_source_audio=any(stream.get("codec_type")=="audio" for stream in streams)
        if source_duration < 55:
            raise RuntimeError(f"Source clip is only {source_duration:.1f} seconds. A 60-second Short requires a source clip of at least 55 seconds; the source will not be looped or padded.")
        if not has_source_audio:
            raise RuntimeError("Original Twitch clip has no audio stream; refusing to add synthetic audio.")
        analysis=media_analysis(media)
        analysis_path=out.parent/"render-analysis.json"
        analysis_path.write_text(json.dumps(analysis,indent=2),encoding="utf-8")
        duration=min(60.0,source_duration)
        vf="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1"
        render_cmd=["ffmpeg","-nostdin","-hide_banner","-loglevel","info","-stats_period","1",
             "-filter_threads","1","-threads","2","-y","-i",str(media),"-vf",vf,
             "-map","0:v:0","-map","0:a:0","-t",str(duration),"-r","30",
             "-c:v","libx264","-preset","ultrafast","-crf","23",
             "-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",str(out)]
        print("RENDER_STAGE: encoding original Twitch video and audio only",flush=True)
        run(render_cmd)
        print("RENDER_STAGE: final encode completed",flush=True)
    check=json.loads(run(["ffprobe","-v","error","-show_entries","stream=codec_type,codec_name,width,height",
                          "-show_entries","format=duration","-of","json",str(out)]))
    video=next((x for x in check["streams"] if x["codec_type"]=="video"),{})
    if video.get("width")!=1080 or video.get("height")!=1920 or video.get("codec_name")!="h264":
        raise RuntimeError("Output validation failed: expected 1080x1920 H.264.")
    if not any(x.get("codec_type")=="audio" and x.get("codec_name")=="aac" for x in check["streams"]):
        raise RuntimeError("Output validation failed: AAC audio missing.")
    print(json.dumps({"ok":True,"output":str(out),"duration":check["format"]["duration"],
                      "width":1080,"height":1920,"video":"h264","audio":"aac",
                      "original_audio_preserved":has_source_audio,
                      "analysis":analysis}))

if __name__=="__main__":
    try: main()
    except Exception as e: print(f"RENDER_FAILED: {e}",file=sys.stderr); sys.exit(1)
