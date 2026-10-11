"""Fuente única de verdad: tempo, rejilla y eventos. Audio y vídeo leen de aquí,
así cada golpe cae exactamente en el mismo fotograma que su transitorio."""
FPS = 60
SR = 48000
BPM = 150
DUR = 15.0
NFRAMES = int(DUR * FPS)          # 900
STEP = 60.0 / BPM / 4             # semicorchea = 0.1 s = 6 fotogramas exactos
STEP_FR = 6


def st(step):
    """Paso de semicorchea -> segundos."""
    return step * STEP


def fr(step):
    return step * STEP_FR


# --- Eventos (en pasos de semicorchea) -------------------------------------
HEART = [0, 8, 16, 20, 24, 28, 108]            # "lub" (el "dub" va +2 pasos)
WORDS = [(16, "TOO EARLY"), (20, "TOO COLD"), (24, "TOO TIRED"), (28, "TOO LATE")]
ROLL = list(range(24, 31))                      # redoble de tensión
GAP_PRE_DROP = 31                               # silencio de una semicorchea
DROP = 32

GROOVE_BARS = [32, 48, 64]                      # compases de groove
KICK, CLAP = [], []
for b in GROOVE_BARS:
    KICK += [b + 0, b + 6, b + 10]
    CLAP += [b + 4, b + 12]
BUILD = 80                                       # compás de subida
KICK += [80, 84, 88, 92]
CLAP += [84, 92]
BUILD_ROLL = list(range(88, 94))
GAP_PRE_TAG = 94                                 # dos semicorcheas de silencio
STABS = [(96, "JUST"), (100, "DO"), (104, "IT.")]
FINAL = 112                                      # swoosh / impacto final
LOCK = 120                                       # tagline se asienta
END_STEP = 150

# Acordes (MIDI) por sección
CHORDS = {
    32: [53, 56, 60, 63],   # Fm7
    48: [53, 56, 60, 65],   # Fm
    64: [49, 53, 56, 61],   # Db
    80: [51, 55, 58, 63],   # Eb
}
STAB_CHORDS = {96: [49, 56, 61, 65, 68], 100: [51, 58, 63, 67, 70], 104: [53, 60, 65, 68, 72]}
FINAL_CHORD = [41, 53, 57, 60, 65, 67, 69, 72]    # F mayor add9 (picarda)
BASS = {32: 29, 38: 29, 42: 32, 48: 29, 54: 29, 58: 27, 64: 25, 70: 25, 74: 25,
        80: 27, 84: 27, 88: 27, 92: 27}            # notas 808
