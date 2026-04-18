import cv2
import numpy as np
from scipy.io import wavfile
import os
import glob

# ── Parameters — must match decoder exactly ───────────────────────────────────
SAMPLE_RATE    = 44100
IMG_SIZE       = 192
PIXEL_DURATION = 0.002       # 88 samples/pixel (doubled for better Hilbert accuracy)
FREQ_MIN       = 1000.0      # Widened band: was 1500
FREQ_MAX       = 3400.0      # Widened band: was 2300 → now 2400 Hz range = ~9.4 Hz/level
SYNC_FREQ      = 600.0       # Sync well outside image band to avoid false triggers
SYNC_DURATION  = 0.015       # 661 samples — longer for rock-solid detection
GUARD_DURATION = 0.001       # 44 samples guard between B/G/R channels (kills boundary bleed)
GAMMA          = 0.75        # Slightly lower gamma for better mid-tone distribution
# ─────────────────────────────────────────────────────────────────────────────


def get_first_image():
    base_dir     = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(base_dir, "..", "Inputs")
    for ext in ("*.png", "*.jpg", "*.jpeg"):
        files = glob.glob(os.path.join(input_folder, ext))
        if files:
            return os.path.basename(files[0])
    return None


def pixel_to_freq(pixel_value: int) -> float:
    """Map pixel 0-255 → frequency with gamma pre-correction."""
    normalized = (pixel_value / 255.0) ** GAMMA
    return FREQ_MIN + normalized * (FREQ_MAX - FREQ_MIN)


def image_to_audio(image_name=None):
    base_dir = os.path.dirname(os.path.abspath(__file__))

    if image_name is None:
        image_name = get_first_image()
        if not image_name:
            print("[ERROR] No image found in Inputs folder.")
            return False

    input_path  = os.path.join(base_dir, "..", "Inputs",  image_name)
    output_path = os.path.join(base_dir, "..", "Outputs", "signal.wav")

    img = cv2.imread(input_path)
    if img is None:
        print(f"[ERROR] Cannot read image: {input_path}")
        return False

    img = cv2.resize(img, (IMG_SIZE, IMG_SIZE), interpolation=cv2.INTER_AREA)
    print(f"Encoding: {image_name} -> {IMG_SIZE}x{IMG_SIZE} ...")

    pixel_samples = int(SAMPLE_RATE * PIXEL_DURATION)
    sync_samples  = int(SAMPLE_RATE * SYNC_DURATION)
    guard_samples = int(SAMPLE_RATE * GUARD_DURATION)

    # ── Build frequency array for the entire signal ───────────────────────────
    # Layout per row: [sync | B_pixels | guard | G_pixels | guard | R_pixels]
    samples_per_row = sync_samples + IMG_SIZE * 3 * pixel_samples + 2 * guard_samples
    total_samples   = IMG_SIZE * samples_per_row
    freq_arr        = np.empty(total_samples, dtype=np.float64)

    GUARD_FREQ = (FREQ_MIN + FREQ_MAX) / 2.0   # Neutral mid-range guard tone

    pos = 0
    for row in img:
        # Sync pulse
        freq_arr[pos : pos + sync_samples] = SYNC_FREQ
        pos += sync_samples

        # B, G, R channels with guard intervals between them
        for ch in range(3):
            for pixel_val in row[:, ch]:
                f = pixel_to_freq(int(pixel_val))
                freq_arr[pos : pos + pixel_samples] = f
                pos += pixel_samples

            # Guard interval after B and G (not after R — row ends there)
            if ch < 2:
                freq_arr[pos : pos + guard_samples] = GUARD_FREQ
                pos += guard_samples

    # ── Phase-continuous synthesis ────────────────────────────────────────────
    omega = 2.0 * np.pi * freq_arr / SAMPLE_RATE
    phase = np.cumsum(omega)
    audio = np.sin(phase).astype(np.float32)

    # Normalize to [-1, 1]
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio /= max_val

    wavfile.write(output_path, SAMPLE_RATE, audio)
    duration = len(audio) / SAMPLE_RATE
    print(f"Success: {duration:.1f}s audio written to {output_path}")
    return True


if __name__ == "__main__":
    image_to_audio()