from flask import Flask, render_template, request, send_from_directory
import numpy as np
import cv2
import os

app = Flask(__name__)

UPLOAD_FOLDER = 'upload'
OUTPUT_FOLDER = 'output'

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER


def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def caesar_encrypt(text, key):
    encrypted_text = ""
    for char in text:
        if char.isalpha():
            if char.islower():
                encrypted_char = chr(((ord(char) - ord('a') + key) % 26) + ord('a'))
            else:
                encrypted_char = chr(((ord(char) - ord('A') + key) % 26) + ord('A'))
        else:
            encrypted_char = char
        encrypted_text += encrypted_char
    return encrypted_text

def caesar_decrypt(text, key):
    decrypted_text = ""
    for char in text:
        if char.isalpha():
            if char.islower():
                decrypted_char = chr(((ord(char) - ord('a') - key) % 26) + ord('a'))
            else:
                decrypted_char = chr(((ord(char) - ord('A') - key) % 26) + ord('A'))
        else:
            decrypted_char = char
        decrypted_text += decrypted_char
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

def embed(frame, data):
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
            total_bytes = [data_binary[i: i + 8] for i in range(0, len(data_binary), 8)]
            decoded_data = ""
            for byte in total_bytes:
                decoded_data += chr(int(byte, 2))
                if decoded_data[-5:] == "*^*^*":
                    for i in range(0, len(decoded_data) - 5):
                        final_decoded_msg += decoded_data[i]
                    final_decoded_msg = caesar_decrypt(final_decoded_msg, key=3)
                    return final_decoded_msg


def encode_video(file, data):
    vidcap = cv2.VideoCapture(file)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    frame_width = int(vidcap.get(3))
    frame_height = int(vidcap.get(4))
    size = (frame_width, frame_height)
    output_path = os.path.join(app.config['OUTPUT_FOLDER'], 'stego_video.mp4')
    out = cv2.VideoWriter(output_path, fourcc, 25.0, size)
    frame_number = 0
    total_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))
    while (vidcap.isOpened()):
        frame_number += 1
        ret, frame = vidcap.read()
        if ret == False:
            break
        if frame_number == total_frames:  # Sisipkan pesan hanya pada frame terakhir
            change = embed(frame, data)
            frame = change
        out.write(frame)
    out.release()
    vidcap.release()
    return frame



def decode_video(file):
    vidcap = cv2.VideoCapture(file)
    frame_number = 0
    total_frames = int(vidcap.get(cv2.CAP_PROP_FRAME_COUNT))  # Jumlah total frame dalam video
    while (vidcap.isOpened()):
        frame_number += 1
        ret, frame = vidcap.read()
        if ret == False:
            break
        if frame_number == total_frames:  # Frame terakhir di mana pesan disisipkan
            extracted_data = extract(frame)
    vidcap.release()
    return extracted_data


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/encode', methods=['GET', 'POST'])
def encode():
    if request.method == 'POST':
        if 'video' not in request.files or 'message' not in request.form:
            return "Missing required parameters", 400

        video = request.files['video']
        message = request.form['message']

        if video.filename == '':
            return "No selected file", 400

        # Memeriksa apakah file yang diunggah adalah file video
        allowed_extensions = {'mp4', 'avi', 'mkv'}  # Ganti dengan ekstensi yang sesuai
        if not allowed_file(video.filename, allowed_extensions):
            return "Unsupported file format", 400

        # Save the video file
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
        video.save(video_path)

        # Memanggil fungsi encode_video
        try:
            encode_video(video_path, message)
        except Exception as e:
            return str(e), 500
        
    return render_template('index.html')  # Menampilkan halaman HTML untuk mengunggah video dan pesan


@app.route('/decode', methods=['GET', 'POST'])
def decode():
    if request.method == 'POST':
        if 'video' not in request.files:
            return "Missing video file", 400

        video = request.files['video']

        if video.filename == '':
            return "No selected file", 400

        # Memeriksa apakah file yang diunggah adalah file video
        allowed_extensions = {'mp4', 'avi', 'mkv'}  # Ganti dengan ekstensi yang sesuai
        if not allowed_file(video.filename, allowed_extensions):
            return "Unsupported file format", 400

        # Simpan file video yang diunggah
        video_path = os.path.join(app.config['UPLOAD_FOLDER'], video.filename)
        video.save(video_path)

        try:
            decoded_message = decode_video(video_path)
            if decoded_message is not None:
                return f"Decoded message: {decoded_message}"
            else:
                return "No message found in the video", 400
        except Exception as e:
            return str(e), 500

    return render_template('decode.html')  # Menampilkan halaman HTML untuk mengunggah video yang akan didekode


if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    app.run(debug=True)