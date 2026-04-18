import cv2
import numpy as np
import os

# Try to import dnn_superres (requires opencv-contrib-python)
try:
    from cv2 import dnn_superres
    _HAS_SUPERRES = True
except ImportError:
    _HAS_SUPERRES = False


def _color_correction(img: np.ndarray) -> np.ndarray:
    """
    Apply per-channel CLAHE to correct color balance distortions
    introduced by frequency decoding errors.
    Works in LAB color space to fix luminance and chroma independently.
    """
    lab   = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # CLAHE on L channel only — preserves color while fixing contrast
    clahe   = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_fixed = clahe.apply(l)

    # Mild stretch on a and b channels to recover color saturation
    for ch in [a, b]:
        ch_min, ch_max = ch.min(), ch.max()
        if ch_max > ch_min:
            pass   # keep as-is; over-stretching chroma causes artifacts

    lab_fixed = cv2.merge([l_fixed, a, b])
    return cv2.cvtColor(lab_fixed, cv2.COLOR_LAB2BGR)


def _adaptive_denoise(img: np.ndarray) -> np.ndarray:
    """
    Two-stage denoising:
    Stage 1 — Fast NL-Means with conservative h values to remove pixel noise
               without destroying edge detail.
    Stage 2 — Bilateral filter to smooth flat regions while preserving edges.
    """
    # Stage 1: NL-Means (light settings — avoid over-smoothing)
    denoised = cv2.fastNlMeansDenoisingColored(
        img, None,
        h=5,           # luminance filter strength (was 7 — slightly lighter)
        hColor=5,      # color filter strength
        templateWindowSize=7,
        searchWindowSize=21
    )

    # Stage 2: Bilateral (sigma tuned for 192→768 upscaled images)
    denoised = cv2.bilateralFilter(denoised, d=9, sigmaColor=40, sigmaSpace=40)
    return denoised


def _unsharp_mask(img: np.ndarray, strength: float = 1.3, sigma: float = 1.2) -> np.ndarray:
    """
    Unsharp masking for controlled edge sharpening.
    strength=1.3 is conservative — avoids halo artifacts on already-noisy input.
    """
    blurred   = cv2.GaussianBlur(img, (0, 0), sigmaX=sigma)
    sharpened = cv2.addWeighted(img, strength, blurred, -(strength - 1.0), 0)
    return sharpened


def enhance_image(input_name: str) -> bool:
    try:
        base_dir    = os.path.dirname(os.path.abspath(__file__))
        model_path  = os.path.join(base_dir, "..", "Models", "EDSR_x4.pb")
        image_path  = os.path.join(base_dir, "..", "Outputs", input_name)
        output_path = os.path.join(base_dir, "..", "Outputs", "final_ai_image.png")

        if not os.path.exists(image_path):
            print(f"[ERROR] Image not found: {image_path}")
            return False

        img = cv2.imread(image_path)
        if img is None:
            print("[ERROR] Failed to read image.")
            return False

        # ── Step 0: Color correction BEFORE upscaling ────────────────────────
        # Fix LAB-space distortions first — more effective on small image
        img = _color_correction(img)
        print("Color correction applied.")

        # ── Step 1: Upscale 4× ───────────────────────────────────────────────
        upscaled = None

        if _HAS_SUPERRES and os.path.exists(model_path):
            try:
                sr = dnn_superres.DnnSuperResImpl_create()
                sr.readModel(model_path)
                sr.setModel("edsr", 4)
                upscaled = sr.upsample(img)
                print(f"EDSR x4: {img.shape[1]}x{img.shape[0]} → "
                      f"{upscaled.shape[1]}x{upscaled.shape[0]}")
            except Exception as e:
                print(f"[WARNING] EDSR failed ({e}), using Lanczos fallback.")
                upscaled = None

        if upscaled is None:
            h, w     = img.shape[:2]
            upscaled = cv2.resize(img, (w * 4, h * 4),
                                  interpolation=cv2.INTER_LANCZOS4)
            print(f"Lanczos x4: {w}x{h} → {upscaled.shape[1]}x{upscaled.shape[0]}")

        # ── Step 2: Adaptive denoise (light — preserve detail) ───────────────
        denoised = _adaptive_denoise(upscaled)
        print("Denoising done.")

        # ── Step 3: Unsharp mask (controlled sharpening) ─────────────────────
        sharpened = _unsharp_mask(denoised, strength=1.3, sigma=1.2)
        print("Sharpening done.")

        # ── Step 4: Final color pass in LAB (recover any saturation lost) ────
        final = _color_correction(sharpened)

        cv2.imwrite(output_path, final)
        print(f"SUCCESS: Final image {final.shape[1]}x{final.shape[0]} saved.")
        return True

    except Exception as e:
        print(f"[CRITICAL ERROR] Enhancer failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    enhance_image("received_raw.png")