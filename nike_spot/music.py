"""Música compuesta y sintetizada desde cero con numpy/scipy. Sin samples:
cada sonido nace de osciladores, ruido y envolventes."""
import numpy as np
from scipy import signal
import wave

from timeline import *

N = int(DUR * SR)
rng = np.random.default_rng(7)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def place(buf, x, t, gain=1.0):
    i = int(round(t * SR))
    if i >= len(buf):
        return
    n = min(len(x), len(buf) - i)
    buf[i:i + n] += x[:n] * gain


def tt(d):
    return np.arange(int(d * SR)) / SR


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "highpass", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "lowpass", fs=SR, output="sos"), x)


def noise(d):
    return rng.standard_normal(int(d * SR))


# --- Instrumentos ------------------------------------------------------------

def kick(big=False):
    t = tt(0.9 if big else 0.5)
    f = 46 + 190 * np.exp(-t * 32) + 40 * np.exp(-t * 200)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * np.exp(-t * (3.2 if big else 6.5))
    click = hp(noise(0.004), 2500) * np.linspace(1, 0, int(0.004 * SR))
    x = body
    x[:len(click)] += click * 0.6
    return np.tanh(x * 1.8) * 0.95


def heart(soft=False):
    t = tt(0.35)
    f = 58 + 30 * np.exp(-t * 40)
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) * np.exp(-t * 14) * (1 - np.exp(-t * 400))
    thump = lp(noise(0.35), 180) * np.exp(-t * 30) * 0.8
    x = np.tanh((x + thump) * 2.2)
    return x * (0.55 if soft else 1.0)


def clap():
    t = tt(0.45)
    env = np.zeros_like(t)
    for k, o in enumerate([0, 0.009, 0.019, 0.027]):
        m = t >= o
        env[m] += np.exp(-(t[m] - o) * (110 if k < 3 else 13))
    x = bp(noise(0.45), 900, 4200) * env
    return x * 0.9


def snare(v=1.0):
    t = tt(0.25)
    tone = np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)
    nz = bp(noise(0.25), 1500, 9000) * np.exp(-t * 22)
    return (tone * 0.5 + nz) * v * 0.6


def hat(open_=False):
    d = 0.32 if open_ else 0.06
    t = tt(d)
    x = hp(noise(d), 7500, 4) * np.exp(-t * (9 if open_ else 70))
    return x * 0.35


def tick():
    """Golpe seco tipo cronómetro / mecanismo: FM metálico corto + ruido."""
    t = tt(0.12)
    mod = np.sin(2 * np.pi * 3170 * t) * 4 * np.exp(-t * 60)
    x = np.sin(2 * np.pi * 2100 * t + mod) * np.exp(-t * 55)
    x += hp(noise(0.12), 3000) * np.exp(-t * 120) * 0.5
    return x * 0.45


def saw(f, t, phase=0.0):
    # Diente de sierra limitado en banda (aditivo, armónicos < 16 kHz).
    x = np.zeros_like(t)
    kmax = int(16000 / max(f, 1))
    for k in range(1, max(kmax, 1) + 1):
        x += ((-1) ** (k + 1)) * np.sin(2 * np.pi * k * f * t + k * phase) / k
    return x * (2 / np.pi)


