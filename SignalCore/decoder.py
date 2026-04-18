import numpy as np
import cv2
from scipy.io import wavfile
from scipy.signal import hilbert
import os

# ── Parameters — must match encoder exactly ───────────────────────────────────
SAMPLE_RATE    = 44100
IMG_SIZE       = 192
PIXEL_DURATION = 0.002       # Must match encoder
FREQ_MIN       = 1000.0      # Must match encoder
FREQ_MAX       = 3400.0      # Must match encoder
SYNC_FREQ      = 600.0       # Must match encoder
SYNC_DURATION  = 0.015       # Must match encoder
GUARD_DURATION = 0.001       # Must match encoder
GAMMA          = 0.75        # Must match encoder
SYNC_TOLERANCE = 80          # Hz — tighter now that sync is far from image band
# ─────────────────────────────────────────────────────────────────────────────


def compute_instantaneous_freq(signal: np.ndarray, sr: int) -> np.ndarray:
    """
    Compute instantaneous frequency for every sample using the Hilbert transform.

    Unlike FFT (which needs ~1000 samples for 1 Hz resolution), this approach
    measures frequency accurately even with short chunks, making it ideal
    for SSTV pixel decoding.

    Returns array of length len(signal)-1 with frequency in Hz at each sample.
    """
    signal   = signal - np.mean(signal)           # remove DC offset
    analytic = hilbert(signal)
    phase    = np.unwrap(np.angle(analytic))
    inst_freq = np.diff(phase) / (2.0 * np.pi) * sr
    # Clamp extreme outliers from Hilbert edge artifacts
    inst_freq = np.clip(inst_freq, FREQ_MIN - 200, FREQ_MAX + 200)
    return inst_freq.astype(np.float32)


def freq_to_pixel(freq: float) -> int:
    """
    Inverse map: frequency → pixel value.
    Applies inverse gamma to match encoder's gamma pre-correction.
    """
    normalized = (freq - FREQ_MIN) / (FREQ_MAX - FREQ_MIN)
    normalized = float(np.clip(normalized, 0.0, 1.0))
    # Inverse gamma: encoder did pixel^gamma → frequency,
    # so decoder does: normalized^(1/gamma) → pixel
    pixel = (normalized ** (1.0 / GAMMA)) * 255.0
    return int(np.clip(round(pixel), 0, 255))


