package com.unimagdalena.assistivevision.modules

import android.content.Context
import android.content.res.AssetManager
import android.graphics.RectF
import android.util.Log
import com.unimagdalena.assistivevision.model.Detection
import org.tensorflow.lite.Interpreter
import java.io.FileInputStream
import java.nio.ByteBuffer
import java.nio.MappedByteBuffer
import java.nio.channels.FileChannel

class DetectionModule(context: Context) {
    private val interpreter: Interpreter
    private val maxModelDetections: Int

    /** Guards [detect]/[close] so the interpreter is never closed mid-inference. */
    private val inferenceLock = Any()

    @Volatile
    private var isClosed = false

    companion object {
        const val MAX_DETECTIONS = 15
        const val INPUT_SIZE = 448
        val TARGET_LABELS = mapOf(
            1 to "person",
            62 to "chair",
            63 to "couch",
            65 to "bed",
            67 to "table",
            70 to "toilet",
            72 to "tv",
            73 to "computer",
            81 to "sink",
            82 to "refrigerator"
        )
    }

    init {
        val model = loadModelFile(context.assets)
        interpreter = Interpreter(model)
        maxModelDetections = validateBoxesTensor(interpreter.getOutputTensor(0))
    }

    /**
     * Output tensor 0 must be the boxes tensor with shape [1, N, 4]
     * (normalized ymin/xmin/ymax/xmax per EfficientDet-Lite metadata).
     */
    private fun validateBoxesTensor(tensor: org.tensorflow.lite.Tensor): Int {
        val shape = tensor.shape()
        if (shape.size != 3 || shape[1] <= 0 || shape[2] != 4) {
            interpreter.close()
            throw IllegalStateException(
                "Unexpected model output tensor shape ${shape.toList()}; " +
                    "expected [1, N, 4] boxes as first output"
            )
        }
        return shape[1]
    }

    fun detect(inputBuffer: ByteBuffer, confidenceThreshold: Float): List<Detection> {
        synchronized(inferenceLock) {
            if (isClosed) return emptyList()

            val boxes = Array(1) { Array(maxModelDetections) { FloatArray(4) } }
            val classes = Array(1) { FloatArray(maxModelDetections) }
            val scores = Array(1) { FloatArray(maxModelDetections) }
            val count = FloatArray(1)

            interpreter.runForMultipleInputsOutputs(
                arrayOf(inputBuffer),
                mapOf(0 to boxes, 1 to classes, 2 to scores, 3 to count)
            )

            val numDetections = count[0].toInt().coerceAtMost(maxModelDetections)

            Log.d("DetectionModule", "Raw detections: $numDetections")

            return (0 until numDetections)
                .asSequence()
                .filter { scores[0][it] >= confidenceThreshold }
                .filter { TARGET_LABELS.containsKey(classes[0][it].toInt() + 1) }
                .map { i ->
                    val classId = classes[0][i].toInt() + 1
                    Log.d("DetectionModule", "classId raw=${classes[0][i]} adjusted=$classId label=${TARGET_LABELS[classId]}")
                    Detection(
                        classId = classId,
                        className = TARGET_LABELS[classId]!!,
                        score = scores[0][i],
                        bbox = RectF(
                            boxes[0][i][1] * INPUT_SIZE,  // xmin
                            boxes[0][i][0] * INPUT_SIZE,  // ymin
                            boxes[0][i][3] * INPUT_SIZE,  // xmax
                            boxes[0][i][2] * INPUT_SIZE   // ymax
                        )
                    )
                }
                .sortedByDescending { it.score }
                .take(MAX_DETECTIONS)
                .toList()
        }
    }

    private fun loadModelFile(assets: AssetManager): MappedByteBuffer {
        val fd = assets.openFd("efficientdet-lite2-detection-metadata.tflite")
        val stream = FileInputStream(fd.fileDescriptor)
        val channel = stream.channel
        return channel.map(FileChannel.MapMode.READ_ONLY, fd.startOffset, fd.declaredLength)
    }

    /**
     * Releases the interpreter. Waits for any in-flight [detect] to complete
     * first, so native inference never runs against a closed interpreter.
     */
    fun close() {
        synchronized(inferenceLock) {
            if (!isClosed) {
                isClosed = true
                interpreter.close()
            }
        }
    }
}
