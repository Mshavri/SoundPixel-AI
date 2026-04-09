import cv2
import numpy as np
from scipy.io import wavfile
import os

def generate_tone(frequency, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration))
    return np.sin(2 * np.pi * frequency * t)

def image_to_audio(image_name):
    input_path = os.path.join('../Inputs', image_name)
    output_audio_path = os.path.join('../Outputs', 'signal.wav')

    img = cv2.imread(input_path) # قراءة بالألوان
    if img is None: return
    
    img_resized = cv2.resize(img, (128, 128))
    sample_rate = 44100
    pixel_duration = 0.005 
    audio_signal = []

    print("Encoding Color Channels (R, G, B)... This will take more time.")

    # تشفير قنوات الألوان بالتسلسل
    for channel in range(3): # 0: Blue, 1: Green, 2: Red
        for row in img_resized[:, :, channel]:
            for pixel in row:
                freq = 1500 + (pixel / 255.0) * 1000
                tone = generate_tone(freq, pixel_duration, sample_rate)
                audio_signal.extend(tone)

    wavfile.write(output_audio_path, sample_rate, np.array(audio_signal).astype(np.float32))
    print(f"Success: Full Color Audio saved. Duration: {len(audio_signal)/sample_rate:.2f}s")

if __name__ == "__main__":
    image_to_audio('test.png')