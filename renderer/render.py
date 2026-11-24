#!/usr/bin/env python3
"""Vertical Shorts renderer with silence trimming, original audio, branding overlays and unique covers."""
import argparse, json, math, os, shutil, struct, subprocess, sys, tempfile, wave
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

def validate_source_url(value):
    try:
        parsed = urlsplit(value)
        host = (parsed.hostname or "").lower().rstrip(".")
        if not host or host in ("localhost", "localhost.localdomain"):
            return False
        import ipaddress
        try:
            address = ipaddress.ip_address(host)
            if not address.is_global:
                return False
        except ValueError:
            if "." not in host or host.endswith(".local"):
                return False
        secure_public_url = (
            parsed.scheme == "https"
            and parsed.username is None
            and parsed.password is None
            and parsed.port in (None, 443)
            and not parsed.fragment
        )
        # Production inputs must be Twitch clips only. The isolated CI fixture
        # uses a local file and bypasses this URL check in main().
        twitch_clip = (
            (host == "clips.twitch.tv" and len([p for p in parsed.path.split("/") if p]) >= 1)
            or (
                host in ("twitch.tv", "www.twitch.tv", "m.twitch.tv")
                and len([p for p in parsed.path.split("/") if p]) >= 3
                and [p.lower() for p in parsed.path.split("/") if p][-2] == "clip"
            )
        )
        return secure_public_url and twitch_clip
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
    silence_intervals=[]
    open_silence=None
    for line in log.splitlines():
        if "silence_start:" in line:
            try: open_silence=float(line.split("silence_start:",1)[1].strip().split()[0])
            except ValueError: pass
        if "silence_duration:" in line:
            try: silence_total+=float(line.rsplit("silence_duration:",1)[1].strip())
            except ValueError: pass
        if "silence_end:" in line and open_silence is not None:
            try:
                silence_end=float(line.split("silence_end:",1)[1].split("|",1)[0].strip())
                silence_intervals.append((open_silence,silence_end))
                open_silence=None
            except ValueError: pass
    if open_silence is not None: silence_intervals.append((open_silence,duration))
    scene_cmd=["ffmpeg","-nostdin","-hide_banner","-loglevel","info","-i",str(media),"-vf","select='gt(scene,0.30)',metadata=print","-an","-f","null","-"]
    try:
        scene_log=subprocess.run(scene_cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,timeout=120).stdout or ""
        scene_times=[]
        for line in scene_log.splitlines():
            if "pts_time:" in line:
                try: scene_times.append(float(line.split("pts_time:",1)[1].split()[0]))
                except ValueError: pass
        scene_changes=len(scene_times)
    except (subprocess.TimeoutExpired, OSError):
        scene_times=[]
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
        "usable_for_shorts":bool(video and duration>=25),
        "_silence_intervals":silence_intervals,
        "_scene_change_times":scene_times
    }




def request_vision_completion(request):
    """Retry transient OpenAI rate limits, but fail clearly when project quota is exhausted."""
    import time
    import urllib.error
    import urllib.request

    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", "replace")
            try:
                error = json.loads(body).get("error", {})
            except (json.JSONDecodeError, AttributeError):
                error = {}
            code = str(error.get("code") or "")
            message = str(error.get("message") or body or exc)
            if exc.code == 429 and code == "insufficient_quota":
                raise RuntimeError("OpenAI API quota/billing is exhausted for this API project. Add API credits or raise its usage limit; no unreviewed video was rendered.") from exc
            if exc.code == 429 and attempt < 2:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                try:
                    delay = max(1, min(10, int(float(retry_after)))) if retry_after else 2 ** (attempt + 1)
                except (TypeError, ValueError):
                    delay = 2 ** (attempt + 1)
                time.sleep(delay)
                continue
            raise RuntimeError(f"OpenAI vision API HTTP {exc.code}: {message}") from exc
    raise RuntimeError("OpenAI vision API remained rate-limited after three attempts.")


