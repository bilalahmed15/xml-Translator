import os
from flask import Flask, render_template, request, send_from_directory
import xml.etree.ElementTree as ET
import deepl
import html

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DOWNLOAD_FOLDER'] = 'downloads'
app.config['ALLOWED_EXTENSIONS'] = {'xml'}

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

if not os.path.exists(app.config['DOWNLOAD_FOLDER']):
    os.makedirs(app.config['DOWNLOAD_FOLDER'])

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def translate_xml(file_path, download_path, target_lang="en-us"):
    auth_key = os.environ.get("DEEPL_AUTH_KEY")
    if not auth_key:
        raise ValueError("DeepL authentication key is not set")
    translator = deepl.Translator(auth_key)
    tree = ET.parse(file_path)
    root = tree.getroot()

    def translate_element(element):
        if element.text:
            translated_text = translator.translate_text(element.text, target_lang=target_lang).text
            element.text = translated_text
        for child in element:
            translate_element(child)

    translate_element(root)
    tree.write(download_path)

def decode_entities_in_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    decoded_content = html.unescape(content)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(decoded_content)

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        target_lang = request.form.get('target_lang')
        if file and allowed_file(file.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            download_path = os.path.join(app.config['DOWNLOAD_FOLDER'], "translated_" + file.filename)
            file.save(filename)
            translate_xml(filename, download_path, target_lang=target_lang)
            decode_entities_in_file(download_path)  # Decode HTML entities in the downloaded file
            return send_from_directory(app.config['DOWNLOAD_FOLDER'], "translated_" + file.filename, as_attachment=True)

    # List of languages supported by DeepL
    languages = [
        "BG", "CS", "DA", "DE", "EL", "EN-GB", "EN-US", "ES", "ET", "FI", "FR", "HU", "IT", "JA", "LT", "LV", "NL", "PL", "PT-PT", "PT-BR", "RO", "RU", "SK", "SL", "SV", "ZH","KO"
    ]
    return render_template('index.html', languages=languages)

if __name__ == "__main__":
    app.run(debug=True)
