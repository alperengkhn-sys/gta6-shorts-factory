#!/usr/bin/env python3
"""Rights-gated vertical Shorts renderer. Requires ffmpeg, ffprobe, yt-dlp and espeak-ng."""
import argparse, json, subprocess, sys, tempfile
from pathlib import Path
from urllib.parse import urlsplit

def run(cmd):
    p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    if p.returncode: raise RuntimeError(p.stdout[-5000:])
    return p.stdout

def clean(s): return " ".join((s or "").split())

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

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-url",required=True)
    ap.add_argument("--title",required=True)
    ap.add_argument("--narration",required=True)
    ap.add_argument("--output",default="short.mp4")
    ap.add_argument("--rights-approved",required=True)
    a=ap.parse_args()
    if a.rights_approved.lower()!="true": raise SystemExit("BLOCKED: rights approval is not true.")
    if not validate_source_url(a.source_url): raise SystemExit("Invalid source URL: use an HTTPS Twitch clip URL only.")
    title=clean(a.title)[:90]; narration=clean(a.narration)
    if len(narration)<20: raise SystemExit("Narration is too short.")
    out=Path(a.output).resolve(); out.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory() as td:
        w=Path(td); media=w/"source.mp4"; voice=w/"voice.wav"; srt=w/"captions.srt"; titlefile=w/"title.txt"
        run(["yt-dlp","--no-playlist","--merge-output-format","mp4","-o",str(media),a.source_url])
        if not media.exists():
            found=list(w.glob("source.*"))
            if not found: raise RuntimeError("Source download produced no media file.")
            media=found[0]
        run(["espeak-ng","-v","en-us","-s","165","-w",str(voice),narration])
        voice_info=json.loads(run(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(voice)]))
        voice_duration=float(voice_info["format"]["duration"])
        source_info=json.loads(run(["ffprobe","-v","error","-show_entries","format=duration:stream=codec_type","-of","json",str(media)]))
        source_duration=float(source_info["format"].get("duration") or 0)
        if source_duration<=0: raise RuntimeError("Could not determine source clip duration.")
        duration=min(59.9,max(source_duration,voice_duration))
        has_source_audio=any(stream.get("codec_type")=="audio" for stream in source_info.get("streams",[]))
        chunks=split_caption(narration)
        with srt.open("w",encoding="utf-8") as f:
            for i,chunk in enumerate(chunks):
                f.write(f"{i+1}\n{stamp(voice_duration*i/len(chunks))} --> {stamp(voice_duration*(i+1)/len(chunks))}\n{chunk}\n\n")
        titlefile.write_text(title,encoding="utf-8")
        vf=("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,"
            "drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            "textfile="+str(titlefile)+":fontcolor=white:fontsize=58:borderw=4:bordercolor=black:"
            "x=(w-text_w)/2:y=120,"
            "subtitles="+str(srt).replace("\\","\\\\").replace(":","\\:"))
        if has_source_audio:
            audio_filter=f"[0:a:0]volume=0.22[bg];[1:a:0]volume=1.0[vo];[bg][vo]amix=inputs=2:duration=longest:dropout_transition=2,apad=whole_dur={duration}[aout]"
        else:
            audio_filter=f"[1:a:0]apad=whole_dur={duration}[aout]"
        run(["ffmpeg","-y","-stream_loop","-1","-i",str(media),"-i",str(voice),
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
                      "source_audio_mixed":has_source_audio,"voiceover_duration":round(voice_duration,2)}))

if __name__=="__main__":
    try: main()
    except Exception as e: print(f"RENDER_FAILED: {e}",file=sys.stderr); sys.exit(1)
