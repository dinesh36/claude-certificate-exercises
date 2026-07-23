package com.example.app

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

sealed class SettingsState {
    object Loading : SettingsState()
    data class Loaded(val darkModeEnabled: Boolean) : SettingsState()
}

class SettingsActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)
        findViewById<android.widget.TextView>(R.id.darkModeLabel).text =
            getString(R.string.darkModeLabel)
    }
}
