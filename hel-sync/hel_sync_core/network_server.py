import os, logging
from flask import Flask, request, render_template_string, abort, send_from_directory, jsonify
from werkzeug.utils import secure_filename

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = None 

UPLOAD_DIR = os.path.expanduser("~/Downloads/HelSync")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# تحويل المتغير لقائمة لاستيعاب كل الملفات المبعوثة من الكمبيوتر
FILES_TO_SHARE = [] 
ACCESS_TOKEN = ""
gui_callback = None

@app.route('/')
def index():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    
    # توليد أزرار لكل ملف في القائمة
    files_list_html = ""
    for i, path in enumerate(FILES_TO_SHARE):
        name = os.path.basename(path)
        files_list_html += f'''
        <div style="display:flex; justify-content:space-between; padding:10px; border-bottom:1px solid #333;">
            <span>📄 {name}</span>
            <a href="/download/{i}?token={token}" style="color:#28a745; text-decoration:none; font-weight:bold;">Download</a>
        </div>'''

    return render_template_string(f"""
    <html>
    <head><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{ background:#0c0c0c; color:#eee; font-family:sans-serif; padding:20px; }}
        .box {{ background:#161616; padding:15px; border-radius:10px; margin-bottom:20px; border:1px solid #333; }}
        .btn {{ background:#a349a4; color:white; padding:10px; border:none; width:100%; border-radius:5px; cursor:pointer; }}
    </style></head>
    <body>
        <div class="box"><h3>Files from PC</h3>{files_list_html if FILES_TO_SHARE else "No files shared"}</div>
        <div class="box"><h3>Send to PC</h3>
            <input type="file" id="f" multiple style="display:none">
            <button class="btn" onclick="document.getElementById('f').click()">Select & Send All</button>
            <div id="prog" style="margin-top:10px; font-size:12px; color:#aaa;"></div>
        </div>
        <script>
            document.getElementById('f').onchange = function() {{
                const fd = new FormData();
                for(let file of this.files) fd.append('files', file);
                const xhr = new XMLHttpRequest();
                xhr.open('POST', '/upload?token={token}', true);
                xhr.upload.onprogress = (e) => {{
                    document.getElementById('prog').innerText = "Uploading: " + Math.round((e.loaded/e.total)*100) + "%";
                }};
                xhr.onload = () => {{ alert('Sent!'); location.reload(); }};
                xhr.send(fd);
            }};
        </script>
    </body></html>
    """)

@app.route('/upload', methods=['POST'])
def handle_upload():
    if request.args.get('token') != ACCESS_TOKEN: abort(403)
    files = request.files.getlist('files')
    for file in files:
        if file.filename:
            fname = secure_filename(file.filename)
            file.save(os.path.join(UPLOAD_DIR, fname))
            if gui_callback: gui_callback(fname) # تحديث الواجهة باسم كل ملف يوصل
    return "OK"

@app.route('/download/<int:fid>')
def download(fid):
    if request.args.get('token') != ACCESS_TOKEN: abort(403)
    if fid < len(FILES_TO_SHARE):
        path = FILES_TO_SHARE[fid]
        return send_from_directory(os.path.dirname(path), os.path.basename(path))
    abort(404)

def start_network_service(callback, clip_cb, token, host="0.0.0.0", port=8080):
    global gui_callback, ACCESS_TOKEN
    gui_callback = callback; ACCESS_TOKEN = token
    app.run(host=host, port=port, threaded=True) # Threaded=True تمنع التعارض