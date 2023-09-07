from flask import Flask, render_template, request, redirect, url_for, send_file
import cv2
import numpy as np

app = Flask(__name__)

def BinaryToDecimal(binary):
    string = int(binary, 2)
    return string

def txt_encode(text, frame):
    l = len(text)
    i = 0
    add = ''
    while i < l:
        t = ord(text[i])
        if t >= 32 and t <= 64:
            t1 = t + 48
            t2 = t1 ^ 170
            res = bin(t2)[2:].zfill(8)
            add += "0011" + res
        else:
            t1 = t - 48
            t2 = t1 ^ 170
            res = bin(t2)[2:].zfill(8)
            add += "0110" + res
        i += 1
    res1 = add + "111111111111"
    print("The string after binary conversion applying all the transformations: " + res1)
    length = len(res1)
    print("Length of binary after conversion: ", length)
    HM_SK = ""
    ZWC = {"00": u'\u200C', "01": u'\u202C', "11": u'\u202D', "10": u'\u200E'}
    word = frame.split()
    i = 0
    while i < len(res1):
        s = word[int(i / 12)]
        j = 0
        x = ""
        HM_SK = ""
        while j < 12:
            x = res1[j + i] + res1[i + j + 1]
            HM_SK += ZWC[x]
            j += 2
        s1 = s + HM_SK
        frame = frame.replace(s, s1, 1)
        i += 12
    t = int(len(res1) / 12)
    while t < len(word):
        frame += " " + word[t]
        t += 1
    return frame

def encode_vid_data(frame_number, text):
    cap = cv2.VideoCapture("Sample_cover_files/cover_video.avi")
    vidcap = cv2.VideoCapture("Sample_cover_files/cover_video.avi")
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    frame_width = int(vidcap.get(3))
    frame_height = int(vidcap.get(4))
    size = (frame_width, frame_height)
    out = cv2.VideoWriter('stego_video.avi', fourcc, 25.0, size)
    max_frame = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if ret == False:
            break
        max_frame += 1
    cap.release()
    print("Total number of frames in the selected video:", max_frame)
    print("Enter the frame number where you want to embed data:")
    frame_number = int(input())
    frame_count = 0
    while vidcap.isOpened():
        frame_count += 1
        ret, frame = vidcap.read()
        if ret == False:
            break
        if frame_count == frame_number:
            frame = txt_encode(text, frame)
        out.write(frame)
    print("\nData has been successfully embedded in the video file.")
    out.release()

def decode_vid_data(frame_number):
    ZWC_reverse = {u'\u200C': "00", u'\u202C': "01", u'\u202D': "11", u'\u200E': "10"}
    stego = input("\nPlease enter the stego file name (with extension) to decode the message: ")
    file4 = open(stego, "r", encoding="utf-8")
    temp = ''
    for line in file4:
        for words in line.split():
            T1 = words
            binary_extract = ""
            for letter in T1:
                if letter in ZWC_reverse:
                    binary_extract += ZWC_reverse[letter]
            if binary_extract == "111111111111":
                break
            else:
                temp += binary_extract
    print("\nEncrypted message presented in code bits:", temp)
    lengthd = len(temp)
    print("\nLength of encoded bits: ", lengthd)
    i = 0
    a = 0
    b = 4
    c = 4
    d = 12
    final = ''
    while i < len(temp):
        t3 = temp[a:b]
        a += 12
        b += 12
        i += 12
        t4 = temp[c:d]
        c += 12
        d += 12
        if t3 == '0110':
            decimal_data = BinaryToDecimal(t4)
            final += chr((decimal_data ^ 170) + 48)
        elif t3 == '0011':
            decimal_data = BinaryToDecimal(t4)
            final += chr((decimal_data ^ 170) - 48)
    print("\nMessage after decoding from the stego file: ", final)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    if request.method == 'POST':
        text = request.form['text']
        frame_number = int(request.form['frame_number'])
        frame = txt_encode(text, frame_number)
        return render_template('result.html', result="Data berhasil disisipkan")

@app.route('/decode', methods=['POST'])
def decode():
    if request.method == 'POST':
        frame_number = int(request.form['frame_number'])
        result = decode_vid_data(frame_number)
        return render_template('result.html', result=result)

if __name__ == '__main__':
    app.run(debug=True)
