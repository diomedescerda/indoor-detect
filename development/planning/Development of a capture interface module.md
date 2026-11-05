
ImageProxy (camera hardware buffer)
    ↓ imageProxy.toBitmap()
Bitmap (standard memory, 800KB, ARGB_8888)
    ↓ onFrameReady(bitmap)
PreprocessingModule
    ↓ resize + letterbox + normalize
ByteBuffer (448×448×3 bytes, uint8)
    ↓ interpreter.run()
EfficientDet-Lite2
    ↓
detections

Purpose: Encapsulates all CameraX setup for camera preview and frame capture, decoupled from the Activity.

Key implementation details:
- Library: CameraX (v1.6.1) — the Jetpack camera library that abstracts device-specific camera APIs
- Use cases bound simultaneously:
	- Preview — renders the live camera feed to a PreviewView (4:3 aspect ratio)
	- ImageAnalysis — captures frames for processing, configured with STRATEGY_KEEP_ONLY_LATEST (drops frames if the consumer is slow, preventing memory buildup) and OUTPUT_IMAGE_FORMAT_RGBA_8888 (direct bitmap-compatible format)
- Frame processing pipeline: Each ImageProxy is converted to a Bitmap via toBitmap(), passed to a callback (onFrameReady), then closed to free the buffer
- Threading: A dedicated single-thread executor (Executors.newSingleThreadExecutor()) runs the analyzer off the main thread, keeping the UI responsive
- Camera selection: Uses DEFAULT_BACK_CAMERA
- Lifecycle-aware: Bound to the Activity's LifecycleOwner so CameraX automatically pauses/resumes the camera
- Architecture: Follows a modular pattern — the Activity only calls start(previewView) and shutdown(), while all CameraX internals are encapsulated