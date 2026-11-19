# Original score + sound design for the HogentX film. 96 BPM, 12 bars = 30 s. Everything synthesised here.
import numpy as np, scipy.signal as sg, wave, sys

SR = 48000; DUR = 30.0; N = int(SR * DUR)
BPM = 96; BEAT = 60 / BPM; BAR = 4 * BEAT; S16 = BEAT / 4
import os
CUT = os.environ.get('CUT', 'main')
rs = np.random.RandomState(7)
hz = lambda m: 440.0 * 2 ** ((m - 69) / 12)
tb = lambda bar, beat=1.0, s=0: (bar - 1) * BAR + (beat - 1) * BEAT + s * S16

dry = np.zeros((N, 2)); rev = np.zeros((N, 2)); dly = np.zeros((N, 2))

def put(sig, t0, gain=1.0, pan=0.0, r=0.0, d=0.0, bus=None):
    """mix a mono/stereo signal in at time t0 (s)."""
    i = int(round(t0 * SR))
    if sig.ndim == 1:
        a = (pan + 1) * np.pi / 4
        sig = np.stack([sig * np.cos(a), sig * np.sin(a)], 1) * 1.414
    if i < 0: sig = sig[-i:]; i = 0
    n = min(len(sig), N - i)
    if n <= 0: return
    s = sig[:n] * gain
    (dry if bus is None else bus)[i:i + n] += s
    if r: rev[i:i + n] += s * r
    if d: dly[i:i + n] += s * d

def env_ar(n, a=0.005, rel=0.05):
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, int(rel * SR))
    e[:na] = np.linspace(0, 1, na) ** 1.5
    e[-nr:] *= np.linspace(1, 0, nr) ** 1.5
    return e

def biquad(kind, fc, q=0.707):
    w = 2 * np.pi * min(fc, SR * 0.45) / SR; al = np.sin(w) / (2 * q); c = np.cos(w)
    if kind == 'lp': b = [(1 - c) / 2, 1 - c, (1 - c) / 2]
    elif kind == 'hp': b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]
    else: b = [al, 0, -al]
    a = [1 + al, -2 * c, 1 - al]
    return np.array(b) / a[0], np.array(a) / a[0]

def tvf(x, fc, kind='lp', q=0.707, block=96, passes=1):
    """time-varying biquad: fc is an array (len x) or scalar."""
    if np.isscalar(fc): fc = np.full(len(x), float(fc))
    y = x.copy()
    for _ in range(passes):
        zi = np.zeros(2); o = np.empty_like(y)
        for i in range(0, len(y), block):
            b, a = biquad(kind, fc[i], q)
            o[i:i + block], zi = sg.lfilter(b, a, y[i:i + block], zi=zi)
        y = o
    return y

def filt(x, fc, kind='lp', order=2):
    sos = sg.butter(order, fc / (SR / 2), 'low' if kind == 'lp' else 'high' if kind == 'hp' else 'band', output='sos')
    return sg.sosfilt(sos, x, axis=0)

# ---------------- voices ----------------
def pluck(f, dur=1.0, d0=3.5, d1=1.1, tilt=1.0, K=26):
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n)
    K = max(1, min(K, int(0.42 * SR / f)))
    for k in range(1, K + 1):
        out += (1.0 / k ** tilt) * np.sin(2 * np.pi * f * k * t + rs.rand() * 0.6) * np.exp(-t * (d0 + d1 * k))
    return out * (1 - np.exp(-t / 0.0015)) * env_ar(n, 0.001, 0.03)

def bell(f, dur=2.0, ratio=3.01, idx=2.2, dec=2.6):
    n = int(dur * SR); t = np.arange(n) / SR
    m = np.sin(2 * np.pi * f * ratio * t) * idx * np.exp(-t * dec * 2.2)
    y = np.sin(2 * np.pi * f * t + m) * np.exp(-t * dec)
    y += 0.3 * np.sin(2 * np.pi * f * 2 * t) * np.exp(-t * dec * 1.6)
    return y * (1 - np.exp(-t / 0.002)) * env_ar(n, 0.001, 0.05)

def keys(f, dur=2.5):
    """soft felt-piano-ish tone."""
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros(n)
    for k in range(1, min(14, int(0.4 * SR / f)) + 1):
        fk = f * k * np.sqrt(1 + 0.0004 * k * k)
        out += (1.0 / k ** 1.6) * np.sin(2 * np.pi * fk * t + rs.rand()) * np.exp(-t * (1.3 + 0.55 * k))
    return out * (1 - np.exp(-t / 0.004)) * env_ar(n, 0.001, 0.08)

def supersaw(notes, dur, cut, a=0.3, rel=0.7, det=11, voices=5, q=0.8):
    """stereo detuned-saw pad. cut: scalar or array of cutoff Hz over the note length."""
    n = int(dur * SR); t = np.arange(n) / SR; L = np.zeros(n); R = np.zeros(n)
    for m in notes:
        for v in range(voices):
            c = (v - (voices - 1) / 2) / max(1, (voices - 1) / 2)
            f = hz(m) * 2 ** (c * det / 1200)
            s = sg.sawtooth(2 * np.pi * f * t + rs.rand() * 6.28)
            p = c * 0.8; ang = (p + 1) * np.pi / 4
            L += s * np.cos(ang); R += s * np.sin(ang)
    if np.isscalar(cut): cut = np.full(n, float(cut))
    L = tvf(L, cut, 'lp', q, passes=2); R = tvf(R, cut, 'lp', q, passes=2)
    e = env_ar(n, a, rel)
    return np.stack([L, R], 1) * e[:, None] / (len(notes) * voices) * 3.0

