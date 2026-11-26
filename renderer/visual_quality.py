"""Offline visual screening and visual-content deduplication."""
from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Any
import cv2
import numpy as np

FINGERPRINT_VERSION = "vertical-dhash-v1"

def _vertical_crop(frame: np.ndarray) -> np.ndarray:
    h, w = frame.shape[:2]
    target_w = int(round(h * 9.0 / 16.0))
    if w > target_w:
        left = (w - target_w) // 2
        frame = frame[:, left:left + target_w]
    return frame

def is_blurry(sharpness_scores: list[float]) -> bool:
    if not sharpness_scores:
        return True
    median = float(np.median(sharpness_scores))
    very_blurred = sum(float(v) < 22.0 for v in sharpness_scores) / len(sharpness_scores)
    return median < 35.0 or very_blurred >= 0.60

def has_persistent_facecam(corner_hits: dict[str, int], sample_count: int) -> tuple[bool, str | None, int, int]:
    if sample_count <= 0:
        return False, None, 0, 0
    required = max(4, int(math.ceil(sample_count * 0.40)))
    corner = max(corner_hits, key=corner_hits.get) if corner_hits else ""
    hits = int(corner_hits.get(corner, 0)) if corner else 0
    return hits >= required, (corner if hits >= required else None), hits, required

def _sample_times(duration: float, count: int = 10) -> list[float]:
    if duration <= 0:
        return []
    start, end = min(1.0, duration * 0.05), max(1.0, duration - min(1.0, duration * 0.05))
    if count <= 1 or end <= start:
        return [duration / 2.0]
    return [float(x) for x in np.linspace(start, end, count)]