def vision_review(media, workdir):
    """Use sampled real frames for semantic highlight review when an API key is configured."""
    # The isolated CI fixture has no real Twitch content and must not call a paid vision API.
    if os.environ.get("RENDER_TEST_MODE") == "1":
        return {"score":100,"compelling":True,"event":"CI synthetic fixture",
          "category":"other","youtube_safe":True,"age_restriction_recommended":False,
          "editing_treatment":"standard","editorial_tone":"neutral",
          "reasons":["isolated synthetic CI fixture"],"confidence":1.0,
          "status":"passed","provider":"test_fixture","model":"none","frames_sampled":0,
          "age_restriction_status":"not_recommended"}
    api_key=(os.environ.get("OPENAI_API_KEY") or "").strip()
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured; refusing to render without visual AI review.")
    import base64, urllib.request, urllib.error
    duration=float(json.loads(run(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(media)])).get("format",{}).get("duration") or 0)
    if duration<=0:
        raise RuntimeError("Vision review could not determine source duration.")
    frames=[]
    # Six evenly spaced frames let the reviewer judge what actually happens, not just the clip title.
    for i in range(6):
        at=max(0.1,min(duration-0.1,duration*(i+0.5)/6))
        frame=workdir/f"vision-frame-{i}.jpg"
        run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y","-ss",str(at),"-i",str(media),"-frames:v","1","-vf","scale=512:-2","-q:v","5",str(frame)])
        if frame.is_file():
            frames.append({"type":"image_url","image_url":{"url":"data:image/jpeg;base64,"+base64.b64encode(frame.read_bytes()).decode("ascii"),"detail":"low"}})
    if len(frames)<4:
        raise RuntimeError("Vision review failed: fewer than four frames could be sampled.")
    prompt=("Review these timestamp-ordered frames sampled from a GTA VI gameplay clip. Judge the actual visible content, not its title. "
      "Return ONLY JSON with keys: score (0-100), compelling (boolean), event (short factual description), "
      "category (action|comedy|police|vehicle|story|nightlife|mature_suggestive|exploration|mundane|other), "
      "youtube_safe (boolean), age_restriction_recommended (boolean), editing_treatment "
      "(standard|mature_non_explicit|reject), editorial_tone (short string), "
      "reasons (array of short strings), confidence (0-1). "
      "Score the actual clip from 0 to 100 using these priorities: immediate attention-grabbing hook in the opening (15), clear and understandable event (15), funny or surprising payoff (15), action/intensity or genuinely interesting NPC/streamer reaction (15), visual quality and readable framing (10), replay value (10), strong Shorts title potential (10), and originality/non-repetition (10). "
      "85-100 means priority, 70-84 means suitable for publishing, 45-69 means review only and must not be auto-published, 0-44 means reject. "
      "Prioritize funny moments, unexpected events, fails, interesting NPC behavior, discoveries/easter eggs, vehicles/races, conflicts/action, visible streamer reactions, viral short-form gameplay moments, and clearly demonstrated updates/new features. "
      "A clip must show the event itself; a promising title alone is not enough. "
      "Strong action, funny incidents, chases, crashes, fights, surprising interactions and non-explicit adult nightlife/suggestive scenes can score highly. "
      "Do NOT penalize a clip merely because it shows nightclubs, strip-club settings, adult jokes, flirting, suggestive dancing, romance, revealing outfits or mature atmosphere. "
      "For non-explicit adult material that is otherwise suitable, set category=mature_suggestive, editing_treatment=mature_non_explicit, "
      "and age_restriction_recommended=true when the visible material reasonably warrants an 18+ audience. "
      "The edit should preserve the context and strongest moment, avoid sensational sexual framing, and use neutral factual English captions/narration. "
      "For ordinary gameplay use editing_treatment=standard and age_restriction_recommended=false. "
      "Penalize uneventful walking, running, ordinary driving, static scenes and unclear clips. "
      "Mark youtube_safe=false and editing_treatment=reject for explicit sexual activity or visible explicit nudity; do not recommend uploading those. "
      "Do not infer events that are not visible in these frames.")
    payload={"model":os.environ.get("VISION_MODEL","gpt-4o-mini"),"temperature":0,"max_tokens":350,
      "response_format":{"type":"json_object"},"messages":[{"role":"user","content":[{"type":"text","text":prompt},*frames]}]}
    req=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=json.dumps(payload).encode("utf-8"),
      headers={"Authorization":"Bearer "+api_key,"Content-Type":"application/json"},method="POST")
    try:
        result = request_vision_completion(req)
    except RuntimeError as exc:
        error_text = str(exc).lower()
        if any(marker in error_text for marker in ("quota/billing is exhausted", "no credits remaining", "insufficient_quota", "billing hard limit")):
            # Keep production moving, but never publish an unreviewed clip publicly.
            return {
                "score": 0, "compelling": False, "event": "AI review unavailable",
                "category": "unreviewed", "youtube_safe": False,
                "age_restriction_recommended": True,
                "editing_treatment": "standard", "editorial_tone": "neutral",
                "reasons": ["OpenAI quota exhausted; generated without visual AI review and held private."],
                "confidence": 0.0, "status": "unreviewed_private",
                "provider": "none", "model": "none", "frames_sampled": len(frames),
                "age_restriction_status": "manual_review_required"
            }
        raise RuntimeError(f"Vision review API failed; refusing an unreviewed render: {exc}") from exc
    except Exception as exc:
        raise RuntimeError(f"Vision review API failed; refusing an unreviewed render: {exc}") from exc
    try:
        review=json.loads(result["choices"][0]["message"]["content"])
        score=max(0,min(100,int(review.get("score",0))))
    except Exception as exc:
        raise RuntimeError("Vision review returned an invalid response; refusing an unreviewed render.") from exc
    review["score"]=score
    review["category"]=review.get("category","other")
    review["age_restriction_recommended"]=bool(review.get("age_restriction_recommended",False))
    review["editing_treatment"]=review.get("editing_treatment","standard")
    if review["category"]=="mature_suggestive" and review.get("youtube_safe") is True:
        review["editing_treatment"]="mature_non_explicit"
        review["age_restriction_recommended"]=True
    review["age_restriction_status"]=("platform_setting_unavailable_via_data_api"
        if review["age_restriction_recommended"] else "not_recommended")
    review["status"]="passed" if score>=int(os.environ.get("VISION_MIN_SCORE","58")) and review.get("youtube_safe") is True else "rejected"
    review["provider"]="openai"
    review["model"]=payload["model"]
    review["frames_sampled"]=len(frames)
    if review["status"]!="passed":
        raise RuntimeError("Visual AI rejected this clip (score="+str(score)+", safe="+str(review.get("youtube_safe"))+"): "+clean("; ".join(review.get("reasons",[]))))
    return review

