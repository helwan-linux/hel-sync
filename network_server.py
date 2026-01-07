import os, logging, math, shutil, pyautogui, platform, subprocess, zipfile
from flask import Flask, request, render_template_string, abort, send_from_directory, jsonify, make_response
from werkzeug.utils import secure_filename



# 1. إلغاء التأخير الافتراضي تماماً (أهم خطوة للسرعة)
pyautogui.PAUSE = 0

# 2. جعل مدة الحركة صفر (لجعل الماوس يقفز فوراً للمكان الجديد)
pyautogui.MINIMUM_DURATION = 0

# 3. تعطيل خاصية الأمان (ضروري جداً في السيرفر)
# لو تركتها True، بمجرد وصول الماوس لزاوية الشاشة سينهار السيرفر ويظهر خطأ
pyautogui.FAILSAFE = False


try:
	import winsound
except:
	winsound = None

# إعدادات الحالة العامة
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

# تقليل إزعاج السجل
logging.getLogger('werkzeug').setLevel(logging.ERROR)
pyautogui.PAUSE = 0 


def helper_format_size(s):
	if s == 0: return "0B"
	try:
		units = ['B', 'KB', 'MB', 'GB']
		i = int(math.floor(math.log(s, 1024)))
		return f"{round(s / math.pow(1024, i), 2)} {units[i]}"
	except:
		return f"{s} B"
		
		
