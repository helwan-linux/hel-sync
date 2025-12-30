import os, logging, math
from flask import Flask, request, render_template_string, abort, send_from_directory, jsonify, make_response
from werkzeug.utils import secure_filename

# المخازن العامة للبيانات للربط مع الـ GUI
CLIP_HISTORY = {} 
FILES_TO_SHARE = [] 
ACCESS_TOKEN = ""
gui_callback = None
clip_callback = None
permission_callback = None 
progress_callback = None 

app = Flask(__name__)
UPLOAD_DIR = os.path.expanduser("~/Downloads/HelSync")
os.makedirs(UPLOAD_DIR, exist_ok=True)

logging.getLogger('werkzeug').setLevel(logging.ERROR)

@app.route('/')
def index():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    
    display_files = [os.path.basename(f) for f in FILES_TO_SHARE]
    
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { background: #0c0c0c; color: #eee; font-family: sans-serif; text-align: center; padding: 15px; }
                .card { background: #1a1a1a; padding: 15px; border-radius: 10px; border: 1px solid #333; margin-bottom: 15px; }
                button { background: #007bff; color: white; border: none; padding: 10px; border-radius: 5px; width: 100%; cursor: pointer; font-weight: bold; }
                textarea { width: 100%; background: #222; color: #0f0; border: 1px solid #444; padding: 10px; box-sizing: border-box; border-radius: 5px; }
                .file-item { display: flex; justify-content: space-between; align-items: center; padding: 8px; border-bottom: 1px solid #333; text-align: left; }
                .selected-list { text-align: left; font-size: 12px; color: #aaa; margin: 10px 0; background: #222; border-radius: 5px; padding: 5px; }
                h4 { color: #a349a4; margin: 5px 0; }
            </style>
        </head>
        <body>
            <h3>Hel-Sync Pro Portal</h3>
            
            <div class="card">
                <h4>Text Transfer</h4>
                <div id="pc_text" style="background:#000; padding:10px; margin-bottom:10px; border:1px dashed #555; color:#0f0;">{{ clip }}</div>
                <textarea id="mobile_input" placeholder="Type text to send to PC..."></textarea>
                <button onclick="sendText()" style="margin-top:5px; background:#a349a4;">SEND TEXT TO PC</button>
            </div>

            <div class="card">
                <h4>Upload to PC</h4>
                <form id="uploadForm" action="/upload" method="post" enctype="multipart/form-data">
                    <input type="hidden" name="token" value="{{token}}">
                    <input type="file" name="files" id="fileInput" multiple style="margin-bottom:10px;" onchange="updateSelectedList()">
                    <div id="selectedFiles" class="selected-list">No files selected yet</div>
                    <button type="submit">UPLOAD FILES</button>
                </form>
            </div>

            <div class="card">
                <h4>Download from PC</h4>
                {% if f_list %}
                    {% for f in f_list %}
                        <div class="file-item">
                            <span>📄 {{ f }}</span>
                            <a href="/download/{{ loop.index0 }}?token={{token}}"><button style="width:auto; padding:5px 15px; background:#28a745;">GET</button></a>
                        </div>
                    {% endfor %}
                {% else %}
                    <p style="color:#666;">No files shared from PC</p>
                {% endif %}
            </div>

            <script>
                function updateSelectedList() {
                    const input = document.getElementById('fileInput');
                    const list = document.getElementById('selectedFiles');
                    list.innerHTML = "<strong>Files to send:</strong><br>";
                    if(input.files.length === 0) { list.innerText = "No files selected"; return; }
                    for(let i=0; i<input.files.length; i++) {
                        list.innerHTML += (i+1) + ". " + input.files[i].name + " (" + (input.files[i].size/1024).toFixed(1) + " KB)<br>";
                    }
                }

                function sendText() {
                    const txt = document.getElementById('mobile_input').value;
                    if(!txt) return;
                    fetch('/send_from_mobile?token={{token}}', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({text: txt})
                    }).then(() => { document.getElementById('mobile_input').value = ''; alert('Text sent to PC!'); });
                }

                setInterval(() => {
                    fetch('/get_clip?token={{token}}').then(r => r.json()).then(d => {
                        if(d.text) document.getElementById('pc_text').innerText = d.text;
                    });
                }, 3000);
            </script>
        </body>
        </html>
    ''', token=token, clip=CLIP_HISTORY.get(ACCESS_TOKEN, "Waiting..."), f_list=display_files)

@app.route('/upload', methods=['POST'])
def upload():
    token = request.form.get('token')
    if token != ACCESS_TOKEN: abort(403)
    files = request.files.getlist('files')
    if not files: return "No files selected", 400

    if permission_callback:
        ts = 0
        for f in files: f.seek(0, 2); ts += f.tell(); f.seek(0)
        def fmt(s):
            i = int(math.floor(math.log(s, 1024))) if s > 0 else 0
            return f"{round(s/math.pow(1024,i),2)} {['B','KB','MB','GB'][i]}"
        if not permission_callback(len(files), fmt(ts)): return "PC denied transfer", 403

    for file in files:
        if file.filename:
            fn = secure_filename(file.filename)
            path = os.path.join(UPLOAD_DIR, fn)
            file.save(path)
            if gui_callback: gui_callback(fn, os.path.getsize(path))
    return render_template_string('<script>alert("Files uploaded successfully!"); window.location.href="/?token={{t}}";</script>', t=ACCESS_TOKEN)

@app.route('/send_from_mobile', methods=['POST'])
def send_from_mobile():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    data = request.get_json()
    if clip_callback and data.get('text'):
        clip_callback(data['text'])
    return jsonify({"status": "ok"})

@app.route('/download/<int:file_id>')
def download(file_id):
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    if 0 <= file_id < len(FILES_TO_SHARE):
        p = FILES_TO_SHARE[file_id]
        resp = make_response(send_from_directory(os.path.dirname(p), os.path.basename(p)))
        resp.headers["Content-Disposition"] = f"attachment; filename={os.path.basename(p)}"
        return resp
    return "Not Found", 404

@app.route('/get_clip')
def get_clip():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    return jsonify({"text": CLIP_HISTORY.get(ACCESS_TOKEN, "")})

def start_network_service(gui_cb, clip_cb, token, perm_cb, prog_cb):
    global gui_callback, clip_callback, ACCESS_TOKEN, permission_callback, progress_callback
    gui_callback, clip_callback, ACCESS_TOKEN, permission_callback, progress_callback = gui_cb, clip_cb, token, perm_cb, prog_cb
    app.run(host='0.0.0.0', port=8080, threaded=True, debug=False)
