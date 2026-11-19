#!/usr/bin/env python3
"""Rights-gated vertical Shorts renderer. Requires ffmpeg, ffprobe, yt-dlp and espeak-ng."""
import argparse, json, os, re, subprocess, sys, tempfile
from pathlib import Path

def run(cmd):
    p=subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if p.returncode:
        raise RuntimeError(p.stdout[-5000:])
    return p.stdout

def clean(s):
    return re.sub(r"\s+", " ", s or "").strip()

def split_caption(text, limit=38):
    words=clean(text).split()
    lines=[]; current=""
    for word in words:
        nxt=(current+" "+word).strip()
        if len(nxt)>limit and current:
            lines.append(current); current=word
        else: current=nxt
    if current: lines.append(current)
    # 2-line chunks keep captions readable on phones.
    return ["\n".join(lines[i:i+2]) for i in range(0,len(lines),2)]

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--source-url",required=True)
    ap.add_argument("--title",required=True)
    ap.add_argument("--narration",required=True)
    ap.add_argument("--output",default="short.mp4")
    ap.add_argument("--rights-approved",required=True)
    args=ap.parse_args()
    if args.rights_approved.lower()!="true":
        raise SystemExit("BLOCKED: rights approval is not true.")
    if not args.source_url.startswith(("https://","http://")):
        raise SystemExit("Invalid source URL.")
    title=clean(args.title)[:100]
    narration=clean(args.narration)
    if len(narration)<20: raise SystemExit("Narration is too short.")
    out=Path(args.output).resolve()
    with tempfile.TemporaryDirectory() as td:
        work=Path(td); media=work/"source.mp4"; voice=work/"voice.wav"; srt=work/"captions.srt"
        run(["yt-dlp","--no-playlist","--merge-output-format","mp4","-o",str(media),args.source_url])
        if not media.exists():
            # yt-dlp may select a different extension/container; locate its output.
            candidates=list(work.glob("source.*"))
            if not candidates: raise RuntimeError("Source download produced no media file.")
            media=candidates[0]
        run(["espeak-ng","-v","en-us","-s","165","-w",str(voice),narration])
        probe=json.loads(run(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(voice)]))
        duration=float(probe["format"]["duration"])
        chunks=split_caption(narration)
        # Evenly time caption chunks across the narration duration.
        with srt.open("w",encoding="utf-8") as f:
            for i,chunk in enumerate(chunks):
                start=duration*i/len(chunks); end=duration*(i+1)/len(chunks)
                def stamp(t):
                    ms=int(t*1000); h=ms//3600000; m=(ms%3600000)//60000; s=(ms%60000)//1000; milli=ms%1000
                    return f"{h:02}:{m:02}:{s:02},{milli:03}"
                f.write(f"{i+1}\n{stamp(start)} --> {stamp(end)}\n{chunk}\n\n")
        # Crop/scale to 9:16; burn readable captions; voiceover is the primary audio.
        vf="scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,subtitles="+str(srt).replace("\\","\\\\").replace(":","\\:")
        run(["ffmpeg","-y","-i",str(media),"-i",str(voice),"-vf",vf,"-map","0:v:0","-map","1:a:0","-t",str(duration),"-r","30","-c:v","libx264","-preset","veryfast","-crf","22","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",str(out)])
    check=json.loads(run(["ffprobe","-v","error","-show_entries","stream=codec_type,codec_name,width,height","-show_entries","format=duration","-of","json",str(out)]))
    video=next((x for x in check["streams"] if x["codec_type"]=="video"),{})
    if video.get("width")!=1080 or video.get("height")!=1920 or video.get("codec_name")!="h264":
        raise RuntimeError("Output validation failed: expected 1080x1920 H.264.")
    if not any(x.get("codec_type")=="audio" and x.get("codec_name")=="aac" for x in check["streams"]):
        raise RuntimeError("Output validation failed: AAC audio missing.")
    print(json.dumps({"ok":True,"output":str(out),"duration":check["format"]["duration"],"width":1080,"height":1920,"video":"h264","audio":"aac"}))

if __name__=="__main__":
    try: main()
    except Exception as e:
        print(f"RENDER_FAILED: {e}",file=sys.stderr); sys.exit(1)