def inspect_visual_quality(media_path: str | Path, sample_count: int = 10) -> dict[str, Any]:
    """Inspect the final centered 9:16 crop for a persistent face-cam or heavy blur."""
    cap = cv2.VideoCapture(str(media_path))
    if not cap.isOpened():
        raise RuntimeError("Visual quality screening could not open the decoded clip.")
    fps, frame_count = float(cap.get(cv2.CAP_PROP_FPS) or 0), float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    times = _sample_times(frame_count / fps if fps > 0 else 0, sample_count)
    if not times:
        cap.release()
        raise RuntimeError("Visual quality screening could not determine clip duration.")
    frontal = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / "haarcascade_frontalface_default.xml"))
    profile = cv2.CascadeClassifier(str(Path(cv2.data.haarcascades) / "haarcascade_profileface.xml"))
    if frontal.empty():
        cap.release()
        raise RuntimeError("Built-in face detector is unavailable.")
    corners = {n: 0 for n in ("top_left","top_center","top_right","middle_left","middle_right","bottom_left","bottom_center","bottom_right")}
    sharpness = []
    for timestamp in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp * 1000.0)
        ok, frame = cap.read()
        if not ok or frame is None:
            continue
        gray = cv2.cvtColor(cv2.resize(_vertical_crop(frame), (360,640), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        h,w = gray.shape
        sharpness.append(float(cv2.Laplacian(gray, cv2.CV_64F).var()))
        tw,th = int(w*0.38), int(h*0.30)
        xs,ys = (0,(w-tw)//2,w-tw), (0,h-th)
        tiles = {
            "top_left":(xs[0],ys[0]),"top_center":(xs[1],ys[0]),"top_right":(xs[2],ys[0]),
            "middle_left":(xs[0],(h-th)//2),"middle_right":(xs[2],(h-th)//2),
            "bottom_left":(xs[0],ys[1]),"bottom_center":(xs[1],ys[1]),"bottom_right":(xs[2],ys[1])
        }
        for name,(x,y) in tiles.items():
            tile = gray[y:y+th,x:x+tw]
            minimum = max(18,int(min(tile.shape)*0.13))
            faces = frontal.detectMultiScale(tile,scaleFactor=1.08,minNeighbors=5,minSize=(minimum,minimum))
            if len(faces)==0 and not profile.empty():
                faces = profile.detectMultiScale(tile,scaleFactor=1.08,minNeighbors=5,minSize=(minimum,minimum))
            if any(0.005 <= (float(fw)*float(fh))/float(w*h) <= 0.22 for _,_,fw,fh in faces):
                corners[name] += 1
    cap.release()
    if not sharpness:
        raise RuntimeError("Visual quality screening could not decode any frames.")
    facecam,corner,hits,required = has_persistent_facecam(corners,len(sharpness))
    return {
        "samples":len(sharpness),
        "sharpness_median":round(float(np.median(sharpness)),2),
        "blur_rejected":is_blurry(sharpness),
        "facecam_detected":facecam,
        "facecam_corner":corner,
        "facecam_sample_hits":hits,
        "facecam_required_hits":required,
        "facecam_detection":"opencv-haar-persistent-edge-region",
        "inspected_aspect_ratio":"9:16 centered crop"
    }

def select_sharp_frame_time(media_path: str | Path, start_seconds: float = 0.25,
                             end_seconds: float = 8.0, sample_count: int = 20) -> float:
    """Choose a clear early gameplay frame for the opening cover and Shorts thumbnail."""
    cap = cv2.VideoCapture(str(media_path))
    if not cap.isOpened():
        return max(0.0, float(start_seconds))
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 0)
    frame_count = float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration = frame_count / fps if fps > 0 else 0.0
    if duration <= 0:
        cap.release()
        return max(0.0, float(start_seconds))
    left = min(max(0.0, float(start_seconds)), max(0.0, duration - 0.05))
    right = min(max(left + 0.05, float(end_seconds)), max(left + 0.05, duration - 0.05))
    times = np.linspace(left, right, max(2, int(sample_count)))
    best_time, best_score = left, -1.0
    for timestamp in times:
        cap.set(cv2.CAP_PROP_POS_MSEC, float(timestamp) * 1000.0)
        ok, frame = cap.read()
        if not ok or frame is None:
            continue
        gray = cv2.cvtColor(cv2.resize(_vertical_crop(frame), (360, 640), interpolation=cv2.INTER_AREA),
                            cv2.COLOR_BGR2GRAY)
        score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
        if score > best_score:
            best_time, best_score = float(timestamp), score
    cap.release()
    return round(best_time, 3)


def _dhash64(gray: np.ndarray) -> str:
    small = cv2.resize(gray,(9,8),interpolation=cv2.INTER_AREA)
    bits=0
    for row in range(8):
        for col in range(8):
            bits=(bits<<1)|int(small[row,col]>small[row,col+1])
    return f"{bits:016x}"

def compute_content_fingerprint(media_path: str | Path, interval_seconds: float = 2.0,
                                 start_offset_seconds: float = 5.0, max_samples: int = 100) -> dict[str,Any]:
    """Hash visible gameplay in the same centered 9:16 crop; titles/creators are ignored."""
    cap=cv2.VideoCapture(str(media_path))
    if not cap.isOpened():
        raise RuntimeError("Content fingerprint could not open the gameplay clip.")
    fps,frame_count=float(cap.get(cv2.CAP_PROP_FPS) or 0),float(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    duration=frame_count/fps if fps>0 else 0.0
    if duration<=start_offset_seconds+3:
        cap.release()
        raise RuntimeError("Content fingerprint source is too short to compare reliably.")
    times=np.arange(start_offset_seconds,duration-1.0,max(0.5,interval_seconds),dtype=float)
    if len(times)>max_samples:
        times=times[np.linspace(0,len(times)-1,max_samples).astype(int)]
    hashes=[]
    for timestamp in times:
        cap.set(cv2.CAP_PROP_POS_MSEC,float(timestamp)*1000.0)
        ok,frame=cap.read()
        if not ok or frame is None:
            continue
        gray=cv2.cvtColor(cv2.resize(_vertical_crop(frame),(180,320),interpolation=cv2.INTER_AREA),cv2.COLOR_BGR2GRAY)
        hashes.append(_dhash64(gray))
    cap.release()
    if len(hashes)<12:
        raise RuntimeError("Content fingerprint produced too few frames for reliable matching.")
    return {"version":FINGERPRINT_VERSION,"duration_seconds":round(duration,3),
            "interval_seconds":max(0.5,interval_seconds),"frame_hashes":hashes}

def compare_content_fingerprints(first: dict[str,Any], second: dict[str,Any],
                                 max_hamming: int=6,min_coverage: float=0.65) -> dict[str,Any]:
    """Match distinct near-identical frames even when source offsets differ."""
    a=[str(x) for x in first.get("frame_hashes",[])]
    b=[str(x) for x in second.get("frame_hashes",[])]
    if min(len(a),len(b))<12:
        return {"duplicate":False,"matched_frames":0,"coverage":0.0}
    try:
        aa,bb=[int(x,16) for x in a],[int(x,16) for x in b]
    except ValueError:
        return {"duplicate":False,"matched_frames":0,"coverage":0.0}
    pairs=[]
    for i,left in enumerate(aa):
        for j,right in enumerate(bb):
            distance=(left^right).bit_count()
            if distance<=max_hamming:
                pairs.append((distance,i,j))
    pairs.sort()
    used_a,used_b=set(),set()
    total_distance=0
    for distance,i,j in pairs:
        if i in used_a or j in used_b:
            continue
        used_a.add(i);used_b.add(j);total_distance+=distance
    matched=len(used_a);shorter=min(len(a),len(b))
    coverage=matched/shorter if shorter else 0.0
    required=max(12,int(math.ceil(shorter*min_coverage)))
    return {"duplicate":matched>=required and coverage>=min_coverage,
            "matched_frames":matched,"compared_shorter_frames":shorter,
            "coverage":round(coverage,3),
            "mean_hamming_distance":round(total_distance/matched,2) if matched else None,
            "hamming_threshold":max_hamming}

def find_published_duplicate(candidate: dict[str,Any],
                             marker_directory: str | Path=".github/published-clips") -> dict[str,Any] | None:
    """Find a prior published Short with a strong visual-content match."""
    root=Path(marker_directory)
    if not root.is_dir():
        return None
    for marker_path in sorted(root.glob("*.json")):
        try:
            marker=json.loads(marker_path.read_text(encoding="utf-8"))
            previous=marker.get("content_fingerprint")
            if not isinstance(previous,dict) or previous.get("version")!=FINGERPRINT_VERSION:
                continue
            match=compare_content_fingerprints(candidate,previous)
            if match["duplicate"]:
                return {"marker":marker_path.name,"video_url":marker.get("video_url",""),
                        "title":marker.get("title",""),**match}
        except (OSError,ValueError,TypeError):
            continue
    return None
