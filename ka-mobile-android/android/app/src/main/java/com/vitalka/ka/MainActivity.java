package com.vitalka.ka;

import android.os.Bundle;

import com.getcapacitor.BridgeActivity;
import com.getcapacitor.community.speechrecognition.SpeechRecognition;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(SpeechRecognition.class);
        super.onCreate(savedInstanceState);
    }
}
