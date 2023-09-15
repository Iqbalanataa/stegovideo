from flask import Flask, render_template, request
from cryptography.fernet import Fernet
from stegano import lsb
import os

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    if 'video' not in request.files or 'message' not in request.form or 'key' not in request.form:
        return "Missing required parameters", 400

    video = request.files['video']
    message = request.form['message']
    key = int(request.form['key'])

    # Save the video file
    video_path = os.path.join('uploads', video.filename)
    video.save(video_path)

    # Encrypt the message using Caesar Cipher
    encrypted_message = caesar_cipher_encrypt(message, key)
    
    # Encode the encrypted message into the video using LSB algorithm
    encoded_video_path = os.path.join('uploads', 'encoded_' + video.filename)
    lsb.hide(video_path, encoded_video_path, encrypted_message)

    return render_template('encode.html', video_path=encoded_video_path)

@app.route('/decode', methods=['POST'])
def decode():
    if 'video' not in request.files or 'key' not in request.form:
        return "Missing required parameters", 400

    video = request.files['video']
    key = request.form['key']

    # Save the video file
    video_path = os.path.join('uploads', video.filename)
    video.save(video_path)

    # Decode the message from the video using LSB algorithm
    decoded_message = lsb.reveal(video_path)

    # Decrypt the message using Caesar Cipher
    decrypted_message = caesar_cipher_decrypt(decoded_message, key)

    return render_template('decode.html', message=decrypted_message)

def caesar_cipher_encrypt(message: str, key: int) -> str:
    """
    Encrypts a message using the Caesar Cipher algorithm.

    Args:
    - message (str): The message to be encrypted.
    - key (int): The encryption key.

    Returns:
    - str: The encrypted message.
    """
    encrypted_message = ""
    for char in message:
        if char.isalpha():
            ascii_offset = ord('a') if char.islower() else ord('A')
            encrypted_char = chr((ord(char) - ascii_offset + key) % 26 + ascii_offset)
            encrypted_message += encrypted_char
        else:
            encrypted_message += char
    return encrypted_message

def caesar_cipher_decrypt(encrypted_message: str, key: int) -> str:
    """
    Decrypts an encrypted message using the Caesar Cipher algorithm.

    Args:
    - encrypted_message (str): The encrypted message.
    - key (int): The decryption key.

    Returns:
    - str: The decrypted message.
    """
    decrypted_message = ""
    for char in encrypted_message:
        if char.isalpha():
            ascii_offset = ord('a') if char.islower() else ord('A')
            decrypted_char = chr((ord(char) - ascii_offset - key) % 26 + ascii_offset)
            decrypted_message += decrypted_char
        else:
            decrypted_message += char
    return decrypted_message

if __name__ == '__main__':
    app.run(debug=True)