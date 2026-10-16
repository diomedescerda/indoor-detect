"""Insert observational, AI-assisted occlusion results from frozen benchmark outputs."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def add(anchor, add_before, table, H3):
    m=json.loads((ROOT/'Build/Testing/occlusion/results/metrics.json').read_text())
    pct=lambda x:f'{100*x:.1f}'.replace('.',',')+' %' if x is not None else '—'
    ci=lambda r:'['+pct(r['recall_ci95_low'])+'; '+pct(r['recall_ci95_high'])+']'
    names={'none':'Sin oclusión','partial':'Parcial','heavy':'Fuerte','uncertain':'Incierta'}
    rows=[r for r in m['severity'] if r['mode']=='detector']+[r for r in m['uncertainty'] if r['mode']=='detector']
    add_before(anchor,'4.8.1 Análisis observacional de oclusión',H3)
    add_before(anchor,'Se inspeccionaron las 198 fotografías y se asignó una etiqueta suplementaria a cada una de las 889 instancias COCO, sin modificar sus cajas ni volver a ejecutar el detector. Dos lotes disjuntos fueron revisados visualmente con GPT-6 Astra y razonamiento High, sin mostrar predicciones durante el etiquetado. El protocolo distingue ausencia de obstrucción externa, oclusión parcial y fuerte; los casos ambiguos se conservan como inciertos. El truncamiento por borde se registra aparte, y el tamaño pequeño o la perspectiva no se consideran por sí solos oclusión. La severidad es cualitativa y no corresponde a porcentajes medidos de superficie oculta.')
    add_before(anchor,'Las etiquetas son asistidas por IA y provisionales hasta la revisión del autor; los dos lotes no constituyen doble revisión independiente. Se registra motivo, confianza e identificador de anotación, y se proporciona una interfaz local para corregir los casos. El análisis utiliza el emparejamiento del benchmark con confianza 0,30, IoU mínimo 0,50 y coincidencia de clase. Se calcula recall por nivel; los falsos positivos sin objeto de referencia no reciben una etiqueta de oclusión.')
    table(anchor,'Tabla 4.10. Recall por nivel de oclusión con etiquetas asistidas por IA.',['Oclusión','GT','TP','FN','Recall','IC 95 %'],[[names[r['occlusion']],r['gt'],r['tp'],r['fn'],pct(r['recall']),ci(r)] for r in rows])
    add_before(anchor,'Los intervalos percentiles del 95 % se obtienen con 10 000 remuestreos de los 33 grupos completos (semilla 20261013). Los casos inciertos se muestran por separado y no se mezclan con los tres niveles de severidad. Los intervalos reflejan variación entre grupos, pero no incertidumbre del etiquetado ni posibles errores de la verdad de campo. El análisis incluye únicamente instancias ya anotadas, por lo que no cubre objetos completamente ocultos y ausentes de la anotación.')
    a,b,c=rows[:3]
    add_before(anchor,'El recall observado es '+pct(a['recall'])+' sin oclusión, '+pct(b['recall'])+' con oclusión parcial y '+pct(c['recall'])+' con oclusión fuerte. Estos valores describen asociaciones del conjunto; no aíslan el efecto causal de la oclusión. Se conservan desgloses por clase y tamaño aparente conjunto, configuración y truncamiento, además de análisis de sensibilidad con etiquetas de alta confianza y objetos no truncados. El tamaño aparente se define por área de caja dividida entre área de imagen: pequeño < 0,01, mediano de 0,01 a < 0,10 y grande ≥ 0,10; no representa el área completa de la parte oculta.')
    def pick(table_name, **keys):
        return next(r for r in m[table_name] if r['mode']=='detector' and all(r.get(k)==v for k,v in keys.items()))
    hc=pick('by_class',occlusion='heavy',category='chair')
    hs=pick('by_area',occlusion='heavy',area_stratum='small')
    ns=pick('by_area',occlusion='none',area_stratum='small')
    chair=[pick('by_class_area',occlusion=l,category='chair',area_stratum='medium') for l in ['none','partial','heavy']]
    beds=[pick('by_class',occlusion=l,category='bed') for l in ['none','partial']]
    nontr=[pick('sensitivity',occlusion=l,sensitivity='nontruncated') for l in ['none','partial','heavy']]
    high=[pick('sensitivity',occlusion=l,sensitivity='high_confidence') for l in ['none','partial','heavy']]
    add_before(anchor,'La composición limita la interpretación del gradiente: '+str(hc['gt'])+' de las '+str(c['gt'])+' instancias con oclusión fuerte son sillas y '+str(hs['gt'])+' tienen caja pequeña, frente a '+str(ns['gt'])+' de '+str(a['gt'])+' sin oclusión. Dentro de sillas de tamaño mediano, el recall es '+', '.join(pct(r['recall'])+' ('+str(r['tp'])+'/'+str(r['gt'])+')' for r in chair)+' para ausencia de oclusión, parcial y fuerte, respectivamente; aún varían escena, pose y tamaño dentro de la banda. En camas se obtiene '+pct(beds[0]['recall'])+' sin oclusión y '+pct(beds[1]['recall'])+' con oclusión parcial, por lo que el gradiente agrupado no debe asumirse universal. Al excluir objetos truncados, los valores agrupados son '+', '.join(pct(r['recall']) for r in nontr)+'; con etiquetas de alta confianza son '+', '.join(pct(r['recall']) for r in high)+', en el mismo orden de severidad. Estas comprobaciones describen sensibilidad, pero no eliminan la confusión ni sustituyen la revisión de etiquetas.')
    add_before(anchor,'La inspección señaló posibles inconsistencias de clase, cajas que abarcan más de una instancia y duplicados; se registraron como incidencias para revisión sin corregir automáticamente la referencia original. Las celdas con menos de 15 instancias se identifican como escasas. Antes de formular conclusiones definitivas, deben revisarse las etiquetas ambiguas y las incidencias GT, y recalcularse los resultados si cambia la referencia. Las tablas detalladas, los hashes y el protocolo se conservan en Build/Testing/occlusion/.')
