from flask import Flask, request, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
import os
import db_integration

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')  # 使用绝对路径保存

# 定义不同类型文件的存储目录
app.config['DIGITAL_HUMANS_BASE'] = os.path.join(app.config['UPLOAD_FOLDER'], 'digital_humans', 'base')
app.config['DIGITAL_HUMANS_DOCUMENTS'] = os.path.join(app.config['UPLOAD_FOLDER'], 'digital_humans', 'documents')
app.config['DIGITAL_HUMANS_AUDIO'] = os.path.join(app.config['UPLOAD_FOLDER'], 'digital_humans', 'audio')

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@localhost/app_db'  # 改为新数据库名
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'

db = SQLAlchemy(app)

# 音频文件模型
class AudioFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    filepath = db.Column(db.String(255))
    upload_time = db.Column(db.DateTime, server_default=db.func.now())
    digital_human_id = db.Column(db.Integer, db.ForeignKey('digital_human.id'))  # 关联到数字人
    digital_human = db.relationship('DigitalHuman', backref='audio_files', lazy=True)  # 反向关联

# 用户模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)  # 实际应用中应该使用加密密码
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    digital_humans = db.relationship('DigitalHuman', backref='owner', lazy=True)

# 数字人模型
class DigitalHuman(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    description = db.Column(db.Text)
    reference_audio_path = db.Column(db.String(255))  # 参考音频路径
    train_audio_path = db.Column(db.String(255))  # 训练音频路径
    image_path = db.Column(db.String(255))  # 图片路径
    video_path = db.Column(db.String(255))  # 视频路径
    patient_info_path = db.Column(db.String(255))  # 患者信息文件路径
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 关联到用户

# 文档存储模型
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))
    file_size = db.Column(db.Integer)  # 文件大小（字节）
    upload_time = db.Column(db.DateTime, server_default=db.func.now())
    description = db.Column(db.Text)  # 文档描述
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # 关联到用户
    digital_human_id = db.Column(db.Integer, db.ForeignKey('digital_human.id'))  # 关联到数字人
    digital_human = db.relationship('DigitalHuman', backref='documents', lazy=True)  # 反向关联

# 用户配置模型
class UserProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref='profile', lazy=True)

@app.route('/')
def index():
    # 获取第一个用户，如果没有则创建默认用户
    user = User.query.first()
    if not user:
        user = User(username='admin', password='admin')
        db.session.add(user)
        db.session.commit()
    return redirect(url_for('digital_humans', user_id=user.id))

