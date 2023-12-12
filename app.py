############### IMPORT MODULES  ###############
from flask import (
    Flask,
    request,
    render_template,
    session,
    redirect,
    url_for,
    make_response,
    jsonify,
    json,
    Response
)   

from werkzeug.middleware.dispatcher import DispatcherMiddleware
from werkzeug.wrappers import Response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import cv2
import pymysql
import os
from functools import wraps
import random
import face_recognition
import numpy as np
import os
import scipy
import string
import datetime
import pandas as pd
from flask_mail import Mail,Message
from werkzeug.utils import secure_filename
############### IMPORT MODULES  ###############

dbServer = 'localhost'
dbPort = 3306
dbName = 'stu-manage'
dbUserName = 'root'
dbPassword = '2703'

# dbServer = 'sql12.freemysqlhosting.net'
# dbPort = 3306
# dbName = 'sql12662918'
# dbUserName = 'sql12662918'
# dbPassword = 'wHayw3Ny3q'



app = Flask(__name__)
mail = Mail(app)

app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'jdk3080@gmail.com'
app.config['MAIL_PASSWORD'] = 'fjwwjnhbdssxlgmm'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

app.secret_key = 'set'

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"

# app.config['MAIL_SERVER']='smtp.gmail.com'
# app.config['MAIL_PORT'] = 465
# app.config['MAIL_USERNAME'] = 'jdk3080@gmail.com'
# app.config['MAIL_PASSWORD'] = 'fjwwjnhbdssxlgmm'
# app.config['MAIL_USE_TLS'] = False
# app.config['MAIL_USE_SSL'] = True
# mail = Mail(app)
############### DB CONNECTION  ###############
db = pymysql.connect(host=dbServer,
                        port=dbPort,
                        user=dbUserName,
                        password=dbPassword,
                        database=dbName,
                        charset='utf8mb4',
                        cursorclass=pymysql.cursors.DictCursor)

dbCon = db.cursor(pymysql.cursors.DictCursor)
############### DB CONNECTION  ###############

############### LOGIN CHECK  ###############
def loggin_route(f):
    @wraps(f)
    def route_check(*args, **kwargs):
        
        try:
            loginCheck = _loginCheck()
            if loginCheck == False:
                redirectUrl = request.path
                return redirect(url_for("login", redirectUrl=redirectUrl))
            userDetail=session.get("userInfo")
            userId = int(userDetail['userId'])
            userType = userDetail['userType']
            userEmail = userDetail['email']
            if userType == 'Admin':
                return f(*args, **kwargs)
            if userType == 'Staff':
                return f(*args, **kwargs)
            if userType == 'Student':
                return f(*args, **kwargs)
            else:
                return render_template("404.html", loggedIn = 1, headerMenu = 1, homePage = 1, Bookmarks = 0, setting = 0,userDetail=userDetail)
        except TypeError as e:
            return redirect("/login")
    return route_check

def _loginCheck():
    if "userInfo" in session:
        return True
    else:
        return False
############### LOGIN CHECK  ###############

@app.route('/login', methods=['GET'])
def login():
    session.clear()

    # Get redirectUrl
    redirectUrl = request.args.get('redirectUrl')

    response = make_response(render_template("login2.html",redirectUrl=redirectUrl,loginPage=1))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response


@app.route('/userLogin', methods=['POST'])
def userLogin():
    txtUserName = request.form.get("txtUserName")
    txtPassword = request.form.get("txtPassword")

    dbCon.execute("SELECT * FROM tbl_users WHERE deleted = 0 AND userEmail = %s LIMIT 1", (txtUserName))
    row = dbCon.fetchone()
    if row:
        hashPassword = row['password']
        hashCheck = check_password_hash(hashPassword, txtPassword)

        if hashCheck == True:
            userInfo = {
                'userName': row['userName'], 'userId': row['id'], 'fullName': row['userName'], 'userType': row['userType'],'email':row['userEmail'],'tbl_Id': row['userId']}
            session["userInfo"] = userInfo
            print(userInfo)
            return jsonify({'status': 'success', 'response': userInfo}), 200
        else:
            return jsonify({'status': 'fail'}), 200
    else:
        return jsonify({'status': 'fail'}), 200


