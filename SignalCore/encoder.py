import cv2
import numpy as np
from scipy.io import wavfile
import os
import glob

def get_first_image():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(base_dir, "..", "Inputs")
    types = ('*.png', '*.jpg', '*.jpeg')
    files_found = []
    for t in types:
        files_found.extend(glob.glob(os.path.join(input_folder, t)))
    return os.path.basename(files_found[0]) if files_found else None

def image_to_audio(image_name=None):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        if image_name is None:
            image_name = get_first_image()
            if not image_name:
                print("[ERROR] No image found in Inputs folder.")
                return False
        
        input_path = os.path.join(base_dir, "..", "Inputs", image_name)
        output_audio_path = os.path.join(base_dir, "..", "Outputs", "signal.wav")

        if not os.path.exists(input_path):
            print(f"[ERROR] Image not found at: {input_path}")
            return False

        img = cv2.imread(input_path)
        
        if img is None:
            print(f"[ERROR] '{image_name}' is not a valid image.")
            return False

        print(f"Processing: {image_name}...")
        
        img_resized = cv2.resize(img, (128, 128))
        
        sample_rate = 44100
        pixel_duration = 0.005 
        audio_signal = []

        for channel in range(3):
            for row in img_resized[:, :, channel]:
                for pixel in row:
                    freq = 1000 + (pixel / 255.0) * 2000 
                    t = np.linspace(0, pixel_duration, int(sample_rate * pixel_duration))
                    tone = np.sin(2 * np.pi * freq * t)
                    audio_signal.extend(tone)

        wavfile.write(output_audio_path, sample_rate, np.array(audio_signal).astype(np.float32))
        print("Success: Audio generated.")
        return True

    except Exception as e:
        print(f"[CRITICAL ERROR] Encoder failed: {e}")
        return False

if __name__ == "__main__":
    image_to_audio()