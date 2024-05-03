from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
import numpy as np
import os
import cv2

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
CARTOON_FOLDER= 'cartoon_images'
app.config['CARTOON_FOLDER'] =CARTOON_FOLDER

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to render the main page
@app.route('/')
def index():
    # Get the list of images in the uploads folder
    images = os.listdir(app.config['UPLOAD_FOLDER'])
    # Render the HTML template with the image list
    return render_template('index.html', images=images)

def cartoonify_image(input_path, output_path):
    # Read the input image
    img = cv2.imread(input_path)

    # Convert the image to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Apply a bilateral filter to reduce noise while keeping edges sharp
    gray = cv2.bilateralFilter(gray, 9, 300, 300)

    # Apply an adaptive thresholding to get a binary image
    edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
#  ADAPTIVE_THRESH_GAUSSIAN_C,ADAPTIVE_THRESH_MEAN_C
    # Convert the image to a color image
    color = cv2.bilateralFilter(img, 9, 300, 300)

    # Combine the color image with the edges
    cartoon = cv2.bitwise_and(color, color, mask=edges)

    # Save the cartoonified image
    cv2.imwrite(output_path, cartoon)

@app.route('/upload', methods=['POST'])
def upload_file():
    # Check if the 'file' key is in the request files
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    # Get the uploaded file
    file = request.files['file']

    # Check if no file was selected
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    # Check if the file format is allowed
    if file and allowed_file(file.filename):
        # Securely save the file to the uploads folder
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Generate the filename for the cartoonified image
        cartoonified_filename = 'cartoon_' + filename

        # Cartoonify the image and save it
        cartoonify_image(os.path.join(app.config['UPLOAD_FOLDER'], filename),
                          os.path.join(app.config['CARTOON_FOLDER'], cartoonified_filename))

        # Return JSON response with redirect URL
        return jsonify({'redirect_url': url_for('select_image', filename=filename)})

    return jsonify({'error': 'Invalid file format'})

# Route to display the selected image and its cartoonified version
@app.route('/select/<filename>')
def select_image(filename):
    selected_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # Check if the selected image exists
    if not os.path.isfile(selected_image_path):
        return render_template('index.html', error='Selected image not found.', images=os.listdir(app.config['UPLOAD_FOLDER']))

    cartoonified_filename = 'cartoon_' + filename
    cartoonified_image_path = os.path.join(app.config['CARTOON_FOLDER'], cartoonified_filename)

    # Check if the cartoonified image exists
    if not os.path.isfile(cartoonified_image_path):
        return render_template('index.html', error='Cartoonified image not found.', images=os.listdir(app.config['UPLOAD_FOLDER']))

    # Render the HTML template with selected image and its cartoonified version
    return render_template('index.html', selected_image=filename, cartoonified_image=cartoonified_filename, images=os.listdir(app.config['UPLOAD_FOLDER']))

# Run the Flask app if executed as the main script
if __name__ == '__main__':
    app.run(debug=True,port=5001)