@app.route('/logout', methods=['GET'])
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route('/index')
@app.route('/')
@loggin_route
def index():
    
    userDetail=session.get("userInfo")
    userType = userDetail['userType']
    userId = userDetail['userId']

    
    
    if userType == 'Admin':
        dbCon.execute('SELECT * FROM tbl_students')
        students = len(dbCon.fetchall())
            
        dbCon.execute('SELECT * FROM tbl_lecturers')
        lecturers = len(dbCon.fetchall())
            
        dbCon.execute('SELECT * FROM tbl_cource')
        cources = len(dbCon.fetchall())
            
        dbCon.execute('SELECT * FROM tbl_subject')
        subject = len(dbCon.fetchall())
        
        dbCon.execute('SELECT * FROM tbl_classes')
        classes = len(dbCon.fetchall())
        return render_template("dashboard.html",students=students,lecturers=lecturers,cources=cources,subject=subject,classes=classes)
    if userType == 'Staff':
        dbCon.execute(f'''select  
                        *
                        from tbl_classes
                        left join tbl_subject  on tbl_classes.subjectId =  tbl_subject.subjectId 
                        left join tbl_cource on tbl_subject.courceId = tbl_cource.courceId
                        left join tbl_lecturers on tbl_subject.lecturerId = tbl_lecturers.id where tbl_lecturers.id ={userId}''')
        students = len(dbCon.fetchall())
            
        dbCon.execute("""select  tbl_cource.courceName,tbl_cource.courceDetails,tbl_lecturers.lecturerName,tbl_lecturers.id
                        from tbl_subject
                        left join tbl_cource on tbl_subject.courceId = tbl_cource.courceId
                        left join tbl_lecturers on tbl_subject.lecturerId = tbl_lecturers.id
                        where tbl_lecturers.id =%s""",(userId))
        cources = len(dbCon.fetchall())
        
        print(cources,students)   
        dbCon.execute('SELECT * FROM tbl_subject WHERE lecturerId=%s',(userId))
        subject = len(dbCon.fetchall())
        
        dbCon.execute('SELECT * FROM tbl_classes')
        classes = len(dbCon.fetchall())
        
        return render_template("staffHome.html",students=students,cources=cources,subject=subject,classes=classes)
    if userType == 'Student':
                    
        dbCon.execute('SELECT * FROM tbl_cource')
        cources = len(dbCon.fetchall())
            
        dbCon.execute('SELECT * FROM tbl_subject')
        subject = len(dbCon.fetchall())
        
        dbCon.execute('SELECT * FROM tbl_classes')
        classes = len(dbCon.fetchall())
        
        return render_template("stuHome.html",cources=cources,subject=subject,classes=classes)

############## STUDENTS #############
@app.route('/manage-students')
@loggin_route
def manage_students():
    dbCon.execute('SELECT * FROM tbl_students')
    students = dbCon.fetchall()
    return render_template('manage-students.html',students=students)

@app.route('/add-student', methods=['POST'])
def add_student():
    print(request.form.get)
    txtStudentName = request.form.get("txtStudentName")
    txtStudentAddress = request.form.get("txtStudentAddress") 
    txtStudentHomeNo = request.form.get("txtStudentHomeNo")
    txtStudentNo = request.form.get("txtStudentNo") 
    txtStudentDob = request.form.get("txtStudentDob") 
    txtStudentEmail = request.form.get("txtStudentEmail")
    txtStudentgender = request.form.get("txtStudentgender")

    dbCon.execute('INSERT INTO tbl_students(studentName,address,homeNo,mobileNo,dob,email,gender) VALUES(%s,%s,%s,%s,%s,%s,%s)', (txtStudentName, txtStudentAddress, txtStudentHomeNo, txtStudentNo, txtStudentDob, txtStudentEmail,txtStudentgender))
    db.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/edit-student', methods=['POST'])
