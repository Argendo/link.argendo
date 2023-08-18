import os, uuid, sqlite3
import qrcode
from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

# Директория для сохранения QR-кодов
qrcodes_dir = os.path.join(app.static_folder, 'qrcodes')
os.makedirs(qrcodes_dir, exist_ok=True)

conn = sqlite3.connect('urls.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS urls
             (id INTEGER PRIMARY KEY AUTOINCREMENT,
              original_url TEXT NOT NULL,
              short_url TEXT NOT NULL)''')
conn.commit()
conn.close()

def create_short_url():
    return str(uuid.uuid4().hex)[:8]

def generate_qr_code(short_url):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(short_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img

def save_qr_code(short_url):
    qr_code = generate_qr_code(short_url)
    qr_code_filename = f'{short_url}.png'
    qr_code_path = os.path.join(qrcodes_dir, qr_code_filename)
    qr_code.save(qr_code_path)
    return qr_code_filename

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        original_url = request.form['original_url']
        if original_url:
            short_url = create_short_url()
            conn = sqlite3.connect('urls.db')
            c = conn.cursor()

            short_url = create_short_url()
            c.execute("INSERT INTO urls (original_url, short_url) VALUES (?, ?)",
                      (original_url, short_url))

            conn.commit()
            conn.close()
            qr_code_filename = save_qr_code(short_url)
            return render_template('result.html', short_url=short_url, qr_code_filename=qr_code_filename)
    return render_template('index.html')

@app.route('/<short_url>', methods=['GET'])
def redirect_to_original_url(short_url):
    conn = sqlite3.connect('urls.db')
    c = conn.cursor()

    c.execute("SELECT original_url FROM urls WHERE short_url=?", (short_url,))
    result = c.fetchone()

    conn.close()

    if result:
        original_url = result[0]
        if not original_url.startswith(('http://', 'https://')):
            original_url = 'http://' + original_url
        return redirect(original_url, code=302)
    else:
        return render_template('error.html', message='Short URL not found'), 404


if __name__ == '__main__':
    app.run(debug=True)
