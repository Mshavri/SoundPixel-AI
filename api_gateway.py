from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
import uvicorn
import uuid
import json
from datetime import datetime
from PIL import Image
import numpy as np
from skimage.metrics import mean_squared_error, peak_signal_noise_ratio

app = FastAPI(title="SoundPixel-AI Encrypted Messaging API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# إنشاء المجلدات المطلوبة
os.makedirs("Inputs", exist_ok=True)
os.makedirs("Outputs", exist_ok=True)
os.makedirs("Reports", exist_ok=True)

# متغير عام لتخزين اسم آخر صورة تمت معالجتها
last_processed_image = None

def clean_inputs_folder():
    """تنظيف مجلد Inputs فقط (نحتفظ بـ Outputs للتقارير)"""
    folder = "Inputs"
    if os.path.exists(folder):
        for f in os.listdir(folder):
            file_path = os.path.join(folder, f)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception as e:
                print(f"Cleanup error for {f}: {e}")

def calculate_metrics(original_path: str, reconstructed_path: str):
    """حساب MSE و PSNR بين الصورة الأصلية والمعاد بناؤها"""
    try:
        original = Image.open(original_path).convert('L')
        reconstructed = Image.open(reconstructed_path).convert('L')
        
        # توحيد الحجم للمقارنة
        if original.size != reconstructed.size:
            reconstructed = reconstructed.resize(original.size)
        
        original_array = np.array(original).astype(np.float64)
        reconstructed_array = np.array(reconstructed).astype(np.float64)
        
        mse = mean_squared_error(original_array, reconstructed_array)
        
        if mse == 0:
            psnr = 100.0
        else:
            psnr = peak_signal_noise_ratio(original_array, reconstructed_array, data_range=255)
        
        return round(mse, 4), round(psnr, 2)
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        return 0.0, 0.0

def get_quality_status(psnr: float) -> str:
    """تحديد حالة الجودة بناءً على PSNR"""
    if psnr >= 35:
        return "Excellent"
    elif psnr >= 30:
        return "Good"
    elif psnr >= 20:
        return "Fair"
    else:
        return "Poor"

# ============================================================
# SENDER - تشفير الصورة إلى صوت
# ============================================================
@app.post("/sender/process")
async def process_image(file: UploadFile = File(...)):
    """
    يستقبل صورة من المستخدم المرسل
    يحولها إلى صوت مشفر
    يرجع الصوت للمشاركة
    """
    global last_processed_image
    
    try:
        print(f"\n📤 [SENDER] Receiving image: {file.filename}")
        
        # تنظيف مجلد Inputs للمعالجة الجديدة
        clean_inputs_folder()
        
        # حفظ الصورة الأصلية في Inputs
        original_filename = file.filename or "image.png"
        input_path = os.path.join("Inputs", original_filename)
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"✅ Image saved: {input_path}")
        
        # تخزين اسم الصورة للمقارنة لاحقاً
        last_processed_image = original_filename
        
        # تحويل الصورة إلى صوت مشفر
        from SignalCore.encoder import image_to_audio
        success = image_to_audio(original_filename)
        
        if not success:
            raise Exception("Encoder failed to process the image")
        
        audio_output = "Outputs/signal.wav"
        
        if os.path.exists(audio_output):
            print(f"✅ Audio generated: {audio_output}")
            return FileResponse(
                audio_output,
                media_type="audio/wav",
                headers={"X-Original-Image": original_filename}
            )
        else:
            raise Exception("Audio file not created")

    except Exception as e:
        print(f"❌ Sender Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# RECEIVER - فك تشفير الصوت إلى صورة
# ============================================================
@app.post("/receiver/process")
async def receive_sound_pipeline(file: UploadFile = File(...)):
    """
    يستقبل صوت مشفر من المستخدم المستقبل
    يفك تشفيره إلى صورة
    يرجع الصورة المستعادة
    """
    try:
        print(f"\n📥 [RECEIVER] Receiving audio: {file.filename}")
        
        # حفظ الصوت المستلم في Inputs
        audio_filename = f"received_{uuid.uuid4().hex[:8]}.wav"
        input_path = os.path.join("Inputs", audio_filename)
        
        with open(input_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        print(f"✅ Audio saved: {input_path}")
        
        # فك تشفير الصوت إلى صورة
        from SignalCore.decoder import audio_to_image
        success = audio_to_image(audio_filename)
        
        if not success:
            raise Exception("Decoder failed to process the audio")
        
        print("✅ Raw image reconstructed")
        
        # تحسين الصورة بالذكاء الاصطناعي
        from AIEnhancer.enhancer import enhance_image
        enhance_image("received_raw.png")
        
        final_image_path = "Outputs/final_ai_image.png"
        
        if os.path.exists(final_image_path):
            print(f"✅ Final image ready: {final_image_path}")
            return FileResponse(
                final_image_path,
                media_type="image/png",
                headers={"X-Original-Image": last_processed_image or "unknown"}
            )
        else:
            raise Exception("Enhancer failed to produce final image")

    except Exception as e:
        print(f"❌ Receiver Error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# REPORT - تقرير جودة فك التشفير
# ============================================================
@app.get("/receiver/report/latest")
async def get_latest_report():
    """
    يرجع تقرير جودة آخر عملية فك تشفير
    يقارن الصورة الأصلية (من SENDER) مع الصورة المستعادة (من RECEIVER)
    """
    global last_processed_image
    
    try:
        # البحث عن الصورة الأصلية في Inputs
        original_path = None
        if last_processed_image:
            temp_path = os.path.join("Inputs", last_processed_image)
            if os.path.exists(temp_path):
                original_path = temp_path
        
        # إذا ما لقينا الصورة المخزنة، نبحث عن أي صورة في Inputs
        if original_path is None:
            for f in os.listdir("Inputs"):
                if f.endswith(('.png', '.jpg', '.jpeg')):
                    original_path = os.path.join("Inputs", f)
                    last_processed_image = f
                    break
        
        if original_path is None:
            return JSONResponse(content={
                "status": "No original image found",
                "message": "Please process an image through SENDER first",
                "quality_status": "Unknown"
            })
        
        reconstructed_path = "Outputs/final_ai_image.png"
        
        if not os.path.exists(reconstructed_path):
            return JSONResponse(content={
                "status": "No reconstructed image found",
                "message": "Please process audio through RECEIVER first",
                "quality_status": "Unknown"
            })
        
        # حساب المقاييس الحقيقية
        mse, psnr = calculate_metrics(original_path, reconstructed_path)
        quality = get_quality_status(psnr)
        
        original_img = Image.open(original_path)
        
        report = {
            "image_name": os.path.basename(original_path),
            "original_size": f"{original_img.size[0]}x{original_img.size[1]}",
            "mse": mse,
            "psnr": psnr,
            "quality_status": quality,
            "timestamp": datetime.now().isoformat(),
            "status": "Success"
        }
        
        print(f"\n📊 [REPORT] Generated for {os.path.basename(original_path)}")
        print(f"   MSE: {mse}, PSNR: {psnr} dB, Quality: {quality}")
        
        return JSONResponse(content=report)
        
    except Exception as e:
        print(f"❌ Report Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"status": "Error", "message": str(e), "quality_status": "Error"}
        )

# ============================================================
# HEALTH CHECK
# ============================================================
@app.get("/health")
async def health_check():
    return {"status": "SoundPixel API is running", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    print("\n" + "="*50)
    print("🔐 SoundPixel - Encrypted Audio Messaging")
    print("="*50)
    print("📤 SENDER:  POST /sender/process")
    print("📥 RECEIVER: POST /receiver/process")
    print("📊 REPORT:   GET /receiver/report/latest")
    print("="*50 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)