@app.route('/audio', methods=['GET', 'POST'])
def audio():
    # 检查用户ID
    user_id = request.args.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('index'))
    
    # 获取当前数字人ID（从URL参数）
    current_dh_id = request.args.get('dh_id')
    current_dh = None
    if current_dh_id:
        current_dh = DigitalHuman.query.get(current_dh_id)
    
    if request.method == 'POST':
        if 'audio' not in request.files:
            flash('没有上传文件!')
            return redirect(url_for('audio', user_id=user_id, dh_id=current_dh_id))
        
        file = request.files['audio']
        if file.filename == '':
            flash('没有选择文件!')
            return redirect(url_for('audio', user_id=user_id, dh_id=current_dh_id))
        
        existing_file = AudioFile.query.filter_by(filename=file.filename).first()
        if existing_file:
            flash(f"{file.filename} 已经上传过了！")
            return redirect(url_for('audio', user_id=user_id, dh_id=current_dh_id))
        
        # 获取数字人ID（从表单提交）
        digital_human_id = request.form.get('digital_human_id', current_dh_id)
        
        # 生成文件名和保存路径
        filename = f"audio_{user_id}_{digital_human_id}_{file.filename}"
        save_path = os.path.join(app.config['DIGITAL_HUMANS_AUDIO'], filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        
        # 保存相对路径到数据库
        relative_path = f'digital_humans/audio/{filename}'
        audio = AudioFile(
            filename=file.filename, 
            filepath=relative_path,
            digital_human_id=digital_human_id if digital_human_id else None
        )
        db.session.add(audio)
        db.session.commit()
        
        flash(f"{file.filename} 上传成功！")
        
        # 如果有关联的数字人，重定向到数字人页面
        if digital_human_id:
            return redirect(url_for('digital_humans', user_id=user_id) + f'#dh-{digital_human_id}')
        return redirect(url_for('audio', user_id=user_id))
    
    # 获取用户的数字人列表，用于音频关联
    digital_humans = DigitalHuman.query.filter_by(user_id=user_id).all()
    files = AudioFile.query.all()
    return render_template('upload.html', files=files, user_id=user_id, digital_humans=digital_humans, current_dh=current_dh)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    audio = AudioFile.query.get_or_404(id)
    user_id = request.args.get('user_id')
    return_to = request.args.get('return_to', 'audio')
    
    # 保存digital_human_id以便之后重定向
    dh_id = audio.digital_human_id

    file_path = os.path.join(app.root_path, 'static', audio.filepath)
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        flash(f"文件 {audio.filename} 不存在，可能已被删除！")
    
    db.session.delete(audio)
    db.session.commit()
    flash(f"{audio.filename} 删除成功！")
    
    if return_to == 'digital_humans' and dh_id:
        return redirect(url_for('digital_humans', user_id=user_id) + f'#dh-{dh_id}')
    return redirect(url_for('audio', user_id=user_id))

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        email = request.form['email']
        phone = request.form['phone']

        profile = UserProfile(
            name=name,
            age=int(age) if age else None,
            gender=gender,
            email=email,
            phone=phone
        )
        db.session.add(profile)
        db.session.commit()
        flash('个人信息提交成功！')
        return redirect(url_for('profile'))

    profiles = UserProfile.query.all()
    return render_template('profile.html', profiles=profiles)

@app.route('/delete_profile/<int:id>', methods=['POST'])
def delete_profile(id):
    profile = UserProfile.query.get_or_404(id)
    db.session.delete(profile)
    db.session.commit()
    flash('个人信息删除成功！')
    return redirect(url_for('profile'))

@app.route('/edit_profile/<int:id>', methods=['GET', 'POST'])
def edit_profile(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.username = request.form['username']
        if request.form['password']:  # 只有在提供了新密码时才更新密码
            user.password = request.form['password']
        db.session.commit()
        flash('用户信息修改成功！')
        return redirect(url_for('user_profile', id=user.id))
    
    return render_template('edit_profile.html', user=user)

# 文档管理路由
@app.route('/documents', methods=['GET', 'POST'])
def documents():
    user_id = request.args.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    
    user = User.query.get(user_id)
    if not user:
        return redirect(url_for('index'))
    
    # 获取当前数字人ID（从URL参数或表单提交）
    current_dh_id = request.args.get('dh_id')
    current_dh = None
    if current_dh_id:
        current_dh = DigitalHuman.query.get(current_dh_id)
    
    if request.method == 'POST':
        if 'document' not in request.files:
            flash('没有上传文件!')
            return redirect(url_for('documents', user_id=user_id, dh_id=current_dh_id))
        
        file = request.files['document']
        if file.filename == '':
            flash('没有选择文件!')
            return redirect(url_for('documents', user_id=user_id, dh_id=current_dh_id))

        # 获取文件信息
        title = request.form.get('title', file.filename)
        description = request.form.get('description', '')
        file_type = file.filename.split('.')[-1] if '.' in file.filename else ''
        digital_human_id = request.form.get('digital_human_id')  # 获取关联的数字人ID
        
        # 生成文件名和保存路径
        filename = f"document_{user_id}_{digital_human_id}_{file.filename}"
        save_path = os.path.join(app.config['DIGITAL_HUMANS_DOCUMENTS'], filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file.save(save_path)
        
        # 创建文档记录
        document = Document(
            title=title,
            filename=file.filename,
            filepath=f'digital_humans/documents/{filename}',
            file_type=file_type,
            file_size=os.path.getsize(save_path),
            description=description,
            user_id=user_id,
            digital_human_id=digital_human_id if digital_human_id else None
        )
        db.session.add(document)
        db.session.commit()
        
        flash(f"{file.filename} 上传成功！")
        
        # 如果有关联的数字人，重定向到数字人页面
        if digital_human_id:
            return redirect(url_for('digital_humans', user_id=user_id) + f'#dh-{digital_human_id}')
        return redirect(url_for('documents', user_id=user_id))
    
    # 获取用户的数字人列表，用于文档关联
    digital_humans = DigitalHuman.query.filter_by(user_id=user_id).all()
    documents = Document.query.filter_by(user_id=user_id).all()
    return render_template('documents.html', documents=documents, user_id=user_id, digital_humans=digital_humans, current_dh=current_dh)

@app.route('/delete_document/<int:id>', methods=['POST'])
def delete_document(id):
    document = Document.query.get_or_404(id)
    user_id = request.args.get('user_id')
    return_to = request.args.get('return_to', 'documents')
    
    # 保存digital_human_id以便之后重定向
    dh_id = document.digital_human_id

    file_path = os.path.join(app.root_path, 'static', document.filepath)
    if os.path.exists(file_path):
        os.remove(file_path)
    else:
        flash(f"文件 {document.filename} 不存在，可能已被删除！")
    
    db.session.delete(document)
    db.session.commit()
    flash(f"{document.filename} 删除成功！")
    
    if return_to == 'digital_humans' and dh_id:
        return redirect(url_for('digital_humans', user_id=user_id) + f'#dh-{dh_id}')
    return redirect(url_for('documents', user_id=user_id))

@app.route('/digital_humans', methods=['GET', 'POST'])
def digital_humans():
    user_id = request.args.get('user_id')
    if not user_id:
        return redirect(url_for('index'))
    
    user = db.session.get(User, user_id)
    if not user:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        name = request.form['name']
        phone = request.form['phone']
        description = request.form['description']
        
        # 处理文件上传
        reference_audio = request.files.get('reference_audio')
        train_audio = request.files.get('train_audio')
        image = request.files.get('image')
        video = request.files.get('video')
        patient_info = request.files.get('patient_info')
        
        # 创建数字人记录
        digital_human = DigitalHuman(
            name=name,
            phone=phone,
            description=description,
            user_id=user_id
        )
        db.session.add(digital_human)
        db.session.commit()
        
        # 保存上传的文件
        if reference_audio and reference_audio.filename:
            filename = f"reference_audio_{user_id}_{digital_human.id}_{reference_audio.filename}"
            save_path = os.path.join(app.config['DIGITAL_HUMANS_BASE'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            reference_audio.save(save_path)
            digital_human.reference_audio_path = f'digital_humans/base/{filename}'
        
        if train_audio and train_audio.filename:
            filename = f"train_audio_{user_id}_{digital_human.id}_{train_audio.filename}"
            save_path = os.path.join(app.config['DIGITAL_HUMANS_BASE'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            train_audio.save(save_path)
            digital_human.train_audio_path = f'digital_humans/base/{filename}'
        
        if image and image.filename:
            filename = f"image_{user_id}_{digital_human.id}_{image.filename}"
            save_path = os.path.join(app.config['DIGITAL_HUMANS_BASE'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            image.save(save_path)
            digital_human.image_path = f'digital_humans/base/{filename}'
        
        if video and video.filename:
            filename = f"video_{user_id}_{digital_human.id}_{video.filename}"
            save_path = os.path.join(app.config['DIGITAL_HUMANS_BASE'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            video.save(save_path)
            digital_human.video_path = f'digital_humans/base/{filename}'
        
        if patient_info and patient_info.filename:
            filename = f"patient_info_{user_id}_{digital_human.id}_{patient_info.filename}"
            save_path = os.path.join(app.config['DIGITAL_HUMANS_BASE'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            patient_info.save(save_path)
            digital_human.patient_info_path = f'digital_humans/base/{filename}'
        
        db.session.commit()
        flash(f"数字人 {name} 创建成功！")
        return redirect(url_for('digital_humans', user_id=user_id))
    
    digital_humans = DigitalHuman.query.filter_by(user_id=user_id).all()
    return render_template('digital_humans.html', digital_humans=digital_humans, user_id=user_id, user=user)

@app.route('/edit_digital_human/<int:id>', methods=['GET', 'POST'])
def edit_digital_human(id):
    digital_human = DigitalHuman.query.get_or_404(id)
    user_id = request.args.get('user_id')
    
    if request.method == 'POST':
        digital_human.name = request.form['name']
        digital_human.phone = request.form['phone']
        digital_human.description = request.form['description']
        
        # 处理文件上传
        reference_audio = request.files.get('reference_audio')
        train_audio = request.files.get('train_audio')
        image = request.files.get('image')
        video = request.files.get('video')
        patient_info = request.files.get('patient_info')
        
        # 保存上传的文件
        if reference_audio and reference_audio.filename:
            filename = f"reference_audio_{user_id}_{digital_human.id}_{reference_audio.filename}"
            save_path = os.path.join(app.config['DIGITAL_HUMANS_BASE'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            reference_audio.save(save_path)
            digital_human.reference_audio_path = f'digital_humans/base/{filename}'
        
        if train_audio and train_audio.filename:
            filename = f"train_audio_{user_id}_{digital_human.id}_{train_audio.filename}"
            save_path = os.path.join(app.config['DIGITAL_HUMANS_BASE'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            train_audio.save(save_path)
            digital_human.train_audio_path = f'digital_humans/base/{filename}'
        
        if image and image.filename:
            filename = f"image_{user_id}_{digital_human.id}_{image.filename}"
            save_path = os.path.join(app.config['DIGITAL_HUMANS_BASE'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            image.save(save_path)
            digital_human.image_path = f'digital_humans/base/{filename}'
        
        if video and video.filename:
            filename = f"video_{user_id}_{digital_human.id}_{video.filename}"
            save_path = os.path.join(app.config['DIGITAL_HUMANS_BASE'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            video.save(save_path)
            digital_human.video_path = f'digital_humans/base/{filename}'
        
        if patient_info and patient_info.filename:
            filename = f"patient_info_{user_id}_{digital_human.id}_{patient_info.filename}"
            save_path = os.path.join(app.config['DIGITAL_HUMANS_BASE'], filename)
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            patient_info.save(save_path)
            digital_human.patient_info_path = f'digital_humans/base/{filename}'
        
        db.session.commit()
        flash(f"数字人 {digital_human.name} 修改成功！")
        return redirect(url_for('digital_humans', user_id=user_id))
    
    return render_template('edit_digital_human.html', digital_human=digital_human, user_id=user_id)

@app.route('/delete_digital_human/<int:id>', methods=['POST'])
def delete_digital_human(id):
    digital_human = DigitalHuman.query.get_or_404(id)
    user_id = request.args.get('user_id')
    
    # 删除关联的文件
    for file_path in [
        digital_human.reference_audio_path,
        digital_human.train_audio_path,
        digital_human.image_path,
        digital_human.video_path,
        digital_human.patient_info_path
    ]:
        if file_path:
            full_path = os.path.join(app.root_path, 'static', file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
    
    # 删除数字人记录
    db.session.delete(digital_human)
    db.session.commit()
    flash(f"数字人 {digital_human.name} 删除成功！")
    return redirect(url_for('digital_humans', user_id=user_id))

@app.route('/import_chat', methods=['POST'])
def import_chat():
    user_id = request.args.get('user_id')
    dh_id = request.args.get('dh_id')
    
    if not user_id or not dh_id:
        flash('缺少必要的参数')
        return redirect(url_for('digital_humans', user_id=user_id))
    
    user = db.session.get(User, user_id)
    digital_human = db.session.get(DigitalHuman, dh_id)
    
    if not user or not digital_human:
        flash('用户或数字人不存在')
        return redirect(url_for('digital_humans', user_id=user_id))
    
    if 'chat_file' not in request.files:
        flash('没有上传文件')
        return redirect(url_for('digital_humans', user_id=user_id))
    
    file = request.files['chat_file']
    if file.filename == '':
        flash('没有选择文件')
        return redirect(url_for('digital_humans', user_id=user_id))
    
    if not file.filename.endswith('.txt'):
        flash('只支持.txt格式的聊天记录文件')
        return redirect(url_for('digital_humans', user_id=user_id))
    
    try:
        # 读取聊天记录内容
        chat_content = file.read().decode('utf-8')
        
        # 保存聊天记录
        result = db_integration.save_chat_to_database(
            chat_content=chat_content,
            digital_human_id=dh_id
        )
        
        if result['success']:
            flash(f"聊天记录导入成功！")
        else:
            flash(f"导入失败：{result.get('error', '未知错误')}")
            
    except Exception as e:
        flash(f"导入失败：{str(e)}")
    
    return redirect(url_for('digital_humans', user_id=user_id))

@app.route('/user_profile/<int:id>')
def user_profile(id):
    user = User.query.get_or_404(id)
    return render_template('user_profile.html', user=user)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 