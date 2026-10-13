package com.unimagdalena.assistivevision.modules

import android.graphics.Bitmap
import android.graphics.Canvas
import android.graphics.Color
import androidx.core.graphics.createBitmap
import androidx.core.graphics.scale
import com.unimagdalena.assistivevision.model.LetterboxMapper
import java.nio.ByteBuffer
import java.nio.ByteOrder

class PreprocessingModule(private val inputSize: Int = 448) {

    private val inputBuffer = ByteBuffer
        .allocateDirect(1 * inputSize * inputSize * 3)
        .order(ByteOrder.nativeOrder())

    fun preprocess(bitmap: Bitmap): ByteBuffer {
        inputBuffer.rewind()
        val resized = letterboxResize(bitmap)
        val pixels = IntArray(resized.width * resized.height)
        resized.getPixels(pixels, 0, resized.width, 0, 0, resized.width, resized.height)
        resized.recycle()
        for (pixel in pixels) {
            inputBuffer.put((pixel shr 16 and 0xFF).toByte()) // R
            inputBuffer.put((pixel shr 8 and 0xFF).toByte())  // G
            inputBuffer.put((pixel and 0xFF).toByte())        // B
        }
        return inputBuffer
    }

    private fun letterboxResize(bitmap: Bitmap): Bitmap {
        val geometry = LetterboxMapper.forward(bitmap.width, bitmap.height, inputSize)

        val output = createBitmap(inputSize, inputSize)
        val canvas = Canvas(output)
        canvas.drawColor(Color.rgb(114, 114, 114))
        val resized = bitmap.scale(geometry.dstWidth, geometry.dstHeight)
        canvas.drawBitmap(resized, geometry.dx, geometry.dy, null)
        resized.recycle()
        return output
    }
}
