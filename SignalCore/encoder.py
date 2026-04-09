import cv2
import numpy as np
from scipy.io import wavfile
import os

def generate_tone(frequency, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration))
    return np.sin(2 * np.pi * frequency * t)

def image_to_audio(image_name):
    # مسارات الملفات
    input_path = os.path.join('../Inputs', image_name)
    output_audio_path = os.path.join('../Outputs', 'signal.wav')

    # 1. قراءة الصورة
    img = cv2.imread(input_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        print(f"Error: {image_name} not found in Inputs folder.")
        return
    
    # تصغير الصورة (64x64) لضمان صوت قصير جداً
    img_resized = cv2.resize(img, (64, 64))
    
    sample_rate = 44100
    pixel_duration = 0.005 # زمن البكسل
    audio_signal = []

    print("Encoding: Converting pixels to sound...")

    # 2. التشفير
    for row in img_resized:
        for pixel in row:
            freq = 1500 + (pixel / 255.0) * 1000
            tone = generate_tone(freq, pixel_duration, sample_rate)
            audio_signal.extend(tone)

    # 3. الحفظ في المخرجات
    wavfile.write(output_audio_path, sample_rate, np.array(audio_signal).astype(np.float32))
    
    print(f"Done! Audio saved in Outputs as signal.wav")
    print(f"Audio Duration: {len(audio_signal)/sample_rate:.2f} seconds")

if __name__ == "__main__":
    # نحدد اسم الصورة الموجودة داخل مجلد Inputs
    image_to_audio('test.png')