import os, logging, math
from flask import Flask, request, render_template_string, abort, send_from_directory, jsonify
from werkzeug.utils import secure_filename

# إعدادات المخزن العام للبيانات للربط مع الـ GUI والـ main
CLIP_HISTORY = {} 
FILES_TO_SHARE = [] 
ACCESS_TOKEN = ""
gui_callback = None
clip_callback = None
permission_callback = None 
progress_callback = None 

app = Flask(__name__)
# مسار التحميل الافتراضي
UPLOAD_DIR = os.path.expanduser("~/Downloads/HelSync")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# إخفاء سجلات Flask المزعجة
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.route('/')
def index():
    token = request.args.get('token')
    if token != ACCESS_TOKEN:
        abort(403)
    
    # واجهة الموبايل (HTML/CSS)
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Hel-Sync Portal</title>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { background: #0c0c0c; color: #eee; font-family: sans-serif; text-align: center; padding: 20px; }
                .card { background: #1a1a1a; padding: 20px; border-radius: 10px; border: 1px solid #333; margin-bottom: 20px; }
                button { background: #007bff; color: white; border: none; padding: 12px 25px; border-radius: 5px; font-size: 16px; width: 100%; cursor: pointer; }
                input[type="file"] { margin: 15px 0; color: #888; }
                .clip-area { background: #222; padding: 15px; border-radius: 5px; min-height: 50px; margin: 10px 0; word-break: break-all; border: 1px dashed #444; }
                h3 { color: #a349a4; }
            </style>
        </head>
        <body>
            <h1>Hel-Sync Mobile</h1>
            <div class="card">
                <h3>Shared Text from PC</h3>
                <div class="clip-area" id="clipBox">Waiting for text...</div>
                <button onclick="fetchClip()">Refresh Text</button>
            </div>
            <div class="card">
                <h3>Send Files to PC</h3>
                <form action="/upload" method="post" enctype="multipart/form-data">
                    <input type="hidden" name="token" value="{{token}}">
                    <input type="file" name="files" multiple>
                    <button type="submit" style="background: #a349a4;">Upload Files</button>
                </form>
            </div>
            <div class="card">
                <h3>Download from PC</h3>
                <div id="fileList">
                    {% if files %}
                        {% for file in files %}
                            <div style="margin: 10px 0; border-bottom: 1px solid #333; padding-bottom: 10px; text-align: left;">
                                <span>📄 {{ file.name }}</span>
                                <a href="/download/{{ loop.index0 }}?token={{token}}"><button style="background:#28a745; margin-top:5px; width:auto; padding:5px 15px; float:right; font-size:12px;">Download</button></a>
                                <div style="clear:both;"></div>
                            </div>
                        {% endfor %}
                    {% else %}
                        <p style="color:#666;">No files shared yet.</p>
                    {% endif %}
                </div>
            </div>
            <script>
                function fetchClip() {
                    fetch('/get_clip?token={{token}}').then(r => r.json()).then(data => {
                        document.getElementById('clipBox').innerText = data.text || "No text shared";
                    });
                }
                setInterval(fetchClip, 3000);
                fetchClip();
            </script>
        </body>
        </html>
    ''', token=token, files=[{"name": os.path.basename(f)} for f in FILES_TO_SHARE])

@app.route('/upload', methods=['POST'])
def upload():
    token = request.form.get('token')
    if token != ACCESS_TOKEN: abort(403)
    
    files = request.files.getlist('files')
    if not files: return "No files selected", 400

    if permission_callback:
        # حساب الحجم الكلي
        total_size = 0
        for f in files:
            f.seek(0, os.SEEK_END)
            total_size += f.tell()
            f.seek(0)
            
        def format_bytes(size):
            if size == 0: return "0B"
            i = int(math.floor(math.log(size, 1024)))
            return f"{round(size / math.pow(1024, i), 2)} {['B', 'KB', 'MB', 'GB'][i]}"

        if not permission_callback(len(files), format_bytes(total_size)):
            return "PC rejected the transfer", 403

    for file in files:
        if file.filename:
            filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_DIR, filename)
            file.save(path)
            if gui_callback:
                gui_callback(filename, os.path.getsize(path))
    
    return "Files uploaded successfully!"

@app.route('/download/<int:file_id>')
def download(file_id):
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    
    if 0 <= file_id < len(FILES_TO_SHARE):
        file_path = FILES_TO_SHARE[file_id]
        return send_from_directory(os.path.dirname(file_path), os.path.basename(file_path))
    return "File not found", 404

@app.route('/get_clip')
def get_clip():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    return jsonify({"text": CLIP_HISTORY.get(token, "")})

# --- الدالة المطلوبة التي يستدعيها ملف main.py ---
def start_network_service(gui_cb, clip_cb, token, perm_cb, prog_cb):
    global gui_callback, clip_callback, ACCESS_TOKEN, permission_callback, progress_callback
    gui_callback = gui_cb
    clip_callback = clip_cb
    ACCESS_TOKEN = token
    permission_callback = perm_cb
    progress_callback = prog_cb
    
    # تشغيل السيرفر ليكون متاحاً للموبايل على نفس الشبكة
    app.run(host='0.0.0.0', port=8080, threaded=True, debug=False)