@app.route('/')
def index():
	token = request.args.get('token')
	if token != ACCESS_TOKEN: abort(403)
	return render_template_string('''
		<!DOCTYPE html>
		<html>
		<head>
			<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
			<style>
				body { background: #0c0c0c; color: #eee; font-family: sans-serif; text-align: center; padding: 10px; transition: background 0.1s; }
				.card { background: #1a1a1a; padding: 15px; border-radius: 10px; border: 1px solid #333; margin-bottom: 12px; }
				button { background: #007bff; color: white; border: none; padding: 12px; border-radius: 5px; width: 100%; cursor: pointer; font-weight: bold; margin: 2px 0; }
				#touchpad { width: 100%; height: 200px; background: #000; border: 1px solid #444; border-radius: 10px; touch-action: none; display: flex; align-items: center; justify-content: center; color: #444; }
				.grid-ctrl { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-top: 10px; }
				.file-item { display: flex; justify-content: space-between; align-items: center; padding: 8px; border-bottom: 1px solid #333; font-size: 13px; text-align: left; }
				#pc_clip { background: #000; padding: 10px; border: 1px dashed #555; color: #0f0; margin-bottom: 10px; font-size: 13px; min-height: 20px; }
				#progBar { width: 0%; height: 100%; background: #007bff; transition: width 0.1s; }
			</style>
		</head>
		<body>
			<h3>Hel-Sync Pro 2026</h3>
			
			<div class="card">
				<h4>🖱️ Touchpad</h4>
				<div id="touchpad">Touch Here to Move Mouse</div>
				<div class="grid-ctrl">
					<button onclick="mouseBtn('left')" style="background:#333;">Left Click</button>
					<button onclick="mouseBtn('right')" style="background:#333;">Right Click</button>
				</div>
			</div>

			<div class="card">
				<h4>🎮 Quick Control</h4>
				<div class="grid-ctrl">
					<button onclick="doCmd('volup')" style="background:#444;">🔊 Vol Up</button>
					<button onclick="doCmd('voldown')" style="background:#444;">🔉 Vol Down</button>
					<button onclick="doCmd('mute')" style="background:#dc3545;">🔇 Mute</button>
					<button onclick="doCmd('buzz_pc')" style="background:#ffc107; color:black;">🔔 Buzz PC</button>
					<button onclick="doCmd('lock')" style="background:#6c757d; grid-column: span 2;">🔒 Lock PC</button>
				</div>
			</div>

			<div class="card">
				<h4>↑ Upload to PC</h4>
				<input type="file" id="fileInput" multiple onchange="updateList()" style="width:100%;">
				<div id="fileList" style="font-size:11px; color:#888; margin:10px 0;"></div>
				<div id="progContainer" style="width:100%; height:8px; background:#333; display:none; border-radius:4px; overflow:hidden;">
					<div id="progBar"></div>
				</div>
				<button onclick="upload()">START UPLOAD</button>
			</div>

			<div class="card">
				<h4>↓ Download from PC</h4>
				<button id="btnDlAll" onclick="downloadAll()" style="background:#28a745; margin-bottom:10px; display:none;">📥 GET ALL FILES</button>
				<div id="download_list"></div>
			</div>

			<div class="card">
				<h4>Clipboard</h4>
				<div id="pc_clip">Waiting...</div>
				<textarea id="mob_txt" placeholder="Send text to PC..." style="width:100%; height:50px; background:#222; color:#fff; border:1px solid #444; padding:5px; box-sizing:border-box;"></textarea>
				<button onclick="sendTxt()" style="margin-top:10px; background:#a349a4;">SEND TEXT</button>
			</div>

			<script>
				const TOKEN = "{{token}}";
				let lastX = 0, lastY = 0, isBuzzing = false, flashInterval = null;

				// --- التحكم بالماوس ---
				const pad = document.getElementById('touchpad');
				pad.addEventListener('touchstart', e => { lastX = e.touches[0].clientX; lastY = e.touches[0].clientY; });
				pad.addEventListener('touchmove', e => {
					e.preventDefault();
					let dx = Math.round((e.touches[0].clientX - lastX) * 1.8);
					let dy = Math.round((e.touches[0].clientY - lastY) * 1.8);
					if (Math.abs(dx) > 0 || Math.abs(dy) > 0) {
						fetch(`/mouse_move?token=${TOKEN}&x=${dx}&y=${dy}`);
						lastX = e.touches[0].clientX; lastY = e.touches[0].clientY;
					}
				}, {passive: false});

				function mouseBtn(type) { fetch(`/mouse_click?token=${TOKEN}&btn=${type}`); }
				function doCmd(a) { fetch(`/remote_cmd?token=${TOKEN}&action=${a}`); }

				// --- وظائف الصوت والوميض للموبايل (Buzz) ---
function startBuzz() {
    if(isBuzzing) return; 
    isBuzzing = true;
    
    // 1. الاهتزاز بنمط التنبيه
    if(navigator.vibrate) navigator.vibrate([500, 200, 500, 200, 500, 200, 1000]);

    // 2. نطق الجملة أولاً
    let m = new SpeechSynthesisUtterance("I am here!");
    window.speechSynthesis.speak(m);

    // 3. "الصرخة" أو الصافرة (تبدأ فوراً بعد الكلام)
    m.onend = function() {
        if(!isBuzzing) return;
        
        let audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        let oscillator = audioCtx.createOscillator();
        let gainNode = audioCtx.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(audioCtx.destination);

        // نوع الموجة 'sawtooth' يعطي صوتاً حاداً يشبه الصرخة أو المنبه
        oscillator.type = 'sawtooth'; 
        
        // تغيير التردد صعوداً وهبوطاً لمحاكاة صوت السرينة (Siren)
        oscillator.frequency.setValueAtTime(440, audioCtx.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(1000, audioCtx.currentTime + 0.5);
        oscillator.frequency.exponentialRampToValueAtTime(440, audioCtx.currentTime + 1);
        
        oscillator.loop = true;
        oscillator.start();

        // اجعلها تصرخ لمدة 5 ثوانٍ ثم تتوقف
        setTimeout(() => {
            oscillator.stop();
            audioCtx.close();
        }, 5000);
    };

    // 4. الوميض البصري (أحمر وأبيض)
    flashInterval = setInterval(() => {
        document.body.style.backgroundColor = (document.body.style.backgroundColor==='red')?'white':'red';
    }, 150);
}
				function stopBuzz() { 
					isBuzzing = false; clearInterval(flashInterval); 
					document.body.style.backgroundColor = '#0c0c0c'; 
					window.speechSynthesis.cancel();
				}

				// --- إدارة الملفات ---
				function refreshFileList() {
					fetch(`/get_files?token=${TOKEN}`).then(r => r.json()).then(files => {
						const list = document.getElementById('download_list');
						const dlBtn = document.getElementById('btnDlAll');
						if (files.length === 0) {
							list.innerHTML = '<p style="color:#666; font-size:12px;">No files shared.</p>';
							dlBtn.style.display = 'none';
						} else {
							dlBtn.style.display = 'block';
							list.innerHTML = files.map((f, i) => `
								<div class="file-item">
									<span>📄 ${f}</span>
									<button onclick="forceDl('/download/${i}?token=${TOKEN}')" style="width:auto; padding:4px 10px; background:#444;">GET</button>
								</div>
							`).join('');
						}
					});
				}
				function forceDl(url) { const a = document.createElement('a'); a.href = url; a.download = ''; a.click(); }
				function downloadAll() {
					const btns = document.querySelectorAll('#download_list button');
					btns.forEach((b, i) => setTimeout(() => b.click(), i * 600));
				}

				function upload() {
					const input = document.getElementById('fileInput');
					const fd = new FormData(); fd.append("token", TOKEN);
					for(let f of input.files) fd.append("files", f);
					document.getElementById('progContainer').style.display = "block";
					const xhr = new XMLHttpRequest();
					xhr.open("POST", "/upload");
					xhr.upload.onprogress = (e) => { document.getElementById('progBar').style.width = Math.round((e.loaded/e.total)*100) + "%"; };
					xhr.onload = () => { document.getElementById('progContainer').style.display = "none"; refreshFileList(); };
					xhr.send(fd);
				}

				function sendTxt() {
					const val = document.getElementById('mob_txt').value;
					fetch(`/send_from_mobile?token=${TOKEN}`, {
						method: 'POST', headers: {'Content-Type': 'application/json'},
						body: JSON.stringify({text: val})
					}).then(() => { document.getElementById('mob_txt').value=''; });
				}

				// التحديث التلقائي للحالة
				setInterval(() => {
					fetch(`/get_clip?token=${TOKEN}`).then(r => r.json()).then(d => {
						let display = document.getElementById('pc_clip');
						if (d.text === "___BUZZ_NOW___") {
							display.innerText = "🔔 PC IS SEARCHING FOR YOU!"; startBuzz();
						} else {
							display.innerText = d.text || "Waiting for PC..."; stopBuzz();
						}
					});
					refreshFileList();
				}, 2500);
			</script>
		</body>
		</html>
	''', token=token)

