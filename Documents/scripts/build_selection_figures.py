"""Publication-size Spanish versions of the archived Android selection plots.

Requires NumPy and Matplotlib. Reads saved results; does not rerun inference.
"""
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / 'Build/Testing/benchmark/results/android'
OUT = ROOT / 'Documents/Figures'
CONFIGS = ['Head 1x', 'Head 0.5x', 'Chest 1x', 'Chest 0.5x', 'Gorillapod 1x', 'Gorillapod 0.5x']
LABELS = ['Cabeza 1x', 'Cabeza 0,5x', 'Pecho 1x', 'Pecho 0,5x', 'Gorillapod 1x', 'Gorillapod 0,5x']

def main():
    OUT.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 8})
    rows = list(csv.DictReader((RESULTS / 'scenes/scene_counts.csv').open()))
    summary = list(csv.DictReader((RESULTS / 'scenes/count_summary.csv').open()))
    stats = {(r['mode'], r['configuration']): r for r in summary}
    fig, axes = plt.subplots(3, 1, figsize=(6.08, 6.6), layout='constrained')
    colors = ['#246B9C', '#D17822']
    for ax, metric, title in zip(axes, ('precision', 'recall', 'f1'), ('Precisión', 'Recall', 'F1')):
        for mode, offset, color, label in zip(('detector', 'app_output'), (-.19, .19), colors,
                                             ('Detector', 'Lista de hasta dos objetos')):
            vals = []
            for config in CONFIGS:
                r = stats[mode, config];tp,fp,fn = (int(r[k]) for k in ('tp','fp','fn'))
                vals.append({'precision':tp/(tp+fp), 'recall':tp/(tp+fn), 'f1':2*tp/(2*tp+fp+fn)}[metric]*100)
            ax.bar(np.arange(6)+offset, vals, width=.36, color=color, label=label)
        ax.set_ylim(0, 100);ax.set_yticks([0,25,50,75,100]);ax.set_ylabel(title+' (%)')
        ax.set_xticks(range(6), LABELS, rotation=16, ha='right');ax.grid(axis='y', alpha=.2);ax.set_axisbelow(True)
    axes[0].legend(loc='upper center', bbox_to_anchor=(.5,1.26), ncol=2, frameon=False, fontsize=8)
    fig.savefig(OUT/'seleccion_metricas.png', dpi=300);plt.close(fig)
    # Configuration/group keys are taken from the scene CSV, not reconstructed image IDs.
    mounts = {'head_harness':'Head', 'chest_harness':'Chest', 'gorillapod':'Gorillapod'}
    lookup = {(r['mode'], int(r['capture_group']), mounts[r['mount']]+' '+r['lens']): r for r in rows}
    fig, axes = plt.subplots(1,3,figsize=(6.08,6.6),layout='constrained')
    short = ['Cab. 1x','Cab. 0,5x','Pec. 1x','Pec. 0,5x','Gor. 1x','Gor. 0,5x']
    for ax,key,title,cmap in zip(axes,('gt','tp','fp'),('Visibles (GT)','Correctas (TP)','Falsas (FP)'),('Blues','Greens','Reds')):
        values = np.array([[int(lookup['detector',g,c][key]) for c in CONFIGS] for g in range(1,34)])
        ax.imshow(values,aspect='auto',cmap=cmap,vmin=0)
        for y in range(33):
            for x in range(6):
                ax.text(x,y,str(values[y,x]),ha='center',va='center',fontsize=7.5,
                        color='white' if values[y,x]>values.max()*.58 else '#17202a')
        ax.set_xticks(range(6),short,rotation=90,fontsize=7.5)
        ax.set_yticks(range(33),range(1,34),fontsize=7.5);ax.tick_params(length=0)
        ax.set_title(title,fontsize=9)
    axes[0].set_ylabel('Grupo de captura / escena')
    fig.savefig(OUT/'seleccion_escenas.png',dpi=300);plt.close(fig)

if __name__ == '__main__':
    main()
