import os, logging, math
from flask import Flask, request, render_template_string, abort, send_from_directory, jsonify, make_response
from werkzeug.utils import secure_filename

# المخازن العامة - الربط الأساسي
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

# كتم الـ Logs المزعجة
logging.getLogger('werkzeug').setLevel(logging.ERROR)

@app.route('/')
def index():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    
    # واجهة الموبايل مع عرض النصوص والملفات المتاحة
    return render_template_string('''
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { background: #0c0c0c; color: #eee; font-family: sans-serif; text-align: center; padding: 20px; }
                .box { background: #1a1a1a; padding: 15px; border: 1px solid #333; border-radius: 8px; margin-bottom: 15px; }
                button { background: #007bff; color: #fff; border: none; padding: 10px; width: 100%; border-radius: 5px; cursor: pointer; }
                .clip-area { background: #222; padding: 10px; border: 1px dashed #555; margin: 10px 0; word-break: break-all; color: #00ff00; }
                h3 { color: #a349a4; margin-top: 0; }
            </style>
        </head>
        <body>
            <h3>Hel-Sync Pro Mobile</h3>
            <div class="box">
                <h4>PC Clipboard</h4>
                <div class="clip-area" id="cb">{{ clip }}</div>
                <button onclick="location.reload()">Refresh Content</button>
            </div>
            <div class="box">
                <h4>Send to PC</h4>
                <form action="/upload" method="post" enctype="multipart/form-data">
                    <input type="hidden" name="token" value="{{token}}">
                    <input type="file" name="files" multiple style="margin-bottom:10px;">
                    <button type="submit" style="background:#a349a4;">Upload Files</button>
                </form>
            </div>
            <div class="box">
                <h4>Available for Download</h4>
                {% for f in f_list %}
                    <div style="text-align:left; border-bottom:1px solid #333; padding:5px;">
                        <span>📄 {{ f }}</span>
                        <a href="/download/{{ loop.index0 }}?token={{token}}"><button style="width:auto; float:right; background:#28a745; padding:2px 10px;">Get</button></a>
                        <div style="clear:both;"></div>
                    </div>
                {% endfor %}
            </div>
            <script>
                setInterval(() => {
                    fetch('/get_clip?token={{token}}').then(r => r.json()).then(d => {
                        if(d.text) document.getElementById('cb').innerText = d.text;
                    });
                }, 3000);
            </script>
        </body>
        </html>
    ''', token=token, clip=CLIP_HISTORY.get(ACCESS_TOKEN, "No text shared yet"), f_list=[os.path.basename(x) for x in FILES_TO_SHARE])

@app.route('/upload', methods=['POST'])
def upload():
    token = request.form.get('token')
    if token != ACCESS_TOKEN: abort(403)
    files = request.files.getlist('files')
    
    if permission_callback:
        # حساب الحجم لطلب الإذن
        ts = 0
        for f in files: f.seek(0, 2); ts += f.tell(); f.seek(0)
        
        def fmt(s):
            i = int(math.floor(math.log(s, 1024))) if s > 0 else 0
            return f"{round(s/math.pow(1024,i),2)} {['B','KB','MB','GB'][i]}"
            
        if not permission_callback(len(files), fmt(ts)):
            return "PC rejected transfer", 403

    for file in files:
        if file.filename:
            fn = secure_filename(file.filename)
            path = os.path.join(UPLOAD_DIR, fn)
            file.save(path)
            # إرسال إشارة للـ GUI عشان الملف يظهر في الـ List
            if gui_callback:
                gui_callback(fn, os.path.getsize(path))
    return "Done!"

@app.route('/download/<int:file_id>')
def download(file_id):
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    if 0 <= file_id < len(FILES_TO_SHARE):
        path = FILES_TO_SHARE[file_id]
        # إجبار التحميل (Download) بدلاً من الفتح (Preview)
        resp = make_response(send_from_directory(os.path.dirname(path), os.path.basename(path)))
        resp.headers["Content-Disposition"] = f"attachment; filename={os.path.basename(path)}"
        return resp
    return "Not Found", 404

@app.route('/get_clip')
def get_clip():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    return jsonify({"text": CLIP_HISTORY.get(ACCESS_TOKEN, "")})

# الدالة المطلوبة لملف main.py
def start_network_service(gui_cb, clip_cb, token, perm_cb, prog_cb):
    global gui_callback, clip_callback, ACCESS_TOKEN, permission_callback, progress_callback
    gui_callback = gui_cb
    clip_callback = clip_cb
    ACCESS_TOKEN = token
    permission_callback = perm_cb
    progress_callback = prog_cb
    app.run(host='0.0.0.0', port=8080, threaded=True, debug=False)
