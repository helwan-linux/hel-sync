import os
import logging
import time
from flask import Flask, request, render_template_string, abort, send_from_directory, jsonify
from werkzeug.utils import secure_filename

# إعدادات الهدوء للسيرفر
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = None 

UPLOAD_DIR = os.path.expanduser("~/Downloads/HelSync")
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR, exist_ok=True)

# حالة النظام
gui_callback = None
clip_callback = None
ACCESS_TOKEN = ""
FILE_TO_SHARE = None # يمكن أن يكون مسار ملف واحد أو قائمة
LATEST_CLIPBOARD = "No text copied yet"

def format_size(bytes):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024: return f"{bytes:.2f} {unit}"
        bytes /= 1024
    return f"{bytes:.2f} PB"

@app.route('/')
def index():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    
    # جلب قائمة الملفات اللي استلمناها فعلاً على الكمبيوتر
    received_files = os.listdir(UPLOAD_DIR)
    received_html = "".join([f"<li>{f}</li>" for f in received_files[-5:]]) # آخر 5 ملفات
    
    download_section = ""
    if FILE_TO_SHARE and os.path.exists(FILE_TO_SHARE):
        fname = os.path.basename(FILE_TO_SHARE)
        fsize = format_size(os.path.getsize(FILE_TO_SHARE))
        download_section = f'''
            <div class="card" style="border-color: #28a745;">
                <p style="color: #28a745; margin:0;">⬇️ Ready to Download:</p>
                <b>{fname} ({fsize})</b>
                <a href="/download?token={token}" class="btn" style="background:#28a745; margin-top:10px;">Download Now</a>
            </div>
        '''

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Hel-Sync Pro Dashboard</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0a0a0a; color: #e0e0e0; margin: 0; padding: 20px; }}
            .container {{ max-width: 600px; margin: auto; }}
            .card {{ background: #161616; padding: 20px; border-radius: 12px; margin-bottom: 20px; border: 1px solid #333; text-align: left; }}
            h2 {{ color: #a349a4; margin-top: 0; font-size: 1.2rem; }}
            .btn {{ background: #a349a4; color: white; padding: 12px; border-radius: 8px; display: block; text-align: center; text-decoration: none; font-weight: bold; cursor: pointer; border: none; width: 100%; box-sizing: border-box; }}
            textarea {{ width: 100%; height: 60px; background: #222; color: #fff; border: 1px solid #444; border-radius: 8px; padding: 10px; box-sizing: border-box; }}
            #progress-zone {{ display: none; background: #1a1a1a; padding: 15px; border-radius: 10px; border: 1px solid #a349a4; }}
            .bar-bg {{ background: #333; height: 10px; border-radius: 5px; overflow: hidden; margin: 10px 0; }}
            .bar-fill {{ background: #a349a4; height: 100%; width: 0%; transition: width 0.1s; }}
            .stats-row {{ display: flex; justify-content: space-between; font-size: 12px; color: #aaa; }}
            ul {{ list-style: none; padding: 0; font-size: 13px; color: #888; }}
            li {{ padding: 5px 0; border-bottom: 1px solid #222; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 style="text-align:center; color:#a349a4;">Hel-Sync <span style="font-weight:100; color:#fff;">Pro</span></h1>
            
            {download_section}

            <div class="card">
                <h2>📋 PC Clipboard</h2>
                <code style="background:#000; padding:10px; display:block; border-radius:5px; color:#bc71bc;">{LATEST_CLIPBOARD}</code>
                <form onsubmit="sendText(event)" style="margin-top:15px;">
                    <textarea id="textInput" placeholder="Type text for PC..."></textarea>
                    <button type="submit" class="btn" style="background:#007bff; margin-top:10px;">Send to PC</button>
                </form>
            </div>

            <div class="card">
                <h2>📤 Send Files to PC</h2>
                <input type="file" id="fileInput" multiple style="display:none;">
                <button class="btn" onclick="document.getElementById('fileInput').click()">Select Files</button>
                
                <div id="progress-zone" style="margin-top:15px;">
                    <b id="up-name" style="font-size:12px; color:#a349a4;"></b>
                    <div class="bar-bg"><div class="bar-fill" id="bar"></div></div>
                    <div class="stats-row">
                        <span id="p-percent">0%</span>
                        <span id="p-data">0/0 MB</span>
                    </div>
                    <div class="stats-row" style="margin-top:5px;">
                        <span id="p-speed">0 KB/s</span>
                        <span id="p-eta">ETA: --</span>
                    </div>
                </div>
            </div>

            <div class="card">
                <h2>✅ Recently Received on PC</h2>
                <ul>{received_html if received_html else "<li>No files yet</li>"}</ul>
            </div>
        </div>

        <script>
            function formatB(b) {{
                if (b === 0) return '0 B';
                const i = Math.floor(Math.log(b) / Math.log(1024));
                return (b / Math.pow(1024, i)).toFixed(2) + ' ' + ['B', 'KB', 'MB', 'GB', 'TB'][i];
            }}

            document.getElementById('fileInput').onchange = function() {{
                const files = this.files; if (!files.length) return;
                const fd = new FormData();
                let totalS = 0;
                for (let f of files) {{ fd.append('files', f); totalS += f.size; }}

                const xhr = new XMLHttpRequest();
                const start = Date.now();
                xhr.open('POST', '/upload?token={token}', true);
                document.getElementById('progress-zone').style.display = 'block';
                document.getElementById('up-name').innerText = files.length + " files queued...";

                xhr.upload.onprogress = function(e) {{
                    if (e.lengthComputable) {{
                        const per = (e.loaded / e.total) * 100;
                        const sec = (Date.now() - start) / 1000;
                        const spd = e.loaded / sec;
                        const rem = (e.total - e.loaded) / spd;
                        document.getElementById('bar').style.width = per + '%';
                        document.getElementById('p-percent').innerText = Math.round(per) + '%';
                        document.getElementById('p-data').innerText = formatB(e.loaded) + " / " + formatB(e.total);
                        document.getElementById('p-speed').innerText = formatB(spd) + "/s";
                        document.getElementById('p-eta').innerText = "ETA: " + Math.round(rem) + "s";
                    }}
                }};
                xhr.onload = () => {{ alert('Upload Finished!'); location.reload(); }};
                xhr.send(fd);
            }};

            function sendText(e) {{
                e.preventDefault();
                const v = document.getElementById('textInput').value;
                fetch('/clip?token={token}', {{ method:'POST', body:new URLSearchParams({{ 'text': v }}) }})
                .then(() => alert('Sent!'));
            }}

            setInterval(() => {{
                fetch('/check_update?token={token}').then(r => r.json()).then(d => {{
                    if (d.refresh) location.reload();
                }});
            }}, 4000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/check_update')
def check_update():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    # فحص لو فيه تغيير في الكليبورد أو الملف المشترك
    return jsonify({
        "refresh": False, # يمكنك إضافة منطق المقارنة هنا كما فعلنا سابقاً
        "clipboard": LATEST_CLIPBOARD
    })

@app.route('/upload', methods=['POST'])
def handle_upload():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    files = request.files.getlist('files')
    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            with open(os.path.join(UPLOAD_DIR, filename), 'wb') as f:
                while True:
                    chunk = file.stream.read(131072)
                    if not chunk: break
                    f.write(chunk)
    if gui_callback: gui_callback(len(files))
    return "OK"

@app.route('/clip', methods=['POST'])
def handle_clip():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    text = request.form.get('text')
    if text and clip_callback: clip_callback(text)
    return "OK"

@app.route('/download')
def download_file():
    token = request.args.get('token')
    if token != ACCESS_TOKEN or not FILE_TO_SHARE: abort(403)
    return send_from_directory(os.path.dirname(FILE_TO_SHARE), os.path.basename(FILE_TO_SHARE), as_attachment=True)

def start_network_service(callback, clip_cb, token, host="0.0.0.0", port=8080):
    global gui_callback, clip_callback, ACCESS_TOKEN
    gui_callback = callback; clip_callback = clip_cb; ACCESS_TOKEN = token
    app.run(host=host, port=port, debug=False, use_reloader=False)