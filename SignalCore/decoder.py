import numpy as np
import cv2
from scipy.io import wavfile
import os

def audio_to_image(audio_name):
    audio_path = os.path.join('../Outputs', audio_name)
    output_image_path = os.path.join('../Outputs', 'received_raw.png')

    sample_rate, data = wavfile.read(audio_path)
    pixel_duration = 0.005 
    samples_per_pixel = int(sample_rate * pixel_duration)
    
    pixels = []
    for i in range(0, len(data), samples_per_pixel):
        chunk = data[i:i + samples_per_pixel]
        if len(chunk) < samples_per_pixel: break
        fft_data = np.abs(np.fft.rfft(chunk))
        freq = np.fft.rfftfreq(len(chunk), 1/sample_rate)[np.argmax(fft_data)]
        pixels.append(np.clip(int(((freq - 1500) / 1000) * 255), 0, 255))

    # دمج القنوات الثلاث (16384 بكسل لكل قناة)
    total_pixels = 128 * 128
    if len(pixels) >= total_pixels * 3:
        b = np.array(pixels[:total_pixels]).reshape((128, 128))
        g = np.array(pixels[total_pixels:total_pixels*2]).reshape((128, 128))
        r = np.array(pixels[total_pixels*2:total_pixels*3]).reshape((128, 128))
        
        img_color = cv2.merge([b, g, r]).astype(np.uint8)
        cv2.imwrite(output_image_path, img_color)
        print("Success: Full Color image reconstructed.")
    else:
        print("Error: Audio data incomplete for color reconstruction.")

if __name__ == "__main__":
    audio_to_image('signal.wav')