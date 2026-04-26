from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uuid
import json
from datetime import datetime
from PIL import Image
import numpy as np

app = FastAPI(title="SoundPixel-AI Encrypted Messaging API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("Inputs",  exist_ok=True)
os.makedirs("Outputs", exist_ok=True)
os.makedirs("Reports", exist_ok=True)

STATE_FILE = "Reports/state.json"


# ── State helpers ─────────────────────────────────────────────────────────────
def save_state(image_name: str):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump({"last_image": image_name}, f)
    except Exception as e:
        print(f"State save error: {e}")


def load_state() -> str | None:
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                return json.load(f).get("last_image")
    except Exception:
        pass
    return None


# ── Folder helpers ────────────────────────────────────────────────────────────
def clean_inputs_folder():
    for f in os.listdir("Inputs"):
        try:
            os.remove(os.path.join("Inputs", f))
        except Exception as e:
            print(f"Cleanup error {f}: {e}")


def clean_outputs_folder():
    for f in os.listdir("Outputs"):
        try:
            os.remove(os.path.join("Outputs", f))
        except Exception as e:
            print(f"Cleanup error {f}: {e}")


def clean_old_audio(keep_filename: str):
    for f in os.listdir("Inputs"):
        if f.endswith(".wav") and f != keep_filename:
            try:
                os.remove(os.path.join("Inputs", f))
            except Exception as e:
                print(f"Audio cleanup error {f}: {e}")


# ── Quality metrics — NO original needed ─────────────────────────────────────
# Compares received_raw.png (raw decode) vs final_ai_image.png (AI enhanced).
# MSE  → how much noise/distortion the AI had to correct.
# PSNR → signal quality after reconstruction (higher = cleaner output).
def calculate_metrics(raw_path: str, final_path: str):
    """
    Compare the raw decoded image with the AI-enhanced image.
    Both files are produced by the RECEIVER pipeline, so this metric
    is completely independent of the SENDER and always available.

    Interpretation:
      High PSNR (>30 dB) → raw signal was already clean; minor enhancement.
      Medium PSNR (20–30) → noticeable noise corrected by AI.
      Low PSNR (<20 dB)  → heavily distorted signal; significant correction.
    """
    try:
        raw   = np.array(Image.open(raw_path).convert("L"),   dtype=np.float64)
        final = np.array(Image.open(final_path).convert("L"), dtype=np.float64)

        # Match sizes (final is 4× upscaled by enhancer)
        if raw.shape != final.shape:
            h, w = raw.shape
            final_pil = Image.fromarray(final.astype(np.uint8)).resize(
                (w, h), Image.LANCZOS
            )
            final = np.array(final_pil, dtype=np.float64)

        mse  = float(np.mean((raw - final) ** 2))
        psnr = 100.0 if mse == 0 else float(10 * np.log10((255.0 ** 2) / mse))
        return round(mse, 4), round(psnr, 2)
    except Exception as e:
        print(f"Metrics error: {e}")
        return None, None


def get_quality_status(psnr: float) -> str:
    if psnr >= 35:  return "Excellent"
    if psnr >= 28:  return "Good"
    if psnr >= 20:  return "Fair"
    return "Poor"


# ============================================================
# SENDER — image → encrypted audio
# ============================================================
@app.post("/sender/process")
async def process_image(file: UploadFile = File(...)):
    try:
        print(f"\n📤 [SENDER] Receiving image: {file.filename}")

        clean_inputs_folder()
        clean_outputs_folder()

        original_filename = os.path.basename(file.filename or "image.png")
        input_path = os.path.join("Inputs", original_filename)

        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"✅ Image saved: {input_path}")
        save_state(original_filename)

        from SignalCore.encoder import image_to_audio
        if not image_to_audio(original_filename):
            raise Exception("Encoder failed")

        audio_output = "Outputs/signal.wav"
        if not os.path.exists(audio_output):
            raise Exception("Audio file was not created")

        print(f"✅ Audio generated: {audio_output}")
        return FileResponse(audio_output, media_type="audio/wav",
                            headers={"X-Original-Image": original_filename})

    except Exception as e:
        print(f"❌ Sender Error: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# RECEIVER — encrypted audio → image
# ============================================================
@app.post("/receiver/process")
async def receive_sound_pipeline(file: UploadFile = File(...)):
    try:
        print(f"\n📥 [RECEIVER] Receiving audio: {file.filename}")

        audio_filename = f"received_{uuid.uuid4().hex[:8]}.wav"
        input_path     = os.path.join("Inputs", audio_filename)

        clean_old_audio(audio_filename)

        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print(f"✅ Audio saved: {input_path}")

        from SignalCore.decoder import audio_to_image
        if not audio_to_image(audio_filename):
            raise Exception("Decoder failed")

        print("✅ Raw image reconstructed")

        raw_path   = "Outputs/received_raw.png"
        final_path = "Outputs/final_ai_image.png"

        from AIEnhancer.enhancer import enhance_image
        enhance_ok = enhance_image("received_raw.png")

        if not enhance_ok:
            print("⚠️  Enhancer failed — using raw image as final")
            if os.path.exists(raw_path):
                shutil.copy(raw_path, final_path)
            else:
                raise Exception("Both enhancer and raw image unavailable")

        if not os.path.exists(final_path):
            raise Exception("Final image not found")

        print(f"✅ Final image ready: {final_path}")
        last_image = load_state() or "unknown"
        return FileResponse(final_path, media_type="image/png",
                            headers={"X-Original-Image": last_image})

    except Exception as e:
        print(f"❌ Receiver Error: {e}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# REPORT — always computed from receiver outputs (no sender needed)
# ============================================================
@app.get("/receiver/report/latest")
async def get_latest_report():
    """
    Computes quality metrics by comparing:
      received_raw.png    →  raw SSTV decoded image
      final_ai_image.png  →  AI-enhanced output

    Both files are produced by the RECEIVER pipeline.
    No original image from the SENDER is needed.
    """
    try:
        raw_path   = "Outputs/received_raw.png"
        final_path = "Outputs/final_ai_image.png"

        # Both files must exist (produced by the receiver)
        if not os.path.exists(raw_path):
            return JSONResponse(content={
                "status":         "No decoded image found",
                "message":        "Process an audio file through RECEIVER first.",
                "quality_status": "Unknown",
                "mse":            None,
                "psnr":           None,
            })

        if not os.path.exists(final_path):
            return JSONResponse(content={
                "status":         "No enhanced image found",
                "message":        "Enhancement step did not produce output.",
                "quality_status": "Unknown",
                "mse":            None,
                "psnr":           None,
            })

        mse, psnr = calculate_metrics(raw_path, final_path)

        if mse is None or psnr is None:
            return JSONResponse(content={
                "status":         "Metrics calculation failed",
                "quality_status": "Unknown",
                "mse":            None,
                "psnr":           None,
            })

        quality = get_quality_status(psnr)

        with Image.open(final_path) as img:
            final_size = f"{img.size[0]}x{img.size[1]}"

        report = {
            "status":         "Success",
            "final_size":     final_size,
            "mse":            mse,
            "psnr":           psnr,
            "quality_status": quality,
            "timestamp":      datetime.now().isoformat(),
        }

        print(f"\n📊 [REPORT] MSE={mse}, PSNR={psnr} dB, Quality={quality}")
        return JSONResponse(content=report)

    except Exception as e:
        print(f"❌ Report Error: {e}")
        import traceback; traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={
                "status":         "Error",
                "message":        str(e),
                "quality_status": "Unknown",
                "mse":            None,
                "psnr":           None,
            }
        )


# ============================================================
# HEALTH CHECK
# ============================================================
@app.get("/health")
async def health_check():
    return {
        "status":    "SoundPixel API is running ✅",
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    print("\n" + "=" * 50)
    print("🔐  SoundPixel — Encrypted Audio Messaging")
    print("=" * 50)
    print("📤  SENDER:   POST /sender/process")
    print("📥  RECEIVER: POST /receiver/process")
    print("📊  REPORT:   GET  /receiver/report/latest")
    print("=" * 50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)