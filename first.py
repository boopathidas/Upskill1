from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
import uuid
import hashlib
import datetime
import logging

app = Flask(__name__)

# Connect to the database
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="upskill"
)

# Define your functions here (login, signup_user, get_course_list, get_exam_questions_with_options, insert_exam_result, calculate_overall_score)

# Function to login
def login(username, password):
    cursor = mydb.cursor()
    query = "SELECT user_id FROM users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

# Function to handle signup logic
def signup_user(username, password):
    cursor = mydb.cursor()
    try:
        query = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(query, (username, password))
        mydb.commit()
        user_id = cursor.lastrowid
        cursor.close()
        return user_id
    except mysql.connector.Error as err:
        print("Error: {}".format(err))
        return None

# Function to retrieve the list of available courses
def get_course_list():
    cursor = mydb.cursor()
    query = "SELECT course_id, course_name FROM courses"
    cursor.execute(query)
    course_list = cursor.fetchall()
    cursor.close()
    return course_list

# Function to retrieve all exam questions with options for a specific course
def get_exam_questions_with_options(course_id):
    cursor = mydb.cursor()
    query = "SELECT q.question_id, q.question_text, o.option_text, o.is_correct \
             FROM questions q \
             INNER JOIN options o ON q.question_id = o.question_id \
             WHERE q.course_id = %s"
    cursor.execute(query, (course_id,))
    questions_with_options = {}
    for question_id, question_text, option_text, is_correct in cursor.fetchall():
        if question_id not in questions_with_options:
            questions_with_options[question_id] = {
                'question_text': question_text,
                'options': []
            }
        questions_with_options[question_id]['options'].append({
            'option_text': option_text,
            'is_correct': bool(is_correct)
        })
    cursor.close()
    return questions_with_options
@app.route('/api/get_exam_questions_with_options', methods=['GET'])
def api_get_exam_questions_with_options():
    course_id = request.args.get('course_id')
    if not course_id:
        return jsonify({'error': 'course_id is required'}), 400
    try:
        course_id = int(course_id)
    except ValueError:
        return jsonify({'error': 'course_id must be an integer'}), 400
    questions_with_options = get_exam_questions_with_options(course_id)
    return jsonify(questions_with_options)


# Function to insert exam results
def insert_exam_result(user_id, course_id, score):
    cursor = mydb.cursor()
    query = "INSERT INTO exam_results (user_id, course_id, score) VALUES (%s, %s, %s)"
    cursor.execute(query, (user_id, course_id, score))
    mydb.commit()
    cursor.close()

# Function to calculate overall score for a user
def calculate_overall_score(user_id):
    cursor = mydb.cursor()
    query = "SELECT SUM(score) FROM exam_results WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    total_score = cursor.fetchone()[0]
    cursor.close()
    return total_score

# Main route
@app.route('/')
def index():
    return render_template('login.html')

# Route to handle form submission
@app.route('/submit', methods=['POST'])
def submit():
    username = request.form['username']
    password = request.form['password']
    user_id = login(username, password)
    if user_id:
        return render_template('course_selection.html', user_id=user_id, courses=get_course_list())
    else:
        return render_template('login.html', message="Invalid username or password. Please try again.")

# Route to handle course selection form submission
@app.route('/select_course', methods=['POST'])
def select_course():
    user_id = request.form['user_id']
    course_id = request.form['course_id']
    return render_exam_page(user_id, course_id)

# Render exam page
def render_exam_page(user_id, course_id):
    questions_with_options = get_exam_questions_with_options(course_id)
    return render_template('exam.html', questions_with_options=questions_with_options, user_id=user_id)

def get_correct_option_for_question(question_id):
    cursor = mydb.cursor()
    query = "SELECT option_text FROM options WHERE question_id = %s AND is_correct = 1"
    cursor.execute(query, (question_id,))
    correct_option = cursor.fetchone()[0]
    cursor.close()
    return correct_option


