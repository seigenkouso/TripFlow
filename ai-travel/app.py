from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.hunyuan.v20230901 import hunyuan_client, models
from dotenv import load_dotenv  # 👈 导入 dotenv 库
import json
import os
import random
import string
import datetime

# 1. 加载 .env 文件中的环境变量
load_dotenv()

app = Flask(__name__)

# 2. 从环境变量读取 Flask 密钥 (如果没有则使用默认值 'dev_key')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev_key_for_testing')

# --- 📧 邮件配置 (通用) ---
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.qq.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 465))
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = app.config['MAIL_USERNAME']

mail = Mail(app)

# 内存验证码存储 { "email": {"code": "123456", "expire": datetime} }
verification_codes = {}

# --- 💾 数据库配置 ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///travel.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

# --- 🤖 腾讯云混元配置 ---
try:
    # 3. 从环境变量读取腾讯云密钥
    secret_id = os.environ.get("TENCENT_SECRET_ID")
    secret_key = os.environ.get("TENCENT_SECRET_KEY")

    if not secret_id or not secret_key:
        print("⚠️ 警告: 未检测到腾讯云密钥，请检查 .env 文件！")
    
    cred = credential.Credential(secret_id, secret_key) 
    httpProfile = HttpProfile()
    httpProfile.endpoint = "hunyuan.tencentcloudapi.com"
    clientProfile = ClientProfile()
    clientProfile.httpProfile = httpProfile
    client = hunyuan_client.HunyuanClient(cred, "ap-guangzhou", clientProfile)
except Exception as e:
    print(f"腾讯云配置初始化失败: {e}")

# --- 📝 数据模型 ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=True)
    itineraries = db.relationship('Itinerary', backref='author', lazy=True)

class Itinerary(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(100), nullable=False)
    days = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=False) # 存JSON字符串
    date_created = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_saved = db.Column(db.Boolean, default=False) # 是否已收藏

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- 🛣️ 路由接口 ---

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/current_user')
def get_current_user():
    if current_user.is_authenticated:
        name = current_user.username if current_user.username else current_user.email.split('@')[0]
        return jsonify({'is_logged_in': True, 'username': name})
    return jsonify({'is_logged_in': False})

# 1. 发送验证码接口
@app.route('/api/send-code', methods=['POST'])
def send_code():
    email = request.json.get('email')
    if not email:
        return jsonify({'success': False, 'message': '请输入邮箱'})
    
    code = ''.join(random.choices(string.digits, k=6))
    verification_codes[email] = {
        'code': code,
        'timestamp': datetime.datetime.now()
    }
    
    try:
        msg = Message("TripFlow 登录验证码", recipients=[email])
        msg.body = f"Your verification code is: {code}. Please use it within 5 minutes."
        mail.send(msg)
        print(f"验证码已发送至 {email}")
        return jsonify({'success': True, 'message': '验证码已发送'})
    except Exception as e:
        print(f"发送失败: {e}")
        return jsonify({'success': False, 'message': '邮件发送失败，请检查配置'})

# 2. 邮箱登录/注册接口
@app.route('/api/login-via-email', methods=['POST'])
def login_via_email():
    data = request.json
    email = data.get('email')
    code = data.get('code')
    
    record = verification_codes.get(email)
    if not record or record['code'] != code:
        return jsonify({'success': False, 'message': '验证码错误或失效'})
    
    # 自动注册逻辑
    user = User.query.filter_by(email=email).first()
    if not user:
        new_user = User(email=email, username=email.split('@')[0])
        db.session.add(new_user)
        db.session.commit()
        user = new_user
    
    login_user(user)
    verification_codes.pop(email, None) # 清除验证码
    return jsonify({'success': True, 'username': user.username})

@app.route('/api/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'success': True})

@app.route('/api/history')
@login_required
def get_history():
    history = Itinerary.query.filter_by(user_id=current_user.id).order_by(Itinerary.id.desc()).all()
    res = []
    for item in history:
        try:
            res.append({
                'id': item.id,
                'city': item.city,
                'days': item.days,
                'date': item.date_created,
                'content': json.loads(item.content)
            })
        except:
            continue
    return jsonify({'success': True, 'history': res})

@app.route('/api/saved_list')
@login_required
def get_saved_list():
    # 只查询 is_saved = True 的记录
    saved = Itinerary.query.filter_by(user_id=current_user.id, is_saved=True).order_by(Itinerary.id.desc()).all()
    res = [{'id': i.id, 'city': i.city, 'days': i.days, 'date': i.date_created, 'content': json.loads(i.content)} for i in saved]
    return jsonify({'success': True, 'saved': res})

# 收藏/取消收藏指定行程
@app.route('/api/bookmark/<int:itinerary_id>', methods=['POST'])
@login_required
def bookmark_itinerary(itinerary_id):
    item = Itinerary.query.get(itinerary_id)
    if item and item.user_id == current_user.id:
        item.is_saved = True # 标记为收藏
        db.session.commit()
        return jsonify({'success': True})
    return jsonify({'success': False, 'message': '未找到行程或权限不足'})

# 核心：生成行程 (修复了返回 ID 的问题)
@app.route('/api/generate', methods=['POST'])
def generate_itinerary():
    data = request.json
    city = data.get('city')
    days = data.get('days')
    preferences = data.get('preferences', [])
    
    prompt = f"请为我规划一个去{city}的{days}天旅行行程。偏好：{', '.join(preferences)}。请直接返回JSON格式，不要Markdown代码块。格式包含：title, days(数组，包含day_title, spots(数组，包含name, time, reason, description))。"

    req = models.ChatCompletionsRequest()
    req.Model = "hunyuan-pro"
    req.Messages = [{"Role": "user", "Content": prompt}]

    try:
        resp = client.ChatCompletions(req)
        raw_content = resp.Choices[0].Message.Content
        
        print("\n=== AI 原始回复开始 ===")
        print(raw_content)
        print("=== AI 原始回复结束 ===\n")
        
        clean_text = raw_content.replace("```json", "").replace("```", "").strip()
        itinerary_data = json.loads(clean_text)
        
        new_id = None 

        # 登录用户自动保存
        if current_user.is_authenticated:
            new_record = Itinerary(
                city=city, days=days, content=json.dumps(itinerary_data),
                date_created=datetime.datetime.now().strftime("%Y-%m-%d"),
                user_id=current_user.id,
                is_saved=False # 默认为未收藏
            )
            db.session.add(new_record)
            db.session.commit()
            
            # ✅ 获取新生成的 ID
            new_id = new_record.id 
            print(f"✅ 新行程已保存，ID: {new_id}")
        
        # ✅ 将 ID 返回给前端，解决无法收藏的问题
        return jsonify({
            'success': True, 
            'data': itinerary_data, 
            'id': new_id 
        })

    except Exception as e:
        print(f"AI Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=80)