from flask import Flask, render_template, request, redirect, url_for, flash
import cv2
import numpy as np
import os
from werkzeug.utils import secure_filename
from moviepy.editor import *

app = Flask(__name__)
app.secret_key = "your_secret_key"
ALLOWED_EXTENSIONS = {'mp4'}

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Fungsi untuk mengecek ekstensi file yang diizinkan
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def caesar_cipher_encrypt(plaintext, key):
    ciphertext = ""
    for char in plaintext:
        if char.isalpha():
            shifted = ord(char) + key
            if char.islower():
                if shifted > ord('z'):
                    shifted -= 26
            elif char.isupper():
                if shifted > ord('Z'):
                    shifted -= 26
            ciphertext += chr(shifted)
        else:
            ciphertext += char
    return ciphertext

def caesar_cipher_decrypt(ciphertext, key):
    decrypted_text = ""
    for char in ciphertext:
        if char.isalpha():
            shifted = ord(char) - key
            if char.islower():
                if shifted < ord('a'):
                    shifted += 26
            elif char.isupper():
                if shifted < ord('A'):
                    shifted += 26
            decrypted_text += chr(shifted)
        else:
            decrypted_text += char
    return decrypted_text

def msgtobinary(msg):
    if type(msg) == str:
        result = ''.join([format(ord(i), "08b") for i in msg])
    elif type(msg) == bytes or type(msg) == np.ndarray:
        result = [format(i, "08b") for i in msg]
    elif type(msg) == int or type(msg) == np.uint8:
        result = format(msg, "08b")
    else:
        raise TypeError("Input type is not supported in this function")
    return result

def encryption(plaintext, key):
    # key = int(input('keys'))
    key = key % 26  # Pastikan kunci berada dalam rentang [0, 25]
    plaintext = caesar_cipher_encrypt(plaintext, key)
    return plaintext

def decryption(ciphertext, key):
    key = key % 26  # Pastikan kunci berada dalam rentang [0, 25]
    decrypted_text = caesar_cipher_decrypt(ciphertext, key)
    return decrypted_text

def embed(frame):
    data = request.form['secret_message']
    data = encryption(data)
    print("The encrypted data is: ", data)
    if len(data) == 0:
        raise ValueError('Data entered to be encoded is empty')
    data += '*^*^*'
    binary_data = msgtobinary(data)
    length_data = len(binary_data)
    index_data = 0
    for i in frame:
        for pixel in i:
            r, g, b = msgtobinary(pixel)
            if index_data < length_data:
                pixel[0] = int(r[:-1] + binary_data[index_data], 2)
                index_data += 1
            if index_data < length_data:
                pixel[1] = int(g[:-1] + binary_data[index_data], 2)
                index_data += 1
            if index_data < length_data:
                pixel[2] = int(b[:-1] + binary_data[index_data], 2)
                index_data += 1
            if index_data >= length_data:
                break
    return frame

def extract(frame):
    data_binary = ""
    final_decoded_msg = ""
    for i in frame:
        for pixel in i:
            r, g, b = msgtobinary(pixel)
            data_binary += r[-1]
            data_binary += g[-1]
            data_binary += b[-1]
            total_bytes = [data_binary[i: i+8] for i in range(0, len(data_binary), 8)]
            decoded_data = ""
            for byte in total_bytes:
                decoded_data += chr(int(byte, 2))
                if decoded_data[-5:] == "*^*^*":
                    for i in range(0, len(decoded_data)-5):
                        final_decoded_msg += decoded_data[i]
                    final_decoded_msg = decryption(final_decoded_msg)
                    return final_decoded_msg
                
def video_path(filename):
    upload_folder = 'uploads'
    
    # Pastikan direktori upload_folder ada
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Mengamankan nama file menggunakan secure_filename
    secure_filename = filename
    # Gabungkan nama file dengan jalur direktori upload_folder
    path = os.path.join(upload_folder, secure_filename)
    
    return path

def encode_vid_data(data, frame_number):
    video_path = os.path.join(app.config['UPLOAD_FOLDER'], 'your_video.mp4')
    cap = cv2.VideoCapture(video_path)
    vidcap = cv2.VideoCapture(video_path)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    frame_width = int(vidcap.get(3))
    frame_height = int(vidcap.get(4))
    size = (frame_width, frame_height)
    out = cv2.VideoWriter('stego_video.mp4', fourcc, 25.0, size)
    max_frame = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if ret == False:
            break
        max_frame += 1
    cap.release()
    if frame_number < 1 or frame_number > max_frame:
        return "Invalid frame number"
    frame_number -= 1
    frame_number = 0
    while vidcap.isOpened():
        frame_number += 1
        ret, frame = vidcap.read()
        if ret == False:
            break
        if frame_number == frame_number:
            change_frame_with = embed(frame, data)
            frame_ = change_frame_with
            frame = change_frame_with
        out.write(frame)
    return "Data has been successfully embedded in the video file."

def decode_vid_data(frame_):
    cap = cv2.VideoCapture('stego_video.mp4')
    max_frame = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if ret == False:
            break
        max_frame += 1
    print("Total number of Frame in selected Video:", max_frame)
    print("Enter the secret frame number from where you want to extract data")
    n = int(input())
    vidcap = cv2.VideoCapture('stego_video.mp4')
    frame_number = 0
    while vidcap.isOpened():
        frame_number += 1
        ret, frame = vidcap.read()
        if ret == False:
            break
        if frame_number == n:
            extract(frame_)
            return

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    message = request.form['message']
    key = int(request.form['key'])
    
    # Lakukan enkripsi pesan dan sisipkan ke dalam video
    frame_ = encode_vid_data(message, key)
    
    return render_template('result.html', frame=frame_)

@app.route('/decode', methods=['GET', 'POST'])
def decode():
    if request.method == 'POST':
        key = int(request.form['key'])
        # Panggil fungsi decode_vid_data untuk mengekstrak pesan tersembunyi
        decoded_message = decode_vid_data(key)
        return render_template('decoded.html', decoded_message=decoded_message)
    return render_template('decode.html')

if __name__ == '__main__':
    app.run(debug=True)