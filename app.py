from flask import Flask, render_template, request, json, redirect, session
from flaskext.mysql import MySQL
from werkzeug import generate_password_hash, check_password_hash
import requests
import json
app = Flask(__name__)
mysql = MySQL()

# MySQL configurations
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'BucketList'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)
conn = mysql.connect()
cursor = conn.cursor()
app.secret_key = 'secret key'
apikey = "7b363e36"


@app.route("/")
def main():
    return render_template('index.html')


@app.route('/showSignUp')
def showSignUp():
    return render_template('signup.html')


@app.route('/signUp', methods=['POST'])
def signUp():
    _name = request.form['inputName']
    _email = request.form['inputEmail']
    _password = request.form['inputPassword']
    if _name and _email and _password:
        _hashed_password = generate_password_hash(_password)
        # print(_hashed_password)
        cursor.callproc('sp_createUser', (_name, _email, _hashed_password))
        data = cursor.fetchall()

        if len(data) is 0:
            conn.commit()
            return json.dumps({'message': 'User created successfully !'})
        else:
            return json.dumps({'error': str(data[0])})
    else:
        return json.dumps({'html': '<span>Enter the required fields</span>'})


@app.route('/showSignin')
def showSignin():
    if session.get('user'):
        return render_template('userHome.html')
    else:
        return render_template('signin.html')


@app.route('/validateLogin', methods=['POST'])
def validateLogin():
    try:
        _username = request.form['inputEmail']
        _password = request.form['inputPassword']

        # connect to mysql
        cursor.callproc('sp_validateLogin', (_username,))
        data = cursor.fetchall()
        if len(data) > 0:
            if check_password_hash(str(data[0][3]), str(_password)):
                session['user'] = data[0][0]
                return redirect('/userHome')
            else:
                return render_template('error.html', error='Wrong Email address or Password.')
        else:
            return render_template('error.html', error='Wrong Email address or Password.')

    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/userHome')
def userHome():
    if session.get('user'):
        return render_template('userHome.html')
    else:
        return render_template('error.html', error='Unauthorized Access')


@app.route('/showAddWish')
def showAddWish():
    return render_template('addWish.html')


@app.route('/showAddItem')
def showAddItem():
    return render_template('addItem.html')


@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')


@app.route('/addWish', methods=['POST'])
def addWish():
    try:
        if session.get('user'):
            _title = request.form['inputTitle']
            _rate = request.form['inputRate']
            _description = request.form['inputDescription']
            _user = session.get('user')

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_addWish', (_title, _rate, _description, _user))
            data = cursor.fetchall()

            if len(data) is 0:
                conn.commit()
                return redirect('/showAddWish')
            else:
                return render_template('error.html', error='An error occurred!')

        else:
            return render_template('error.html', error='Unauthorized Access')
    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/addItem', methods=['POST'])
def addItem():
    try:
        if session.get('user'):
            _title = request.form['inputTitle']
            _user = session.get('user')

            conn = mysql.connect()
            cursor = conn.cursor()
            cursor.callproc('sp_addItem', (_title, _user))
            data = cursor.fetchall()

            if len(data) is 0:
                conn.commit()
                return redirect('/showAddItem')
            else:
                return render_template('error.html', error='An error occurred!')

        else:
            return render_template('error.html', error='Unauthorized Access')
    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/getWish')
def getWish():
    try:
        if session.get('user'):
            _user = session.get('user')
            con = mysql.connect()
            cursor = con.cursor()
            cursor.callproc('sp_GetWishByUser', (_user,))
            reviews = cursor.fetchall()
            reviews_dict = []
            for revs in reviews:
                revs_dict = {'Id': revs[0], 'Title': revs[1],
                             'Rate': revs[2], 'Description': revs[3]}
                reviews_dict.append(revs_dict)
            return json.dumps(reviews_dict)
        else:
            return render_template('error.html', error='Unauthorized Access')
    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route('/showBucket')
def showBucket():
    return render_template('showBucket.html')


@app.route('/getItem')
def getItem():
    try:
        if session.get('user'):
            _user = session.get('user')
            con = mysql.connect()
            cursor = con.cursor()
            cursor.callproc('sp_GetItemByUser', (_user,))
            reviews = cursor.fetchall()
            reviews_dict = []
            for revs in reviews:
                revs_dict = {'Id': revs[0], 'Title': revs[1]}
                reviews_dict.append(revs_dict)
            return json.dumps(reviews_dict)
        else:
            return render_template('error.html', error='Unauthorized Access')
    except Exception as e:
        return render_template('error.html', error=str(e))


@app.route("/showMore", methods=['GET', 'POST'])
def showMore():
    # movie = 0
    movie = request.form.get('movie')
    url = "http://www.omdbapi.com/?t={}&apikey={}".format(movie, apikey)
    url = url.replace(" ", "%20")
    r = requests.get(url=url)
    res = json.loads(r.content)
    return render_template('showMore.html', Movie=movie.upper(), img=res['Poster'], date=res['Released'], dir=res['Director'], actors=res['Actors'], plot=res['Plot'])


if __name__ == "__main__":
    app.run(debug=True, port=5000)
