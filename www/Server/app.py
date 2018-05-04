import pymysql
import mkdb3
from threading import Thread
from flask import Flask, render_template, request, url_for, redirect, session, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "$ome RaNdOm text"
app.debug = True

working = []


def hashNcheck(username, password):
    db = pymysql.connect("localhost", "cereal", "toor", "website")
    cursor = db.cursor()
    genQuery = "select password from login where username='{}'".format(username)
    cursor.execute(genQuery)
    temp = cursor.fetchone()
    if temp is not None and check_password_hash(temp[0], password):
        db.close()
        return True
    else:
        db.close()
        return False


def add_to_db(to_add):
    try:
        db = pymysql.connect("localhost", "cereal", "toor", "website")
        cursor = db.cursor()
        sql = '''select * from students where id="{}"'''.format(to_add["id"])
        cursor.execute(sql)
        data = cursor.fetchall()
        data = tuple(j for i in data for j in i)
        sql = '''insert into `{}` values ("{}","{}","{}","{}")'''.\
        format(to_add["table"], data[0], data[1], data[2], data[3])
        cursor.execute(sql)
        db.commit()
        db.close()
    except:
        pass


def remove_from_db(to_remove):
    db = pymysql.connect("localhost", "cereal", "toor", "website")
    cursor = db.cursor()
    try:
        print(to_remove)
        if len(to_remove) is not 1:
            temp = '''delete from `{}` where id = "{}"'''.format(to_remove['table'], to_remove['id'])
            cursor.execute(temp)
        else:
            print("executing")
            temp = '''drop table `{}`'''.format(to_remove['table'])
            cursor.execute(temp)
        print("removed !")
        db.commit()
        db.close()
    except:
        pass


def start_app(target, ip):
    target.main()
    working.remove(ip)


@app.before_request
def before_request():
    g.user = None
    if 'username' in session:
        g.user = session['username']


@app.route('/')
def index():
    return render_template("test2.html")


@app.route('/home')
def home():
    if g.user:
        db = pymysql.connect("localhost", "cereal", "toor", "website")
        cursor = db.cursor()
        user = g.user.split("@")
        sql = '''show tables like "{}%"'''.format(user[0])
        cursor.execute(sql)
        tables = cursor.fetchall()
        sql = '''describe stub'''
        cursor.execute(sql)
        description = cursor.fetchall()
        # sql = '''select * from aashimaDATE20180306'''
        # cursor.execute(sql)
        # selection = cursor.fetchall()
        selection = {}
        for i in tables:
            sql = '''select id,name,section from students natural join `{}`'''.format(i[0])
            cursor.execute(sql)
            selection[i[0]] = cursor.fetchall()
        print(selection)
        if request.remote_addr in working:
            blocked = True
        else:
            blocked = False
        return render_template("home.html", username=g.user, tables=tables, description=description,
                               selection=selection, user=user[0], blocked=blocked)
    return redirect(url_for('index'))


@app.route('/login', methods=["POST"])
def login():
    result = request.form
    session.pop('username', None)
    print(result['username'])
    if hashNcheck(result['username'], result['password']) is True:
        session['username'] = result['username']
        return redirect(url_for('home'))

    return redirect(url_for('index'))


@app.route('/remove', methods=["POST"])
def remove():
    result = request.form
    print(len(result))
    remove_from_db(result)
    return "200"


@app.route('/start', methods=["POST", "GET"])
def start():
    if request.method == "POST":
        global working
        result = request.form
        ip = request.remote_addr
        print("IP IS -----> "+ip)
        print(result)
        create_instance = mkdb3.module(ip, result['teacher'], result['section'], result['timeout'])
        if ip not in working:
            make_worker = Thread(target=start_app, args=[create_instance, ip])
            working.append(ip)
            make_worker.daemon = True
            make_worker.start()
        else:
            print("An Instance is already running !")
        return "200"
    else:
        if request.remote_addr in working:
            blocked = True
        else:
            blocked = False
        return "{}".format(blocked)


@app.route('/add', methods=["POST"])
def add():
    if request.method == "POST":
        to_add = request.form
        add_to_db(to_add)
        return redirect(url_for("home"))


@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))


if __name__ == "__main__":
    app.run(host="192.168.100.2", port=5000)