def bass(m, dur, cut=420):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    s = 0.9 * np.sin(2 * np.pi * f * t) + 0.45 * sg.sawtooth(2 * np.pi * f * t) + 0.25 * sg.square(2 * np.pi * f * 2 * t, 0.5) * 0.4
    fc = cut * (0.6 + 1.6 * np.exp(-t / 0.09))
    s = tvf(s, fc, 'lp', 0.9, passes=2)
    return np.tanh(s * 1.3) * env_ar(n, 0.004, 0.05)

def kick(big=1.0):
    n = int(0.6 * SR); t = np.arange(n) / SR
    f = 44 + 120 * np.exp(-t / 0.032) ; ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.exp(-t / (0.17 * big))
    y += 0.35 * filt(rs.randn(n), 3000, 'hp') * np.exp(-t / 0.004)
    return np.tanh(y * 1.6) * env_ar(n, 0.0005, 0.05)

def clap():
    n = int(0.35 * SR); t = np.arange(n) / SR
    x = sg.sosfilt(sg.butter(2, [900 / (SR / 2), 4200 / (SR / 2)], 'band', output='sos'), rs.randn(n))
    e = sum(np.exp(-np.clip(t - d, 0, None) / 0.007) * (t >= d) for d in (0, 0.011, 0.023)) * 0.6 + np.exp(-np.clip(t - 0.03, 0, None) / 0.07) * (t >= 0.03)
    return x * e

def hat(dec=0.02):
    n = int(max(0.05, dec * 6) * SR); t = np.arange(n) / SR
    return filt(rs.randn(n), 7500, 'hp', 4) * np.exp(-t / dec)

def tick(f=2400, dec=0.012):
    n = int(0.08 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * f * t) * np.exp(-t / dec) + 0.4 * filt(rs.randn(n), 5000, 'hp') * np.exp(-t / 0.002)) * env_ar(n, 0.0003, 0.01)

def blip(f0, f1, dur=0.12):
    n = int(dur * SR); t = np.arange(n) / SR
    f = f0 * (f1 / f0) ** (t / dur); ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t / (dur * 0.45)) * env_ar(n, 0.002, 0.02)

def whoosh(dur_in=0.38, dur_out=0.55, f0=500, f1=6500, f2=900, q=1.3):
    """stereo noise sweep, peak at dur_in."""
    n = int((dur_in + dur_out) * SR); t = np.arange(n) / SR; ni = int(dur_in * SR)
    fc = np.empty(n)
    fc[:ni] = f0 * (f1 / f0) ** (np.linspace(0, 1, ni) ** 1.6)
    fc[ni:] = f1 * (f2 / f1) ** (np.linspace(0, 1, n - ni) ** 0.6)
    x = tvf(rs.randn(n), fc, 'bp', q)
    e = np.empty(n); e[:ni] = np.linspace(0, 1, ni) ** 2.6; e[ni:] = np.linspace(1, 0, n - ni) ** 2.0
    pan = np.linspace(-0.75, 0.75, n); a = (pan + 1) * np.pi / 4
    x = x * e
    return np.stack([x * np.cos(a), x * np.sin(a)], 1) * 1.4

def riser(dur, f0=300, f1=9000):
    n = int(dur * SR); t = np.arange(n) / SR; u = t / dur
    x = tvf(rs.randn(n), f0 * (f1 / f0) ** (u ** 1.4), 'bp', 2.2)
    tone = np.sin(2 * np.pi * np.cumsum(180 * (4.0 ** (u ** 1.5))) / SR) * 0.25
    return (x * 1.2 + tone) * u ** 2.2 * env_ar(n, 0.01, 0.012)

def impact(size=1.0):
    n = int(3.2 * SR); t = np.arange(n) / SR
    sub = np.sin(2 * np.pi * np.cumsum(36 + 80 * np.exp(-t / 0.07)) / SR) * np.exp(-t / (0.75 * size))
    thump = np.tanh(np.sin(2 * np.pi * np.cumsum(50 + 160 * np.exp(-t / 0.02)) / SR) * 2.2) * np.exp(-t / 0.12)
    crash = filt(rs.randn(n), 2500, 'hp') * (np.exp(-t / 0.05) * 0.9 + np.exp(-t / (0.9 * size)) * 0.35)
    mid = sg.sosfilt(sg.butter(2, [180 / (SR / 2), 900 / (SR / 2)], 'band', output='sos'), rs.randn(n)) * np.exp(-t / 0.18)
    return np.tanh((sub * 1.0 + thump * 0.8) * 1.2), crash + mid * 0.6

def revswell(dur=1.3):
    n = int(dur * SR); t = np.arange(n) / SR
    x = filt(rs.randn(n), 3200, 'hp') * (t / dur) ** 3.2
    return x * env_ar(n, 0.01, 0.01)

