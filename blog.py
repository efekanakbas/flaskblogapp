from flask import Flask,render_template,request,url_for,logging,redirect,flash,session,make_response
from wtforms import validators,TextAreaField,PasswordField,StringField,Form,FileField
from passlib.hash import sha256_crypt
from flask_mysqldb import MySQL
from functools import wraps
from werkzeug.utils import secure_filename
from uuid import uuid1
import os

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

app=Flask(__name__)
app.secret_key="efinem"
app.config["UPLOAD_FOLDER"]=UPLOAD_FOLDER    
app.config["MYSQL_HOST"]="localhost"
app.config["MYSQL_USER"]="root"
app.config["MYSQL_PASSWORD"]=""
app.config["MYSQL_DB"]="efinemblog"
app.config["MYSQL_CURSORCLASS"]="DictCursor"
mysql=MySQL(app)
#Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "logged_in" in session:
            return f(*args, **kwargs)
        else:
            flash("Bu siteye girmek için lütfen giriş yapın!","danger")
            return redirect(url_for("login"))
    return decorated_function
class RegisterForm(Form):
    name=StringField("İsim Soyisim",validators=[validators.Length(min=5,max=25,message="Geçersiz karakter")])
    username=StringField("Kullanıcı Adı",validators=[validators.Length(min=5,max=25,message="Geçersiz karakter")])
    email=StringField("E-Mail",validators=[validators.Email(message="Geçersiz E-Mail")])
    password=PasswordField("Parola",validators=[
        validators.DataRequired(message="Lütfen değer giriniz"),validators.EqualTo(fieldname="confirm",message="Şifreler uyuşmuyor!")
    ])
    confirm=PasswordField("Parola tekrarı")
    pic=FileField("Dosya Yükleme")
class LoginForm(Form):
    username=StringField("Kullanıcı Adı",validators=[validators.DataRequired(message="Lütfen kullanıcı adı giriniz!")])
    password=PasswordField("Parola",validators=[validators.DataRequired(message="Lütfen parola giriniz!")])
class ArticleForm(Form):
    title=StringField("Makale Başlığı",validators=[validators.Length(min=5,max=100)])
    content=TextAreaField("Makale İçeriği",validators=[validators.Length(min=10)])
class ProfileEditForm(Form):
    name=StringField("İsim")
    email=StringField("E-Mail",validators=[validators.Email(message=("Lütfen geçerli bir e-posta giriniz!"))])
    username=StringField("Kullanıcı Adı")
    password=PasswordField("Parola",validators=[
        validators.DataRequired(message="Lütfen değer giriniz"),validators.EqualTo(fieldname="confirm",message="Şifreler uyuşmuyor!")
    ])
    pic=FileField("Fotoğraf")

@app.route("/")
def home():
    return render_template("home.html")


@app.route("/upload",methods=["POST","GET"])
def upload():
    if request.method=="POST":
        pic=request.files("pic")
        if not pic:
            flash("Böyle bir dosya yok","danger")
            return redirect(url_for("profile"))
    else:
        return render_template("/")
      
    
    



@app.route("/about")
def about():
    return render_template("about.html")
@app.route("/profile", methods=["GET","POST"])
@login_required
def profile():
    if request.method=="POST":
        pass
    else:
        cursor=mysql.connection.cursor()
        sorgu="select * from efinemtablo where id=%s"
        cursor.execute(sorgu,(session["id"],))
        data=cursor.fetchone()
        if data["id"]==session["id"]:
            return render_template("profile.html",data=data)
        else:
            flash("Böyle bir yetkiniz yok","danger")
            return render_template("home.html")     
@app.route("/profile/<string:id>",methods=["GET","POST"])  
@login_required
def profileEdit(id):
    cursor=mysql.connection.cursor()
    sorgu="select * from efinemtablo where id=%s"
    cursor.execute(sorgu,(id,))
    data=cursor.fetchone()
    if data["id"]==session["id"]:
        if request.method=="POST":
                form=ProfileEditForm(request.form)
                name2=form.name.data 
                email2=form.email.data
                username2=form.username.data
                password2=sha256_crypt.encrypt(form.password.data)
                pic=request.files["pic"]
                picName=str(uuid1()) + os.path.splitext(pic.filename)[1]
                pic.save(os.path.join("static/images",picName))
                cursor=mysql.connection.cursor()
                sorgu2="update efinemtablo set name=%s,email=%s,username=%s,password=%s,pic=%s where id=%s"
                cursor.execute(sorgu2,(name2,email2,username2,password2,picName,id))
                mysql.connection.commit()
                cursor.close()
                flash("Başarılı bir şekilde profil bilgilerinizi güncellediniz...","success")
                return redirect(url_for("login"))
        else:
            form=ProfileEditForm()
            form.name.data=data["name"]
            form.email.data=data["email"]
            form.username.data=data["username"]
            return render_template("profileEdit.html",form=form)
    else:
        flash("Böyle bir yetkiniz yok","danger")
        return render_template("home.html")   
@app.route("/dashboard")
@login_required
def dashboard():
    cursor=mysql.connection.cursor()
    sorgu="select * from articles where author=%s"
    result=cursor.execute(sorgu,(session["username"],))
    if result>0:
        data=cursor.fetchall()
        return render_template("dashboard.html",data=data)
    return render_template("dashboard.html")
