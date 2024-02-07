
import pdftotext
import openai

from parser_1 import ResumeParser

# Set your OpenAI API key
OPENAI_API_KEY = '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'
#client = OpenAI(api_key=OPENAI_API_KEY)
import re
import logging
import json
from tokenizer import num_tokens_from_string
import pandas as pd
import spacy
import os
from flask import Flask, flash, request, redirect, session, url_for, render_template
chat = ResumeParser(OPENAI_API_KEY)
app = Flask(__name__)
class ResumeRanker:
 
    
  def __init__(self):
        # Load spaCy model
        self.nlp = spacy.load("en_core_web_sm")
    
  def extract_criteria_from_job_description(self, job_description):
        # Process the job description text with spaCy
        doc = self.nlp(job_description)

        # Extract entities identified as 'SKILL' or 'ORG' (organization)
        skills = set()
        for ent in doc.ents:
            if ent.label_ == "SKILL" or ent.label_ == "ORG":
                skills.add(ent.text)

        return list(skills)
  
  
  def query_gpt_for_evaluation(self, resume, job_criteria):
    prompt = (
        f"Given the job criteria: {job_criteria}\n"
        f"And the resume details: {json.dumps(resume, indent=2)}\n"
        f"Please provide a rating and detailed analysis as follows:\n"
        f"'Score: [Rating out of 10]'\n"
        f"'Explanation: [Extremely Detailed analysis]'."
    )

    messages = [{"role": "user", "content": prompt}]

    try:
        response = openai.ChatCompletion.create(
            model="ft:gpt-3.5-turbo-1106:personal::8kdMygLg",
            messages=messages,
            max_tokens=2400
        )

        response_text = response.choices[0].message['content'].strip()
        logging.info("Response Text: " + response_text)

        score_match = re.search(r'Score:\s*(\d+)', response_text)
        explanation_match = re.search(r'Explanation:\s*(.+)', response_text, re.DOTALL)

        score = int(score_match.group(1)) if score_match else None
        explanation = explanation_match.group(1).strip() if explanation_match else "Explanation not found"

        return score, explanation

    except Exception as e:
        logging.error(f"Error in query_gpt_for_evaluation: {e}")
        return None, "Error in processing"




  def rank_resumes(self, resumes, job_criteria):
        scored_resumes = []

        for resume in resumes:
            score, explanation = self.query_gpt_for_evaluation(resume, job_criteria)
            if score is not None:
                scored_resumes.append((resume, score, explanation))
            else:
                # Handle case where no score is returned
                scored_resumes.append((resume, None, explanation))

        # Sort resumes based on score, highest first, handle None scores
        scored_resumes.sort(key=lambda x: (x[1] is not None, x[1]), reverse=True)
        return scored_resumes

  def chatbot_query(self, user_query, all_resume_data):
        # Format each resume individually and combine into a single context
        combined_context = ""
        for resume_data in all_resume_data:
            formatted_resume = chat.format_resume_for_chatbot(resume_data)
            combined_context += formatted_resume + "\n\n"

        messages = [
            {"role": "system", "content": combined_context},
            {"role": "user", "content": user_query}
        ]

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=200,
                temperature=0.5
            )
            # Ensure response parsing matches the actual structure
            if response and 'choices' in response and len(response['choices']) > 0 and 'message' in response['choices'][0]:
                answer = response['choices'][0]['message']['content'].strip()
                logging.info(f"Query: {user_query}, Answer: {answer}")
                return answer
            else:
                logging.error("Missing 'message' or 'content' in response choice")
                return "Missing 'message' or 'content' in response choice."
        except Exception as e:
            logging.error(f"An error occurred in chatbot_query: {e}")
            return "I'm sorry, I couldn't process that query."