def edit_student():
    txtStudentId = request.form.get("txtStudentId")
    txtStudentName = request.form.get("txtStudentName")
    txtStudentAddress = request.form.get("txtStudentAddress") 
    txtStudentHomeNo = request.form.get("txtStudentHomeNo")
    txtStudentNo = request.form.get("txtStudentNo") 
    txtStudentDob = request.form.get("txtStudentDob") 
    txtStudentEmail = request.form.get("txtStudentEmail")
    txtStudentgender = request.form.get("txtStudentgender")

    dbCon.execute('UPDATE tbl_students SET studentName=%s ,address=%s, homeNo=%s, mobileNo=%s, dob=%s, email=%s, gender=%s WHERE id=%s', (txtStudentName, txtStudentAddress, txtStudentHomeNo, txtStudentNo, txtStudentDob, txtStudentEmail, txtStudentgender, txtStudentId))
    db.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/delete-student', methods=['POST'])
def delete_student():
    txtStudentId = request.form.get("txtStudentId")
    
    dbCon.execute('SELECT * FROM tbl_classes WHERE studentId=%s', (txtStudentId))
    row = dbCon.fetchone()
    
    dbCon.execute('SELECT * FROM tbl_students')
    student = dbCon.fetchall()
    
    if row:
        return jsonify({'status': 'error'}), 200
    else:
        os.remove(student['attachment'])
        dbCon.execute('DELETE FROM tbl_students WHERE id=%s', (txtStudentId))
        db.commit()
        return jsonify({'status': 'success'}), 200
############## STUDENTS ##############

############## LETCTURES ##############
@app.route('/manage-lecturers')
@loggin_route
def manage_lecturers():
    dbCon.execute('SELECT * FROM tbl_lecturers')
    lecturers = dbCon.fetchall()
    
    return render_template('manage-lecturers.html',lecturers=lecturers)

@app.route('/add-lecturer', methods=['POST'])
def add_lecturer():
    print(request.form)
    txtLecturerName = request.form.get("txtLecturerName")
    txtLecturerDOB = request.form.get("txtLecturerDOB")
    txtLecturerNIC = request.form.get("txtLecturerNIC")
    txtLecturerMobile = request.form.get("txtLecturerMobile")
    txtLecturerEmail = request.form.get("txtLectureremail")
    txtLecturerAddress = request.form.get("txtLecturerAddress")

    dbCon.execute('INSERT INTO tbl_lecturers(lecturerName,dob,nic,mobileNo,address,email) VALUES(%s,%s,%s,%s,%s,%s)', (txtLecturerName,txtLecturerDOB,txtLecturerNIC,int(txtLecturerMobile),txtLecturerAddress,txtLecturerEmail))
    db.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/edit-lecturer', methods=['POST'])
def edit_lecturer():
    txtlecturerId = request.form.get("txtLecturerId")
    txtlecturerName = request.form.get("txtLecturerName")
    txtLecturerDOB = request.form.get("txtLecturerDOB")
    txtLecturerNIC = request.form.get("txtLecturerNIC")
    txtLecturerMobile = request.form.get("txtLecturerMobile")
    txtLecturerEmail = request.form.get("txtLectureremail")
    txtLecturerAddress = request.form.get("txtLecturerAddress")
    
    dbCon.execute('UPDATE tbl_lecturers SET lecturerName=%s ,dob=%s, nic=%s, mobileNo=%s, address=%s, email=%s WHERE id=%s', (txtlecturerName,txtLecturerDOB,txtLecturerNIC,txtLecturerMobile,txtLecturerAddress,txtLecturerEmail,txtlecturerId))
    db.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/delete-lecturer', methods=['POST'])
def delete_lecturer():
    txtlecturerId = request.form.get("txtLecturerId")
    
    dbCon.execute('SELECT * FROM tbl_subject WHERE lecturerId=%s', (txtlecturerId))
    row = dbCon.fetchall()
    
    
    if row:
        return jsonify({'status': 'error'}), 200
    else:
        dbCon.execute('DELETE FROM tbl_lecturers WHERE id=%s', (txtlecturerId))
        db.commit()
        return jsonify({'status': 'success'}), 200
############## LETCTURES ##############

############## COURCES #############
@app.route('/manage-cource')
@loggin_route
def manage_cources():
    dbCon.execute('SELECT * FROM tbl_cource')
    cources = dbCon.fetchall()
    return render_template('manage-cource.html',cources=cources)

@app.route('/manage-cource-stu')
@loggin_route
def manage_cources_stu():
    dbCon.execute('SELECT * FROM tbl_cource')
    cources = dbCon.fetchall()
    return render_template('stu_cource.html',cources=cources)