# Route to handle exam form submission
@app.route('/result', methods=['POST'])
def result():
    user_id = request.form['user_id']
    course_id = request.form['course_id']
    correct_answers = 0
    for question_id, option_chosen in request.form.items():
        if question_id != 'user_id' and question_id != 'course_id':
            correct_option = get_correct_option_for_question(question_id)
            if option_chosen == correct_option:
                correct_answers += 1
            insert_exam_result(user_id, course_id, int(option_chosen == correct_option))
    overall_score = calculate_overall_score(user_id)
    total_questions = len(request.form) - 2  # Exclude user_id and course_id from the count
    incorrect_answers = total_questions - correct_answers
    return render_template('result.html', overall_score=overall_score, correct_answers=correct_answers, incorrect_answers=incorrect_answers)

# Function to authenticate admin users
def admin_login(username, password):
    cursor = mydb.cursor()
    query = "SELECT id FROM admin_users WHERE username = %s AND password = %s"
    cursor.execute(query, (username, password))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

# Route for admin login page
@app.route('/admin/login')
def admin_login_page():
    return render_template('admin_login.html')

# Route to authenticate admin users
@app.route('/admin/authenticate', methods=['POST'])
def admin_authenticate():
    username = request.form['username']
    password = request.form['password']
    id = admin_login(username, password)
    if id:
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('admin_login_page', message="Invalid username or password"))

# Route for admin dashboard
@app.route('/admin/dashboard')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/fetch_enquiry_details', methods=['POST'])
def fetch_enquiry_details():
    name = request.form['name']
    cursor = mydb.cursor()
    cursor.execute("SELECT email, mobile, gender, qualification, address FROM enquiries1 WHERE name = %s", (name,))
    enquiry_details = cursor.fetchone()
    cursor.close()
    if enquiry_details:
        return jsonify({
            'email': enquiry_details[0],
            'mobile': enquiry_details[1],
            'gender': enquiry_details[2],
            'qualification': enquiry_details[3],
            'address': enquiry_details[4]
        })
    else:
        return jsonify({})

@app.route('/submit_enquiry', methods=['POST'])
def submit_enquiry_page():
    if request.method == 'POST':
        enquiry_date = request.form['enquiry_date']
        name = request.form['name']
        address = request.form['address']
        mobile = request.form['mobile']
        email = request.form['email']
        qualification = request.form['qualification']
        gender = request.form.get('gender', '')

        # Generate unique identifier for the enquiry
        enquiry_no = generate_enquiry_number()

        # Insert enquiry details into the database
        enquiry_id = submit_enquiry(enquiry_no, enquiry_date, name, address, mobile, email, qualification, gender)

        if enquiry_id:
            # Pass the enquiry details to the template
            return render_template('enquiry_form.html', today_date=enquiry_date, enquiry_no=enquiry_no, enquiry_id=enquiry_id)
        else:
            return render_template('enquiry_form.html', message="Error: Failed to submit enquiry. Please try again.")
    else:
        return render_template('enquiry_form.html', message="Error: Invalid request method.")

# Modify the submit_enquiry() function to fix the SQL query and insert data into the database
def submit_enquiry(enquiry_no, enquiry_date, name, address, mobile, email, qualification, gender):
    cursor = mydb.cursor()
    try:
        print("Inserting enquiry...")
        query = "INSERT INTO enquiries1 (enquiry_date, enquiry_no, name, address, mobile, email, qualification, gender) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (enquiry_no, enquiry_date, name, address, mobile, email, qualification, gender))
        mydb.commit()
        enquiry_id = cursor.lastrowid
        cursor.close()
        print("Enquiry inserted successfully.")
        return enquiry_id
    except mysql.connector.Error as err:
        print("Error: {}".format(err))
        return None

def generate_enquiry_number():
    cursor = mydb.cursor()
    try:
        cursor.execute("SELECT enquiry_no FROM enquiries1")
        existing_enquiries = cursor.fetchall()
        existing_numbers = []
        if existing_enquiries:
            for enquiry_tuple in existing_enquiries:
                enquiry = enquiry_tuple[0]
                if enquiry:
                    existing_numbers.append(int(enquiry[3:]))
        max_number = max(existing_numbers) if existing_numbers else 0
        new_number = max_number + 1
        enquiry_no = 'ENQ' + str(new_number).zfill(3)  # Pad with zeros if necessary
        cursor.close()
        return enquiry_no
    except mysql.connector.Error as err:
        print("Error: {}".format(err))
        return None

