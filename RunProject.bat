@echo off
title SoundPixel-AI Auto System
cls

echo =====================================================
echo           SOUNDPIXEL-AI: AUTO DETECTION START
echo =====================================================

:: 1. Clean Output Folder
echo [1/5] Cleaning old results...
if exist Outputs (
    del /q Outputs\*
)
echo Done.

:: 2. Run Encoder (يتحقق تلقائياً من الصورة)
echo.
echo [2/5] Searching for image and Encoding...
cd SignalCore
python encoder.py
cd ..

:: 3. Run Decoder
echo.
echo [3/5] Running Decoder...
cd SignalCore
python decoder.py
cd ..

:: 4. Run AI Enhancer
echo.
echo [4/5] Running AI Enhancement...
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