@app.route('/add-cource', methods=['POST'])
def add_cource():
    txtCourceName = request.form.get("txtCourceName")
    txtCourceStartDate = request.form.get("txtCourceStartDate")
    txtCourceDetail = request.form.get("txtCourceDetail")
    

    dbCon.execute('INSERT INTO tbl_cource(courceName,courceStartDate,courceDetails) VALUES(%s,%s,%s)', (txtCourceName,txtCourceStartDate,txtCourceDetail))
    db.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/edit-cource', methods=['POST'])
def edit_cource():
    txtCourceId = request.form.get("txtCourceId")
    txtCourceName = request.form.get("txtCourceName")
    txtCourceStartDate = request.form.get("txtCourceStartDate")
    txtCourceDetail = request.form.get("txtCourceDetail")
    

    dbCon.execute('UPDATE tbl_cource SET courceName=%s ,courceStartDate=%s ,courceDetails=%s WHERE courceId=%s', (txtCourceName,txtCourceStartDate,txtCourceDetail,txtCourceId))
    db.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/delete-cource', methods=['POST'])
def delete_cource():
    txtCourceId = request.form.get("txtCourceId")
    
    dbCon.execute('SELECT * FROM tbl_subject WHERE courceId=%s', (txtCourceId))
    row = dbCon.fetchall()
    
    if row:
        return jsonify({'status': 'error'}), 200
    else:
        dbCon.execute('DELETE FROM tbl_cource WHERE courceId=%s', (txtCourceId))
        db.commit()
        return jsonify({'status': 'success'}), 200

############## COURCES ##############

############## Subject ##############

@app.route('/manage-subjects')
@loggin_route
def manage_subject():
    dbCon.execute('SELECT * FROM tbl_subject')
    subjects = dbCon.fetchall()
    dbCon.execute('SELECT * FROM tbl_cource')
    course = dbCon.fetchall()
    dbCon.execute('SELECT * FROM tbl_lecturers')
    lecturer = dbCon.fetchall()

    return render_template('manage-subjects.html',subjects=subjects,course=course,lecturer=lecturer)

@app.route('/manage-subjects-stu')
@loggin_route
def manage_subject_stu():
    dbCon.execute('SELECT * FROM tbl_subject')
    subjects = dbCon.fetchall()
    dbCon.execute('SELECT * FROM tbl_cource')
    course = dbCon.fetchall()
    dbCon.execute('SELECT * FROM tbl_lecturers')
    lecturer = dbCon.fetchall()

    return render_template('stu_sub.html',subjects=subjects,course=course,lecturer=lecturer)

@app.route('/add-subject', methods=['POST'])
def add_subject():
    
    txtSubjectName = request.form.get("txtSubjectName")
    txtCourseId = request.form.get("txtCourseId")
    txtLecturerId = request.form.get("txtLecturerId")
    
    dbCon.execute('INSERT INTO tbl_subject(subjectName,courceId,lecturerId) VALUES(%s,%s,%s)', (txtSubjectName,txtCourseId,txtLecturerId))
    db.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/edit-subject', methods=['POST'])
def edit_subject():
    print(request.form)
    txtSubjectId = request.form.get("txtSubjectId")
    txtLecturerId = request.form.get("txtLecturerId")
    txtCourceId = request.form.get("txtCourseId")
    txtSubjetName = request.form.get("txtSubjectName")

    dbCon.execute('UPDATE tbl_subject SET subjectName=%s, courceId=%s, lecturerId=%s WHERE subjectId=%s', (txtSubjetName,int(txtCourceId),int(txtLecturerId),int(txtSubjectId)))
    db.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/delete-subject', methods=['POST'])
def delete_subject():
    txtSubjectId = request.form.get("txtSubjectId")
    
    dbCon.execute('SELECT * FROM tbl_class WHERE subjectId=%s', (txtSubjectId))
    row = dbCon.fetchall()
    
    if row:
        return jsonify({'status': 'error'}), 200
    else:
        dbCon.execute('DELETE FROM tbl_lecturers WHERE id=%s', (txtSubjectId))
        db.commit()
        return jsonify({'status': 'success'}), 200

############## Subject ##############