def supersaw(midis, d, voices=5, detune=0.14, cutoff=(6000, 900), decay=4.0):
    t = tt(d)
    x = np.zeros_like(t)
    for m in midis:
        for v in range(voices):
            cents = (v - (voices - 1) / 2) / ((voices - 1) / 2) * detune * 100
            f = mtof(m) * 2 ** (cents / 1200)
            x += saw(f, t, phase=rng.uniform(0, 2 * np.pi))
    x /= (len(midis) * voices) ** 0.5
    # filtro paso bajo con envolvente (barrido por bloques)
    out = np.zeros_like(x)
    blk = 512
    zi = None
    for i in range(0, len(x), blk):
        tc = i / SR
        fc = cutoff[1] + (cutoff[0] - cutoff[1]) * np.exp(-tc * decay)
        sos = signal.butter(2, min(fc, 18000), "lowpass", fs=SR, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        out[i:i + blk], zi = signal.sosfilt(sos, x[i:i + blk], zi=zi)
    return out


def bass808(m, d):
    t = tt(d)
    f = mtof(m) * (1 + 0.9 * np.exp(-t * 45))
    ph = 2 * np.pi * np.cumsum(f) / SR
    x = np.sin(ph) + 0.25 * np.sin(2 * ph)
    env = np.minimum(1, t / 0.004) * np.exp(-t * 1.2)
    rel = np.clip((d - t) / 0.03, 0, 1)
    return np.tanh(x * env * rel * 2.4) * 0.7


def pad(midis, d, cutoff_start=300, cutoff_end=2400):
    t = tt(d)
    x = np.zeros_like(t)
    for m in midis:
        for det in (-0.08, 0.0, 0.07):
            x += saw(mtof(m) * 2 ** (det / 12), t, rng.uniform(0, 6.28))
    x /= len(midis) * 3
    out = np.zeros_like(x); blk = 1024; zi = None
    for i in range(0, len(x), blk):
        a = i / len(x)
        fc = cutoff_start * (cutoff_end / cutoff_start) ** (a ** 2)
        sos = signal.butter(2, fc, "lowpass", fs=SR, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        out[i:i + blk], zi = signal.sosfilt(sos, x[i:i + blk], zi=zi)
    fade = np.minimum(1, t / 0.6)
    return out * fade


def riser(d):
    t = tt(d)
    x = noise(d)
    out = np.zeros_like(x); blk = 512; zi = None
    for i in range(0, len(x), blk):
        a = i / len(x)
        fc = 400 * (9000 / 400) ** a
        sos = signal.butter(2, [fc * 0.7, min(fc * 1.4, 20000)], "bandpass", fs=SR, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        out[i:i + blk], zi = signal.sosfilt(sos, x[i:i + blk], zi=zi)
    f = 110 * 2 ** (t / d * 3)
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.25
    return (out + tone) * (t / d) ** 2


def whoosh(d, rev=False):
    t = tt(d)
    x = noise(d)
    out = np.zeros_like(x); blk = 256; zi = None
    for i in range(0, len(x), blk):
        a = i / len(x)
        fc = 300 + 5000 * np.sin(np.pi * a) ** 2
        sos = signal.butter(2, [fc * 0.6, fc * 1.6], "bandpass", fs=SR, output="sos")
        if zi is None:
            zi = np.zeros((sos.shape[0], 2))
        out[i:i + blk], zi = signal.sosfilt(sos, x[i:i + blk], zi=zi)
    env = (t / d) ** 3 if rev else np.sin(np.pi * t / d) ** 2
    return out * env


def boom(d=3.0):
    t = tt(d)
    f = 34 + 50 * np.exp(-t * 8)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 1.6)
    return np.tanh(x * 1.6)


def crash(d=2.5):
    t = tt(d)
    return hp(noise(d), 4000) * np.exp(-t * 2.2) * 0.35


def reverb_ir(d=2.4, decay=3.0):
    t = tt(d)
    l = lp(noise(d), 7000) * np.exp(-t * decay)
    r = lp(noise(d), 7000) * np.exp(-t * decay)
    pre = int(0.012 * SR)
    l = np.concatenate([np.zeros(pre), l]); r = np.concatenate([np.zeros(pre), r])
    return l / np.sqrt(np.sum(l ** 2)), r / np.sqrt(np.sum(r ** 2))


# --- Composición -------------------------------------------------------------

def compose():
    drums = np.zeros(N); bass = np.zeros(N); music = np.zeros(N)
    fx = np.zeros(N); send = np.zeros(N)
    kicks_t = []

    # A/B: latido (se acelera al doble en B: la ansiedad sube)
    for s in HEART:
        soft = s == 108
        place(drums, heart(), st(s), 0.95 if not soft else 0.8)
        place(drums, heart(soft=True), st(s + 2), 0.7)
        send_amt = 0.25
        place(send, heart(), st(s), send_amt)

    # Dron oscuro que se abre durante la duda
    dr = pad([41, 48, 56, 60], st(31) - 0.0, 160, 1800)
    place(music, dr, 0.0, 0.55)

    # Palabras: cada excusa es un "tick" + golpe grave
    for s, _w in WORDS:
        place(fx, tick(), st(s), 1.0)
        place(send, tick(), st(s), 0.6)
    for s in range(16, 31, 2):  # pulso de corcheas sutil en B
        place(drums, hat(), st(s), 0.5)
    for i, s in enumerate(ROLL):
        place(drums, snare(0.25 + 0.75 * i / len(ROLL)), st(s), 0.8)
        place(drums, snare(0.2 + 0.6 * i / len(ROLL)), st(s + 0.5), 0.6)
    place(fx, riser(st(31) - st(20)), st(20), 0.55)
    # (paso 31: silencio absoluto antes del drop)

    # DROP + groove
    for s in KICK:
        big = s in (DROP,)
        place(drums, kick(big), st(s), 1.0)
        kicks_t.append(st(s))
    for s in CLAP:
        place(drums, clap(), st(s), 0.85)
        place(send, clap(), st(s), 0.5)
    for b in GROOVE_BARS:
        for k in range(0, 16, 2):
            place(drums, hat(), st(b + k), 0.55 if k % 4 else 0.35)
        place(drums, hat(), st(b + 7), 0.3)
        place(drums, hat(), st(b + 15), 0.3)
        place(drums, hat(True), st(b + 14), 0.5)
    for k in range(0, 16, 1):
        place(drums, hat(), st(BUILD + k), 0.25 + 0.35 * k / 16)
    for i, s in enumerate(BUILD_ROLL):
        for sub in (0, 0.5):
            place(drums, snare(0.4 + 0.6 * i / len(BUILD_ROLL)), st(s + sub), 0.75)
    place(fx, crash(), st(DROP), 1.0)
    place(fx, riser(st(94) - st(80)), st(80), 0.5)

    # 808
    keys = sorted(BASS)
    for i, s in enumerate(keys):
        end = keys[i + 1] if i + 1 < len(keys) else GAP_PRE_TAG
        place(bass, bass808(BASS[s], st(end) - st(s)), st(s), 1.0)

    # Acordes del groove: golpes sincopados en los bombos (mismo golpe = mismo corte)
    for b, ch in CHORDS.items():
        hits = [b, b + 6, b + 10] if b != BUILD else [b, b + 4, b + 8, b + 12]
        for h in hits:
            nxt = min([x for x in hits + [b + 16] if x > h])
            d = st(nxt) - st(h)
            x = supersaw(ch, d, cutoff=(5200, 700), decay=9)
            x *= np.clip((d - tt(d)) / 0.02, 0, 1)
            place(music, x, st(h), 0.55)
            place(send, x, st(h), 0.25)

    # Tagline: tres stabs en silencio
    for s, _w in STABS:
        place(drums, kick(True), st(s), 1.0)
        kicks_t.append(st(s))
        x = supersaw(STAB_CHORDS[s], 1.6, voices=7, cutoff=(9000, 600), decay=5)
        x *= np.exp(-tt(1.6) * 3.2)
        place(music, x, st(s), 0.9)
        place(send, x, st(s), 0.35)
        place(fx, crash(1.5), st(s), 0.5)
        place(bass, bass808(STAB_CHORDS[s][0] - 24, 1.5), st(s), 0.9)

    # Whoosh hacia el swoosh final
    place(fx, whoosh(0.55, rev=True), st(FINAL) - 0.55, 0.9)
    # Impacto final
    place(drums, kick(True), st(FINAL), 1.0); kicks_t.append(st(FINAL))
    place(bass, boom(3.5), st(FINAL), 0.9)
    place(fx, crash(3.0), st(FINAL), 0.8)
    fin_d = DUR - st(FINAL)
    x = supersaw(FINAL_CHORD, fin_d, voices=7, cutoff=(8000, 500), decay=1.2)
    x *= np.exp(-tt(fin_d) * 0.9) * np.clip((fin_d - tt(fin_d)) / 0.4, 0, 1)
    place(music, x, st(FINAL), 0.85)
    place(send, x, st(FINAL), 0.7)
    # Lock del tagline: pluck brillante
    t = tt(1.4)
    pl = sum(np.sin(2 * np.pi * mtof(m) * t) for m in (77, 84, 89)) * np.exp(-t * 4) / 3
    place(fx, pl, st(LOCK), 0.35)
    place(send, pl, st(LOCK), 0.8)

    # Sidechain: la música respira con cada bombo
    sc = np.ones(N)
    tn = np.arange(N) / SR
    for k in kicks_t:
        m = tn >= k
        sc[m] *= 1 - 0.55 * np.exp(-(tn[m] - k) / 0.11)
    music *= sc

    return drums, bass, music, fx, send


def master(drums, bass, music, fx, send):
    irl, irr = reverb_ir()
    wl = signal.fftconvolve(send, irl)[:N]
    wr = signal.fftconvolve(send, irr)[:N]
    # leve ensanche estéreo de la música (Haas en la parte aguda)
    d = int(0.011 * SR)
    mus_hi = hp(music, 600)
    musL = music
    musR = music - mus_hi + np.concatenate([np.zeros(d), mus_hi[:-d]])
    L = drums + bass + musL + fx + wl * 0.35
    R = drums + bass + musR + fx + wr * 0.35
    st_ = np.stack([L, R])
    st_ = hp(st_.T, 28).T
    # silencios de respiración antes de cada drop (incluida la reverb)
    tn = np.arange(N) / SR
    g = np.ones(N)
    for a, b in ((st(GAP_PRE_DROP), st(DROP)), (st(GAP_PRE_TAG), st(96))):
        g *= np.clip(np.maximum((a - tn) / 0.004, (tn - b + 0.002) / 0.002), 0, 1)
    st_ *= g
    st_ /= np.max(np.abs(st_))
    st_ = np.tanh(st_ * 1.6) / np.tanh(1.6)                     # saturación suave / limitador
    st_ /= np.max(np.abs(st_)) / 0.89      # -1 dBFS
    # micro-fades
    f = int(0.002 * SR)
    st_[:, :f] *= np.linspace(0, 1, f)
    st_[:, -int(0.05 * SR):] *= np.linspace(1, 0, int(0.05 * SR))
    return st_


def write_wav(path, x):
    y = (np.clip(x, -1, 1) * 32767).astype(np.int16).T.copy()
    with wave.open(path, "wb") as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes(y.tobytes())


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "music.wav"
    write_wav(out, master(*compose()))
    print("wrote", out)