def create_brand_sting(workdir, duration=4.0):
    """Create an original, non-sampled 4-second VI RUSH sonic logo."""
    sample_rate = 44100
    total = int(sample_rate * duration)
    # Original rising electronic motif: D minor / F / A with a warm low pulse.
    notes = [(146.83, 0.00, 0.85), (220.00, 0.34, 1.05),
             (293.66, 0.78, 1.35), (440.00, 1.28, 2.05),
             (587.33, 2.02, 3.10), (440.00, 2.55, 3.65)]
    frames = bytearray()
    for i in range(total):
        t = i / sample_rate
        value = 0.0
        # Soft cinematic low pulse, fading before the source clip takes over.
        bass_env = min(1.0, t / 0.08) * max(0.0, 1.0 - t / 3.8)
        value += 0.19 * bass_env * math.sin(2 * math.pi * (55 + 8 * t) * t)
        for freq, start, end in notes:
            local = t - start
            if 0 <= local <= 0.72:
                attack = min(1.0, local / 0.025)
                decay = math.exp(-3.0 * local)
                env = attack * decay
                phase = 2 * math.pi * freq * local
                value += 0.105 * env * (math.sin(phase) + 0.22 * math.sin(2 * phase))
        # Short airy upward sweep, entirely synthesized (no third-party samples).
        if 0.05 <= t <= 2.4:
            sweep = (t - 0.05) / 2.35
            env = math.sin(math.pi * sweep) ** 1.5
            freq = 520 + 1250 * sweep
            value += 0.035 * env * math.sin(2 * math.pi * freq * t)
        # Gentle stereo width without changing pitch or timing.
        left = max(-1.0, min(1.0, value * 0.92))
        right = max(-1.0, min(1.0, value * 0.86))
        frames.extend(struct.pack("<hh", int(left * 32767), int(right * 32767)))
    path = Path(workdir) / "vi-rush-original-sonic-logo.wav"
    with wave.open(str(path), "wb") as audio:
        audio.setnchannels(2)
        audio.setsampwidth(2)
        audio.setframerate(sample_rate)
        audio.writeframes(frames)
    return path