# ---------------- harmony ----------------
CH = {  # bar -> (bass midi, pad notes)
    1: (29, [41, 48, 56, 60, 63]), 2: (29, [41, 48, 56, 60, 63]),
    3: (37, [49, 56, 60, 65]), 4: (39, [51, 56, 58, 63]),
    5: (32, [56, 58, 60, 63]), 6: (31, [55, 58, 63, 65]), 7: (29, [53, 56, 60, 63]), 8: (37, [53, 56, 60, 65]),
    9: (34, [53, 56, 58, 61]), 10: (39, [51, 56, 58, 63]),
    11: (32, [56, 60, 63, 67, 70]), 12: (32, [56, 60, 63, 67, 70]),
}
pad_bus = np.zeros((N, 2)); bass_bus = np.zeros((N, 2)); arp_bus = np.zeros((N, 2))

def lin(n, a, b, p=1.0): return a + (b - a) * np.linspace(0, 1, n) ** p
def mixs(*sigs):
    """sum signals of different lengths."""
    n = max(len(x) for x in sigs); o = np.zeros(n)
    for x in sigs: o[:len(x)] += x
    return o

# pads -------------------------------------------------------------
def pad_at(bar, bars, cut, gain, a=0.35, rel=0.9, notes=None, det=11):
    dur = bars * BAR + rel * 0.7
    n = int(dur * SR)
    c = cut(n) if callable(cut) else cut
    s = supersaw(notes or CH[bar][1], dur, c, a, rel, det)
    put(s, tb(bar) - 0.03, gain, bus=pad_bus)

pad_at(1, 2, lambda n: lin(n, 380, 1500, 1.6), 0.95, a=1.0, rel=0.5)
pad_at(3, 1, lambda n: lin(n, 3000, 1500, 0.5), 0.8, a=0.02)
pad_at(4, 1, lambda n: lin(n, 1300, 3800, 2.0), 0.75, a=0.2, notes=[51, 56, 58, 63])
put(supersaw([51, 55, 58, 63, 67], BAR / 2 + 0.3, lin(int((BAR / 2 + 0.3) * SR), 2000, 5200, 1.5), 0.15, 0.3), tb(4, 3), 0.5, bus=pad_bus)
for b in (5, 6, 7, 8):
    pad_at(b, 1, lambda n: lin(n, 3400, 2200, 0.6), 0.52, a=0.03, rel=0.5)
pad_at(9, 1, lambda n: lin(n, 1000, 2000, 1.5), 0.85, a=0.25, rel=0.5)
pad_at(10, 1, lambda n: lin(n, 2600, 5200, 1.6), 0.46, a=0.02, rel=0.25)
put(supersaw([51, 55, 58, 63, 67], BAR / 2 + 0.2, lin(int((BAR / 2 + 0.2) * SR), 3000, 6500, 1.5), 0.1, 0.2), tb(10, 3), 0.3, bus=pad_bus)
pad_at(11, 2, lambda n: lin(n, 7000, 1700, 0.35), 1.0, a=0.01, rel=1.8, det=13)
# high airy layer on the logo
put(supersaw([68, 75, 79, 82], 2 * BAR, lin(int(2 * BAR * SR), 5000, 2400, 0.5), 0.5, 2.0, det=9), tb(11), 0.22, bus=pad_bus)

# sub / bass ---------------------------------------------------------
def sub(m, dur, a=0.3, rel=0.5):
    n = int(dur * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * hz(m) * t) + 0.15 * np.sin(2 * np.pi * hz(m) * 2 * t)) * env_ar(n, a, rel)
put(sub(29, 2 * BAR + 0.2, 1.5, 0.4), 0, 0.12, bus=bass_bus)
put(sub(37, BAR, 0.02, 0.3), tb(3), 0.17, bus=bass_bus)
put(sub(39, BAR, 0.05, 0.2), tb(4), 0.17, bus=bass_bus)
BASS_PAT = [(0, 3, 0), (6, 1.6, 0), (8, 2.6, 0), (11, 1.6, 12), (14, 1.6, 0)]
for b in (5, 6, 7, 8, 10):
    for (s, ln, tr) in BASS_PAT:
        put(bass(CH[b][0] + 12 + tr, ln * S16), tb(b, 1, s), 0.36, bus=bass_bus)
put(sub(34, BAR, 0.05, 0.3), tb(9), 0.17, bus=bass_bus)
put(sub(32, 2 * BAR, 0.01, 2.2), tb(11), 0.17, bus=bass_bus)

# arp ----------------------------------------------------------------
ARP_IDX = [0, 2, 1, 3, 2, 4, 3, 5, 4, 3, 2, 4, 3, 1, 2, 3]
def arp_bar(b, vol, steps=range(16), bright=1.0, d0=5.0):
    tones = sorted(set([m + 12 for m in CH[b][1]] + [m + 24 for m in CH[b][1][:3]]))
    for s in steps:
        m = tones[ARP_IDX[s] % len(tones)]
        v = vol * (1.0 if s % 4 == 0 else 0.62 if s % 2 == 0 else 0.45)
        put(pluck(hz(m), 0.7, d0, 0.9 / bright), tb(b, 1, s), v, pan=0.45 * np.sin(s * 1.7), r=0.25, d=0.35, bus=arp_bus)
