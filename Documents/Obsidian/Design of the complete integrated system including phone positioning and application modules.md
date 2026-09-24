
**1. Phone positioning** 
Need to define:
- Exact position (chest, neck lanyard, shirt pocket)
- Angle (horizontal, slightly downward)
- Justification based on camera field of view and what's most useful for navigation
>Chest Strap Mount
>Head Mount

**2. System architecture diagram** 
![[system_architecture_diagram.png]]
Related to the parameters
#### Phone positioning
> got to do it by myself

The most cited position in assistive vision literature is **chest-level, 10–15° downward tilt**. Here's why that works for your context:

- At chest height (~120cm from ground) the camera captures the floor ahead and objects at waist-to-head height simultaneously
- A slight downward tilt ensures the floor boundary is visible, which helps detect objects resting on it (chairs, tables)
- Horizontal mounting (landscape) maximizes the horizontal field of view, which is what you need for left/center/right classification

**Decision: chest mount, landscape orientation, 10° downward tilt** ????

Based on everything we've defined, here are the module definitions:

---
**3. Module definitions**
### Capture Module

**Responsibility:** Access the device camera and deliver frames to the preprocessing pipeline at a consistent rate.

**Input:** Camera hardware stream via CameraX

**Output:** Raw RGB bitmap frame at the device's native resolution

**Key decisions:**

- Rear-facing camera
- Landscape orientation, chest mount, 10° downward tilt (maybe)
- Frame rate capped to match inference speed (~9 FPS) to avoid queuing frames faster than the model processes them

---

### Preprocessing Module

**Responsibility:** Transform raw camera frames into the tensor format expected by EfficientDet-Lite2.

**Input:** Raw RGB bitmap (variable resolution)

**Output:** Float32 tensor of shape `[1, 448, 448, 3]`, values normalized to `[0, 255]` uint8 (EfficientDet-Lite2 expects uint8, not float)

**Key decisions:**

- Letterbox resize to preserve aspect ratio without distortion
- Gray padding (114, 114, 114) for letterbox borders
- No color space conversion needed (Camera outputs RGB, model expects RGB)

---

### Detection Module

**Responsibility:** Run inference on the preprocessed tensor and return raw detections.

**Input:** Uint8 tensor `[1, 448, 448, 3]`

**Output:**

```
boxes:   [1, N, 4]  — normalized [ymin, xmin, ymax, xmax]
classes: [1, N]     — class index (0-indexed)
scores:  [1, N]     — confidence score [0.0, 1.0]
count:   [1]        — number of detections
```

**Key decisions:**

- EfficientDet-Lite2 TFLite, CPU backend
- Confidence threshold: 0.30 (discard detections below this)
- 10 target classes from MS COCO (person, chair, couch, bed, tv, sink, toilet, computer, refrigerator, table)
- Model loaded once at app startup, reused across frames

---

### Spatial Localization Module

**Responsibility:** Assign a spatial zone to each detection based on its bounding box center position within the frame.

**Input:** List of filtered detections `(class_id, score, bbox)` + frame dimensions `(width, height)`

**Output:** List of detections with zone label appended `(class_id, score, bbox, zone)`

**Zone logic:**

```python
def get_zone(box_center_x, box_center_y, frame_width, frame_height):
    if box_center_x < frame_width * 0.35:
        h_zone = "a la izquierda"
    elif box_center_x > frame_width * 0.65:
        h_zone = "a la derecha"
    else:
        h_zone = "frente a ti" if v_zone == "inferior" else "arriba al centro"

    v_zone = "abajo" if box_center_y >= frame_height * 0.5 else "arriba"

    if h_zone not in ["a la izquierda", "a la derecha"]:
        return "frente a ti" if v_zone == "abajo" else "arriba al centro"
    
    return f"{v_zone} {h_zone}"
```

---

### Priority & Filtering Module

**Responsibility:** Given all zoned detections for a frame, select which objects to announce and in what order.

**Input:** List of `(class_id, score, bbox, zone)` detections

**Output:** Ordered list of max 2 descriptors ready for audio output

**Priority rules:**

1. Person — always first regardless of zone
2. Objects in center zone
3. Objects in lateral zones — left before right

**Cooldown check:** Before adding a descriptor to the output list, verify that more than 2 seconds have elapsed since the last announcement of that class. If not, skip it.

---

### Audio Module

**Responsibility:** Convert filtered descriptors into spoken audio using Android TTS.

**Input:** Ordered list of max 2 `(class_name, zone)` tuples

**Output:** Audio playback via device speaker or connected earpiece

**Key decisions:**

- Android `TextToSpeech` API, language set to `Locale("es", "CO")`
- `QUEUE_FLUSH` mode — interrupts current speech if a higher priority object appears
- Descriptor format: `"[objeto] [zona]"` e.g. "persona frente a ti", "silla abajo a la izquierda"
- Cooldown state maintained per class: `Map<ClassId, Long>` storing last announcement timestamp

```kotlin
fun speak(objectName: String, zone: String) {
    tts.speak("$objectName $zone", TextToSpeech.QUEUE_FLUSH, null, null)
}
```

---

**4. Class diagram or component diagram** 
![[component_diagram_android.png]]
Color encoding: 
teal = components that interact with external systems (CameraX captures from hardware, DetectionModule runs TFLite, AudioModule calls TTS). 
Gray = internal processing modules. 
Purple = the ViewModel container that owns all processing logic.

#### Sequence Diagram
![[sequence_diagram_frame_cycle.png]]
The two `alt` blocks are the key decision points:

**Alt 1 (cooldown check inside Priority)** — if an object was announced less than 2 seconds ago, it gets skipped. This happens per-object, so the module may still return 1 descriptor even if the other is in cooldown.

**Alt 2 (no descriptors)** — if after applying priority and cooldown filtering the result is empty (no detections above threshold, or all objects in cooldown), the AudioModule is never called and the system immediately waits for the next frame.

---