def branding_assets():
    root = Path("branding")
    specs = [
        ("banner.png", "1080:-1", "(W-w)/2", "0", "always"),
        ("logo.png", "190:-1", "40", "40", "always"),
        ("subscribe.png", "390:-1", "(W-w)/2", "H-h-130", "ending"),
        ("notification.png", "460:-1", "(W-w)/2", "H-h-420", "ending"),
        # Supplied VI RUSH / Leonida Loop artwork is used as a short branded
        # opening bumper and closing end card, not merely archived in the ZIP.
        ("image_50843161.jpg", "1080:1920", "0", "0", "intro"),
        ("image_50843161.jpg", "1080:1920", "0", "0", "outro"),
    ]
    return [(root / name, scale, x, y, timing) for name, scale, x, y, timing in specs if (root / name).is_file()]

def video_filter(duration, assets, subtitles_path=None, mature=False):
    base = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1"
    if subtitles_path:
        subtitle_file = str(subtitles_path).replace("\\", "\\\\").replace(":", "\\:")
        base += (f",subtitles='{subtitle_file}':force_style="
                 "'FontName=DejaVu Sans,FontSize=18,PrimaryColour=&H00FFFFFF,"
                 "OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=1,"
                 "Alignment=2,MarginV=330'")
    if not assets:
        return base, []
    parts = [f"[0:v]{base}[base]"]
    inputs = []
    current = "base"
    for index, (_, scale, x, y, timing) in enumerate(assets, start=1):
        label = f"ov{index}"
        next_label = f"v{index}"
        if timing in ("intro", "outro"):
            # Full-frame vertical branded bumper/end card.
            image_filter = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,format=rgba"
        else:
            image_filter = f"scale={scale}:force_original_aspect_ratio=decrease,format=rgba"
        parts.append(f"[{index}:v]{image_filter}[{label}]")
        if timing == "always":
            enable = f"between(t,0,{duration:.3f})"
        elif timing == "intro":
            enable = f"between(t,0,{min(2.5,duration):.3f})"
        elif timing == "ending":
            enable = f"between(t,{max(0,duration-5):.3f},{duration:.3f})"
        else:
            enable = f"between(t,{max(0,duration-3):.3f},{duration:.3f})"
        parts.append(f"[{current}][{label}]overlay=x={x}:y={y}:eof_action=pass:enable='{enable}'[{next_label}]")
        current = next_label
        inputs.extend(["-loop", "1", "-i", str(assets[index-1][0])])
    if mature:
        parts.append(
            f"[{current}]drawtext=fontfile=/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf:"
            "text='MATURE THEMES':fontcolor=white:fontsize=34:borderw=3:bordercolor=black:"
            "box=1:boxcolor=black@0.55:boxborderw=12:x=(w-text_w)/2:y=110:"
            "enable='between(t,0,5)'[mature]"
        )
        current = "mature"
    return ";".join(parts), inputs + ["-map", f"[{current}]"]