def trimmed_mean_freq(inst_freq: np.ndarray, start: int, n_samples: int) -> float:
    """
    Extract the trimmed-mean instantaneous frequency for a chunk of n_samples.
    Trims 25% from each side to reject edge transients, then uses mean
    (more stable than median for Gaussian noise profiles).
    """
    end    = start + n_samples - 1            # inst_freq is 1 shorter than signal
    margin = max(2, n_samples // 4)           # trim 25% each side
    chunk  = inst_freq[start + margin : end - margin]
    if len(chunk) == 0:
        chunk = inst_freq[start:end]
    if len(chunk) == 0:
        return (FREQ_MIN + FREQ_MAX) / 2.0

    # Trimmed mean: sort and remove top/bottom 10% of what remains
    sorted_chunk = np.sort(chunk)
    extra_trim   = max(1, len(sorted_chunk) // 10)
    trimmed      = sorted_chunk[extra_trim : -extra_trim] if len(sorted_chunk) > 2 * extra_trim else sorted_chunk
    return float(np.mean(trimmed))


def find_sync_sample_accurate(inst_freq: np.ndarray, sync_samples: int, row_samples: int) -> int:
    """
    Two-pass sync detection:
    Pass 1 — coarse scan at sync_samples//4 steps to find approximate location.
    Pass 2 — fine scan ±step around best candidate at 1-sample resolution.
    Returns sample index of sync start.
    """
    scan_step    = max(1, sync_samples // 4)
    search_limit = min(len(inst_freq) - sync_samples, row_samples * 2)

    best_score   = float('inf')
    best_pos     = 0

    # Pass 1: coarse
    for probe in range(0, search_limit, scan_step):
        f     = trimmed_mean_freq(inst_freq, probe, sync_samples)
        score = abs(f - SYNC_FREQ)
        if score < best_score:
            best_score = score
            best_pos   = probe
        if score < 10:
            break   # Tight enough — stop early

    # Pass 2: fine (±step at 1-sample resolution)
    refine_start = max(0, best_pos - scan_step)
    refine_end   = min(len(inst_freq) - sync_samples, best_pos + scan_step)
    for probe in range(refine_start, refine_end):
        f     = trimmed_mean_freq(inst_freq, probe, sync_samples)
        score = abs(f - SYNC_FREQ)
        if score < best_score:
            best_score = score
            best_pos   = probe

    print(f"Sync locked at sample {best_pos} (freq error: {best_score:.1f} Hz)")
    return best_pos


def audio_to_image(audio_name: str) -> bool:
    base_dir    = os.path.dirname(os.path.abspath(__file__))
    audio_path  = os.path.join(base_dir, "..", "Inputs",  audio_name)
    output_path = os.path.join(base_dir, "..", "Outputs", "received_raw.png")

    if not os.path.exists(audio_path):
        print(f"[ERROR] Audio not found: {audio_path}")
        return False

    sr, data = wavfile.read(audio_path)

    # Normalise to float32 in [-1, 1]
    if data.dtype != np.float32:
        data = data.astype(np.float64)
        m    = np.max(np.abs(data))
        if m > 0:
            data = (data / m)
    data = data.astype(np.float32)

    sync_samples  = int(sr * SYNC_DURATION)
    pixel_samples = int(sr * PIXEL_DURATION)
    guard_samples = int(sr * GUARD_DURATION)
    row_samples   = sync_samples + IMG_SIZE * 3 * pixel_samples + 2 * guard_samples

    print("Computing instantaneous frequency (Hilbert transform) ...")
    inst_freq = compute_instantaneous_freq(data, sr)

    # ── Locate first sync pulse (sample-accurate two-pass) ───────────────────
    start_offset = find_sync_sample_accurate(inst_freq, sync_samples, row_samples)

    print(f"Decoding {IMG_SIZE} rows ...")

    # ── Decode row by row at fixed offsets ────────────────────────────────────
    image = []

    for row_idx in range(IMG_SIZE):
        row_start = start_offset + row_idx * row_samples

        # Skip sync pulse, land on first pixel
        pixel_start = row_start + sync_samples

        if pixel_start + IMG_SIZE * 3 * pixel_samples + 2 * guard_samples > len(inst_freq):
            print(f"[WARNING] Audio ended at row {row_idx}. Padding with zeros.")
            break

        # ── Optional sync health check ────────────────────────────────────────
        sync_f = trimmed_mean_freq(inst_freq, row_start, sync_samples)
        if abs(sync_f - SYNC_FREQ) > SYNC_TOLERANCE * 2:
            print(f"[WARNING] Row {row_idx}: expected sync {SYNC_FREQ} Hz, got {sync_f:.0f} Hz")

        # ── Decode pixels for this row ────────────────────────────────────────
        row_pixels = []
        pos        = pixel_start

        for ch in range(3):
            for _ in range(IMG_SIZE):
                freq = trimmed_mean_freq(inst_freq, pos, pixel_samples)
                row_pixels.append(freq_to_pixel(freq))
                pos += pixel_samples

            # Skip guard interval between channels
            if ch < 2:
                pos += guard_samples

        # Layout: B[0..191] G[192..383] R[384..575]
        b = np.array(row_pixels[0          : IMG_SIZE    ], dtype=np.uint8)
        g = np.array(row_pixels[IMG_SIZE   : IMG_SIZE * 2], dtype=np.uint8)
        r = np.array(row_pixels[IMG_SIZE*2 : IMG_SIZE * 3], dtype=np.uint8)

        row_img = np.stack([b, g, r], axis=1)   # shape (192, 3) — BGR order for cv2
        image.append(row_img)

    if len(image) == 0:
        print("[ERROR] No rows decoded.")
        return False

    # Pad incomplete images
    img = np.array(image, dtype=np.uint8)
    if img.shape[0] < IMG_SIZE:
        pad = np.zeros((IMG_SIZE - img.shape[0], IMG_SIZE, 3), dtype=np.uint8)
        img = np.vstack([img, pad])

    cv2.imwrite(output_path, img)
    print(f"Success: {img.shape[0]}x{img.shape[1]} raw image saved.")
    return True


if __name__ == "__main__":
    audio_to_image("signal.wav")