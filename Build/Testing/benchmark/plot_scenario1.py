"""Escenario 1 support: box plots of detections per photo/scene by mount and configuration,
plus paired t tests over the 33 paired capture groups. Uses saved per-image results only."""
import argparse, csv, json, math
from collections import defaultdict
from pathlib import Path
import numpy as np
from evaluate import CONFIGS, ROOT, write_csv

ROOT = ROOT
OUT = ROOT / 'benchmark/results/android/scenario1'
NAMES = [m.replace('_harness', '').capitalize() + ' ' + l for m, l in CONFIGS]
MOUNTS = ['head_harness', 'chest_harness', 'gorillapod']
MOUNT_NAMES = {'head_harness': 'Head', 'chest_harness': 'Chest', 'gorillapod': 'Gorillapod'}


def _betacf(a, x, b):
    """Continued fraction for the regularised incomplete beta function (Lentz, NR style)."""
    tiny, eps = 1e-30, 3e-14
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c = 1.0
    d = 1.0 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1.0 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        aa = -(a + m) * (qap + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < tiny:
            d = tiny
        c = 1.0 + aa / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < eps:
            return h
    raise RuntimeError('betacf did not converge')


def student_t_pvalue(t, df):
    """Two-sided p value for Student t via the regularised incomplete beta function."""
    a, x, b = df / 2.0, df / (df + t * t), 1.0 / 2
    if t == 0:
        return 1.0
    if x in (0.0, 1.0):
        return 1.0 if x == 0 else 0.0
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        ibeta = front * _betacf(a, x, b) / a
    else:  # symmetry form, required when x is close to 1 (small |t|); lgamma terms are shared
        ibeta = 1.0 - front * _betacf(b, 1.0 - x, a) / b
    return min(1.0, max(0.0, ibeta))  # two-sided p


def paired_t(a, b):
    d = np.array([x - y for x, y in zip(a, b)], dtype=float)
    n = len(d)
    mean, sd = d.mean(), d.std(ddof=1)
    se = sd / math.sqrt(n)
    t = mean / se if se else float('inf')
    df = n - 1
    p = student_t_pvalue(abs(t), df) if math.isfinite(t) else 0.0
    return dict(mean_diff=mean, sd_diff=sd, t=t, df=df, p=p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('run', type=Path, nargs='?', default=ROOT / 'benchmark/results/android.json')
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader((ROOT / 'benchmark/results/android/per_image.csv').open()))
    for r in rows:
        for k in ('capture_group', 'image_id', 'gt', 'tp', 'fp', 'fn', 'predictions'):
            r[k] = int(r[k])

    tests, plotdata = [], defaultdict(list)
    for mode in ('detector', 'app_output'):
        sel = [r for r in rows if r['mode'] == mode]
        # Paired t test on per-scene correct counts per mount (lenses pooled, 33 groups).
        by_mount_group = defaultdict(list)
        for r in sel:
            by_mount_group[(r['mount'], r['capture_group'])].append(r['tp'])
        pairs = [('head_harness', 'chest_harness'), ('head_harness', 'gorillapod'), ('chest_harness', 'gorillapod')]
        for left, right in pairs:
            la = [sum(by_mount_group[(left, g)]) for g in range(1, 34)]
            lb = [sum(by_mount_group[(right, g)]) for g in range(1, 34)]
            res = paired_t(la, lb)
            tests.append(dict(mode=mode, config_a=MOUNT_NAMES[left], config_b=MOUNT_NAMES[right], **res))
            plotdata[mode].append((MOUNT_NAMES[left], MOUNT_NAMES[right], la, lb))
        # per-configuration paired tests (detector only): gorillapod 0.5x vs each alternative,
        # mirroring the paired scene count comparisons.
        if mode == 'detector':
            pooled = {(r['mount'], r['lens'], r['capture_group']): r['tp'] for r in sel}
            for ca in CONFIGS[:-1]:
                seq = [pooled[(ca[0], ca[1], g)] for g in range(1, 34)]
                seq2 = [pooled[('gorillapod', '0.5x', g)] for g in range(1, 34)]
                res = paired_t(seq, seq2)
                tests.append(dict(mode=mode, config_a=NAMES[CONFIGS.index(ca)], config_b='Gorillapod 0.5x', **res))
    write_csv(OUT / 'paired_t_tests.csv', tests)

    # Box plot figures.
    import os
    os.environ.setdefault('MPLCONFIGDIR', str(ROOT / 'benchmark/.mplconfig'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    per_photo = defaultdict(list)
    per_config = defaultdict(list)
    for r in rows:
        if r['mode'] != 'detector':
            continue
        per_photo[r['mount']].append(r['tp'])
        per_config[f"{MOUNT_NAMES[r['mount']]} {r['lens']}"].append(r['tp'])

    fig, ax = plt.subplots(figsize=(6, 4.5), layout='constrained')
    ax.boxplot([per_photo[m] for m in MOUNTS], tick_labels=[MOUNT_NAMES[m] for m in MOUNTS], showfliers=True)
    ax.set_xlabel('Posición del montaje')
    ax.set_ylabel('Objetos correctos por foto (top 2 deshabilitado)')
    ax.grid(axis='y', alpha=.2)
    fig.savefig(OUT / 'boxplot_mount.png', dpi=180)
    fig.savefig(OUT / 'boxplot_mount.pdf')
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 4.5), layout='constrained')
    ax.boxplot([per_config[n] for n in NAMES], tick_labels=NAMES)
    ax.set_ylabel('Objetos correctos por foto')
    ax.tick_params(axis='x', rotation=30)
    ax.grid(axis='y', alpha=.2)
    fig.savefig(OUT / 'boxplot_configuration.png', dpi=180)
    fig.savefig(OUT / 'boxplot_configuration.pdf')
    plt.close(fig)

    # Per-mount complementary stats used by section 4.2.
    stats = []
    for mode in ('detector', 'app_output'):
        for m in MOUNTS:
            rr = [r for r in rows if r['mode'] == mode and r['mount'] == m]
            tp = sum(r['tp'] for r in rr)
            fp, fn = sum(r['fp'] for r in rr), sum(r['fn'] for r in rr)
            stats.append(dict(mode=mode, mount=MOUNT_NAMES[m], photos=len(rr), gt=sum(r['gt'] for r in rr), tp=tp, fp=fp, fn=fn,
                              mean_objects_per_photo=tp / len(rr),
                              precision=tp / (tp + fp) if tp + fp else None,
                              recall=tp / (tp + fn) if tp + fn else None,
                              f1=2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else None))
    write_csv(OUT / 'mount_stats.csv', stats)

    lines = ['Escenario 1: posiciones del arnés (helper outputs)', '',
             'Per-scene paired t test, correct object counts (33 groups):',
             'mode | A | B | mean diff | sd | t | df | p (two-sided)']
    for t in tests:
        lines.append(f"{t['mode']} | {t['config_a']} | {t['config_b']} | {t['mean_diff']:+.3f} | {t['sd_diff']:.3f} | {t['t']:.3f} | {t['df']} | {t['p']:.4f}")
    lines += ['', 'Per-mount pooled stats (mean objects/photo, P/R/F1):']
    for s in stats:
        lines.append(f"{s['mode']} | {s['mount']}: tp {s['tp']}, media {s['mean_objects_per_photo']:.2f}, P {fmt(s['precision'])}, R {fmt(s['recall'])}, F1 {fmt(s['f1'])}")
    (OUT / 'report.txt').write_text('\n'.join(lines) + '\n')
    print(OUT)


def fmt(v):
    return 'n/a' if v is None else f'{v:.1%}'


if __name__ == '__main__':
    main()