for i, s in enumerate(range(16)):   # bar 4: fades in
    arp_bar(4, 0.03 + 0.14 * (i / 15) ** 1.5, [s], bright=0.7 + 0.5 * i / 15)
for b in (5, 6, 7, 8): arp_bar(b, 0.2)
arp_bar(9, 0.17, range(0, 16, 2), bright=0.8)
arp_bar(10, 0.2)

# lead (bell) -----------------------------------------------------------
LEAD = [(5, 1, 75, 1.5), (5, 2.5, 72, 0.5), (5, 3, 70, 1), (5, 4, 72, 1),
        (6, 1, 70, 2), (6, 3, 67, 1), (6, 4, 70, 1),
        (7, 1, 72, 1.5), (7, 2.5, 68, 0.5), (7, 3, 65, 1), (7, 4, 68, 1),
        (8, 1, 77, 2), (8, 3, 75, 1), (8, 4, 73, 1),
        (10, 1, 70, 1), (10, 2, 72, 1), (10, 3, 75, 1), (10, 4, 79, 1)]
for (b, bt, m, ln) in LEAD:
    put(mixs(bell(hz(m), 1.6, 2.0, 1.4, 3.0) * 0.8, keys(hz(m), 1.8) * 0.9), tb(b, bt), 0.27, pan=0.1, r=0.4, d=0.3)

# drums --------------------------------------------------------------------
kicks = []
def K(t, g=0.85, big=1.0): put(kick(big), t, g); kicks.append((t, g))
for b in (5, 6, 7, 8, 10):
    for s in (0, 6, 8): K(tb(b, 1, s))
    if b in (6, 8): K(tb(b, 1, 15), 0.6)
    for s in (4, 12): put(clap(), tb(b, 1, s), 0.5, r=0.22)
    for s in range(16):
        g = 0.14 if s % 2 == 0 else 0.07
        put(hat(0.016 if s != 14 else 0.07), tb(b, 1, s), g * (1.3 if s % 4 == 2 else 1), pan=0.25)
K(tb(3), 0.75); K(tb(3, 3), 0.5); K(tb(4), 0.6); K(tb(4, 3), 0.55)
K(tb(9), 0.7); K(tb(9, 3), 0.4)
# builds into bar 5 and bar 11
def build(t_end, beats=2.0, vol=0.3):
    t = t_end - beats * BEAT; i = 0
    while t < t_end - 0.01:
        u = 1 - (t_end - t) / (beats * BEAT)
        put(mixs(clap() * 0.7, hat(0.02) * 0.6), t, vol * (0.25 + 0.75 * u ** 1.5), r=0.15)
        t += S16 if u < 0.5 else S16 / 2; i += 1
build(tb(5), 2, 0.26); build(tb(11), 2, 0.28)
# soft pulse in the intro (a clock, a heartbeat)
for b in (1, 2):
    for bt in range(4):
        if b == 1 and bt == 0: continue
        put(tick(900, 0.02), tb(b, bt + 1), 0.05 + 0.02 * (b - 1), pan=-0.3, r=0.5)
        put(tick(1300, 0.012), tb(b, bt + 1, 2), 0.03, pan=0.3, r=0.5)