def create_voiceover(package_text, workdir):
    import re
    match = re.search(r"ORIGINAL VOICEOVER DRAFT:\s*([\s\S]*?)(?=\n\n[A-Z][A-Z /_-]+:|\Z)", package_text or "")
    narration = clean(match.group(1)) if match else ""
    if len(narration) < 35:
        return None, None
    audio = workdir / "editorial-voiceover.mp3"
    result = subprocess.run(
        ["edge-tts", "--voice", "en-US-GuyNeural", "--rate=+5%", "--text", narration, "--write-media", str(audio)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL, timeout=120
    )
    if result.returncode or not audio.is_file() or audio.stat().st_size < 1000:
        raise RuntimeError("English editorial voiceover generation failed: " + (result.stdout or "")[-1200:])
    info = json.loads(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(audio)]))
    voice_duration = float(info.get("format", {}).get("duration") or 0)
    if voice_duration < 2:
        raise RuntimeError("Generated editorial voiceover is unexpectedly short.")
    sentences = [clean(x) for x in re.split(r"(?<=[.!?])\s+", narration) if clean(x)]
    chunks = []
    for sentence in sentences:
        words = sentence.split()
        while words:
            chunks.append(" ".join(words[:7]))
            words = words[7:]
    if not chunks:
        chunks = [narration]
    weights = [max(1, len(x.split())) for x in chunks]
    total = sum(weights)
    cursor = 0.0
    srt = []
    def stamp(seconds):
        ms = int(seconds * 1000)
        return f"{ms//3600000:02}:{(ms%3600000)//60000:02}:{(ms%60000)//1000:02},{ms%1000:03}"
    for index, (chunk, weight) in enumerate(zip(chunks, weights), 1):
        start = cursor
        cursor += voice_duration * weight / total
        srt.append(f"{index}\n{stamp(start)} --> {stamp(cursor)}\n{chunk}\n")
    subtitles = workdir / "editorial-captions.srt"
    subtitles.write_text("\n".join(srt), encoding="utf-8")
    return audio, subtitles

def make_cover(video, title, duration, destination):
    safe = (clean(title)[:52].replace("\\", "\\\\").replace(":", "\\:")
            .replace("'", "\\'").replace("%", "\\%").replace("[", "\\[")
            .replace("]", "\\]").replace(",", "\\,").replace(";", "\\;"))
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    vf = ("scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,"
          f"drawtext=fontfile={font}:text='{safe}':fontcolor=white:fontsize=66:"
          "borderw=4:bordercolor=black:box=1:boxcolor=black@0.48:boxborderw=24:"
          "x=(w-text_w)/2:y=h-text_h-180")
    run(["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
         "-ss", str(min(max(duration * 0.35, 0.5), max(duration - 0.5, 0.5))),
         "-i", str(video), "-frames:v", "1", "-vf", vf, "-q:v", "2", str(destination)])



def select_highlight_window(duration, silence_intervals, scene_times, window=55.0, stride=10.0):
    """Choose an active window using non-silent audio and detected scene changes."""
    duration=float(duration)
    if duration<=window:
        return 0.0,duration,0.0
    window=min(float(window),duration)
    stride=max(1.0,float(stride))
    last=max(0.0,duration-window)
    starts=[]
    cursor=0.0
    while cursor<last:
        starts.append(cursor)
        cursor+=stride
    starts.append(last)
    best=(0.0,-1.0)
    for start in starts:
        end=start+window
        silent=0.0
        for silence_start,silence_end in silence_intervals:
            silent+=max(0.0,min(end,silence_end)-max(start,silence_start))
        active=max(0.0,window-min(window,silent))
        scenes=sum(1 for point in scene_times if start<=point<end)
        score=active+1.5*scenes
        if score>best[1]:
            best=(start,score)
    return round(best[0],2),round(window,2),round(best[1],2)


