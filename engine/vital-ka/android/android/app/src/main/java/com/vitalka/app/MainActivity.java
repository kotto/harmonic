package com.vitalka.app;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;
import com.getcapacitor.community.speechrecognition.SpeechRecognition;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        // Enregistrer les plugins natifs AVANT super.onCreate()
        registerPlugin(SpeechRecognition.class);
        super.onCreate(savedInstanceState);
    }
}
