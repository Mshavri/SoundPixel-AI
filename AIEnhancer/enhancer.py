import cv2
import os

def enhance_image(input_name):
    # إعداد المسارات بدقة
    model_path = "../Models/EDSR_x4.pb"
    image_path = f"../Outputs/{input_name}"
    output_path = "../Outputs/final_ai_image.png"

    # التحقق من وجود الموديل
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return

    # 1. إنشاء كائن تحسين الدقة (Super Resolution)
    sr = cv2.dnn_superres.DnnSuperResImpl_create()

    print("Loading AI Model into memory... please wait.")
    sr.readModel(model_path)
    sr.setModel("edsr", 4) # استخدام موديل EDSR وتكبير الصورة 4 مرات

    # 2. قراءة الصورة المستلمة المشوشة
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not find {image_path}")
        return

    print("AI is now analyzing and reconstructing pixels...")
    
    # 3. معالجة الصورة بالذكاء الاصطناعي
    result = sr.upsample(img)

    # 4. حفظ النتيجة النهائية
    cv2.imwrite(output_path, result)
    print("-" * 30)
    print(f"SUCCESS: Image enhanced!")
    print(f"Original Size: 64x64")
    print(f"AI Output Size: 256x256")
    print(f"File saved: Outputs/final_ai_image.png")
    print("-" * 30)

if __name__ == "__main__":
    # سنقوم بتحسين الصورة التي استخرجناها من الصوت سابقاً
    enhance_image("received_raw.png")