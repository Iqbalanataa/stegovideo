from flask import Flask, request, render_template_string
import numpy as np
import cv2

app = Flask(__name__)

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
    key = key % 26  # Make sure the key is within the range [0, 25]
    plaintext = caesar_cipher_encrypt(plaintext, key)
    return plaintext

def decryption(ciphertext, key):
    key = key % 26  # Make sure the key is within the range [0, 25]
    decrypted_text = caesar_cipher_decrypt(ciphertext, key)
    return decrypted_text

def embed(frame, data, key):
    data = encryption(data, key)
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

def extract(frame, key):
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
                    final_decoded_msg = decryption(final_decoded_msg, key)
                    return final_decoded_msg

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        video = request.files['video']
        message = request.form['message']
        key = int(request.form['key'])
        
        # Read the video file
        video_data = video.read()
        
        # Convert the video data to a numpy array
        nparr = np.frombuffer(video_data, np.uint8)
        
        # Decode the video using OpenCV
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Embed the message in the video frame
        embedded_frame = embed(frame, message, key)
        
        # Encode the video frame back to bytes
        _, encoded_frame = cv2.imencode('.mp4', embedded_frame)
        
        # Convert the encoded frame to bytes
        encoded_data = encoded_frame.tobytes()
        
        return encoded_data
    
    return render_template_string('''
        <form method="POST" enctype="multipart/form-data">
            <input type="file" name="video" accept="video/*" required><br>
            <input type="text" name="message" placeholder="Message" required><br>
            <input type="number" name="key" placeholder="Key" required><br>
            <input type="submit" value="Encode">
        </form>
    ''')

if __name__ == '__main__':
    app.run()