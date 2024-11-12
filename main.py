



import pandas as pd
import os.path
import pickle
from flask import Flask, request, session, redirect, send_from_directory
from flask import render_template
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json
from markupsafe import escape
import math
from werkzeug.utils import secure_filename


local_server=True
with open('config.json','r') as c:
    params = json.load(c)["params"]
    #params = json.load(c)["params"]



db = SQLAlchemy()

app= Flask(__name__)
app.secret_key='super-secret-key'
app.config["UPLOAD_FOLDER"]= params['upload_location']

with open('mdl.pkl', 'rb') as model_file:
    model = pickle.load(model_file)

with open('vectorizer.pkl', 'rb') as vectorizer_file:
    vectorizer = pickle.load(vectorizer_file)


if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']

db.init_app(app)



class signup(db.Model):
    Sno = db.Column(db.Integer, primary_key=True)
    Time_Stamp = db.Column(db.String, nullable=True)
    organization = db.Column(db.String, unique=False, nullable=False)
    designation = db.Column(db.String, unique=False, nullable=False)
    name = db.Column(db.String, unique=False, nullable=False)
    email = db.Column(db.String, nullable=False)
    mob = db.Column(db.String(13), nullable=False)
    password = db.Column(db.String, nullable=False)


class visible(db.Model):
    filename = db.Column(db.String, unique=False, nullable=False)
    email = db.Column(db.String, primary_key=True)



@app.route('/')
def home():
    return render_template('title.html', params=params)

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect('/login')

@app.route('/login', methods = ['GET' , 'POST'])
def login():
    if 'user' in session:
        return render_template('dashboard.html', params=params)
    else:
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('pswd')

            # Query the database to check the email and password
            user = signup.query.filter_by(email=email, password=password).first()

            if user:
                session['user'] = email
                return render_template('dashboard.html', params=params, email=email)
            else:
                return render_template('login.html', params=params, error="Invalid email or password")
        else:
            return render_template('login.html', params=params)

    # return render_template('login.html', params=params)

@app.route('/signup', methods = ['GET' , 'POST'])
def handle_signup():
    if (request.method == 'POST'):
        '''Add entry to the database'''
        org = request.form.get('org')
        dsg = request.form.get('dsg')
        pswd = request.form.get('pswd')
        name = request.form.get('name')
        email = request.form.get('email')
        mob = request.form.get('phone')


        entry = signup(name=name, email=email, mob=mob, designation=dsg,organization = org,password = pswd, Time_Stamp=datetime.now())
        db.session.add(entry)
        db.session.commit()
        return render_template('login.html', params=params)
    return render_template('signup.html', params=params)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', params=params)


# @app.route('/upload_categories', methods=['GET', 'POST'])
# def uploader():
#     if 'user' in session:
#         email = session['user']  # Retrieve email from session
#         if request.method == "POST":
#             f = request.files['categories']
#             f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename)))
#             return "Uploaded successfully"
#         else:
#             return render_template('dashboard.html', params=params)
#     else:
#         return render_template('login.html', params=params)

@app.route('/upload_categories', methods=['GET', 'POST'])
def uploader():
    if 'user' in session:
        email = session['user']
        if request.method == "POST":
            if 'categories' not in request.files:
                return "No file part"

            file = request.files['categories']

            if file.filename == '':
                return "No selected file"

            if file:
                try:
                    post = visible.query.filter_by(email=email).first()
                    db.session.delete(post)
                except:
                    pass
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                filename = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(file.filename))

                # filename = filename + str(filename)
                entry = visible(filename=filename, email=email)
                db.session.add(entry)
                db.session.commit()
                return render_template('dashboard.html', params=params)
        else:
            return render_template('dashboard.html', params=params)
    else:
        return render_template('login.html', params=params)





@app.route('/predict_categories', methods=['GET', 'POST'])
def predict_categories():
    if 'user' in session:
        email = session['user']  # Retrieve the user's email from the session
        if request.method == "POST":
            if 'Predictor' not in request.files:
                return "No file part"

            file = request.files['Predictor']

            if file.filename == '':
                return "No selected file"

            if file:
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                # Read the uploaded file into a DataFrame
                try:
                    uploaded_df = pd.read_excel(file_path)
                except Exception as e:
                    return f"Error reading the uploaded file: {str(e)}", 400

                # Check if 'title' column exists
                if 'title' not in uploaded_df.columns:
                    return "The file does not contain a 'title' column", 400

                # Vectorize the titles in the uploaded file
                try:
                    X_upload = vectorizer.transform(uploaded_df['title'])
                except Exception as e:
                    return f"Error transforming the titles: {str(e)}", 400

                # Make predictions
                try:
                    predictions = model.predict(X_upload)
                    uploaded_df['predicted_category'] = predictions
                except Exception as e:
                    return f"Error making predictions: {str(e)}", 400

                # Retrieve the path to the mapping file from the database
                try:
                    post = visible.query.filter_by(email=email).first()
                    mapping_file_path = post.filename  # Assuming filename column stores the mapping file path
                    # print(mapping_file_path)
                except Exception as e:
                    return f"Error retrieving the mapping file path from the database: {str(e)}", 400

                # Load the mapping file
                try:
                    mapping_df = pd.read_excel(mapping_file_path)
                    mapping_dict = dict(zip(mapping_df['Categories_that_we_have'], mapping_df['Categories_that_you_want']))
                except Exception as e:
                    return f"Error reading the mapping file: {str(e)}", 400

                # Debugging: Print the mapping dictionary and predictions
                # print("Mapping Dictionary:", mapping_dict)
                # print("Predicted Categories:", uploaded_df['predicted_category'].unique())

                # Map predictions to 'Categories_that_you_want'
                try:
                    # Remove leading and trailing spaces from predicted categories
                    uploaded_df['predicted_category'] = uploaded_df['predicted_category'].str.strip()

                    # Also ensure the mapping_dict keys are stripped of spaces
                    stripped_mapping_dict = {k.strip(): v for k, v in mapping_dict.items()}

                    # Map the categories
                    uploaded_df['mapped_category'] = uploaded_df['predicted_category'].map(stripped_mapping_dict)
                    # print("Mapped Categories:", uploaded_df['mapped_category'].unique())  # Debugging: Check mapped values
                except Exception as e:
                    return f"Error mapping the categories: {str(e)}", 400

                # Save the results to a new Excel file
                result_filename = 'predicted_categories.xlsx'
                result_filepath = os.path.join(app.config['UPLOAD_FOLDER'], result_filename)
                uploaded_df.to_excel(result_filepath, index=False)

                # Return the results file
                # return f"Predictions saved to {result_filename}. <a href='/download/{result_filename}'>Download</a>"
                prediction_message = f"Predictions saved to {result_filename}. <a href='/download/{result_filename}'>Download</a>"
                return render_template('dashboard.html', params=params, prediction_message=prediction_message)

            else:
                return render_template('dashboard.html', params=params)
        else:
            return render_template('dashboard.html', params=params)
    else:
        return render_template('login.html', params=params)





@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# @app.route('/hello/<name>')
# def hello(name):
#     return f"Hello, {escape(name)}!"

#app.run(debug=True)
# Other code in your main.py

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
