import numpy as np
import cv2
from scipy.io import wavfile
import os

def audio_to_image(audio_name):
    # مسارات الملفات
    audio_path = os.path.join('../Outputs', audio_name)
    output_image_path = os.path.join('../Outputs', 'received_raw.png')

    # 1. قراءة ملف الصوت
    sample_rate, data = wavfile.read(audio_path)
    
    pixel_duration = 0.005 # نفس المدة المستخدمة في التشفير
    samples_per_pixel = int(sample_rate * pixel_duration)
    
    # 2. تحليل الإشارة لاستعادة البكسلات
    pixels = []
    print("Decoding: Converting sound back to pixels...")

    for i in range(0, len(data), samples_per_pixel):
        chunk = data[i:i + samples_per_pixel]
        if len(chunk) < samples_per_pixel:
            break
        
        # استخدام FFT لمعرفة التردد السائد في هذا الجزء من الصوت
        fft_data = np.abs(np.fft.rfft(chunk))
        freq = np.fft.rfftfreq(len(chunk), 1/sample_rate)[np.argmax(fft_data)]
        
        # تحويل التردد إلى قيمة بكسل (0-255)
        pixel_val = int(((freq - 1500) / 1000) * 255)
        pixel_val = np.clip(pixel_val, 0, 255)
        pixels.append(pixel_val)

    # 3. إعادة تشكيل المصفوفة (بناء الصورة 64x64)
    if len(pixels) >= 4096:
        img_array = np.array(pixels[:4096]).reshape((64, 64)).astype(np.uint8)
        cv2.imwrite(output_image_path, img_array)
        print(f"Success! Raw image saved in Outputs as received_raw.png")
    else:
        print("Error: Not enough audio data to reconstruct the image.")

if __name__ == "__main__":
    audio_to_image('signal.wav')