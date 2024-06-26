'''import mysql.connector

# Connect to the database
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="upskill"
)

# Create a cursor object
cursor = connection.cursor()

# Retrieve the course_id values from the courses table
cursor.execute("SELECT course_id FROM course")
course_ids = [row[0] for row in cursor.fetchall()]

# Define the course_id variable (replace 123 with the actual course_id)
course_id = 8

# Check if the course_id being inserted exists in the list of course_ids
if course_id in course_ids:
    print("Course ID exists in the courses table.")
else:
    print("Course ID does not exist in the courses table.")

# Close the cursor and connection
cursor.close()
connection.close()'''

import mysql.connector

# Connect to the database
connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="upskill"
)

# Create a cursor object
cursor = connection.cursor()

# Retrieve the list of course IDs from the courses table
cursor.execute("SELECT course_id FROM courses")
course_ids = [row[0] for row in cursor.fetchall()]

# Get the course ID submitted with the form data
submitted_course_id = request.form['course_id']

# Verify if the submitted course ID exists in the list of course IDs
if submitted_course_id in course_ids:
    print("Submitted course ID is valid.")
else:
    print("Submitted course ID is invalid.")

# Close the cursor and connection
cursor.close()
connection.close()