# ---------------- sound design, on the picture ----------------
if CUT == 'main':
    # intro: descending "drops" (rooms going dark), F minor pentatonic
    DROPS = [84, 80, 77, 75, 72, 80, 77, 75, 72, 70, 75, 72, 70, 68, 65, 63]
    t0 = tb(1, 2, 2)
    for i, m in enumerate(DROPS):
        t = t0 + i * BEAT / 2
        if t > 4.2: break
        put(bell(hz(m), 1.4, 3.5, 1.6, 4.2), t, 0.17 + 0.07 * (i % 2 == 0), pan=0.5 * np.sin(i * 2.1), r=0.65, d=0.4)
    # leak labels
    for i in range(4): put(blip(520 - 40 * i, 300 - 20 * i, 0.14), 1.5625 + i * 0.625, 0.16, pan=-0.3 + 0.2 * i, r=0.4)
    # into the strike
    put(riser(1.5, 250, 7000), 5.0 - 1.5, 0.3, r=0.3)
    put(revswell(1.2), 5.0 - 1.2, 0.2, r=0.4)
    put(whoosh(0.2, 0.5, 900, 9000, 1500), 5.0 - 0.2, 0.55, r=0.3)
    lo, hi = impact(1.0); put(lo, 5.0, 0.55); put(hi, 5.0, 0.62, r=0.7)
    put(blip(220, 880, 0.9), 5.05, 0.12, r=0.6)                    # towers charging
    for t in (6.25, 7.5, 8.75): put(bell(hz(80), 1.5, 2.0, 1.0, 3.5), t, 0.17, pan=0.3, r=0.7, d=0.5)   # pulses on the line
    # the city relights
    for i, m in enumerate([61, 65, 68, 72, 73, 77, 80, 84, 85, 89]): put(pluck(hz(m), 0.9, 4.5, 0.8), 5.625 + i * 0.3125, 0.085 + 0.004 * i, pan=0.5 * np.sin(i * 1.3), r=0.6, d=0.35)
    # camera whips
    for i, t in enumerate([10.0, 12.5, 15.0, 17.5, 20.0, 25.0]):
        big = t in (10.0, 20.0, 25.0)
        put(whoosh(0.36, 0.6, 400, 7500 if big else 5500, 800), t - 0.36, 0.62 if big else 0.42, r=0.25)
    put(riser(1.25, 300, 8000), 10.0 - 1.25, 0.26, r=0.3)
    lo, hi = impact(0.6); put(lo, 10.0, 0.42); put(hi, 10.0, 0.3, r=0.5)
    # 01 revenue: pill, click, bars climbing to the line
    put(blip(700, 1100, 0.09), 10.625, 0.16, r=0.3)
    put(tick(2100, 0.01), 11.25, 0.4, r=0.2); put(blip(900, 1500, 0.1), 11.27, 0.18, r=0.3)
    for i, m in enumerate([68, 70, 72, 75, 77, 80, 84]): put(pluck(hz(m), 0.5, 6, 1.0), 11.37 + i * 0.05, 0.16, pan=-0.4 + i * 0.13, r=0.4, d=0.3)
    # 02 guest relations: card, typing, click, smile
    put(blip(600, 900, 0.09), 12.7, 0.14, r=0.3); put(blip(700, 1000, 0.09), 13.125, 0.14, r=0.3)
    for i in range(9): put(tick(3000 + 300 * (i % 3), 0.005), 13.36 + i * 0.047, 0.1, pan=0.3, r=0.1)
    put(tick(2100, 0.01), 13.75, 0.4, r=0.2)
    put(blip(784, 1175, 0.1), 13.93, 0.2, r=0.4); put(blip(1175, 1568, 0.14), 14.03, 0.2, r=0.4)
    # 03 quality: three checks, the ring closes
    for i, m in enumerate([84, 87, 92]): put(tick(hz(m), 0.03), 15.625 + i * 0.3125, 0.26, pan=0.2, r=0.35)
    put(bell(hz(92), 1.6, 2.0, 1.2, 3.0), 16.5625, 0.2, pan=0.3, r=0.6, d=0.3)
    # 04 morning brief: sunrise shimmer
    n = int(1.6 * SR); sh = tvf(rs.randn(n), lin(n, 2500, 9000, 1.3), 'bp', 3.0) * np.sin(np.pi * np.linspace(0, 1, n)) ** 1.5
    put(sh, 17.7, 0.16, pan=0.4, r=0.6)
    for i in range(4): put(tick(1800 + 250 * i, 0.012), 17.92 + i * 0.11, 0.14, pan=0.2, r=0.3)
    for i in range(4): put(tick(hz(84 + [0, 3, 5, 8][i]), 0.025), 18.45 + i * 0.13, 0.16, pan=0.3, r=0.4)
    # proof: the counter runs down, then the hit
    put(riser(0.9, 500, 6000), 20.0 - 0.9, 0.2, r=0.3)
    lo, hi = impact(0.5); put(lo, 20.0, 0.3); put(hi, 20.0, 0.26, r=0.5)
    tc = 21.25
    while tc < 22.42:
        u = (tc - 21.25) / 1.17
        put(tick(2600 - 1500 * u, 0.006), tc, 0.12 + 0.08 * np.sin(np.pi * u), pan=-0.2 + 0.4 * u, r=0.15)
        tc += 0.028 + 0.05 * abs(u - 0.5) ** 1.5
    put(revswell(0.8), 22.5 - 0.8, 0.16, r=0.4)
    lo, hi = impact(0.7); put(lo, 22.5, 0.55); put(hi, 22.5, 0.4, r=0.6)
    put(bell(hz(75), 2.0, 2.0, 1.4, 2.4) + bell(hz(82), 2.0, 2.0, 1.2, 2.4), 22.5, 0.14, r=0.6, d=0.3)
    # into the logo
    put(riser(1.6, 250, 9000), 25.0 - 1.6, 0.34, r=0.3)
    put(revswell(1.4), 25.0 - 1.4, 0.24, r=0.4)
    lo, hi = impact(1.25); put(lo, 25.0, 0.6); put(hi, 25.0, 0.7, r=0.8)
    kicks.append((25.0, 1.0)); kicks.append((5.0, 1.0)); kicks.append((22.5, 0.8)); kicks.append((10.0, 0.7)); kicks.append((20.0, 0.6))
    # line retracts, lockup slides
    w = whoosh(0.3, 0.25, 6000, 1200, 500)[::-1]; put(np.ascontiguousarray(w), 25.62, 0.22, r=0.3)
    put(whoosh(0.4, 0.5, 300, 2500, 500), 26.05, 0.2, r=0.3)
    # wordmark letters + smile
    for i, m in enumerate([68, 70, 72, 75, 77, 80, 82]): put(pluck(hz(m), 0.6, 5, 0.8), 26.48 + i * 0.065, 0.13, pan=-0.3 + 0.1 * i, r=0.5, d=0.25)
    put(blip(hz(80), hz(84), 0.12), 27.14, 0.16, r=0.5); put(blip(hz(84), hz(87), 0.2), 27.26, 0.16, r=0.5)
    # bar 11: slow rising bells
    for i, m in enumerate([68, 75, 82, 84]): put(bell(hz(m), 2.4, 2.0, 1.0, 2.0), tb(11, 1 + i) + (0.0 if i else 0.02), 0.2, pan=-0.3 + 0.2 * i, r=0.7, d=0.4)
    # bar 12: the tagline motif
    MOT = [(0, 75), (2, 80), (4, 82), (8, 87)]
    for (s, m) in MOT:
        put(mixs(keys(hz(m), 3.0) * 1.0, bell(hz(m), 2.6, 2.0, 0.9, 1.9) * 0.6), tb(12, 1, s), 0.32, pan=0.1 * (s - 4) / 4, r=0.6, d=0.3)
    put(keys(hz(56), 3.2) + keys(hz(63), 3.2) * 0.8 + keys(hz(72), 3.2) * 0.7, tb(12), 0.3, r=0.5)
    K(tb(12), 0.45, 1.3)
    # glint
    n = int(1.0 * SR); gl = tvf(rs.randn(n), lin(n, 5000, 11000, 1.0), 'bp', 4.0) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    put(gl, 28.3, 0.1, pan=0.0, r=0.7)
    for i, m in enumerate([92, 87, 84, 80]): put(bell(hz(m), 1.4, 2.0, 0.8, 3.5), 28.42 + i * 0.1, 0.05, pan=-0.4 + 0.27 * i, r=0.8)

