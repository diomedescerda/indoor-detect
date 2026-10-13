package com.unimagdalena.assistivevision

import android.graphics.BitmapFactory
import android.os.Build
import android.os.SystemClock
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import com.unimagdalena.assistivevision.data.SettingsManager
import com.unimagdalena.assistivevision.model.LetterboxMapper
import com.unimagdalena.assistivevision.modules.DetectionModule
import com.unimagdalena.assistivevision.modules.PreprocessingModule
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import org.json.JSONArray
import org.json.JSONObject
import org.junit.Test
import org.junit.runner.RunWith
import java.io.File
import java.security.MessageDigest

/** Replays staged JPEGs through the production preprocessing and detection modules. */
@RunWith(AndroidJUnit4::class)
class DatasetBenchmarkTest {
    @Test fun benchmarkDataset() = runBlocking {
        val ctx = InstrumentationRegistry.getInstrumentation().targetContext
        val args = InstrumentationRegistry.getArguments()
        val root = File(ctx.filesDir, "benchmark")
        val manifestFile = File(root, "labels.json")
        val manifest = JSONObject(manifestFile.readText())
        val images = manifest.getJSONArray("images")
        require(images.length() == 198)
        val settings = SettingsManager(ctx)
        val confidence = args.getString("confidence")?.toFloat() ?: settings.confidence.first()
        val maxObjects = args.getString("maxObjects")?.toInt() ?: settings.maxObjects.first()
        require(confidence in 0f..1f && maxObjects in 1..15)
        fun sha(bytes: ByteArray) = MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") { "%02x".format(it) }
        val metadata = JSONObject().put("source", "android_app_modules")
            .put("model_sha256", sha(ctx.assets.open("efficientdet-lite2-detection-metadata.tflite").use { it.readBytes() }))
            .put("gt_sha256", sha(manifestFile.readBytes()))
            .put("device", "${Build.MANUFACTURER} ${Build.MODEL}")
            .put("android_sdk", Build.VERSION.SDK_INT).put("confidence", confidence)
            .put("max_objects", maxObjects).put("detector_cap", 15).put("score_floor", 0.001)
            .put("preprocessing", "Production PreprocessingModule and LetterboxMapper")
            .put("timing_scope", "JPEG replay; camera acquisition, UI and speech excluded")
        val frames = JSONArray()
        val detector = DetectionModule(ctx)
        val preprocessing = PreprocessingModule()
        try {
            val first = BitmapFactory.decodeFile(File(root, "data/" + images.getJSONObject(0).getString("file_name")).path)
                ?: error("First photo could not be decoded")
            repeat(3) { detector.detect(preprocessing.preprocess(first), confidence) }
            first.recycle()
            // Fixed shuffled order reduces systematic timing bias from six-image acquisition order.
            val order = (0 until images.length()).shuffled(kotlin.random.Random(20261013))
            for (index in order) {
                val image = images.getJSONObject(index)
                val file = File(root, "data/" + image.getString("file_name"))
                val start = SystemClock.elapsedRealtimeNanos()
                val bitmap = BitmapFactory.decodeFile(file.path) ?: error("Cannot decode $file")
                require(bitmap.width == image.getInt("width") && bitmap.height == image.getInt("height"))
                val tensor = preprocessing.preprocess(bitmap)
                val prepEnd = SystemClock.elapsedRealtimeNanos()
                val detected = detector.detect(tensor, 0.001f)
                val inferEnd = SystemClock.elapsedRealtimeNanos()
                val geometry = LetterboxMapper.forward(bitmap.width, bitmap.height, DetectionModule.INPUT_SIZE)
                val predictions = JSONArray()
                for (d in detected) {
                    val x1 = LetterboxMapper.toFrameX(d.bbox.left, geometry, bitmap.width).coerceIn(0f, bitmap.width.toFloat())
                    val y1 = LetterboxMapper.toFrameY(d.bbox.top, geometry, bitmap.height).coerceIn(0f, bitmap.height.toFloat())
                    val x2 = LetterboxMapper.toFrameX(d.bbox.right, geometry, bitmap.width).coerceIn(0f, bitmap.width.toFloat())
                    val y2 = LetterboxMapper.toFrameY(d.bbox.bottom, geometry, bitmap.height).coerceIn(0f, bitmap.height.toFloat())
                    predictions.put(JSONObject().put("image_id", image.getInt("id"))
                        .put("category_id", d.classId).put("score", d.score)
                        .put("bbox", JSONArray(listOf(x1, y1, x2-x1, y2-y1))))
                }
                frames.put(JSONObject().put("image_id", image.getInt("id"))
                    .put("file_name", image.getString("file_name")).put("predictions", predictions)
                    .put("preprocess_ms", (prepEnd-start)/1e6).put("inference_ms", (inferEnd-prepEnd)/1e6))
                bitmap.recycle()
                // Checkpoint is deliberately named partial; evaluator rejects missing frames.
                File(root, "android.partial.json").writeText(JSONObject().put("metadata", metadata).put("frames", frames).toString(2))
            }
            File(root, "android.json").writeText(JSONObject().put("metadata", metadata).put("frames", frames).toString(2))
        } finally { detector.close() }
    }
}
