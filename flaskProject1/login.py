import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
# from flask import send_file
from io import BytesIO
# from werkzeug.utils import secure_filename
# # from datetime import datetime
app = Flask(__name__)
cors = CORS(app)
#设置好连接数据库的信息
HOSTNAME="127.0.0.1"
PORT=3306
USERNAME="root"
PASSWORD="666666"
DATABASE="login_verification"
app.config['SQLALCHEMY_DATABASE_URI']=f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4"
db = SQLAlchemy(app)
class User(db.Model):
    __tablename__="user"
    id=db.Column(db.Integer,primary_key=True,autoincrement=True)
    username=db.Column(db.String(100),nullable=False)
    password=db.Column(db.String(100),nullable=False)
class Article(db.Model):
    __tablename__ = "article"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(500), nullable=False)
    author = db.Column(db.String(100), nullable=True)
    content = db.Column(db.Text, nullable=False)
    eng_content = db.Column(db.Text, nullable=False)
    post_time = db.Column(db.String(100), nullable=True)
    video_link = db.Column(db.String(100), nullable=True)
class Image(db.Model):
    __tablename__ = "image"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    data = db.Column(db.LargeBinary, nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    article = db.relationship('Article', backref=db.backref('images', lazy=True))

def common_str(s1, s2):
    m, n = len(s1), len(s2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    length, end = 0, 0
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if s1[i - 1] == s2[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
                if dp[i][j] > length:
                    length = dp[i][j]
                    end = i - 1
            else:
                dp[i][j] = 0
    return (length, s1[end - length + 1: end + 1])

with app.app_context():
   db.create_all()
@app.route("/user/query",methods=['POST'])
def query_user():
    login_data=request.get_json()
    username=login_data['username']
    password=login_data['password']
    user = User.query.filter_by(username=username).first()
    # print(type(user),1,user.username)
    # return jsonify({'status': 'success', 'message': 'Login successful'})
    # print(type(user.username), type(user.password))
    if user and user.password == password:
        return jsonify({'status': 'success', 'message': 'Login successful'})
    else:
        return jsonify({'status': 'error', 'message': 'Invalid username or password'})
@app.route("/user/add",methods=['POST'])
def add_user():
    login_data = request.get_json()
    username = login_data['username']
    password = login_data['password']
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'status': 'error', 'message': 'Duplicate username'})
    else:
        user=User(username=username,password=password)
        db.session.add(user)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Register successful'})
@app.route("/article/add",methods=['POST'])
def add_article():
    title = request.form.get('title')
    author = request.form.get('author')
    post_time = request.form.get('post_time')
    content = request.form.get('content')
    eng_content = request.form.get('eng_content')
    video_link = request.form.get('video_link')
    # 创建Article对象保存到数据库
    article = Article(title=title, author=author, post_time=post_time, content=content, video_link=video_link,eng_content=eng_content)
    db.session.add(article)
    db.session.commit()
    article_id = article.id
    images = request.files.getlist('images')
    for image in images:
        image_data = image.read()
        new_image = Image(data=image_data, article_id=article_id)
        db.session.add(new_image)
        db.session.commit()
    return jsonify({'status': 'success', 'message': 'Article uploaded successfully'})
@app.route("/article/search",methods=['GET'])
def search_article():
    search_content = request.args.get('search_content')
    articles=Article.query.all()
    lst=[]
    for articlee in articles:
        result=common_str(search_content, articlee.title)
        if result[0]>0:
            lst.append((result[0],result[1],articlee.id,articlee.title))
    lst_1 = sorted(lst, key=lambda x: x[0], reverse=True)
    print(lst_1)
    if lst_1==[]:
        return jsonify({'status': 'success', 'message': 'none'})
    return jsonify({'status': 'success', 'message': lst_1})
@app.route('/article/<int:id>',methods=['GET'])
def show_search_articles(id):
    article = Article.query.filter_by(id=id).first()
    if article is None:
        return jsonify({"error":"Article not found"})
    else:
        return jsonify({
        "id": article.id,
        "title": article.title,
        "author": article.author,
        "content": article.content,
        "eng_content": article.eng_content,
        "post_time": article.post_time,
        "video_link": article.video_link})
@app.route('/article/getID<int:id>',methods=['GET'])
def show_all_articleID(id):
    articles = Article.query.all()
    lst=[]
    for article in articles:
        if article.id>id and len(lst)<4:
            lst.append(article.id)
    print(lst)
    if lst==[]:
        return jsonify({'status': 'success', 'message': 'none'})
    return jsonify({'status': 'success', 'message': lst})


@app.route('/image/<int:article_id>',methods=['GET'])
def get_image(article_id):
    images = Image.query.filter_by(article_id=article_id).all()
    base64_images=[]
    for image in images:
        image_data = image.data
        # 将二进制图片数据转换为BytesIO对象
        image_stream = BytesIO(image_data)
        base64_image=base64.b64encode(image_stream.getvalue()).decode('utf-8')
        base64_images.append(base64_image)
    # return send_file(image_stream, mimetype='image/jpeg')
    return jsonify({'status': 'success', 'images': base64_images})

if __name__ == '__main__':
    app.run()
