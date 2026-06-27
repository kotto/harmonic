# Harmonie AI ProGuard Rules
# Le moteur ABC est entièrement en Kotlin - pas de réflexion ni de sérialisation externe

# - Keep the engine package
-keep class com.harmonicai.android.engine.** { *; }

# - Keep the model classes used by the engine
-keep class com.harmonicai.android.engine.HarmonicSignature { *; }
-keep class com.harmonicai.android.engine.QuantumState { *; }
-keep class com.harmonicai.android.engine.HarmonicTemplate { *; }
-keep class com.harmonicai.android.engine.ResponseResult { *; }

# - Keep ViewModels
-keep class com.harmonicai.android.ui.MainViewModel { *; }
-keep class com.harmonicai.android.ui.ChatMessage { *; }
-keep class com.harmonicai.android.ui.StatsData { *; }

# - Keep data classes used with LiveData
-keepclassmembers class * {
    @androidx.lifecycle.LiveData <fields>;
}

# - Désactiver l'obfuscation pour le débogage
-dontobfuscate