# --- مسارات التحكم في الماوس ---
@app.route('/mouse_move')
def mouse_move():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    try:
        dx = int(request.args.get('x', 0))
        dy = int(request.args.get('y', 0))
        # الحركة هنا مع التأكد من عدم وجود تأخير
        pyautogui.moveRel(dx, dy, _pause=False)
    except:
        pass
    return "ok"

@app.route('/mouse_click')
def mouse_click():
    token = request.args.get('token')
    if token != ACCESS_TOKEN: abort(403)
    btn = request.args.get('btn', 'left')
    try:
        if btn == 'left':
            pyautogui.click(_pause=False)
        else:
            pyautogui.rightClick(_pause=False)
    except:
        pass
    return "ok"

# --- مسارات الأوامر والملفات ---
# 1. في دالة remote_cmd للإصلاح الشامل
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
    elif action == "buzz_pc": 
        if system == "Windows" and winsound:
            winsound.Beep(1000, 400)
        elif system == "Linux":
            os.system("notify-send '🔔 Hel-Sync' 'Buzzing from Mobile!'")
            os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga || echo -e '\a'")

    return jsonify({"status": "ok"}) 

@app.route('/get_files')
def get_files():
	return jsonify([os.path.basename(f) for f in FILES_TO_SHARE])

@app.route('/download/<int:file_id>')
def download(file_id):
	if 0 <= file_id < len(FILES_TO_SHARE):
		p = FILES_TO_SHARE[file_id]
		return send_from_directory(os.path.dirname(p), os.path.basename(p), as_attachment=True)
	return "Not Found", 404

@app.route('/upload', methods=['POST'])
def upload():
	token = request.form.get('token')
	if token != ACCESS_TOKEN: abort(403)
	
	# التأكد من وجود المجلدات قبل البدء في أي عملية حفظ
	os.makedirs(TEMP_DIR, exist_ok=True)
	os.makedirs(UPLOAD_DIR, exist_ok=True)

	files = request.files.getlist('files')
	for file in files:
		if file.filename:
			fn = secure_filename(file.filename)
			temp_path = os.path.join(TEMP_DIR, fn)
			
			# حفظ الملف في المجلد المؤقت
			file.save(temp_path)
			
			size = os.path.getsize(temp_path)
			allowed = False
			
			if permission_callback:
				# نمرر اسم الملف في قائمة ليتوافق مع الـ GUI الخاص بك
				allowed = permission_callback([fn], helper_format_size(size))
			else:
				allowed = True

			if allowed:
				dest = os.path.join(UPLOAD_DIR, fn)
				# استخدام shutil.move لنقل الملف للمجلد النهائي
				shutil.move(temp_path, dest)
				if gui_callback: 
					gui_callback(fn, size)
			else:
				if os.path.exists(temp_path): 
					os.remove(temp_path)
					
	return "OK"

@app.route('/get_clip')
def get_clip():
	return jsonify({"text": CLIP_HISTORY.get(ACCESS_TOKEN, "")})

@app.route('/send_from_mobile', methods=['POST'])
def send_from_mobile():
	data = request.get_json()
	if clip_callback: clip_callback(data.get('text', ''))
	return "ok"

def start_network_service(gui_cb, clip_cb, token, perm_cb, prog_cb):
	global gui_callback, clip_callback, ACCESS_TOKEN, permission_callback
	gui_callback, clip_callback, ACCESS_TOKEN, permission_callback = gui_cb, clip_cb, token, perm_cb
	app.run(host='0.0.0.0', port=8080, threaded=False, debug=False)
