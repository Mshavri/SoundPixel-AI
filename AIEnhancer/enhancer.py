"""
AIEnhancer/enhancer.py  —  SoundPixel-AI
=========================================
محسّن الصور — EDSR x4 عبر OpenCV dnn_superres
  Primary  : EDSR_x4.pb  (opencv-contrib-python)
  Fallback : Lanczos x4  (مضمون دائماً)
الناتج : 1280x1280 px
"""

import cv2
import numpy as np
import os
import traceback

try:
    from cv2 import dnn_superres as _dnn_sr
    _HAS_SUPERRES = True
except ImportError:
    _HAS_SUPERRES = False

TARGET_SIZE = 1280


# ═══════════════════════════════════════════════════════════
# دوال المعالجة الأصلية (بدون تعديل)
# ═══════════════════════════════════════════════════════════

def _color_correction(img: np.ndarray) -> np.ndarray:
    """CLAHE في فضاء LAB لتصحيح التباين واللون."""
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_fixed = clahe.apply(l)
    lab_fixed = cv2.merge([l_fixed, a, b])
    return cv2.cvtColor(lab_fixed, cv2.COLOR_LAB2BGR)


def _adaptive_denoise(img: np.ndarray) -> np.ndarray:
    """NL-Means خفيف ثم Bilateral للحواف."""
    denoised = cv2.fastNlMeansDenoisingColored(
        img, None,
        h=5, hColor=5,
        templateWindowSize=7,
        searchWindowSize=21
    )
    denoised = cv2.bilateralFilter(denoised, d=9, sigmaColor=40, sigmaSpace=40)
    return denoised


def _unsharp_mask(img: np.ndarray, strength: float = 1.3, sigma: float = 1.2) -> np.ndarray:
    """Unsharp Mask لتحسين الحدة."""
    blurred = cv2.GaussianBlur(img, (0, 0), sigmaX=sigma)
    sharpened = cv2.addWeighted(img, strength, blurred, -(strength - 1.0), 0)
    return sharpened


# ═══════════════════════════════════════════════════════════
# رفع الدقة
# ═══════════════════════════════════════════════════════════

def _upscale_edsr(img: np.ndarray, model_path: str):
    """EDSR x4 عبر OpenCV dnn_superres: 192->768."""
    if not _HAS_SUPERRES:
        print("[Enhancer] opencv-contrib غير متوفر")
        return None
    if not os.path.exists(model_path):
        print(f"[Enhancer] EDSR_x4.pb غير موجود: {model_path}")
        return None
    try:
        sr = _dnn_sr.DnnSuperResImpl_create()
        sr.readModel(model_path)
        sr.setModel("edsr", 4)
        result = sr.upsample(img)
        print(f"[Enhancer] EDSR x4: {img.shape[1]}x{img.shape[0]} -> "
              f"{result.shape[1]}x{result.shape[0]}")
        return result
    except cv2.error as e:
        print(f"[Enhancer] EDSR فشل (OpenCV): {e}")
        return None
    except Exception as e:
        print(f"[Enhancer] EDSR فشل: {type(e).__name__}: {e}")
        return None


# ═══════════════════════════════════════════════════════════
# الدالة الرئيسية — نفس التوقيع الأصلي
# ═══════════════════════════════════════════════════════════

def enhance_image(input_name: str) -> bool:
    """
    192x192 raw -> 1280x1280 final_ai_image.png

    المراحل:
      0. Color correction (على الصورة الصغيرة — أكثر فاعلية)
      1. EDSR x4: 192->768  |  Lanczos x4 fallback
      2. Denoise (NL-Means + Bilateral)
      3. Unsharp Mask
      4. Resize: ->1280x1280
      5. Color correction نهائي
    """
    try:
        base_dir    = os.path.dirname(os.path.abspath(__file__))
        models_dir  = os.path.join(base_dir, "..", "Models")
        edsr_path   = os.path.join(models_dir, "EDSR_x4.pb")
        image_path  = os.path.join(base_dir, "..", "Outputs", input_name)
        output_path = os.path.join(base_dir, "..", "Outputs", "final_ai_image.png")

        if not os.path.exists(image_path):
            print(f"[Enhancer] ERROR: Image not found: {image_path}")
            return False

        img = cv2.imread(image_path)
        if img is None:
            print("[Enhancer] ERROR: cv2.imread returned None")
            return False

        print(f"[Enhancer] Input: {img.shape[1]}x{img.shape[0]} px")

        # Step 0: Color correction قبل التكبير
        img = _color_correction(img)
        print("[Enhancer] Color correction applied.")

        # Step 1: 192->768 (EDSR او Lanczos)
        upscaled = _upscale_edsr(img, edsr_path)
        if upscaled is None:
            upscaled = cv2.resize(img, (768, 768), interpolation=cv2.INTER_LANCZOS4)
            print("[Enhancer] Lanczos x4 fallback: -> 768x768")

        # Step 2: Denoise
        denoised = _adaptive_denoise(upscaled)
        print("[Enhancer] Denoising done.")

        # Step 3: Unsharp Mask
        sharpened = _unsharp_mask(denoised, strength=1.3, sigma=1.2)
        print("[Enhancer] Sharpening done.")

        # Step 4: 768->1280
        final = cv2.resize(sharpened, (TARGET_SIZE, TARGET_SIZE),
                           interpolation=cv2.INTER_LANCZOS4)
        print(f"[Enhancer] Resize -> {TARGET_SIZE}x{TARGET_SIZE}")

        # Step 5: Color pass نهائي
        final = _color_correction(final)

        cv2.imwrite(output_path, final)
        print(f"[Enhancer] SUCCESS: {final.shape[1]}x{final.shape[0]} -> {output_path}")
        return True

    except Exception as e:
        print(f"[Enhancer] CRITICAL ERROR: {type(e).__name__}: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    enhance_image("received_raw.png")