else:
    # ---------- logo film: the mark comes apart, is drawn again, multiplies, dances, lights up ----------
    lo, hi = impact(0.5); put(lo, 0.0, 0.3); put(hi, 0.0, 0.14, r=0.6)
    put(mixs(bell(hz(77), 2.2, 2.0, 1.0, 2.2), bell(hz(84), 2.2, 2.0, 0.8, 2.2)), 0.02, 0.1, r=0.7, d=0.3)
    for i, t0 in enumerate((0.5, 0.65, 0.8)):                     # towers fold back into the line
        w = whoosh(0.3, 0.22, 5200, 1100, 500)[::-1]; put(np.ascontiguousarray(w), t0, 0.2, r=0.3)
        put(blip(660 - 110 * i, 330 - 50 * i, 0.22), t0 + 0.22, 0.1, pan=0.3 - 0.3 * i, r=0.4)
    put(blip(240, 960, 0.55), 1.32, 0.11, r=0.5)                  # line -> point
    put(bell(hz(84), 1.8, 2.0, 1.0, 3.0), 1.875, 0.2, r=0.7, d=0.4)
    put(whoosh(0.07, 0.65, 1200, 9000, 1400), 2.5 - 0.07, 0.5, r=0.3)   # the line shoots out
    lo, hi = impact(0.45); put(lo, 2.5, 0.42); put(hi, 2.5, 0.2, r=0.5); kicks.append((2.5, 0.5))
    for n in range(1, 23): put(tick(2600 + 60 * n, 0.006), 2.5 + n * 0.022, 0.07 * (1 - n / 30), pan=(-1) ** n * 0.5, r=0.15)
    put(blip(520, 1040, 0.7), 3.15, 0.07, r=0.5); put(tick(1900, 0.012), 3.62, 0.2, r=0.3)
    for i, m in enumerate([65, 72, 75, 80]): put(bell(hz(m), 1.8, 2.0, 1.0, 2.8), 2.5 + 0.625 * i, 0.12, pan=-0.3 + 0.2 * i, r=0.7, d=0.4)
    # construction
    put(riser(1.5, 250, 7000), 5.0 - 1.5, 0.3, r=0.3); put(revswell(1.2), 5.0 - 1.2, 0.2, r=0.4)
    lo, hi = impact(1.0); put(lo, 5.0, 0.55); put(hi, 5.0, 0.6, r=0.7); kicks.append((5.0, 1.0))
    for i in range(5): put(tick(2400 - 220 * i, 0.008), 5.02 + i * 0.035, 0.14, pan=-0.4 + 0.2 * i, r=0.2)
    for i, t0 in enumerate((5.3, 5.45, 5.6)):                     # outlines being drawn
        n = int(0.85 * SR); x = tvf(rs.randn(n), lin(n, 1800 + 500 * i, 4200 + 500 * i, 1.0), 'bp', 5.0) * np.sin(np.pi * np.linspace(0, 1, n)) ** 0.8
        put(x, t0, 0.11, pan=-0.4 + 0.4 * i, r=0.25)
    put(tick(2000, 0.012), 6.5, 0.18, r=0.3); put(tick(2300, 0.012), 6.65, 0.18, r=0.3)
    put(mixs(bell(hz(80), 2.0, 2.0, 1.2, 2.6), bell(hz(87), 2.0, 2.0, 1.0, 2.6)), 7.0, 0.14, r=0.6, d=0.3)   # 60 degrees
    put(blip(220, 700, 0.95), 6.5, 0.1, r=0.6)
    lo, hi = impact(0.6); put(lo, 7.5, 0.4); put(hi, 7.5, 0.26, r=0.6); kicks.append((7.5, 0.5))
    w = whoosh(0.3, 0.25, 6000, 1200, 500)[::-1]; put(np.ascontiguousarray(w), 8.75, 0.18, r=0.3)
    # one becomes many
    put(riser(1.25, 300, 8000), 10.0 - 1.25, 0.26, r=0.3)
    put(whoosh(0.36, 0.7, 400, 7500, 700), 10.0 - 0.36, 0.62, r=0.25)
    lo, hi = impact(0.6); put(lo, 10.0, 0.42); put(hi, 10.0, 0.3, r=0.5); kicks.append((10.0, 0.7))
    for i, t0 in enumerate((10.625, 11.875, 13.125)):             # waves through the pattern
        put(whoosh(0.55, 0.75, 500, 5200, 900, 1.6), t0 + 0.15, 0.3, r=0.3)
        for j, m in enumerate([80, 84, 87, 92]): put(bell(hz(m), 1.2, 2.0, 0.9, 3.6), t0 + 0.5 + j * 0.09, 0.06, pan=-0.6 + 0.4 * j, r=0.7)
    put(riser(0.7, 400, 9000), 14.93 - 0.7, 0.3, r=0.3)           # dive into one tower
    put(whoosh(0.42, 0.35, 500, 8500, 1200), 14.93 - 0.42, 0.6, r=0.25)
    lo, hi = impact(0.5); put(lo, 15.0, 0.4); put(hi, 15.0, 0.26, r=0.5); kicks.append((15.0, 0.6))
    # rhythm: the bars find the line
    for i in range(13): put(pluck(hz([56, 58, 60, 63, 65, 68, 70, 72, 75, 77, 80, 82, 84][i]), 0.5, 6, 1.0), 18.62 + i * 0.05, 0.15, pan=-0.6 + i * 0.1, r=0.4, d=0.3)
    put(whoosh(0.3, 0.5, 400, 4500, 700), 19.4, 0.3, r=0.3)
    put(riser(0.9, 500, 6000), 20.0 - 0.9, 0.18, r=0.3)
    lo, hi = impact(0.5); put(lo, 20.0, 0.3); put(hi, 20.0, 0.22, r=0.5); kicks.append((20.0, 0.6))
    w = whoosh(0.3, 0.25, 6000, 1200, 500)[::-1]; put(np.ascontiguousarray(w), 20.02, 0.18, r=0.3)
    # light: the sun crosses, night falls, rooms light up
    n = int(2.4 * SR); sh = tvf(rs.randn(n), lin(n, 5200, 1500, 1.2), 'bp', 2.5) * np.sin(np.pi * np.linspace(0, 1, n)) ** 1.3
    put(sh, 20.3, 0.12, pan=0.0, r=0.6)
    put(revswell(0.8), 22.5 - 0.8, 0.12, r=0.4)
    lo, hi = impact(0.7); put(lo, 22.5, 0.42); put(hi, 22.5, 0.24, r=0.6); kicks.append((22.5, 0.7))
    PENT = [68, 70, 72, 75, 77, 80, 82, 84, 87, 89, 92]
    NW = 30
    for i in range(NW):
        tw = 22.45 + 1.85 * (i / NW) ** 0.72
        put(pluck(hz(PENT[(i * 3) % len(PENT)]), 0.6, 5.5, 0.9), tw, 0.07 + 0.05 * i / NW, pan=0.7 * np.sin(i * 2.4), r=0.5, d=0.25)
    put(riser(1.6, 250, 9000), 25.0 - 1.6, 0.34, r=0.3); put(revswell(1.4), 25.0 - 1.4, 0.24, r=0.4)
    lo, hi = impact(1.25); put(lo, 25.0, 0.6); put(hi, 25.0, 0.7, r=0.8); kicks.append((25.0, 1.0))
    put(blip(220, 880, 0.6), 25.03, 0.1, r=0.6)
    put(whoosh(0.4, 0.5, 300, 2500, 500), 26.0, 0.2, r=0.3)
    for i, m in enumerate([68, 70, 72, 75, 77, 80, 82]): put(pluck(hz(m), 0.6, 5, 0.8), 26.48 + i * 0.065, 0.13, pan=-0.3 + 0.1 * i, r=0.5, d=0.25)
    put(blip(hz(80), hz(84), 0.12), 27.14, 0.16, r=0.5); put(blip(hz(84), hz(87), 0.2), 27.26, 0.16, r=0.5)
    for i, m in enumerate([68, 75, 82, 84]): put(bell(hz(m), 2.4, 2.0, 1.0, 2.0), tb(11, 1 + i) + (0.0 if i else 0.02), 0.2, pan=-0.3 + 0.2 * i, r=0.7, d=0.4)
    for (s16, m) in [(0, 75), (2, 80), (4, 82), (8, 87)]:
        put(mixs(keys(hz(m), 3.0) * 1.0, bell(hz(m), 2.6, 2.0, 0.9, 1.9) * 0.6), tb(12, 1, s16), 0.32, pan=0.1 * (s16 - 4) / 4, r=0.6, d=0.3)
    put(keys(hz(56), 3.2) + keys(hz(63), 3.2) * 0.8 + keys(hz(72), 3.2) * 0.7, tb(12), 0.3, r=0.5)
    K(tb(12), 0.45, 1.3)
    n = int(1.0 * SR); gl = tvf(rs.randn(n), lin(n, 5000, 11000, 1.0), 'bp', 4.0) * np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    put(gl, 28.3, 0.1, pan=0.0, r=0.7)
    for i, m in enumerate([92, 87, 84, 80]): put(bell(hz(m), 1.4, 2.0, 0.8, 3.5), 28.42 + i * 0.1, 0.05, pan=-0.4 + 0.27 * i, r=0.8)