############## classes ##############
@app.route('/manage-classes')
@loggin_route
def manage_classes():
    dbCon.execute('SELECT * FROM tbl_classes')
    classes = dbCon.fetchall()
    
    dbCon.execute('SELECT * FROM tbl_students')
    students = dbCon.fetchall()
    
    dbCon.execute('SELECT * FROM tbl_subject')
    subject = dbCon.fetchall()
    
    return render_template('schedule-course.html',classes=classes, subject=subject, students=students)


@app.route('/manage-classes-stu')
@loggin_route
def manage_classes_stu():
    dbCon.execute('SELECT * FROM tbl_classes')
    classes = dbCon.fetchall()
    
    dbCon.execute('SELECT * FROM tbl_students')
    students = dbCon.fetchall()
    
    dbCon.execute('SELECT * FROM tbl_subject')
    subject = dbCon.fetchall()
    
    return render_template('stu-schedule-course.html',classes=classes, subject=subject, students=students)

@app.route('/add-classes', methods=['POST'])
def add_classes():

    checkedValues = request.form.get("checkedValues")
    txtSubjectId = request.form.get("txtSubjectId")
    txtStudentId = request.form.get("txtStudentId")
    txtStartDate = datetime.datetime.strptime(request.form.get("txtStartDate"), '%Y-%M-%d').date()
    txtEndDate = datetime.datetime.strptime(request.form.get("txtEndDate"), '%Y-%M-%d').date()
    txtStartTime = datetime.datetime.strptime(request.form.get("txtStartTime"), '%H:%M').time()
    txtEndtime = datetime.datetime.strptime(request.form.get("txtEndtime"), '%H:%M').time()
    
    dbCon.execute('INSERT INTO tbl_classes(subjectId, studentId, classStartDate, classStartTime, classEndTime, weekDay, classEndDate) VALUES(%s,%s,%s,%s,%s,%s,%s)', (txtSubjectId,txtStudentId,txtStartDate,txtStartTime,txtEndtime,checkedValues,txtEndDate))
    db.commit()
    return jsonify({'status': 'success'}), 200

@app.route('/delete-classes', methods=['POST'])
def delete_classes():
    txtClassId = request.form.get("txtClassId")
    dbCon.execute('DELETE FROM tbl_classes WHERE classId=%s', (txtClassId))
    db.commit()
    return jsonify({'status': 'success'}), 200
############## classes ##############

############## Student View #############


@app.route('/student-view')
@loggin_route
def student_view():
    dbCon.execute("""select * 
        from tbl_subject
        left join tbl_classes using (subjectId)
        left join tbl_students on tbl_classes.studentId = tbl_students.id """)
    students = dbCon.fetchall()
    return render_template('studentView.html',students=students)

@app.route('/attendance-view/')
@loggin_route
def attendance_view():
    lecturerId = request.args.get('id', default=None, type=int)
    dbCon.execute("select * from tbl_attendance",)
    attendance = dbCon.fetchall() 
    dbCon.execute('SELECT * FROM tbl_students')
    students = dbCon.fetchall()
    
    dbCon.execute('SELECT * FROM tbl_lecturers')
    lecturers = dbCon.fetchall()
    return render_template('attandance.html',attendance=attendance,student=students, lecturers=lecturers)

@app.route('/attendance-stu-view/')
@loggin_route
def attendance_stu_view():
    studentId = request.args.get('id', default=None, type=int)
    dbCon.execute("select * from tbl_attendance")
    attendance = dbCon.fetchall() 
    
    dbCon.execute('SELECT * FROM tbl_students')
    students = dbCon.fetchall()
    
    dbCon.execute('SELECT * FROM tbl_lecturers')
    lecturers = dbCon.fetchall()
    return render_template('stuAttendance.html',attendance=attendance,student=students,lecturers=lecturers)

######################################################################################################################################

############### file uploade ################################
# @app.route('/file-upload', methods=['POST'])
# def fileUploade():
#     studentId = "x"
#     print(studentId)
#     file = request.files['file']
#     print(file)
#     if file.filename == '':
#         return "No selected file"
#     try: 
#         file_extension = os.path.splitext(file.filename)[1] 
#         print(file_extension)
#         if file_extension == "jfif" or file_extension == "JFIF":
#             file_extension = "jpeg"
#             new_filename = f"{str(studentId)}{file_extension}"
#             file.save(os.path.join('static\image\stu', new_filename))
#             print(new_filename)
#         else:
#             new_filename = f"{str(studentId)}{file_extension}"
#             print(new_filename)
#             file.save(os.path.join('static\image\stu', new_filename))     
        
