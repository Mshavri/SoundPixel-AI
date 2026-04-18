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
            json.dump({
                "last_image": image_name,
                "timestamp":  datetime.utcnow().isoformat()
            }, f)
    except Exception as e:
        print(f"State save error: {e}")


def load_state() -> dict:
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


# ── Folder helpers ────────────────────────────────────────────────────────────

def clean_inputs_folder():
    for fname in os.listdir("Inputs"):
        try:
            os.remove(os.path.join("Inputs", fname))
        except Exception:
            pass


def clean_outputs_folder():
    for fname in os.listdir("Outputs"):
        try:
            os.remove(os.path.join("Outputs", fname))
        except Exception:
            pass


def clean_old_audio(keep_filename: str):
    for fname in os.listdir("Inputs"):
        if fname.endswith(".wav") and fname != keep_filename:
            try:
                os.remove(os.path.join("Inputs", fname))
            except Exception:
                pass


# ── Quality metrics ───────────────────────────────────────────────────────────

def calculate_metrics(original_path: str, reconstructed_path: str):
    """
    Returns (MSE, PSNR) comparing grayscale versions of two images.
    Both are resized to the original's dimensions before comparison.
    """
    try:
        orig  = np.array(Image.open(original_path).convert("L"),  dtype=np.float64)
        recon = np.array(Image.open(reconstructed_path).convert("L"), dtype=np.float64)

        if orig.shape != recon.shape:
            recon = np.array(
                Image.fromarray(recon.astype(np.uint8)).resize(
                    (orig.shape[1], orig.shape[0]), Image.LANCZOS
                ),
                dtype=np.float64
            )

        mse  = float(np.mean((orig - recon) ** 2))
        psnr = 100.0 if mse == 0 else float(10 * np.log10((255.0 ** 2) / mse))
        return round(mse, 4), round(psnr, 2)
    except Exception as exc:
        print(f"Metrics error: {exc}")
        return 0.0, 0.0


def get_quality_label(psnr: float) -> str:
    if psnr >= 35: return "Excellent"
    if psnr >= 30: return "Good"
    if psnr >= 20: return "Fair"
    return "Poor"


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/sender/process")
async def process_image(file: UploadFile = File(...)):
    """
    Accepts an image, encodes it to audio via SoundPixel encoder,
    and returns the WAV file.
    """
    try:
        print(f"\n[SENDER] {file.filename}")

        clean_inputs_folder()
        clean_outputs_folder()

        filename   = os.path.basename(file.filename or "image.png")
        input_path = os.path.join("Inputs", filename)

        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        save_state(filename)

        from SignalCore.encoder import image_to_audio

        if not image_to_audio(filename):
            raise Exception("Encoder failed")

        wav_path = os.path.join("Outputs", "signal.wav")
        if not os.path.exists(wav_path):
            raise Exception("Encoder produced no output file")

        return FileResponse(
            wav_path,
            media_type="audio/wav",
            filename="signal.wav"
        )

    except Exception as e:
        print(f"Sender Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/receiver/process")
async def receive_sound_pipeline(file: UploadFile = File(...)):
    """
    Accepts a WAV file, decodes it back to an image via SoundPixel decoder,
    enhances the result with AI, and returns the final PNG.
    """
    try:
        print(f"\n[RECEIVER] {file.filename}")

        audio_name = f"received_{uuid.uuid4().hex[:8]}.wav"
        input_path = os.path.join("Inputs", audio_name)

        clean_old_audio(audio_name)

        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        print("Audio saved.")

        from SignalCore.decoder import audio_to_image

        if not audio_to_image(audio_name):
            raise Exception("Decoder failed")

        print("Raw image decoded.")

        raw_path   = os.path.join("Outputs", "received_raw.png")
        final_path = os.path.join("Outputs", "final_ai_image.png")

        if not os.path.exists(raw_path):
            raise Exception("Decoder produced no output file")

        from AIEnhancer.enhancer import enhance_image

        enhance_ok = enhance_image("received_raw.png")

        if not enhance_ok:
            print("Enhancer failed — using raw image as fallback.")
            shutil.copy(raw_path, final_path)

        if not os.path.exists(final_path):
            raise Exception("No final image available")

        print("Final image ready.")

        state      = load_state()
        last_image = state.get("last_image", "unknown")
        timestamp  = state.get("timestamp",  "unknown")

        return FileResponse(
            final_path,
            media_type="image/png",
            filename="final_ai_image.png",
            headers={
                "X-Original-Image": last_image,
                "X-Encoded-At":     timestamp
            }
        )

    except Exception as e:
        print(f"Receiver Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/receiver/report/latest")
async def get_latest_report():
    """
    Returns MSE, PSNR, and quality label comparing the last original
    image to the reconstructed output.
    """
    try:
        state      = load_state()
        last_image = state.get("last_image")

        if not last_image:
            return JSONResponse({"status": "No data available"}, status_code=404)

        orig  = os.path.join("Inputs",  last_image)
        recon = os.path.join("Outputs", "final_ai_image.png")

        if not os.path.exists(orig):
            return JSONResponse({"status": f"Original not found: {last_image}"}, status_code=404)
        if not os.path.exists(recon):
            return JSONResponse({"status": "Reconstructed image not found"}, status_code=404)

        mse, psnr = calculate_metrics(orig, recon)

        return {
            "original":  last_image,
            "mse":       mse,
            "psnr":      psnr,
            "quality":   get_quality_label(psnr),
            "timestamp": state.get("timestamp", "unknown")
        }

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/health")
async def health():
    return {
        "status":    "OK",
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)