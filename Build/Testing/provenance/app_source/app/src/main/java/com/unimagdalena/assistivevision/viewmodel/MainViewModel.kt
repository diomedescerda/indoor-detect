package com.unimagdalena.assistivevision.viewmodel

import android.app.Application
import android.content.Context
import android.graphics.Bitmap
import android.graphics.RectF
import android.os.Handler
import android.os.Looper
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.viewModelScope
import com.unimagdalena.assistivevision.R
import com.unimagdalena.assistivevision.data.SettingsManager
import com.unimagdalena.assistivevision.model.Detection
import com.unimagdalena.assistivevision.model.FrameStore
import com.unimagdalena.assistivevision.model.LetterboxMapper
import com.unimagdalena.assistivevision.model.LocalizedLabels
import com.unimagdalena.assistivevision.model.SpeechFormatter
import com.unimagdalena.assistivevision.modules.AudioModule
import com.unimagdalena.assistivevision.modules.DetectionModule
import com.unimagdalena.assistivevision.modules.LocalizationModule
import com.unimagdalena.assistivevision.modules.PreprocessingModule
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val settings = SettingsManager(application)

    private lateinit var preprocessingModule: PreprocessingModule
    private lateinit var detectionModule: DetectionModule
    private val localizationModule = LocalizationModule()
    private lateinit var audioModule: AudioModule
    private lateinit var appContext: Context

    /** Owns the latest camera frame; swap/copy/recycle are lock-serialized. */
    private val frameStore = FrameStore()

    private val _detectionCount = MutableLiveData(0)
    val detectionCount: LiveData<Int> = _detectionCount

    private val _zoneLabel = MutableLiveData("")
    val zoneLabel: LiveData<String> = _zoneLabel

    private val _detections = MutableLiveData<List<Detection>>(emptyList())
    val detections: LiveData<List<Detection>> = _detections

    private val _frameSize = MutableLiveData<Pair<Int, Int>>(0 to 0)
    val frameSize: LiveData<Pair<Int, Int>> = _frameSize

    private val _showPreview = MutableLiveData(true)
    val showPreview: LiveData<Boolean> = _showPreview

    private val _isCapturing = MutableLiveData(false)
    val isCapturing: LiveData<Boolean> = _isCapturing

    private val _frozenFrame = MutableLiveData<Bitmap?>(null)
    val frozenFrame: LiveData<Bitmap?> = _frozenFrame

    /** True when the TTS engine failed to initialise and voice output is unavailable. */
    private val _speechUnavailable = MutableLiveData(false)
    val speechUnavailable: LiveData<Boolean> = _speechUnavailable

    private val _confidence = MutableStateFlow(0.30f)
    private val _maxObjects = MutableStateFlow(2)

    private val pipelineMutex = Mutex()

    /** Safety net: releases the frozen frame if TTS never reports completion. */
    private val watchdog = Handler(Looper.getMainLooper())
    private val watchdogRunnable = Runnable { unfreeze() }

    init {
        appContext = application
        preprocessingModule = PreprocessingModule()
        detectionModule = DetectionModule(application)
        audioModule = AudioModule(application)
        audioModule.listener = object : AudioModule.Listener {
            override fun onReady() {
                _speechUnavailable.postValue(false)
            }

            override fun onDone() = unfreeze()

            override fun onError() {
                _speechUnavailable.postValue(true)
                unfreeze()
            }
        }

        viewModelScope.launch {
            settings.confidence.collect { _confidence.value = it }
        }
        viewModelScope.launch {
            settings.maxObjects.collect { _maxObjects.value = it }
        }
        viewModelScope.launch {
            settings.showPreview.collect { _showPreview.postValue(it) }
        }
        viewModelScope.launch {
            settings.language.collect { audioModule.setLanguage(it) }
        }
        viewModelScope.launch {
            settings.speechRate.collect { audioModule.setSpeechRate(it) }
        }
    }

    fun processFrame(bitmap: Bitmap) {
        frameStore.update(bitmap)
        _frameSize.postValue(bitmap.width to bitmap.height)
    }

    fun captureFrame() {
        if (_isCapturing.value == true) return
        if (_frozenFrame.value != null) return
        // The store hands out an isolated copy, so the camera thread may
        // recycle the original frame while the pipeline still runs.
        val frozen = frameStore.copy() ?: return
        _isCapturing.postValue(true)
        _frozenFrame.postValue(frozen)
        runPipeline(frozen)
    }

    private fun runPipeline(bitmap: Bitmap) {
        val confidence = _confidence.value
        val maxObjects = _maxObjects.value
        val frameWidth = bitmap.width
        val frameHeight = bitmap.height

        viewModelScope.launch(Dispatchers.Default) {
            if (!pipelineMutex.tryLock()) return@launch
            try {
                val tensor = preprocessingModule.preprocess(bitmap)
                val detections = detectionModule.detect(tensor, confidence)
                val limited = detections.take(maxObjects)
                val inFrame = limited.map { toFrameCoordinates(it, frameWidth, frameHeight) }
                val localized = localizationModule.localize(inFrame, frameWidth, frameHeight)

                _detectionCount.postValue(localized.size)
                _detections.postValue(localized)

                if (localized.isNotEmpty()) {
                    val top = localized.first()
                    _zoneLabel.postValue(
                        "${LocalizedLabels.classLabel(appContext, top.classId)} · " +
                            LocalizedLabels.zoneShortLabel(appContext, top.zone)
                    )
                    val started = audioModule.speak(buildUtterance(localized))
                    if (started) armWatchdog() else unfreeze()
                } else {
                    _zoneLabel.postValue(appContext.getString(R.string.no_detections))
                    unfreeze()
                }
            } finally {
                _isCapturing.postValue(false)
                pipelineMutex.unlock()
            }
        }
    }

    private fun unfreeze() {
        disarmWatchdog()
        _frozenFrame.postValue(null)
        _detections.postValue(emptyList())
        _zoneLabel.postValue(appContext.getString(R.string.status_ready))
    }

    /**
     * Fallback in case the TTS engine never delivers onDone/onError (e.g. the
     * engine process was killed); without it the frozen frame and capture
     * button would stay stuck forever.
     */
    private fun armWatchdog() {
        watchdog.removeCallbacks(watchdogRunnable)
        watchdog.postDelayed(watchdogRunnable, SPEECH_TIMEOUT_MS)
    }

    private fun disarmWatchdog() {
        watchdog.removeCallbacks(watchdogRunnable)
    }

    private fun toFrameCoordinates(detection: Detection, frameWidth: Int, frameHeight: Int): Detection {
        val geometry = LetterboxMapper.forward(frameWidth, frameHeight, DetectionModule.INPUT_SIZE)
        return detection.copy(
            bbox = RectF(
                LetterboxMapper.toFrameX(detection.bbox.left, geometry, frameWidth)
                    .coerceIn(0f, frameWidth.toFloat()),
                LetterboxMapper.toFrameY(detection.bbox.top, geometry, frameHeight)
                    .coerceIn(0f, frameHeight.toFloat()),
                LetterboxMapper.toFrameX(detection.bbox.right, geometry, frameWidth)
                    .coerceIn(0f, frameWidth.toFloat()),
                LetterboxMapper.toFrameY(detection.bbox.bottom, geometry, frameHeight)
                    .coerceIn(0f, frameHeight.toFloat())
            )
        )
    }

    private fun buildUtterance(localized: List<Detection>): String {
        val spoken = localized.map { detection ->
            LocalizedLabels.classWithArticle(appContext, detection.classId) to
                LocalizedLabels.zoneLabel(appContext, detection.zone)
        }
        val connectors = LocalizedLabels.speechConnectors(appContext)
        return SpeechFormatter.announce(
            spoken,
            connectors.thereIs,
            connectors.alsoThereIs,
            connectors.and,
        )
    }

    override fun onCleared() {
        super.onCleared()
        watchdog.removeCallbacks(watchdogRunnable)
        audioModule.shutdown()
        detectionModule.close()
        frameStore.clear()
    }

    private companion object {
        /** Generous upper bound for one announcement at the slowest speech rate. */
        const val SPEECH_TIMEOUT_MS = 20_000L
    }
}