#         return True
#     except Exception as e:
#         print(e) 
#         return False  
    
@app.route('/upload', methods=['POST'])
def upload():
    name = request.form['name']
    image = request.files['image']
    print(name, image)
    # Process the data as needed, for example, save the image to a folder
    # and return a response
    # ...
    if image.filename == '':
        return "No selected file"
    try: 
        file_extension = os.path.splitext(image.filename)[1] 
        if str(file_extension) == ".jfif" or str(file_extension) == ".JFIF":
            file_extension = ".jpeg"
            new_filename = f"{str(name)}"
            
            path_attach = 'static/image/stu/'+ new_filename
            print(path_attach)
            image.save(os.path.join('static\image\stu', new_filename))
            # dbCon.execute('UPDATE tbl_students SET  attachment=%s WHERE id=%s', (path_attach, int(name)))
            # db.commit()

            
            print('static/image/stu/'+ new_filename)
            
        else:
            file_extension = ".jpeg"
            new_filename = f"{str(name)}{file_extension}"
            
            path_attach = 'static/image/stu/'+ new_filename
            image.save(os.path.join('static\image\stu', new_filename)) 
            # dbCon.execute('UPDATE tbl_students SET  attachment=%s WHERE id=%s', (path_attach, int(name)))
            # db.commit()    
        
        return ('success'),200
    except Exception as e:
        print(e) 
        return False  
############### file uploade #############################

#########################################################################################################
def generate_password(length=12):
    # Define the character set for the password
    characters = string.ascii_letters + string.digits + string.punctuation

    # Generate the password using random characters
    password = ''.join(random.choice(characters) for _ in range(length))

    return password


def email_fun(userEmail,body):
    
    msg = Message('Hello', sender = 'jdk3080@gmail.com', recipients = [str(userEmail)])
    msg.html = body
    mail.send(msg)
    return ('success'),200

@app.route('/forgor-password',methods=['POST'])
def forgor_password():
    
    userEmail = request.form.get('txtEmail')
    userType = request.form.get('txtstatus')
    
    dbCon.execute('SELECT * FROM tbl_users WHERE userEmail=%s',(userEmail))
    user = dbCon.fetchone()
    
    if user:
    
        password = generate_password()
        body = """
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>New Password Message</title>
                <style>
                    body {
                        font-family: 'Arial', sans-serif;
                        background-color: #f5f5f5;
                        text-align: center;
                        padding: 20px;
                    }

                    .message {
                        background-color: #fff;
                        border: 1px solid #ccc;
                        padding: 20px;
                        max-width: 400px;
                        margin: 0 auto;
                        border-radius: 8px;
                        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    }

                    .password {
                        font-size: 1.5em;
                        font-weight: bold;
                        margin-bottom: 15px;
                        color: #4CAF50;
                    }
                </style>
            </head>
            <body>

            <div class="message">
                <p class="password">This is your new password:</p>
                <p>"""+password+"""</p>
                <p>Please don't forget it!</p>
            </div>

            </body>
            </html>

        """
        email_fun(userEmail,body)
        hashPassWord = generate_password_hash(
            password, method='pbkdf2:sha256', salt_length=8)
        dbCon.execute('UPDATE tbl_users SET password=%s WHERE userType=%s AND userEmail=%s', (hashPassWord,userType,userEmail))
        db.commit()
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'status': 'error'}), 200
    

@app.route('/forgot')
def forgot():
    redirectUrl = request.args.get('redirectUrl')
    return render_template('forgot.html',redirectUrl=redirectUrl,loginPage=2)