# Function to retrieve all enquiries from the database
def get_all_enquiries():
    cursor = mydb.cursor(dictionary=True)
    try:
        cursor.execute("SELECT enquiry_no FROM enquiries1")
        enquiries = cursor.fetchall()
        cursor.close()
        return enquiries
    except mysql.connector.Error as err:
        print("Error: {}".format(err))
        cursor.close()
        return None
    
def submit_enquiry(enquiry_no, enquiry_date, name, address, mobile, email, qualification, gender):
    cursor = mydb.cursor()
    try:
        print("Inserting enquiry...")
        query = "INSERT INTO enquiries1 (enquiry_no, enquiry_date, name, address, mobile, email, qualification, gender) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (enquiry_no, enquiry_date, name, address, mobile, email, qualification, gender))
        mydb.commit()  # Commit the transaction
        enquiry_id = cursor.lastrowid
        cursor.close()  # Close the cursor
        print("Enquiry inserted successfully.")
        return enquiry_id
    except mysql.connector.Error as err:
        print("Error: {}".format(err))
        mydb.rollback()  # Rollback the transaction in case of error
        cursor.close()  # Close the cursor
        return None

# Route to render the enquiry form
@app.route('/enquiry')
def enquiry():
    today_date = datetime.date.today().strftime('%Y-%m-%d')
    return render_template('enquiry_form.html', today_date=today_date)


# Route to render all courses
@app.route('/all_courses')
def all_courses():
    return render_template('all_courses.html')
# Function to retrieve names of all enquiries
def get_enquiry_names():
    cursor = mydb.cursor()
    #try:
    cursor.execute("SELECT name FROM enquiries1")
    enquiry_names  = [row[0] for row in cursor.fetchall()]  # Fetch all results
    cursor.close()  # Close cursor after fetching results
    return enquiry_names 
    '''except mysql.connector.Error as err:
        print("Error: {}".format(err))
        cursor.close()
        return []'''
@app.route('/student_registration', methods=['GET', 'POST'])
def student_registration():
    if request.method == 'POST':
        # Extract form data
        registration_no = request.form.get('registration_no')
        date_of_registration = request.form.get('date_of_registration')
        dob = request.form.get('date_of_birth')
        gender = request.form.get('gender', '')
        address = request.form.get('address', '')
        mobile_no = request.form.get('mobile_no', '')
        email = request.form.get('email','')
        qualification = request.form.get('qualification','')
        total_fees = request.form.get('total_fees','')
        #registration_number = generate_registration_number()

        # Insert data into the database
        cursor = mydb.cursor()
        sql = "INSERT INTO student_registration (registration_no, date_of_registration, dob, gender, address, mobile_no, email, qualification, total_fees) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        val = (registration_no, date_of_registration, dob, gender, address, mobile_no, email, qualification, total_fees)

        cursor.execute(sql, val)
        mydb.commit()
        cursor.close()
        
        return "Student registration successful!"
    else:
        enquiry_names = get_enquiry_names()
        registration_number = generate_registration_number()
        current_date = datetime.date.today().strftime('%Y-%m-%d')
        return render_template('student_registration_form.html', registration_number=registration_number, current_date=current_date, enquiry_names=enquiry_names)

# Function to generate registration number
def generate_registration_number():
    cursor = mydb.cursor()
    cursor.execute("SELECT COUNT(*) FROM student_registration")
    registration_count = cursor.fetchone()[0]
    registration_number = f"UPS{registration_count + 1:03d}"
    cursor.close()
    return registration_number

# Modify the database schema to include tables for student exam scores and file-based questions