@app.route("/article/<string:id>")
def article(id):
    cursor=mysql.connection.cursor()
    sorgu="select * from articles where id =%s"
    result=cursor.execute(sorgu,(id,))
    if result>0:
        data=cursor.fetchone()
        return render_template("article.html",data=data)
    else:
        return render_template("article.html")


@app.route("/register", methods=["GET","POST"])
def register():
    form=RegisterForm(request.form)
    if request.method=="POST" and form.validate(): 
        name=form.name.data
        email=form.email.data
        username=form.username.data
        password=sha256_crypt.encrypt(form.password.data) 
        pic=request.files["pic"]
        picName=str(uuid1()) + os.path.splitext(pic.filename)[1]
        pic.save(os.path.join("static/images",picName))
        cursor=mysql.connection.cursor()
        sorgu="insert into efinemtablo(name,email,username,password,pic) VALUES(%s,%s,%s,%s,%s)"
        cursor.execute(sorgu,(name,email,username,password,picName))
        mysql.connection.commit()
        cursor.close()
        flash("Başarılı bir kayıt yaptınız...",category="success")
        return redirect(url_for("login"))
    else:
        return render_template("register.html",form=form)
@app.route("/login",methods=["GET","POST"])
def login():
    form=LoginForm(request.form)
    if request.method=="POST":
        username=form.username.data
        passwordEntered=form.password.data
        cursor=mysql.connection.cursor()
        sorgu="select * from efinemtablo where username=%s"
        result=cursor.execute(sorgu,(username,))
        if result>0:
            data=cursor.fetchone()
            real_password=data["password"]
            if sha256_crypt.verify(passwordEntered,real_password):
                flash("Başarılı bir şekilde girdiniz...","success")
                session["logged_in"]=True
                session["username"]=username
                session["id"]=data["id"]
                return redirect(url_for("home"))
            else:
                flash("Geçersiz parola!","danger")
                return redirect(url_for("login"))

        else:
            flash("Böyle bir kullanıcı yok...","danger")
            return redirect(url_for("login"))

    else:
        return render_template("login.html",form=form)
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))
@app.route("/addarticle",methods=["GET","POST"])
@login_required
def addarticle():
    form=ArticleForm(request.form)
    if request.method=="POST":
        title=form.title.data
        content=form.content.data
        author=session["username"]
        cursor=mysql.connection.cursor()
        sorgu="insert into articles(title,content,author) values(%s,%s,%s)"
        cursor.execute(sorgu,(title,content,author))
        mysql.connection.commit()
        cursor.close()
        flash("Makaleyi başarılı bir şekilde kaydettiniz","success")
        return redirect(url_for("articles"))

    else:
        return render_template("addarticle.html",form=form)
@app.route("/articles")
def articles():
    cursor=mysql.connection.cursor()
    sorgu="select * from articles"
    result=cursor.execute(sorgu)
    if result>0:
        data=cursor.fetchall()
        return render_template("articles.html",data=data)
        

    else:
        return render_template("articles.html")
@app.route("/delete/<string:id>")
@login_required
def delete(id):
    cursor=mysql.connection.cursor()
    sorgu="select * from articles where id=%s and author=%s"
    result=cursor.execute(sorgu,(id,session["username"]))
    if result>0:
        sorgu2="delete from articles where id=%s"
        cursor.execute(sorgu2,(id,))
        mysql.connection.commit()
        cursor.close()
        flash("Başarılı bir şekilde sildiniz...","success")
        return redirect(url_for("dashboard"))
    else:
        flash("Böyle bir makale yok veya bu makaleyi silmeye yetkiniz yok!","danger")
        return redirect(url_for("home"))
@app.route("/edit/<string:id>",methods=["GET","POST"])
@login_required
def edit(id):
    if request.method=="GET":
        cursor=mysql.connection.cursor()
        sorgu="select * from articles where id=%s and author=%s"
        result=cursor.execute(sorgu,(id,session["username"]))
        if result==0:
            flash("Böyle bir makale yok veya böyle bir yetkiniz yok","danger")
            return redirect(url_for("home"))
        else:  
            article=cursor.fetchone()
            form=ArticleForm()
            form.title.data=article["title"]
            form.content.data=article["content"]
            return render_template("edit.html",form=form)
    else:
        form=ArticleForm(request.form)
        newTitle=form.title.data
        newContent=form.content.data
        sorgu2="update articles set title=%s,content=%s where id=%s"
        cursor=mysql.connection.cursor()
        cursor.execute(sorgu2,(newTitle,newContent,id))
        mysql.connection.commit()
        flash("Başarılı bir şekilde makale güncellendi","success")
        return redirect(url_for("articles"))
@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="GET":
        flash("Böyle bir izniniz yok!","danger")
        return render_template("home.html")
    else:
        keyword=request.form.get("keyword")
        cursor=mysql.connection.cursor()
        sorgu="select * from articles where title like '%" + keyword + "%'"
        result=cursor.execute(sorgu)
        if result==0:
            flash("Böyle bir makale bulunmamaktadır...","info")
            return redirect(url_for("articles"))
        else:
            data=cursor.fetchall()
            return render_template("articles.html",data=data)








if __name__=="__main__":
    app.run(debug=True)