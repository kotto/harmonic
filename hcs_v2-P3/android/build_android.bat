@echo off
echo 🌊 HCS V2 - Build Android 8K
echo ==================================
cd /d "%~dp0\android"

echo 📦 Vérification environnement Android...
if not defined ANDROID_HOME (
    echo ❌ ANDROID_HOME non défini
    echo 📦 Installez Android Studio et configurez ANDROID_HOME
    pause
    exit /b 1
)

echo 📦 Vérification Gradle...
if not exist "gradlew.bat" (
    echo ❌ gradlew.bat non trouvé
    echo 📦 Vérifiez que le projet Android est correctement configuré
    pause
    exit /b 1
)

echo 🚀 Nettoyage projet...
call gradlew clean

echo 📦 Téléchargement dépendances...
call gradlew dependencies

echo 🔨 Build Debug APK...
call gradlew assembleDebug

echo 📱 Build Release APK...
call gradlew assembleRelease

echo ✅ Build terminé !
echo 📱 APK Debug: android\app\build\outputs\apk\debug\app-debug.apk
echo 📱 APK Release: android\app\build\outputs\apk\release\app-release.apk

echo 🚀 Installation sur appareil connecté...
adb devices

echo 📱 Voulez-vous installer l'APK Debug ? (O/N)
set /p install="> "
if /i "%install%"=="O" (
    echo 📱 Installation APK Debug...
    adb install android\app\build\outputs\apk\debug\app-debug.apk
    echo ✅ Installation terminée !
)

echo 🌊 HCS V2 Android 8K prêt !
pause