# ---------------- sidechain, fx, master ----------------
sc = np.ones(N); t_all = np.arange(N) / SR
for (tk, gk) in kicks:
    i = int(tk * SR); n = min(N - i, int(0.45 * SR)); tt = np.arange(n) / SR
    sc[i:i + n] = np.minimum(sc[i:i + n], 1 - 0.55 * gk * np.exp(-tt / 0.11))
dry += pad_bus * sc[:, None] * 0.9 + bass_bus * (0.35 + 0.65 * sc)[:, None] + arp_bus * (0.5 + 0.5 * sc)[:, None]
rev += pad_bus * sc[:, None] * 0.35 + arp_bus * 0.0

# ping-pong delay (dotted eighth)
dt = int(3 * S16 * SR); dout = np.zeros((N, 2)); cur = filt(dly, 300, 'hp')
for k in range(1, 6):
    cur = filt(cur, 5200 - 600 * k, 'lp')[:, ::-1] * 0.5
    sh = k * dt
    if sh >= N: break
    dout[sh:] += cur[:N - sh]
# reverb
def make_ir(rt=2.6, pre=0.018):
    n = int(rt * 1.3 * SR); t = np.arange(n) / SR
    ir = rs.randn(n, 2) * np.exp(-6.9 * t / rt)[:, None]
    ir = filt(ir, 250, 'hp'); ir = filt(ir, 6500, 'lp')
    ir *= (1 - np.exp(-t / 0.012))[:, None]
    ir = np.vstack([np.zeros((int(pre * SR), 2)), ir])
    return ir / np.sqrt((ir ** 2).sum(0)).mean()
