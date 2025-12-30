import os, logging, math, shutil
from flask import Flask, request, render_template_string, abort, send_from_directory, jsonify, make_response
from werkzeug.utils import secure_filename

CLIP_HISTORY = {} 
FILES_TO_SHARE = [] 
ACCESS_TOKEN = ""
gui_callback = None
clip_callback = None
permission_callback = None 

app = Flask(__name__)
# فولدر الاستلام النهائي
UPLOAD_DIR = os.path.expanduser("~/Downloads/HelSync")
# فولدر مؤقت للاستلام الفوري
TEMP_DIR = os.path.join(UPLOAD_DIR, "temp")
os.makedirs(TEMP_DIR, exist_ok=True)

logging.getLogger('werkzeug').setLevel(logging.ERROR)

@app.route('/')
def index():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    
    # تجهيز قائمة الملفات المتاحة للتحميل من الكمبيوتر
    display_files = [os.path.basename(f) for f in FILES_TO_SHARE]
    
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { background: #0c0c0c; color: #eee; font-family: sans-serif; text-align: center; padding: 15px; }
                .card { background: #1a1a1a; padding: 15px; border-radius: 10px; border: 1px solid #333; margin-bottom: 15px; }
                button { background: #007bff; color: white; border: none; padding: 12px; border-radius: 5px; width: 100%; cursor: pointer; font-weight: bold; }
                .selected-list { text-align: left; font-size: 12px; color: #aaa; margin: 10px 0; background: #222; border-radius: 5px; padding: 10px; }
                #progContainer { width: 100%; background: #333; height: 15px; border-radius: 8px; margin: 10px 0; display: none; overflow: hidden; border: 1px solid #444; }
                #progBar { width: 0%; height: 100%; background: linear-gradient(90deg, #007bff, #00ff00); transition: width 0.1s; }
                .file-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #333; text-align: left; }
                h4 { color: #a349a4; margin: 5px 0; border-bottom: 1px solid #444; padding-bottom: 5px; }
            </style>
        </head>
        <body>
            <h3>Hel-Sync Pro</h3>
            
            <div class="card">
                <h4>↑ Upload to PC</h4>
                <input type="file" id="fileInput" multiple onchange="updateList()" style="color:#888; width: 100%;">
                <div id="fileList" class="selected-list">No files selected</div>
                <div id="progContainer"><div id="progBar"></div></div>
                <div id="status" style="font-size:12px; color:#0f0;"></div>
                <button id="upBtn" onclick="upload()">START UPLOAD</button>
            </div>

            <div class="card">
                <h4>↓ Download from PC</h4>
                <div id="download_list">
                    {% if f_list %}
                        {% for f in f_list %}
                            <div class="file-item">
                                <span style="font-size: 13px;">📄 {{ f }}</span>
                                <a href="/download/{{ loop.index0 }}?token={{token}}"><button style="width:auto; padding:5px 15px; background:#28a745; font-size:12px;">GET</button></a>
                            </div>
                        {% endfor %}
                    {% else %}
                        <p style="color:#666; font-size:12px;">No files shared from PC yet.</p>
                    {% endif %}
                </div>
            </div>

            <div class="card">
                <h4>Text Clipboard</h4>
                <div id="pc_clip" style="background:#000; padding:10px; border:1px dashed #555; color:#0f0; margin-bottom:10px; font-size:13px;">{{ clip }}</div>
                <textarea id="mob_txt" placeholder="Type text for PC..." style="width:100%; height:60px; background:#222; color:#fff; border:1px solid #444; border-radius:5px; padding:5px; box-sizing:border-box;"></textarea>
                <button onclick="sendTxt()" style="margin-top:10px; background:#a349a4;">SEND TEXT</button>
            </div>

            <script>
                function updateList() {
                    const input = document.getElementById('fileInput');
                    const list = document.getElementById('fileList');
                    list.innerHTML = "";
                    if(input.files.length === 0) { list.innerText = "No files selected"; return; }
                    for(let i=0; i<input.files.length; i++){
                        list.innerHTML += "• " + input.files[i].name + "<br>";
                    }
                }

                function upload() {
                    const input = document.getElementById('fileInput');
                    if(input.files.length === 0) return alert("Please select files!");
                    
                    const formData = new FormData();
                    formData.append("token", "{{token}}");
                    for(let f of input.files) formData.append("files", f);

                    document.getElementById('progContainer').style.display = "block";
                    const xhr = new XMLHttpRequest();
                    xhr.open("POST", "/upload", true);
                    
                    xhr.upload.onprogress = (e) => {
                        const p = Math.round((e.loaded / e.total) * 100);
                        document.getElementById('progBar').style.width = p + "%";
                        document.getElementById('status').innerText = "Uploading: " + p + "%";
                    };

                    xhr.onload = () => {
                        if(xhr.status === 200) {
                            alert("Success! Waiting for PC to accept.");
                            location.reload();
                        } else {
                            alert("Error: " + xhr.responseText);
                        }
                    };
                    xhr.send(formData);
                }

                function sendTxt() {
                    const val = document.getElementById('mob_txt').value;
                    if(!val) return;
                    fetch('/send_from_mobile?token={{token}}', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({text: val})
                    }).then(() => { alert('Text Sent'); document.getElementById('mob_txt').value=''; });
                }

                setInterval(()=> {
                    fetch('/get_clip?token={{token}}').then(r=>r.json()).then(d=>{
                        if(d.text) document.getElementById('pc_clip').innerText=d.text;
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
    
    received_files = []
    total_size = 0
    for file in files:
        if file.filename:
            fn = secure_filename(file.filename)
            temp_path = os.path.join(TEMP_DIR, fn)
            file.save(temp_path)
            size = os.path.getsize(temp_path)
            received_files.append((temp_path, fn, size))
            total_size += size

    if permission_callback:
        def fmt(s): return f"{round(s/1024/1024, 2)} MB"
        if permission_callback(len(received_files), fmt(total_size)):
            for temp_path, fn, size in received_files:
                final_path = os.path.join(UPLOAD_DIR, fn)
                shutil.move(temp_path, final_path)
                if gui_callback: gui_callback(fn, size)
            return "OK"
        else:
            for temp_path, _, _ in received_files: os.remove(temp_path)
            return "PC Rejected", 403
    return "OK"

@app.route('/send_from_mobile', methods=['POST'])
def send_from_mobile():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    data = request.get_json()
    if clip_callback and data.get('text'): clip_callback(data['text'])
    return jsonify({"status": "ok"})

@app.route('/download/<int:file_id>')
def download(file_id):
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    # التأكد إن FILES_TO_SHARE فيها ملفات
    if 0 <= file_id < len(FILES_TO_SHARE):
        p = FILES_TO_SHARE[file_id]
        if os.path.exists(p):
            resp = make_response(send_from_directory(os.path.dirname(p), os.path.basename(p)))
            resp.headers["Content-Disposition"] = f"attachment; filename={os.path.basename(p)}"
            return resp
    return "File Not Found", 404

@app.route('/get_clip')
def get_clip():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    return jsonify({"text": CLIP_HISTORY.get(ACCESS_TOKEN, "")})

def start_network_service(gui_cb, clip_cb, token, perm_cb, prog_cb):
    global gui_callback, clip_callback, ACCESS_TOKEN, permission_callback
    gui_callback, clip_callback, ACCESS_TOKEN, permission_callback = gui_cb, clip_cb, token, perm_cb
    app.run(host='0.0.0.0', port=8080, threaded=True, debug=False)
