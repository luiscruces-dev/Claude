"""Verifica sincronía: detecta transitorios en el audio del MP4 y cambios
bruscos de imagen, y los compara con los eventos del timeline."""
import subprocess, sys
import numpy as np
from timeline import *

mp4 = sys.argv[1]
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp4, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                     capture_output=True).stdout
a = np.frombuffer(raw, np.float32)
hop = SR // FPS                                       # 1 fotograma de audio
e = np.array([np.sum(a[i * hop:(i + 1) * hop] ** 2) for i in range(len(a) // hop)])
le = np.log10(e + 1e-9)
flux = np.maximum(0, np.diff(le, prepend=le[0]))

v = subprocess.run(["ffmpeg", "-v", "error", "-i", mp4, "-vf", "scale=108:192,format=gray", "-f", "rawvideo", "-"],
                   capture_output=True).stdout
fr_ = np.frombuffer(v, np.uint8).reshape(-1, 192, 108).astype(np.float32)
vd = np.r_[0, np.mean(np.abs(np.diff(fr_, axis=0)), axis=(1, 2))]

events = sorted(set([s for s in HEART] + [s for s, _ in WORDS] + [DROP] + KICK + CLAP +
                    [s for s, _ in STABS] + [FINAL, LOCK]))
print(f"frames vídeo={len(fr_)}  duración audio={len(a)/SR:.3f}s")
print("paso  frame  audio_pico(±3)  imagen_pico(±3)")
bad = 0
for s in events:
    f = fr(s)
    lo, hi = max(0, f - 3), f + 4
    fa = lo + int(np.argmax(flux[lo:hi]))
    fv = lo + int(np.argmax(vd[lo:hi])) if f < len(vd) else -1
    da, dv = fa - f, fv - f
    flag = "" if abs(da) <= 1 and abs(dv) <= 1 else "  <-- revisar"
    bad += bool(flag)
    print(f"{s:4d} {f:5d}   {da:+d} (flux {flux[fa]:.2f})   {dv:+d} (Δ {vd[fv]:.1f}){flag}")
print("eventos fuera de ±1 fotograma:", bad)
