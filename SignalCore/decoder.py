import numpy as np
import cv2
from scipy.io import wavfile
import os

def audio_to_image(audio_name):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        audio_path = os.path.join(base_dir, "..", "Inputs", audio_name)
        output_image_path = os.path.join(base_dir, "..", "Outputs", "received_raw.png")

        if not os.path.exists(audio_path):
            print(f"[ERROR] Audio file not found at: {audio_path}")
            return False

        sample_rate, data = wavfile.read(audio_path)
        
        pixel_duration = 0.005 
        samples_per_pixel = int(sample_rate * pixel_duration)
        size = 128
        total_pixels_per_channel = size * size
        
        pixels = []
        print(f"Decoding: Reconstructing {size}x{size} color image...")

        for i in range(0, len(data), samples_per_pixel):
            chunk = data[i:i + samples_per_pixel]
            if len(chunk) < samples_per_pixel: break
            
            fft_data = np.abs(np.fft.rfft(chunk))
            freq = np.fft.rfftfreq(len(chunk), 1/sample_rate)[np.argmax(fft_data)]
            
            pixel_val = int(((freq - 1000) / 2000) * 255)
            pixels.append(np.clip(pixel_val, 0, 255))

        if len(pixels) >= total_pixels_per_channel * 3:
            b = np.array(pixels[:total_pixels_per_channel]).reshape((size, size))
            g = np.array(pixels[total_pixels_per_channel:total_pixels_per_channel*2]).reshape((size, size))
            r = np.array(pixels[total_pixels_per_channel*2:total_pixels_per_channel*3]).reshape((size, size))
            
            img_color = cv2.merge([b, g, r]).astype(np.uint8)
            cv2.imwrite(output_image_path, img_color)
            print("Success: Raw image saved.")
            return True
        else:
            print(f"[ERROR] Incomplete data. Got {len(pixels)} pixels, need {total_pixels_per_channel * 3}.")
            return False

    except Exception as e:
        print(f"[CRITICAL ERROR] Decoder failed: {e}")
        return False

if __name__ == "__main__":
    audio_to_image('signal.wav')