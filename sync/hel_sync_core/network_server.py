import os, logging, math, shutil, pyautogui, platform, subprocess
from flask import Flask, request, render_template_string, abort, send_from_directory, jsonify, make_response 
from werkzeug.utils import secure_filename 
 
try: 
    import winsound 
except: 
    winsound = None 
 
CLIP_HISTORY = {}  
FILES_TO_SHARE = []  
ACCESS_TOKEN = "" 
gui_callback = None 
clip_callback = None 
permission_callback = None  
 
app = Flask(__name__) 
UPLOAD_DIR = os.path.normpath(os.path.join(os.path.expanduser("~"), "Downloads", "HelSync")) 
TEMP_DIR = os.path.join(UPLOAD_DIR, "temp") 
os.makedirs(TEMP_DIR, exist_ok=True) 
 
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
                button { background: #007bff; color: white; border: none; padding: 12px; border-radius: 5px; width: 100%; cursor: pointer; font-weight: bold; margin: 2px 0; } 
                .selected-list { text-align: left; font-size: 12px; color: #aaa; margin: 10px 0; background: #222; border-radius: 5px; padding: 10px; } 
                #progContainer { width: 100%; background: #333; height: 15px; border-radius: 8px; margin: 10px 0; display: none; overflow: hidden; border: 1px solid #444; } 
                #progBar { width: 0%; height: 100%; background: linear-gradient(90deg, #007bff, #00ff00); transition: width 0.1s; } 
                .file-item { display: flex; justify-content: space-between; align-items: center; padding: 10px; border-bottom: 1px solid #333; text-align: left; } 
                h4 { color: #a349a4; margin: 5px 0; border-bottom: 1px solid #444; padding-bottom: 5px; } 
                .grid-ctrl { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; } 
            </style> 
        </head> 
        <body> 
            <h3>Hel-Sync Pro</h3> 
            <div class="card"> 
                <h4>🎮 Remote Control</h4> 
                <div class="grid-ctrl"> 
                    <button onclick="doCmd('volup')" style="background:#444;">🔊 Vol Up</button> 
                    <button onclick="doCmd('voldown')" style="background:#444;">🔉 Vol Down</button> 
                    <button onclick="doCmd('mute')" style="background:#dc3545;">🔇 Mute</button> 
                    <button onclick="doCmd('buzz')" style="background:#ffc107; color:black;">🔔 Buzz PC</button> 
                    <button onclick="doCmd('lock')" style="background:#6c757d; grid-column: span 2;">🔒 Lock PC</button> 
                </div> 
            </div> 
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
                        <p style="color:#666; font-size:12px;">No files shared yet.</p> 
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
                function doCmd(action) { fetch('/remote_cmd?token={{token}}&action=' + action); } 
                function updateList() { 
                    const input = document.getElementById('fileInput'); 
                    const list = document.getElementById('fileList'); 
                    list.innerHTML = ""; 
                    for(let i=0; i<input.files.length; i++) list.innerHTML += "• " + input.files[i].name + "<br>"; 
                } 
                function upload() { 
                    const input = document.getElementById('fileInput'); 
                    if(input.files.length === 0) return alert("Select files!"); 
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
                    xhr.onload = () => { location.reload(); }; 
                    xhr.send(formData); 
                } 
                function sendTxt() { 
                    const val = document.getElementById('mob_txt').value; 
                    if(!val) return; 
                    fetch('/send_from_mobile?token={{token}}', { 
                        method: 'POST', 
                        headers: {'Content-Type': 'application/json'}, 
                        body: JSON.stringify({text: val}) 
                    }).then(() => { alert('Sent'); document.getElementById('mob_txt').value=''; }); 
                } 
                function playBuzzSound() { 
                    if (navigator.vibrate) navigator.vibrate([500, 200, 500]); 
                    let msg = new SpeechSynthesisUtterance(); 
                    msg.text = "I am here!"; msg.lang = 'en-US'; 
                    window.speechSynthesis.speak(msg); 
                    flashScreen(); 
                } 
                function flashScreen() { 
                    let body = document.body; let count = 0; 
                    let interval = setInterval(() => { 
                        if (document.getElementById('pc_clip').innerText.indexOf("SEARCHING") === -1) { 
                            clearInterval(interval); body.style.backgroundColor = "#0c0c0c"; return; 
                        } 
                        body.style.backgroundColor = (count % 2 === 0) ? "#ffffff" : "#ff0000"; 
                        count++; 
                    }, 100);  
                } 
                setInterval(() => { 
                    fetch('/get_clip?token={{token}}').then(r => r.json()).then(d => { 
                        let display = document.getElementById('pc_clip'); 
                        if (d.text === "___BUZZ_NOW___") { 
                            playBuzzSound(); display.style.background = "#ff0000"; 
                            display.innerText = "🔔 PC IS SEARCHING FOR YOU!"; 
                        } else { 
                            window.speechSynthesis.cancel(); display.style.background = "#000"; 
                            display.innerText = d.text || "Waiting for PC..."; 
                            document.body.style.backgroundColor = "#0c0c0c"; 
                        } 
                    }); 
                }, 1000); 
            </script> 
        </body> 
        </html> 
    ''', token=token, clip=CLIP_HISTORY.get(ACCESS_TOKEN, "Waiting..."), f_list=display_files) 
 
@app.route('/remote_cmd') 
def remote_cmd(): 
    token = request.args.get('token') 
    if token != ACCESS_TOKEN: abort(403) 
    action = request.args.get('action') 
    system = platform.system()

    # التحكم في الصوت
    if action in ("volup", "voldown", "mute"):
        if system == "Windows":
            pyautogui.press("volumeup" if action == "volup" else "volumedown" if action == "voldown" else "volumemute")
        elif system == "Linux":
            if action == "volup": subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"])
            elif action == "voldown": subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"])
            else: subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])

    # قفل الشاشة - شامل لكل بيئات لينكس و ويندوز
    elif action == "lock":
        if system == "Windows":
            subprocess.run(["rundll32.exe", "user32.dll,LockWorkStation"])
        elif system == "Linux":
            # تسلسل أوامر يغطي Cinnamon, Gnome, KDE, XFCE والمزيد
            os.system(
                "cinnamon-screensaver-command --lock || "
                "loginctl lock-session || "
                "dbus-send --type=method_call --dest=org.gnome.ScreenSaver /org/gnome/ScreenSaver org.gnome.ScreenSaver.Lock || "
                "qdbus org.freedesktop.ScreenSaver /ScreenSaver Lock || "
                "xdg-screensaver lock"
            )

    # الرنين (Buzz)
    elif action == "buzz": 
        if system == "Windows" and winsound:
            winsound.Beep(1000, 400)
        elif system == "Linux":
            os.system("notify-send '🔔 Hel-Sync' 'Buzzing from Mobile!'")
            os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga || echo -e '\a'")

    return jsonify({"status": "ok"}) 
 
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
        fmt = lambda s: f"{round(s/1024/1024, 2)} MB" if s > 1024*1024 else f"{round(s/1024, 2)} KB" 
        if permission_callback(len(received_files), fmt(total_size)): 
            for temp_path, fn, size in received_files: 
                final_path = os.path.join(UPLOAD_DIR, fn) 
                shutil.move(temp_path, final_path) 
                if gui_callback: gui_callback(fn, size) 
            return "OK" 
    return "Rejected", 403 
 
@app.route('/get_clip') 
def get_clip(): 
    token = request.args.get('token') 
    if token != ACCESS_TOKEN: abort(403) 
    return jsonify({"text": CLIP_HISTORY.get(ACCESS_TOKEN, "")}) 
 
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
    if 0 <= file_id < len(FILES_TO_SHARE): 
        p = FILES_TO_SHARE[file_id] 
        return send_from_directory(os.path.dirname(p), os.path.basename(p)) 
    return "Not Found", 404 
 
def start_network_service(gui_cb, clip_cb, token, perm_cb, prog_cb): 
    global gui_callback, clip_callback, ACCESS_TOKEN, permission_callback 
    gui_callback, clip_callback, ACCESS_TOKEN, permission_callback = gui_cb, clip_cb, token, perm_cb 
    app.run(host='0.0.0.0', port=8080, threaded=True, debug=False)
