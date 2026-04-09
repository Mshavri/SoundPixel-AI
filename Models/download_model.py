import urllib.request
import os

def download():
    url = "https://github.com/Saafke/EDSR_Tensorflow/raw/master/models/EDSR_x4.pb"
    dest = "EDSR_x4.pb"
    
    if not os.path.exists(dest):
        print("Downloading AI Model (EDSR x4)... This may take a minute.")
        urllib.request.urlretrieve(url, dest)
        print("Done! Model is ready in Models folder.")
    else:
        print("Model already exists.")

if __name__ == "__main__":
    download()