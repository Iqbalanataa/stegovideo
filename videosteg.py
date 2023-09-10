import cv2
import numpy as np

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

def encryption(plaintext):
    print("Enter the key for Caesar Cipher: ")
    key = int(input())
    key = key % 26  # Pastikan kunci berada dalam rentang [0, 25]
    plaintext = caesar_cipher_encrypt(plaintext, key)
    return plaintext

def decryption(ciphertext):
    print("Enter the key for Caesar Cipher: ")
    key = int(input())
    key = key % 26  # Pastikan kunci berada dalam rentang [0, 25]
    decrypted_text = caesar_cipher_decrypt(ciphertext, key)
    return decrypted_text

def embed(frame):
    data = input("\nEnter the data to be Encoded in Video: ")
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
                    print("\n\nThe Encoded data which was hidden in the Video was:\n", final_decoded_msg)
                    return

def encode_vid_data():
    cap = cv2.VideoCapture("static/Sample_cover_files/cover_video.mp4")
    vidcap = cv2.VideoCapture("static/Sample_cover_files/cover_video.mp4")
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
    print("Total number of Frame in selected Video:", max_frame)
    print("Enter the frame number where you want to embed data:")
    n = int(input())
    frame_number = 0
    while vidcap.isOpened():
        frame_number += 1
        ret, frame = vidcap.read()
        if ret == False:
            break
        if frame_number == n:
            change_frame_with = embed(frame)
            frame_ = change_frame_with
            frame = change_frame_with
        out.write(frame)
    print("\nEncoded the data successfully in the video file.")
    return frame_

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

def vid_steg():
    while True:
        print("\n\t\tVIDEO STEGANOGRAPHY OPERATIONS")
        print("1. Encode the Text message")
        print("2. Decode the Text message")
        print("3. Exit")
        choice1 = int(input("Enter the Choice:"))
        if choice1 == 1:
            a = encode_vid_data()
        elif choice1 == 2:
            decode_vid_data(a)
        elif choice1 == 3:
            break
        else:
            print("Incorrect Choice")
        print("\n")

if __name__ == "__main__":
    vid_steg()
