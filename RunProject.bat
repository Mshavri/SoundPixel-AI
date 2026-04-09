@echo off
title SoundPixel-AI Master System
cls

echo =====================================================
echo           SOUNDPIXEL-AI: SYSTEM START
echo =====================================================

:: 1. Clean Output Folder
echo [1/5] Cleaning old results...
if exist Outputs (
    del /q Outputs\*
)
echo Done.

:: 2. Run Encoder (Image to Sound)
echo.
echo [2/5] Running Encoder: Image to Sound...
cd SignalCore
python encoder.py
cd ..

:: 3. Run Decoder (Sound to Image)
echo.
echo [3/5] Running Decoder: Sound back to Image...
cd SignalCore
python decoder.py
cd ..

:: 4. Run AI Enhancer
echo.
echo [4/5] Running AI: Enhancing Image Quality...
cd AIEnhancer
python enhancer.py
cd ..

:: 5. Run Analyzer
echo.
echo [5/5] Running Final Analysis...
python analyzer.py

echo.
echo =====================================================
echo         PROCESS FINISHED: CHECK OUTPUTS FOLDER
echo =====================================================
pause