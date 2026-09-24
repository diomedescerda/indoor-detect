You already have most of this documented across our conversation. Let me consolidate it into a clean, complete definition:

---

**Design of Audio Descriptors**

The system generates audio descriptors using the Android TextToSpeech API (available from Android 8.0 / API level 26), which operates entirely on-device without requiring an internet connection and supports Spanish.

**Descriptor structure**

Each descriptor combines three elements:

```
[object name] + [vertical zone] + [horizontal zone]
```

Examples:

- "silla abajo a la izquierda"
- "persona arriba al centro"
- "nevera abajo a la derecha"

**Spatial zones**

The frame is divided into 6 zones using a Cartesian plane as defined in the spatial localization module. The zone is determined by the center point of the detected object's bounding box.

**Priority system**

When multiple objects are detected simultaneously the system applies the following priority order before generating any descriptor:

1. Person — always announced first regardless of zone
2. Objects in the center zone — highest collision risk
3. Objects in lateral zones — left announced before right on equal priority

A maximum of 2 descriptors are generated per cycle to avoid audio overload.

**Cooldown mechanism**

Each object class has an independent cooldown of 2 seconds. If an object was announced less than 2 seconds ago it will not be announced again even if it remains detected in subsequent frames. This prevents repetitive announcements when the user is stationary near an object.

**Output chain**

```
Detection result → zone assignment → priority filter → cooldown check → TTS.speak()
```