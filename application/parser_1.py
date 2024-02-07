import pdftotext
import openai


# Set your OpenAI API key
OPENAI_API_KEY = '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'
import re
import logging
import json
from tokenizer import num_tokens_from_string
import pandas as pd
import os
class ResumeParser():
    def __init__(self, OPENAI_API_KEY):
        # set GPT-3 API key from the environment vairable
        openai.api_key = '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'
        self.prompt_questions = \
"Process the provided resume text and structure it into JSON format. Focus on extracting and clearly delineating the following sections: 'basic_info' (including name, email, phone number, university, graduation year, degree), 'work_experience' (specifying job title, company, location, duration, and a brief summary), 'project_experience' (detailing project name and a short description), and 'skills' (listing all skills). Ensure each section is comprehensively covered and distinctly separated."
       # set up this parser's logger
        logging.basicConfig(filename='logs/parser.log', level=logging.DEBUG)
        self.logger = logging.getLogger()

    def pdf2string(self: object, pdf_path: str) -> str:
        """
        Extract the content of a pdf file to string.
        :param pdf_path: Path to the PDF file.
        :return: PDF content string.
        """
        with open(pdf_path, "rb") as f:
            pdf = pdftotext.PDF(f)
        pdf_str = "\n\n".join(pdf)
        pdf_str = re.sub('\s[,.]', ',', pdf_str)
        pdf_str = re.sub('[\n]+', '\n', pdf_str)
        pdf_str = re.sub('[\s]+', ' ', pdf_str)
        pdf_str = re.sub('http[s]?(://)?', '', pdf_str)
        return pdf_str
    
    def query_completion(self, prompt: str, model: str = 'ft:gpt-3.5-turbo-1106:personal::8kdMygLg', max_tokens: int = 3400):
        self.logger.info(f'query_completion: using {model}')

        messages = [{"role": "user", "content": prompt}]  # Create a message object

        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens
            )
            response_text = response.choices[0].message['content'].strip()  # Adjusted to extract message content
            self.logger.debug(f"API Response Text: {response_text}")  # Log raw response text
            return response_text
        except Exception as e:
            self.logger.error(f"Error in query_completion: {e}")
            if hasattr(e, 'response'):
                if e.response:
                    self.logger.error(f"API Response: {e.response.content}")
            return None


    def query_resume(self, pdf_path: str) -> dict:
        pdf_str = self.pdf2string(pdf_path)
        prompt = self.prompt_questions + '\n' + pdf_str

        response_content = self.query_completion(prompt, model='ft:gpt-3.5-turbo-1106:personal::8kdMygLg', max_tokens=3400)
        
        if response_content:
            try:
                resume = json.loads(response_content)
                self.logger.info(f"Successful response: {resume}")
                return resume
            except json.JSONDecodeError as e:
                self.logger.error(f"Invalid JSON response: {e}")
                self.logger.error(f"Response Content: {response_content}")  # Log the problematic content
                return {}
        else:
            self.logger.error("Invalid or no response returned from query_completion.")
            return {}

    
    def format_resume_for_chatbot(self, resume_data):
        """
        Format the resume data into a text format suitable for GPT prompt.
        :param resume_data: Dictionary containing resume data
        :return: Formatted string
        """
        formatted_data = ""
        for section, contents in resume_data.items():
            formatted_data += f"{section.title()}:\n"
            if isinstance(contents, dict):
                for key, value in contents.items():
                    formatted_data += f"  {key.title()}: {value}\n"
            elif isinstance(contents, list):
                for item in contents:
                    formatted_data += f"  - {item}\n"
            else:
                formatted_data += f"  {contents}\n"
            formatted_data += "\n"
        return formatted_data
    
   