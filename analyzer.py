import cv2
import numpy as np
import os
import glob

def get_input_image():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_folder = os.path.join(base_dir, "Inputs")
    types = ('*.png', '*.jpg', '*.jpeg')
    for t in types:
        files = glob.glob(os.path.join(input_folder, t))
        if files: return files[0]
    return None

def calculate_metrics():
    original_path = get_input_image()
    received_path = 'Outputs/final_ai_image.png'

    if not original_path or not os.path.exists(received_path):
        print("Error: Files not found for analysis.")
        return

    img1 = cv2.imread(original_path)
    img2 = cv2.imread(received_path)
    img2_resized = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    mse = np.mean((img1 - img2_resized) ** 2)
    psnr = cv2.PSNR(img1, img2_resized)

    # تحديد الوصف بناءً على المقياس العالمي
    if psnr >= 35:
        quality_desc = "Excellent"
    elif psnr >= 30:
        quality_desc = "Good"
    elif psnr >= 20:
        quality_desc = "Fair"
    else:
        quality_desc = "Poor"

    report_path = "Outputs/report.txt"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(f"Processed: {os.path.basename(original_path)} (Image Name)\n")
        f.write(f"MSE: {mse:.2f} (Error Level)\n")
        f.write(f"PSNR: {psnr:.2f} dB (Quality Level)\n")
        f.write(f"Status: Success\n")
        f.write("-" * 60 + "\n")
        f.write(f"FINAL PERFORMANCE: MSE[{mse:.2f}] / PSNR[{psnr:.2f}dB]\n")
        f.write(f"RESULT: {quality_desc}\n")
        f.write("-" * 60 + "\n")
        
        # إضافة دليل المقياس للمستخدم (Quality Scale Guide)
        f.write("QUALITY SCALE GUIDE (PSNR):\n")
        f.write("* Above 35 dB: Excellent (Identity to original)\n")
        f.write("* 30 - 35 dB: Good (High reconstruction quality)\n")
        f.write("* 20 - 30 dB: Fair (Acceptable, some noise visible)\n")
        f.write("* Below 20 dB: Poor (Significant data loss)\n")

    print("-" * 30)
    print(f"Analysis Complete. Quality is {quality_desc}.")
    print(f"Report saved to Outputs/report.txt")

if __name__ == "__main__":
    calculate_metrics()