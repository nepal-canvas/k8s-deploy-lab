"""Generate candidate looks for an ORIGINAL AI news presenter (not based on any real person).
Free Pollinations image service (no key). Several seeds/models of one look so the most realistic can be picked.
Writes presenter/cand_*.png (bottom strip cropped, where a free service may stamp its name)."""
import subprocess
import time
import urllib.parse
from pathlib import Path

import requests

OUT = Path("presenter")
OUT.mkdir(exist_ok=True)
PROMPT = ("RAW candid DSLR photo, real photograph, head and shoulders of a fictional 28 year old Nepali woman, "
          "a TV news anchor, original person, not resembling any real or famous person. Long straight black hair, "
          "natural light makeup, calm confident slight smile, looking straight into the camera. Dark navy blazer over a "
          "high-neck cream blouse, small earrings, hands not visible. Real skin texture with pores and fine detail, "
          "natural imperfections, Canon EOS R5, 85mm f/1.8, soft studio lighting, blurred TV newsroom background with "
          "screens. Photorealistic, documentary photo. Not a painting, not illustration, not 3d render, not cartoon, "
          "not anime, not airbrushed, no text, no watermark.")
JOBS = [("flux-realism", 11), ("flux-realism", 22), ("flux", 33), ("flux-realism", 44), ("flux", 55), ("flux-realism", 66)]


def pollinations(prompt, seed, model):
    url = ("https://image.pollinations.ai/prompt/" + urllib.parse.quote(prompt)
           + f"?width=832&height=1216&nologo=true&enhance=false&seed={seed}&model={model}")
    for _ in range(4):
        try:
            r = requests.get(url, timeout=180)
            if r.status_code == 200 and r.headers.get("content-type", "").startswith("image"):
                return r.content
            print(f"[presenter] {model} {r.status_code} {r.text[:120]}")
        except Exception as e:
            print(f"[presenter] {model} {e}")
        time.sleep(30)
    return None


for i, (model, seed) in enumerate(JOBS, 1):
    img = pollinations(PROMPT, seed, model)
    if img:
        f = OUT / f"cand_{i}.png"
        f.write_bytes(img)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(f), "-vf", "crop=iw:ih*0.90:0:0",
                        str(f) + ".png"], check=False)
        Path(str(f) + ".png").replace(f)
        print(f"[presenter] look {i}: {model} seed {seed} {len(img)//1024} KB", flush=True)
    else:
        print(f"[presenter] look {i}: failed", flush=True)
    time.sleep(20)