# Function to store student exam scores in the database
def store_exam_score(user_id, course_id, score):
    cursor = mydb.cursor()
    query = "INSERT INTO exam_scores (user_id, course_id, score) VALUES (%s, %s, %s)"
    cursor.execute(query, (user_id, course_id, score))
    mydb.commit()
    cursor.close()

# Function to retrieve exam scores for a student
def get_student_exam_scores(user_id):
    cursor = mydb.cursor()
    query = "SELECT course_id, score FROM exam_scores WHERE user_id = %s"
    cursor.execute(query, (user_id,))
    scores = cursor.fetchall()
    cursor.close()
    return scores

# Function to upload file-based questions for a course
def upload_file_based_questions(course_id, file):
    # Implement logic to save the uploaded file and store its details in the database
    pass

# Route to handle student's exam scores
@app.route('/exam_scores/<user_id>')
def exam_scores(user_id):
    scores = get_student_exam_scores(user_id)
    return render_template('student_scores.html', scores=scores)

# Route to handle uploading file-based questions by admins
@app.route('/upload_questions/<course_id>', methods=['POST'])
def upload_questions(course_id):
    if request.method == 'POST':
        # Get the uploaded file
        uploaded_file = request.files['file']
        # Save the file and store its details in the database
        upload_file_based_questions(course_id, uploaded_file)
        return redirect(url_for('admin_dashboard'))
    else:
        return "Invalid request method."
    
@app.route('/exam')
def exam():
    return render_template('exam1.html')  

# Function to retrieve student records from the database
# Function to retrieve student records from the database
def get_student_records():
    cursor = mydb.cursor(dictionary=True)
    query = """
        SELECT s.id, s.registration_no, s.date_of_registration, s.total_fees, e.score, c.course_name
        FROM student_registration s
        LEFT JOIN exam_results e ON s.id = e.user_id
        LEFT JOIN courses c ON e.course_id = c.course_id
    """
    cursor.execute(query)
    student_records = cursor.fetchall()
    cursor.close()
    return student_records


# Route to handle student option
@app.route('/exam/student')
def student_exam():
    # Fetch student records from the database
    student_records = get_student_records()
    # Render the student_scores.html template with the fetched records
    return render_template('student_scores.html', student_records=student_records)

# Route to handle staff option
@app.route('/exam/staff', methods=['GET', 'POST'])
def staff_exam():
    if request.method == 'POST':
        # Handle file upload and save questions to the database
        # Implement logic to upload questions
        flash("Questions uploaded successfully!", "success")
        return redirect(url_for('exam'))
    else:
        return render_template('upload_questions.html')
    

@app.route('/student_records')
def student_records():
    # Fetch enquiry count
    enquiry_count = fetch_enquiry_count()

    # Fetch registration records
    registration_records = fetch_registration_records()

    # Fetch details stored in the database for each person
    #person_details = fetch_person_details()

    return render_template('student_records.html', enquiry_count=enquiry_count, registration_records=registration_records)

# Function to fetch enquiry count
def fetch_enquiry_count():
    cursor = mydb.cursor()
    cursor.execute("SELECT COUNT(*) FROM enquiries1")
    enquiry_count = cursor.fetchone()[0]
    cursor.close()
    return enquiry_count
    

# Function to fetch registration records
def fetch_registration_records():
    cursor = mydb.cursor()
    cursor.execute("SELECT * FROM student_registration")
    registration_records = cursor.fetchall()
    cursor.close()
    return registration_records

@app.route('/assessment')
def assessment():
    return render_template('assessment.html')

@app.route('/logout')
def logout():
    # Clear the session data
    session.clear()
    # Redirect to the login page (or any other page)
    return redirect(url_for('index'))
def course_selection():
    if request.method == 'POST':
        course_id = request.form.get('course_id')
        user_id = request.form.get('user_id')
        # Process the selected course here
        return redirect(url_for('assessment'))  # Redirect to assessment or another appropriate page
    return render_template('course_selection.html', courses=courses, user_id=1)  # Replace user_id with actual user ID


if __name__ == "__main__":
    app.run(debug=True)
