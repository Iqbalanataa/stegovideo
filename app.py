from flask import Flask, render_template, request, redirect, url_for
import cv2
import numpy as np
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'  # Folder untuk menyimpan video yang diunggah
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

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

def preparing_key_array(s):
    return [ord(c) for c in s]

def encryption(plaintext, key):
    key = key % 26  # Pastikan kunci berada dalam rentang [0, 25]
    plaintext = caesar_cipher_encrypt(plaintext, key)
    return plaintext

def decryption(ciphertext, key):
    key = key % 26  # Pastikan kunci berada dalam rentang [0, 25]
    decrypted_text = caesar_cipher_decrypt(ciphertext, key)
    return decrypted_text

def embed(frame, data):
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

def encode_vid_data(data, frame_number):
    cap = cv2.VideoCapture("Sample_cover_files/cover_video.mp4")
    vidcap = cv2.VideoCapture("Sample_cover_files/cover_video.mp4")
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

def decode_vid_data(frame_number):
    cap = cv2.VideoCapture('stego_video.mp4')
    max_frame = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if ret == False:
            break
        max_frame += 1
    if frame_number < 1 or frame_number > max_frame:
        return "Invalid frame number"
    frame_number -= 1
    frame_number = 0
    while cap.isOpened():
        frame_number += 1
        ret, frame = cap.read()
        if ret == False:
            break
        if frame_number == frame_number:
            decoded_data = extract(frame)
            return decoded_data
    return "Data extraction failed"

@app.route('/')
def home():
    return render_template('upload.html')  # Tampilkan halaman HTML untuk unggah video

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    file = request.files['file']
    if file.filename == '':
        return "No selected file"
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        return "File uploaded successfully"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        choice = request.form["choice"]
        if choice == "encode":
            data = request.form["data"]
            frame_number = int(request.form["frame_number"])
            result = encode_vid_data(data, frame_number)
            return render_template("index.html", result=result)
        elif choice == "decode":
            frame_number = int(request.form["frame_number"])
            result = decode_vid_data(frame_number)
            return render_template("index.html", result=result)
    return render_template("index.html", result=None)

if __name__ == "__main__":
    app.run(debug=True)