ir = make_ir()
rin = rev + dout * 0.35
rout = np.stack([sg.fftconvolve(rin[:, c], ir[:, c])[:N] for c in range(2)], 1)
mix = dry + dout * 0.8 + rout * 0.46

# section automation
auto = np.ones(N)
def seg_gain(a, b, g0, g1):
    i, j = int(a * SR), int(b * SR); auto[i:j] *= np.linspace(g0, g1, j - i)
seg_gain(0, 0.25, 0.0, 1.0)
seg_gain(28.6, 30.0, 1.0, 0.0)
auto[int(29.97 * SR):] = 0
mix *= auto[:, None]
mix = filt(mix, 28, 'hp'); mix = filt(mix, 17000, 'lp', 4)
# glue: gentle soft clip, normalise
peak = np.abs(mix).max(); mix = mix / peak
drive = float(sys.argv[2]) if len(sys.argv) > 2 else 1.5
mix = np.tanh(mix * drive) / np.tanh(drive)
mix = mix / np.abs(mix).max() * 10 ** (-1.6 / 20)
out = sys.argv[1] if len(sys.argv) > 1 else 'bgm.wav'
with wave.open(out, 'wb') as w:
    w.setnchannels(2); w.setsampwidth(3); w.setframerate(SR)
    d = np.clip(mix, -1, 1); i32 = (d * (2 ** 23 - 1)).astype('<i4')
    w.writeframes(np.ascontiguousarray(i32).view(np.uint8).reshape(-1, 4)[:, :3].tobytes())
print('wrote', out, 'peak', np.abs(mix).max())

# ---------- band envelopes for the equaliser scene (logo film) ----------
if os.environ.get('BANDS'):
    m = mix.mean(1); NBD = 13; F0, F1 = 15 * 60 - 4, 20 * 60 + 4
    edges = np.geomspace(45, 9000, NBD + 1); rows = []
    for k in range(NBD):
        sos = sg.butter(3, [edges[k] / (SR / 2), edges[k + 1] / (SR / 2)], 'band', output='sos')
        e = sg.sosfilt(sos, m) ** 2
        e = np.sqrt(sg.sosfilt(sg.butter(2, 14 / (SR / 2), 'low', output='sos'), e).clip(1e-12))
        idx = (np.arange(F0, F1) * SR / 60).astype(int)
        v = 20 * np.log10(e[idx] + 1e-9)
        lo_, hi_ = np.percentile(v, 12), np.percentile(v, 98.5)
        rows.append(np.clip((v - lo_) / (hi_ - lo_), 0, 1) ** 1.25)
    B = np.array(rows).T                                   # frames x bands
    B = 0.7 * B + 0.15 * np.roll(B, 1, 1) + 0.15 * np.roll(B, -1, 1)
    for i in range(1, len(B)):                                               # limited attack, slow release
        up = B[i - 1] + (B[i] - B[i - 1]) * 0.55
        B[i] = np.where(B[i] > B[i - 1], up, np.maximum(B[i], B[i - 1] * 0.9))
    B = 0.1 + 0.9 * B
    with open(os.environ['BANDS'], 'w') as fh:
        fh.write('const BANDS_F0 = %d;\nconst BANDS = %s;\n' % (F0, '[' + ','.join('[' + ','.join('%.3f' % x for x in r) + ']' for r in B) + ']'))
    print('bands', B.shape, 'mean per band', np.round(B.mean(0), 2))
