#!/usr/bin/env python3
"""KA PHONE APK Builder - Creates WebView wrapper template for Android."""
import json
from pathlib import Path

BASE = Path(__file__).parent.absolute()
with open(BASE / "config.json") as f: CFG = json.load(f)

APP = "KA Phone"
PKG = CFG["mobile_android"]["package"]
VER = CFG["version"]

TD = BASE / "apk_template"
TD.mkdir(exist_ok=True)

(TD / "AndroidManifest.xml").write_text(
    f'<?xml version="1.0"?>\n<manifest xmlns:android="http://schemas.android.com/apk/res/android" package="{PKG}">\n'
    f'<uses-permission android:name="android.permission.INTERNET"/>\n'
    f'<uses-permission android:name="android.permission.CAMERA"/>\n'
    f'<uses-permission android:name="android.permission.RECORD_AUDIO"/>\n'
    f'<application android:label="{APP}" android:usesCleartextTraffic="true">\n'
    f'<activity android:name=".MainActivity" android:exported="true" android:configChanges="orientation|screenSize">\n'
    f'<intent-filter><action android:name="android.intent.action.MAIN"/><category android:name="android.intent.category.LAUNCHER"/></intent-filter>\n'
    f'</activity></application></manifest>\n', encoding="utf-8")

JD = TD / "java" / "ai" / "harmonic" / "kaphone"
JD.mkdir(parents=True, exist_ok=True)
(JD / "MainActivity.java").write_text(
    'package ai.harmonic.kaphone;\n'
    'import android.app.Activity;\nimport android.os.Bundle;\n'
    'import android.webkit.{WebView,WebViewClient,WebSettings};\n'
    'public class MainActivity extends Activity {\n'
    '  WebView w;\n'
    '  @Override protected void onCreate(Bundle s) {\n'
    '    super.onCreate(s);\n'
    '    w=new WebView(this);setContentView(w);\n'
    '    WebSettings ws=w.getSettings();\n'
    '    ws.setJavaScriptEnabled(true);ws.setDomStorageEnabled(true);\n'
    '    ws.setCacheMode(WebSettings.LOAD_DEFAULT);\n'
    '    w.setWebViewClient(new WebViewClient());\n'
    '    w.loadUrl("http://localhost:8900");\n'
    '  }\n'
    '  @Override public void onBackPressed() {\n'
    '    if(w!=null&&w.canGoBack())w.goBack();else super.onBackPressed();\n'
    '  }\n'
    '}\n', encoding="utf-8")

(TD / "build_info.json").write_text(json.dumps({"app":APP,"pkg":PKG,"ver":VER,"mode":"webview"}, indent=2))

print(f"[OK] Template: {TD}")
print(f"Build: Android Studio > Open {TD} > Generate APK")
print(f"Or PWA install: Chrome > Menu > Installer")