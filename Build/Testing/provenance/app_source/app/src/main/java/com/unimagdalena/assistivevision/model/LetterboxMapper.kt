package com.unimagdalena.assistivevision.model

/**
 * Pure letterbox geometry shared by the forward path (bitmap → model input,
 * in [PreprocessingModule]) and the inverse path (model output → frame
 * coordinates), so both always use identical math.
 */
object LetterboxMapper {

    /**
     * @param scale     uniform scale applied to the source content
     * @param dx        left padding of the content inside the model input
     * @param dy        top padding of the content inside the model input
     * @param dstWidth  content width after scaling (floored, as drawn)
     * @param dstHeight content height after scaling (floored, as drawn)
     */
    data class Geometry(
        val scale: Float,
        val dx: Float,
        val dy: Float,
        val dstWidth: Int,
        val dstHeight: Int
    )

    /**
     * Forward geometry for letterboxing a [srcWidth]×[srcHeight] frame into an
     * [inputSize]×[inputSize] model input with gray padding.
     */
    fun forward(srcWidth: Int, srcHeight: Int, inputSize: Int): Geometry {
        require(srcWidth > 0 && srcHeight > 0 && inputSize > 0) {
            "letterbox requires positive dimensions (src=$srcWidth×$srcHeight, input=$inputSize)"
        }
        val scale = minOf(inputSize.toFloat() / srcWidth, inputSize.toFloat() / srcHeight)
        val dstWidth = (srcWidth * scale).toInt()
        val dstHeight = (srcHeight * scale).toInt()
        val dx = (inputSize - dstWidth) / 2
        val dy = (inputSize - dstHeight) / 2
        return Geometry(scale, dx.toFloat(), dy.toFloat(), dstWidth, dstHeight)
    }

    /**
     * Inverse of [forward] for a single coordinate: maps a model-input
     * coordinate back to the source frame. Uses the exact drawn content size
     * (floored [Geometry.dstWidth]/[Geometry.dstHeight]) so the mapping is
     * consistent with the pixels that were actually sent to the model.
     */
    fun toFrameX(modelX: Float, geometry: Geometry, srcWidth: Int): Float =
        (modelX - geometry.dx) * srcWidth / geometry.dstWidth.toFloat()

    fun toFrameY(modelY: Float, geometry: Geometry, srcHeight: Int): Float =
        (modelY - geometry.dy) * srcHeight / geometry.dstHeight.toFloat()
}