@app.route('/createUser', methods=['POST'])
def createUser():
    print(request.form)
    password = request.form.get('txtPassword')
    userEmail = request.form.get('txtEmail')
    userName = request.form.get('txtUserName')
    
    dbCon.execute('SELECT * FROM tbl_users where userEmail=%s',(userEmail))
    row = dbCon.fetchall()
    
    dbCon.execute('SELECT * FROM tbl_students where email=%s',(userEmail))
    students = dbCon.fetchone()
    
    dbCon.execute('SELECT * FROM tbl_lecturers where email=%s',(userEmail))
    lecturers = dbCon.fetchone()
    if row:
        return ('Already Exisit')
    elif students:
        userType = "Student"
        hashPassWord = generate_password_hash(
            password, method='pbkdf2:sha256', salt_length=8)
        dbCon.execute('INSERT INTO tbl_users (userName,userEmail,userType,password,userId) VALUES(%s,%s,%s,%s,%s)',(userName,userEmail,userType,hashPassWord,students['id']))
        return jsonify({'status': 'success'}), 200
    elif lecturers:
        userType = "Staff"
        hashPassWord = generate_password_hash(
            password, method='pbkdf2:sha256', salt_length=8)
        dbCon.execute('INSERT INTO tbl_users (userName,userEmail,userType,password,userId) VALUES(%s,%s,%s,%s,%s)',(userName,userEmail,userType,hashPassWord,lecturers['id']))
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'status': 'error'}), 200

        
    

#######################################################################################################
   #Assign path and create list of images.
@app.route('/take_atus/')
def take_atus():
    staff_id = request.args.get('id', default=None, type=int)

    path = 'static\image\stu'
    images = []
    personNames = []
    myList = os.listdir(path)
    #print(myList)
    for cu_img in myList:
        current_Img = cv2.imread(f'{path}\{cu_img}')
        images.append(current_Img)
        personNames.append(os.path.splitext(cu_img)[0])
    print(personNames)


    def faceEncodings(images):
        encodeList = []
        for img in images:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            encode = face_recognition.face_encodings(img)[0]
            encodeList.append(encode)
        return encodeList


    def check_name_state(name,staff_id):
        now = datetime.datetime.now()

        dbCon.execute('SELECT * FROM tbl_attendance WHERE studentId=%s', (int(name)))
        row = dbCon.fetchone()
        
        if(not row):
            dbCon.execute('INSERT INTO tbl_attendance (studentId,attendanceTime,lecturerId) VALUES(%s,%s,%s)', (int(name),now,int(staff_id)))

        # if (not azuredatabase.exist_name(name,d1)):
        #     dtstring = now.strftime("%d/%m/%Y %H:%M:%S")
        #     azuredatabase.insert_data(name, dtstring)

    encodeListKnown = faceEncodings(images)
    print('All Encodings Complete!!!')

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        faces = cv2.resize(frame, (0, 0), None, 0.25, 0.25)
        faces = cv2.cvtColor(faces, cv2.COLOR_BGR2RGB)

        facesCurrentFrame = face_recognition.face_locations(faces)
        encodesCurrentFrame = face_recognition.face_encodings(faces, facesCurrentFrame)

        for encodeFace, faceLoc in zip(encodesCurrentFrame, facesCurrentFrame):
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            # print(faceDis)
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                name = personNames[matchIndex]
                dbCon.execute('SELECT * FROM tbl_students WHERE id=%s', (int(name)))
                row = dbCon.fetchone()
                
                if row:
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.rectangle(frame, (x1, y2 - 35), (x2, y2), (0, 255, 0), cv2.FILLED)
                    cv2.putText(frame, row['studentName'], (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
                    # MarkAttendance(name)
                    check_name_state(name,staff_id)
                else:
                    y1, x2, y2, x1 = faceLoc
                    y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
                    cv2.rectangle(frame, (x1, y2 - 35), (x2, y2), (0, 0, 255), cv2.FILLED)
                    cv2.putText(frame, "UNKNOWN", (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 0, 0), 2)
                    # MarkAttendance(name)
                    

        cv2.imshow('Webcam', frame)
        if cv2.waitKey(1) == 13:
            break

    cap.release()
    cv2.destroyAllWindows()
    return redirect('/')


# This function will be called for every template rendering.   
@app.context_processor
def common_context():
    if _loginCheck() == True:
        userDetail=session.get("userInfo")
    else:
        userDetail = {}

    return {"userDetail": userDetail}

if __name__ == '__main__':
    HOST = '0.0.0.0'
    PORT = 5000
    app.run(HOST, PORT, debug=True)