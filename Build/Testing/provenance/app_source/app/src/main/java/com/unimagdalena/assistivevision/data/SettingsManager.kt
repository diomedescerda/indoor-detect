package com.unimagdalena.assistivevision.data

import android.content.Context
import androidx.datastore.core.DataStore
import androidx.datastore.preferences.core.Preferences
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.floatPreferencesKey
import androidx.datastore.preferences.core.intPreferencesKey
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

val Context.dataStore: DataStore<Preferences> by preferencesDataStore(name = "settings")

class SettingsManager(private val context: Context) {

    companion object {
        val LANGUAGE          = stringPreferencesKey("language")
        val CONFIDENCE        = floatPreferencesKey("confidence")
        val MAX_OBJECTS       = intPreferencesKey("max_objects")
        val SHOW_PREVIEW      = booleanPreferencesKey("show_preview")
        val SPEECH_RATE       = floatPreferencesKey("speech_rate")
    }

    val language: Flow<String>  = context.dataStore.data.map { it[LANGUAGE] ?: "es" }
    val confidence: Flow<Float> = context.dataStore.data.map { it[CONFIDENCE] ?: 0.30f }
    val maxObjects: Flow<Int>   = context.dataStore.data.map { it[MAX_OBJECTS] ?: 2 }
    val showPreview: Flow<Boolean>     = context.dataStore.data.map { it[SHOW_PREVIEW] ?: true }
    val speechRate: Flow<Float>        = context.dataStore.data.map { it[SPEECH_RATE] ?: 1.0f }

    suspend fun setLanguage(value: String)         { context.dataStore.edit { it[LANGUAGE] = value } }
    suspend fun setConfidence(value: Float)         { context.dataStore.edit { it[CONFIDENCE] = value } }
    suspend fun setMaxObjects(value: Int)           { context.dataStore.edit { it[MAX_OBJECTS] = value } }
    suspend fun setShowPreview(value: Boolean)      { context.dataStore.edit { it[SHOW_PREVIEW] = value } }
    suspend fun setSpeechRate(value: Float)         { context.dataStore.edit { it[SPEECH_RATE] = value } }
}
