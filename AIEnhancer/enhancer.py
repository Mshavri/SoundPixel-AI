import cv2
import os
import numpy as np

def enhance_image(input_name):
    try:
        # إعداد المسارات بدقة
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "..", "Models", "EDSR_x4.pb")
        image_path = os.path.join(base_dir, "..", "Outputs", input_name)
        output_path = os.path.join(base_dir, "..", "Outputs", "final_ai_image.png")

        # 1. التحقق من وجود الموديل
        if not os.path.exists(model_path):
            print(f"[ERROR] AI Model missing at: {model_path}")
            return False

        # 2. التحقق من وجود الصورة الخام
        if not os.path.exists(image_path):
            print(f"[ERROR] Image to enhance not found at: {image_path}")
            return False

        # تحميل الموديل
        sr = cv2.dnn_superres.DnnSuperResImpl_create()
        sr.readModel(model_path)
        sr.setModel("edsr", 4) 

        img = cv2.imread(image_path)
        if img is None:
            print("[ERROR] Failed to read image. File might be corrupted.")
            return False

        print("AI Step: Upscaling (Preserving Texture)...")
        upscaled = sr.upsample(img)

        print("Post-Processing: Gentle Sharpening...")
        kernel = np.array([[-0.5,-0.5,-0.5], [-0.5,5,-0.5], [-0.5,-0.5,-0.5]])
        final_result = cv2.filter2D(upscaled, -1, kernel)

        cv2.imwrite(output_path, final_result)
        
        print("-" * 30)
        print("SUCCESS: Realistic Enhancement Complete!")
        print(f"Final Size: {final_result.shape[1]}x{final_result.shape[0]}")
        print("-" * 30)
        return True

    except cv2.error as e:
        print(f"[AI ERROR] OpenCV failed: {e}")
        return False
    except Exception as e:
        print(f"[CRITICAL ERROR] Enhancer failed: {e}")
        return False

if __name__ == "__main__":
    enhance_image("received_raw.png")