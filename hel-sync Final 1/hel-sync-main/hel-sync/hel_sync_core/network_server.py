import os, logging, math
from flask import Flask, request, render_template_string, abort, send_from_directory, jsonify
from werkzeug.utils import secure_filename

# إيقاف رسائل Flask المزعجة في الترمينال للحفاظ على نظافة المخرجات
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# تحديد مسار التحميل المتوافق مع Arch Linux
UPLOAD_DIR = os.path.expanduser("~/Downloads/HelSync")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# متغيرات الحالة العالمية للربط مع الواجهة (GUI)
FILES_TO_SHARE = [] 
ACCESS_TOKEN = ""
gui_callback = None
clip_callback = None
permission_callback = None 
progress_callback = None # إضافة للعداد

def format_size(size):
    """تحويل الحجم من بايت إلى وحدات مقروءة"""
    if size == 0: return "0B"
    i = int(math.floor(math.log(size, 1024)))
    p = math.pow(1024, i)
    return f"{round(size / p, 2)} {['B', 'KB', 'MB', 'GB'][i]}"

@app.route('/')
def index():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    
    # بناء قائمة الملفات المتاحة للتحميل على الموبايل
    files_html = "".join([f'''
        <div style="display:flex; justify-content:space-between; padding:12px; border-bottom:1px solid #444; align-items:center;">
            <span style="color:#eee">📄 {os.path.basename(p)} ({format_size(os.path.getsize(p))})</span>
            <a href="/download/{i}?token={token}" style="background:#a349a4; color:white; text-decoration:none; padding:8px 15px; border-radius:5px; font-weight:bold; font-size:14px;">Download</a>
        </div>''' for i, p in enumerate(FILES_TO_SHARE) if os.path.exists(p)])

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Hel-Sync Portal</title>
        <style>
            body { background:#0c0c0c; color:#eee; font-family:sans-serif; margin:0; padding:15px; }
            .card { background:#1a1a1a; padding:15px; border-radius:12px; margin-bottom:15px; border:1px solid #333; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
            h3 { color:#a349a4; margin-top:0; border-bottom:1px solid #333; padding-bottom:8px; }
            input[type="file"] { display:none; }
            .btn { background:#007bff; color:white; padding:15px; display:block; text-align:center; border-radius:8px; cursor:pointer; font-weight:bold; margin-top:10px; transition:0.3s; }
            .btn:active { transform: scale(0.98); background:#0056b3; }
            textarea { width:100%; background:#222; border:1px solid #444; color:white; padding:10px; border-radius:5px; box-sizing:border-box; resize:none; }
            #status { margin-top:10px; color:#888; text-align:center; font-size:13px; }
        </style>
    </head>
    <body>
        <h2 style="text-align:center; color:#a349a4;">Hel-Sync Portal</h2>
        
        <div class="card">
            <h3>📥 Downloads from PC</h3>
            ''' + (files_html if files_html else '<p style="color:#666; text-align:center;">No files shared yet.</p>') + '''
        </div>

        <div class="card">
            <h3>📤 Upload to PC</h3>
            <label class="btn" for="f">SELECT FILES</label>
            <input type="file" id="f" multiple onchange="upload()">
            <div id="status">Ready to sync</div>
        </div>

        <div class="card">
            <h3>✂️ Shared Clipboard</h3>
            <textarea id="clipText" rows="3" placeholder="Type text to send to PC..."></textarea>
            <div class="btn" onclick="sendText()" style="background:#28a745; padding:10px;">SEND TEXT</div>
        </div>

        <script>
            function upload() {
                let files = document.getElementById('f').files;
                if(files.length === 0) return;
                let size = 0; for(let f of files) size += f.size;
                document.getElementById('status').innerText = "Requesting permission...";

                fetch(`/ask?count=${files.length}&size=${size}&token={{token}}`)
                .then(r => r.json())
                .then(data => {
                    if(data.ok) {
                        let fd = new FormData();
                        for(let f of files) fd.append('files', f);
                        document.getElementById('status').innerText = "Uploading to PC...";
                        fetch(`/upload?token={{token}}`, {method:'POST', body:fd})
                        .then(() => {
                            document.getElementById('status').innerText = "✅ Upload Successful!";
                            setTimeout(()=>location.reload(), 1500);
                        });
                    } else {
                        document.getElementById('status').innerText = "❌ PC rejected the transfer.";
                    }
                });
            }

            function sendText() {
                let txt = document.getElementById('clipText').value;
                if(!txt) return;
                fetch(`/clip?text=${encodeURIComponent(txt)}&token={{token}}`)
                .then(r => {
                    if(r.ok) { alert("Text sent to PC!"); document.getElementById('clipText').value = ""; }
                });
            }
        </script>
    </body>
    </html>
    ''', token=token)

@app.route('/ask')
def ask():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    if permission_callback:
        count = request.args.get('count')
        size = request.args.get('size')
        return jsonify({"ok": permission_callback(count, size)})
    return jsonify({"ok": False})

@app.route('/upload', methods=['POST'])
def handle_upload():
    if request.args.get('token') != ACCESS_TOKEN: abort(403)
    files = request.files.getlist('files')
    total = len(files)
    for i, file in enumerate(files):
        if file.filename:
            fname = secure_filename(file.filename)
            fpath = os.path.join(UPLOAD_DIR, fname)
            # تحديث العداد في الواجهة
            if progress_callback:
                progress_callback(((i + 1) / total) * 100, fname, i + 1, total)
            file.save(fpath)
            if gui_callback:
                gui_callback(fname, os.path.getsize(fpath))
    return "OK"

@app.route('/download/<int:fid>')
def download(fid):
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    if 0 <= fid < len(FILES_TO_SHARE):
        p = FILES_TO_SHARE[fid]
        # إجبار التحميل (as_attachment=True) لمنع عرض الملفات النصية في المتصفح
        return send_from_directory(os.path.dirname(p), os.path.basename(p), as_attachment=True)
    abort(404)

@app.route('/clip')
def clip():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    text = request.args.get('text')
    if text and clip_callback:
        clip_callback(text)
        return "OK"
    return "No text provided", 400

def start_network_service(gui_cb, clip_cb, token, perm_cb, prog_cb):
    global gui_callback, clip_callback, ACCESS_TOKEN, permission_callback, progress_callback
    gui_callback = gui_cb
    clip_callback = clip_cb
    ACCESS_TOKEN = token
    permission_callback = perm_cb
    progress_callback = prog_cb
    app.run(host='0.0.0.0', port=8080, threaded=True, debug=False)
