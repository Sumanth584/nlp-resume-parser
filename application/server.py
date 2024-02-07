import logging
import os
import secrets
from flask import Flask, flash, request, redirect, send_file, session, url_for, render_template, jsonify
import redis
from werkzeug.utils import secure_filename
from env_parser import parse_env_file
from parser_1 import ResumeParser
import argparse
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
nltk.download('punkt')
nltk.download('stopwords')
from ranker import ResumeRanker
from flask_session import Session 
import json 
import redis
UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = {'pdf'}
from uuid import uuid4
app = Flask(__name__)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_USE_SIGNER'] = True
app.config['SESSION_REDIS'] = redis.Redis(host='localhost', port=6379, db=0)

# Initialize the session
Session(app)

redis_conn = redis.Redis(host='localhost', port=6379, db=0)
# Create an instance of ResumeRanker
ranker = ResumeRanker()


# Usage of extract_criteria_from_job_description
job_description = "Some job description text"
job_criteria = ranker.extract_criteria_from_job_description(job_description)
env_variables = parse_env_file()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000
app.add_url_rule("/resume/<name>", endpoint="resume", build_only=True)
app.secret_key = secrets.token_urlsafe(32)

parser = ResumeParser(os.getenv('OPENAI_API_KEY', env_variables.get('OPENAI_API_KEY')))


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Adjustments are made based on the assumptions about the structure of your resume data
# and the provided code snippets.



@app.route("/", methods=['GET', 'POST'])
def upload_resume():
    if request.method == 'POST':
        uploaded_files = request.files.getlist('files[]')
        if not uploaded_files:
            flash('No files selected')
            return redirect(request.url)

        resume_data_ids = []
        for file in uploaded_files:
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                # Assume parser.query_resume returns a dict with resume data
                resume_data = parser.query_resume(file_path)
                resume_data_id = str(uuid4())
                redis_conn.set(resume_data_id, json.dumps(resume_data))  # Use redis_conn here
                resume_data_ids.append(resume_data_id)

        if resume_data_ids:
            session['resume_data_ids'] = resume_data_ids
            return redirect(url_for('display_resumes', names=','.join(resume_data_ids)))
        else:
            flash('Error processing files or no allowed files were uploaded')
            return redirect(request.url)
    return render_template('index.html')

@app.route('/resumes/<names>')
def display_resumes(names):
    resume_ids = names.split(',')
    resume_details = []

    for resume_id in resume_ids:
        # Fetch and decode the resume data from Redis using the direct connection
        resume_data_str = redis_conn.get(resume_id)
        if resume_data_str:
            resume_data = json.loads(resume_data_str.decode('utf-8'))  # Ensure decoding from bytes to str
            basic_info = resume_data.get("basic_info", {})
            skills_data = resume_data.get("skills", [])
            work_experience = resume_data.get("work_experience", [])

            # Call the format_skills function with skills_data
            formatted_skills = format_skills(skills_data)

            resume_details.append({
                "name": basic_info.get("name", "N/A"),
                "graduation_year": basic_info.get("graduation_year", "N/A"),
                "education_level": basic_info.get("education_level", "N/A"),
                "skills": formatted_skills,
                "work_experience": work_experience
            })

    return render_template('resume_display.html', resumes=resume_details)


def format_skills(skills_data):
    """Utility function to format skills data based on its structure."""
    formatted_skills = []
    if isinstance(skills_data, dict):
        for category, skill_list in skills_data.items():
            if isinstance(skill_list, list):
                formatted_skills.extend([f"{skill} ({category})" for skill in skill_list])
            else:
                print(f"Expected list in skills_data dictionary, got {type(skill_list)} instead.")
    elif isinstance(skills_data, list):
        formatted_skills = skills_data
    else:
        print(f"Unexpected data type for skills_data: {type(skills_data)}")
    return formatted_skills



@app.route('/upload_job_description', methods=['GET', 'POST'])
def upload_job_description():
    if request.method == 'POST':
        file = request.files['job_description']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Extract job criteria from the job description and store in session
            job_criteria = ranker.extract_criteria_from_job_description(file_path)
            session['job_criteria'] = job_criteria

            # Redirect to ranking page or handle next steps
            return redirect(url_for('rank_resumes_page'))
        else:
            flash('Invalid file type')
            return redirect(request.url)
    return render_template('upload_job_description.html')

@app.route('/rank_resumes')
def rank_resumes_page():
    # Ensure there is job criteria available; otherwise, redirect or show an error
    job_criteria = session.get('job_criteria')


    # Ensure there are resume identifiers available; otherwise, redirect or show an error
    resume_data_ids = session.get('resume_data_ids', [])  # Fetch resume data IDs from session

    if not resume_data_ids:
        flash("No resumes to rank.")
        return redirect(url_for('upload_resume'))  # Adjust as per your actual route

    # Create instances of ResumeRanker and ResumeParser
    ranker = ResumeRanker()
    api_key = os.getenv('OPENAI_API_KEY', env_variables.get('OPENAI_API_KEY'))
    parser = ResumeParser(api_key)

    resumes_data = []
    # Iterate over resume_data_ids safely
    for resume_id in resume_data_ids:
        resume_data_str = redis_conn.get(resume_id)  # Use the Redis connection to fetch data
        if resume_data_str:
            resume_data = json.loads(resume_data_str.decode('utf-8'))
            resumes_data.append(resume_data)
    
    # Rank the resumes based on job criteria
    scored_resumes = ranker.rank_resumes(resumes_data, job_criteria)
    
    # Prepare the ranked resumes data for the template
    ranked_resumes = []
    for resume_data, score, explanation in scored_resumes:
        ranked_resume = {
            'score': score,
            'explanation': explanation,
            'details': resume_data
        }
        ranked_resumes.append(ranked_resume)

    return render_template('ranked_resumes.html', ranked_resumes=ranked_resumes)



@app.route('/chatbot', methods=['POST'])
def chatbot():
    # Attempt to get resume data IDs from the session
    resume_data_ids = session.get('resume_data_ids')
    if not resume_data_ids:
        return jsonify({'error': 'No resume data available'}), 400

    # Fetch resume data from Redis
    all_resume_data = []
    for resume_id in resume_data_ids:
        resume_data_str = redis_conn.get(resume_id)
        if resume_data_str:
            resume_data = json.loads(resume_data_str.decode('utf-8'))
            all_resume_data.append(resume_data)

    # Try to parse the incoming JSON data
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            logging.error("Missing or invalid data: " + str(data))
            return jsonify({'error': 'Missing or invalid data'}), 400
    except Exception as e:
        logging.error("JSON parsing error: " + str(e))
        return jsonify({'error': 'JSON parsing error'}), 400

    # Extract the query from the data
    query = data['query']
    logging.info(f"Received chatbot query: {query}")

    # Call your chatbot query function with the extracted query and resume data
    try:
        answer = ranker.chatbot_query(query, all_resume_data)
        return jsonify({'answer': answer})
    except Exception as e:
        logging.error("Error in chatbot query processing: " + str(e))
        return jsonify({'error': 'Error processing chatbot query'}), 500



if __name__ == "__main__":
    host = os.getenv("RESUME_PARSER_HOST", '127.0.0.1')
    port = os.getenv("RESUME_PARSER_PORT", '5001')
    assert port.isnumeric(), 'port must be an integer'
    port = int(port)
    app.run(host=host, port=port, debug=True)