def auto_trim_silence(media, workdir):
    log=run(["ffmpeg","-nostdin","-hide_banner","-i",str(media),"-af","silencedetect=noise=-35dB:d=0.8","-f","null","-"])
    meta=json.loads(run(["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(media)]))
    duration=float(meta.get("format",{}).get("duration") or 0)
    starts=[]; gaps=[]
    for line in log.splitlines():
        if "silence_start:" in line:
            try: starts.append(float(line.split("silence_start:",1)[1].strip().split()[0]))
            except ValueError: pass
        if "silence_end:" in line and "silence_duration:" in line and starts:
            try:
                end=float(line.split("silence_end:",1)[1].split("|",1)[0].strip())
                length=float(line.split("silence_duration:",1)[1].strip().split()[0])
                gaps.append((starts.pop(0),end,length))
            except ValueError: pass
    if starts: gaps.append((starts[0],duration,duration-starts[0]))
    cuts=[(a,b) for a,b,d in gaps if d>=1.25 and a>0.2 and b<duration-0.2]
    if not cuts: return media,duration,0
    keep=[]; cursor=0.0
    for a,b in cuts:
        left=max(cursor,a-0.12); right=min(duration,b+0.12)
        if left-cursor>0.25: keep.append((cursor,left))
        cursor=max(cursor,right)
    if duration-cursor>0.25: keep.append((cursor,duration))
    kept=sum(b-a for a,b in keep)
    if len(keep)<2 or kept<15 or duration-kept<1.5: return media,duration,0
    parts=[]
    for i,(a,b) in enumerate(keep):
        part=workdir/f"trim-{i:02d}.mp4"
        run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y","-ss",str(a),"-i",str(media),"-t",str(b-a),"-map","0:v:0","-map","0:a:0","-c:v","libx264","-preset","ultrafast","-crf","23","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k",str(part)])
        parts.append(part)
    listing=workdir/"concat.txt"
    listing.write_text("".join("file '"+p.as_posix()+"'\\n" for p in parts),encoding="utf-8")
    output=workdir/"trimmed.mp4"
    run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y","-f","concat","-safe","0","-i",str(listing),"-c","copy",str(output)])
    return output,kept,round(duration-kept,2)


def trailing_silence_seconds(log, duration):
    """Return the final silent tail reported by FFmpeg, or zero if audio reaches the end."""
    start = None
    for line in log.splitlines():
        if "silence_start:" in line:
            try:
                start = float(line.split("silence_start:", 1)[1].strip().split()[0])
            except ValueError:
                pass
        if "silence_end:" in line:
            start = None
    return max(0.0, duration - start) if start is not None else 0.0


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
        raise SystemExit("Invalid source URL: production rendering accepts public HTTPS Twitch clip URLs only.")
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
        if source_duration < 25:
            raise RuntimeError(f"Source clip is only {source_duration:.1f} seconds. A Short requires a source clip of at least 25 seconds; the source will not be looped or padded.")
        if not has_source_audio:
            raise RuntimeError("Source clip has no audio stream; refusing to add synthetic audio.")
        analysis=media_analysis(media)
        analysis["vision_review"]=vision_review(media,w)
        silence_intervals=analysis.pop("_silence_intervals",[])
        scene_times=analysis.pop("_scene_change_times",[])
        highlight_start,highlight_duration,highlight_score=select_highlight_window(source_duration,silence_intervals,scene_times)
        selected_source=media
        if source_duration>highlight_duration:
            selected_source=w/"selected-highlight.mp4"
            run(["ffmpeg","-nostdin","-hide_banner","-loglevel","error","-y","-ss",str(highlight_start),"-i",str(media),"-t",str(highlight_duration),"-map","0:v:0","-map","0:a:0","-c:v","libx264","-preset","ultrafast","-crf","23","-pix_fmt","yuv420p","-c:a","aac","-b:a","160k",str(selected_source)])
        analysis["highlight_selection"]={"start_seconds":highlight_start,"duration_seconds":highlight_duration,"activity_score":highlight_score,"method":"non-silent audio + scene-change density"}
        media_for_render,edited_duration,removed_silence=auto_trim_silence(selected_source,w)
        analysis["silence_removed_seconds"]=removed_silence
        analysis["automatic_dead_air_trim"]=removed_silence>0
        analysis_path=out.parent/"render-analysis.json"
        analysis_path.write_text(json.dumps(analysis,indent=2),encoding="utf-8")
        duration=min(60.0,edited_duration)
        assets=branding_assets()
        voiceover, subtitles = create_voiceover(os.environ.get("PACKAGE_TEXT", ""), w)
        brand_sting = create_brand_sting(w, duration=4.0)
        mature_edit = analysis["vision_review"].get("editing_treatment") == "mature_non_explicit"
        vf, overlay_inputs=video_filter(duration,assets,subtitles,mature=mature_edit)
        analysis["mature_content_editing"] = {
            "applied": mature_edit,
            "opening_notice": "MATURE THEMES" if mature_edit else None,
            "narration_tone": analysis["vision_review"].get("editorial_tone", "neutral"),
            "age_restriction_recommended": analysis["vision_review"].get("age_restriction_recommended", False),
            "age_restriction_status": analysis["vision_review"].get("age_restriction_status", "not_recommended")
        }
        render_cmd=["ffmpeg","-nostdin","-hide_banner","-loglevel","info","-stats_period","1",
             "-filter_threads","1","-threads","2","-y","-i",str(media_for_render)]
        if assets:
            render_cmd += overlay_inputs[:-2]
        voice_index = 1 + len(assets)
        if voiceover:
            render_cmd += ["-i", str(voiceover)]
        sting_index = voice_index + (1 if voiceover else 0)
        render_cmd += ["-i", str(brand_sting)]
        if not assets:
            vf = f"[0:v]{vf}[vout]"
            video_map = "[vout]"
        else:
            video_map = overlay_inputs[-1]
            vf += ";" if vf else ""
        if voiceover:
            vf += (f"[0:a][{voice_index}:a]sidechaincompress=threshold=0.025:ratio=8:attack=20:release=450[duck];"
                   f"[duck][{voice_index}:a]amix=inputs=2:duration=longest:dropout_transition=0[aout];")
        else:
            vf += "[0:a:0]anull[aout];"
        vf += (f"[aout][{sting_index}:a]amix=inputs=2:duration=first:"
               "dropout_transition=0:weights='1 0.28'[finala]")
        audio_map = "[finala]"
        render_cmd += ["-filter_complex",vf,"-map",video_map,"-map",audio_map]
        render_cmd += ["-t",str(duration),"-r","30",
             "-c:v","libx264","-preset","ultrafast","-crf","23",
             "-pix_fmt","yuv420p","-c:a","aac","-b:a","160k","-movflags","+faststart",str(out)]
        print(f"RENDER_STAGE: encoding source video and audio with {len(assets)} branding overlays",flush=True)
        run(render_cmd)
        print("RENDER_STAGE: final encode completed",flush=True)
        analysis["ai_voiceover_added"]=bool(voiceover)
        analysis["audio_editing"]="original source audio ducked under English editorial voiceover" if voiceover else "original source audio preserved; no added voiceover"
        analysis_path.write_text(json.dumps(analysis,indent=2),encoding="utf-8")
        cover_path=out.parent/"short-cover.jpg"
        make_cover(out,title,duration,cover_path)
        print(f"RENDER_STAGE: generated cover {cover_path}",flush=True)
    check=json.loads(run(["ffprobe","-v","error","-show_entries","stream=codec_type,codec_name,width,height,duration",
                          "-show_entries","format=duration","-of","json",str(out)]))
    video=next((x for x in check["streams"] if x["codec_type"]=="video"),{})
    if video.get("width")!=1080 or video.get("height")!=1920 or video.get("codec_name")!="h264":
        raise RuntimeError("Output validation failed: expected 1080x1920 H.264.")
    if not any(x.get("codec_type")=="audio" and x.get("codec_name")=="aac" for x in check["streams"]):
        raise RuntimeError("Output validation failed: AAC audio missing.")
    output_duration=float(check.get("format",{}).get("duration") or 0)
    audio_stream=next((x for x in check["streams"] if x.get("codec_type")=="audio"),{})
    audio_duration=float(audio_stream.get("duration") or output_duration)
    if audio_duration < output_duration - 0.5:
        raise RuntimeError(f"Output validation failed: audio track ends early ({audio_duration:.1f}s of {output_duration:.1f}s).")
    silence_log=run(["ffmpeg","-nostdin","-hide_banner","-i",str(out),"-vn","-af","silencedetect=noise=-45dB:d=3","-f","null","-"])
    trailing_silence=trailing_silence_seconds(silence_log,output_duration)
    if trailing_silence >= 3.0:
        raise RuntimeError(f"Output validation failed: audio is silent for the final {trailing_silence:.1f}s; refusing to publish.")
    print(json.dumps({"ok":True,"output":str(out),"duration":check["format"]["duration"],
                      "width":1080,"height":1920,"video":"h264","audio":"aac",
                      "original_audio_preserved":has_source_audio,
                      "analysis":analysis,"cover":str(cover_path),"branding_overlays":len(assets)}))

if __name__=="__main__":
    try: main()
    except Exception as e: print(f"RENDER_FAILED: {e}",file=sys.stderr); sys.exit(1)
