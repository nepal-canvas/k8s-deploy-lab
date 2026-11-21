"""Generate candidate looks for an ORIGINAL AI news presenter (not based on any real person).
Tries Gemini image models (GEMINI_API_KEY), falls back to Pollinations (free, no key).
Writes presenter/cand_*.png and a contact sheet presenter/sheet.jpg."""
import base64
import os
import subprocess
import time
import urllib.parse
from pathlib import Path

import requests

OUT = Path("presenter")
OUT.mkdir(exist_ok=True)
KEY = os.getenv("GEMINI_API_KEY", "")
BASE = ("Photorealistic vertical head-and-shoulders portrait of a fictional {who}, an original character, "
        "not resembling any real or famous person. Friendly, trustworthy, calm half-smile, looking straight at the camera. "
        "{wear}. Soft studio key light, shallow depth of field, plain softly blurred deep-blue news-studio background "
        "with a faint warm accent light. No text, no logos, no watermark, no microphone in front of the face.")
LOOKS = [
    ("Nepali woman news presenter in her late 20s, shoulder-length black hair", "navy blazer over a white top, small simple earrings"),
    ("Nepali man news presenter in his early 30s, short neat black hair, clean shaven", "charcoal suit, light-blue shirt, no tie"),
    ("Nepali woman news presenter in her early 30s, hair in a low bun", "maroon kurta-style top with a subtle dhaka-pattern border"),
    ("Nepali man news presenter in his late 20s, short hair, light stubble", "dark-green bomber jacket over a plain black t-shirt, modern youthful look"),
]
MODELS = ["gemini-2.5-flash-image", "gemini-2.5-flash-image-preview", "gemini-3-pro-image-preview"]


def gemini(prompt):
    for m in MODELS:
        try:
            r = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={KEY}",
                json={"contents": [{"parts": [{"text": prompt}]}],
                      "generationConfig": {"responseModalities": ["IMAGE"]}}, timeout=120)
            if r.status_code != 200:
                print(f"[presenter] {m}: {r.status_code} {r.text[:160]}"); continue
            for part in r.json()["candidates"][0]["content"]["parts"]:
                if "inlineData" in part:
                    return base64.b64decode(part["inlineData"]["data"]), m
        except Exception as e:
            print(f"[presenter] {m}: {e}")
    return None, None


def pollinations(prompt, seed):
    url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
           + f"?width=768&height=1152&nologo=true&seed={seed}&model=flux")
    for _ in range(3):
        try:
            r = requests.get(url, timeout=180)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                return r.content
            print(f"[presenter] pollinations {r.status_code}")
        except Exception as e:
            print(f"[presenter] pollinations {e}")
        time.sleep(10)
    return None


files = []
for i, (who, wear) in enumerate(LOOKS, 1):
    p = BASE.format(who=who, wear=wear)
    img, src = (gemini(p) if KEY else (None, None))
    if img is None:
        img, src = pollinations(p, 1000 + i), "pollinations-flux"
    if img:
        f = OUT / f"cand_{i}.png"
        f.write_bytes(img)
        files.append(f)
        print(f"[presenter] look {i}: {src} {len(img)//1024} KB")
    else:
        print(f"[presenter] look {i}: failed")

if files:
    inputs = sum((["-i", str(f)] for f in files), [])
    n = len(files)
    filt = "".join(f"[{k}:v]scale=384:576:force_original_aspect_ratio=increase,crop=384:576,"
                   f"drawtext=text='{k+1}':fontcolor=white:fontsize=48:box=1:boxcolor=black@0.6:x=16:y=16[v{k}];"
                   for k in range(n)) + "".join(f"[v{k}]" for k in range(n)) + f"hstack=inputs={n}"
    subprocess.run(["ffmpeg", "-y", *inputs, "-filter_complex", filt, "-frames:v", "1",
                    str(OUT / "sheet.jpg")], check=False)
