import cv2
import numpy as np
import os

def calculate_metrics(original_path, received_path):
    # 1. تحميل الصور
    img1 = cv2.imread(original_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(received_path, cv2.IMREAD_GRAYSCALE)

    if img1 is None or img2 is None:
        print("Error: Files not found for analysis.")
        return

    # 2. توحيد الحجم للمقارنة
    img1 = cv2.resize(img1, (64, 64))
    img2 = cv2.resize(img2, (64, 64))

    # 3. حساب متوسط الخطأ التربيعي (MSE)
    mse = np.mean((img1 - img2) ** 2)
    
    # 4. حساب نسبة الإشارة إلى الضجيج (PSNR)
    if mse == 0:
        psnr = 100
    else:
        max_pixel = 255.0
        psnr = 20 * np.log10(max_pixel / np.sqrt(mse))

    print("-" * 30)
    print("       IMAGE INFO          ")
    print("-" * 30)
    print(f"Mean Squared Error (MSE): {mse:.2f}")
    print(f"Peak Signal-to-Noise Ratio (PSNR): {psnr:.2f} dB")
    print("-" * 30)

if __name__ == "__main__":
    # Correct paths for the new structure
    calculate_metrics('Inputs/test.png', 'Outputs/final_ai_image.png')