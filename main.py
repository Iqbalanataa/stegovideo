from flask import Flask, request, render_template, redirect, send_file
import os
import cv2
from moviepy.editor import VideoFileClip
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = 'upload'
OUTPUT_FOLDER = 'output'
UPLOADS_FOLDER = 'uploads'
OUTPUTS_FOLDER = 'outputs'
ALLOWED_EXTENSIONS = {'avi'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['UPLOADS_FOLDER'] = UPLOADS_FOLDER
app.config['OUTPUTS_FOLDER'] = OUTPUTS_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Fungsi untuk menyisipkan pesan pada bit gambar
def embed_message(image_path, message):
    img = Image.open(image_path)
    width, height = img.size
    encoded = message + '%%'
    binary_message = ''.join(format(ord(char), '08b') for char in encoded)
    binary_message += '1111111111111110'  # End of Message (EOM) marker

    if len(binary_message) > width * height:
        raise ValueError("Pesan terlalu panjang untuk disisipkan pada gambar")

    data_index = 0
    encoded_image = img.copy()

    for y in range(height):
        for x in range(width):
            pixel = list(img.getpixel((x, y)))

            for color_channel in range(3):
                if data_index < len(binary_message):
                    pixel[color_channel] = int(format(pixel[color_channel], '08b')[:-1] + binary_message[data_index], 2)
                    data_index += 1

            encoded_image.putpixel((x, y), tuple(pixel))

            if data_index == len(binary_message):
                break

    return encoded_image

# Fungsi untuk mendekripsi pesan dari bit gambar
def decrypt_message(encoded_image_path):
    encoded_image = Image.open(encoded_image_path)
    binary_message = ''

    for y in range(encoded_image.height):
        for x in range(encoded_image.width):
            pixel = encoded_image.getpixel((x, y))

            for color_channel in range(3):
                binary_message += format(pixel[color_channel], '08b')[-1]

    message = ''
    message_list = [binary_message[i:i + 8] for i in range(0, len(binary_message), 8)]

    for binary_char in message_list:
        if binary_char == '1111111111111110':
            break
        else:
            message += chr(int(binary_char, 2))

    return message

# Fungsi untuk menggabungkan frame menjadi video
def create_video(frames_folder, output_path, audio_path, fps=30):
    frames = [f for f in os.listdir(frames_folder) if f.endswith(".bmp")]
    frames.sort()
    
    frame_path = os.path.join(frames_folder, frames[0])
    frame = cv2.imread(frame_path)
    height, width, layers = frame.shape
    
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    for frame in frames:
        frame_path = os.path.join(frames_folder, frame)
        img = cv2.imread(frame_path)
        out.write(img)
    
    out.release()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part"
    
    file = request.files['file']
    
    if file.filename == '':
        return "No selected file"
    
    if file and allowed_file(file.filename):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        
        output_frames_folder = os.path.join(app.config['OUTPUT_FOLDER'], 'frames')
        os.makedirs(output_frames_folder, exist_ok=True)
        
        output_audio_path = os.path.join(app.config['OUTPUT_FOLDER'], 'audio.wav')
        
        with VideoFileClip(file_path) as video:
            video.audio.write_audiofile(output_audio_path)
            
            frame_count = 0
            for frame in video.iter_frames(fps=30, dtype='uint8'):
                frame_path = os.path.join(output_frames_folder, f'frame_{frame_count:04d}.bmp')
                cv2.imwrite(frame_path, frame)
                frame_count += 1
        
        # Embed message in the first 5 frames using LSB
        try:
            for i in range(5):
                frame_path = os.path.join(output_frames_folder, f'frame_{i:04d}.bmp')
                encoded_image = embed_message(frame_path, "Your secret message here")
                encoded_image_path = os.path.join(output_frames_folder, f'encoded_frame_{i:04d}.bmp')
                encoded_image.save(encoded_image_path)
                os.remove(frame_path)
        except Exception as e:
            return str(e)
        
        # Create the final video by combining frames
        output_video_path = os.path.join(app.config['OUTPUT_FOLDER'], 'output_video.avi')
        create_video(output_frames_folder, output_video_path, output_audio_path)
        
        return send_file(output_video_path, mimetype='video/x-msvideo')
    
    return "Invalid file format"

@app.route('/decrypt', methods=['POST'])
def decrypt():
    if 'file' not in request.files:
        return "No file part"

    file = request.files['file']

    if file.filename == '':
        return "No selected file"

    if file and allowed_file(file.filename):
        file_path = os.path.join(app.config['UPLOADS_FOLDER'], file.filename)
        file.save(file_path)

        output_frames_folder = os.path.join(app.config['OUTPUTS_FOLDER'], 'frames')
        os.makedirs(output_frames_folder, exist_ok=True)

        output_audio_path = os.path.join(app.config['OUTPUTS_FOLDER'], 'audio.wav')

        with VideoFileClip(file_path) as video:
            video.audio.write_audiofile(output_audio_path)

            frame_count = 0
            for frame in video.iter_frames(fps=30, dtype='uint8'):
                frame_path = os.path.join(output_frames_folder, f'frame_{frame_count:04d}.bmp')
                cv2.imwrite(frame_path, frame)
                frame_count += 1

        # Langkah 3: Periksa frame pertama hingga kelima untuk pesan yang disisipkan
        messages = []
        for i in range(5):
            frame_path = os.path.join(output_frames_folder, f'frame_{i:04d}.bmp')
            message = decrypt_message(frame_path)  # Fungsi decrypt_message perlu diimplementasikan
            messages.append(f"Frame {i + 1}: {message}")

        # Langkah 4: Tampilkan hasil pesan kepada pengguna
        return render_template('result.html', messages=messages)

    return "Invalid file format"

if __name__ == '__main__':
    app.run(debug=True)