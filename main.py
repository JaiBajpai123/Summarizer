from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from transformers import pipeline
from fpdf import FPDF
import re
import textwrap
from PyPDF2 import PdfReader

app = FastAPI()

def prep_b4_save(text):
    replacements = {'Gods': "God's", 'yours': "your's", 'dont': "don't", 'doesnt': "doesn't",
                    'isnt': "isn't", 'havent': "haven't", 'hasnt': "hasn't", 'wouldnt': "wouldn't",
                    'theyre': "they're", 'youve': "you've", 'arent': "aren't", 'youre': "you're",
                    'cant': "can't", 'whore': "who're", 'whos': "who's", 'whatre': "what're",
                    'whats': "what's", 'hadnt': "hadn't", 'didnt': "didn't", 'couldnt': "couldn't",
                    'theyll': "they'll", 'youd': "you'd"}

    for word, replacement in replacements.items():
        text = re.sub(fr'\b{word}\b', replacement, text)

    return text

def text_to_pdf(text, filename):
    # (your existing code for text_to_pdf function)

@app.post("/summarize")
async def summarize(pdf_file: UploadFile = File(...)):
    # Save the uploaded PDF file
    pdf_path = f"uploaded_files/{pdf_file.filename}"
    with open(pdf_path, "wb") as pdf:
        pdf.write(pdf_file.file.read())

    # Extract text from PDF using PyPDF2
    def extract_text(pdf_path):
        text = ""
        with open(pdf_path, "rb") as file:
            pdf_reader = PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                text += pdf_reader.pages[page_num].extract_text()
        return text

    raw_text = extract_text(pdf_path)
    chunks = text_chunking(raw_text)

    # Summarize text using the transformers pipeline
    summarizer = pipeline("summarization")
    all_summaries = summarizer(chunks, max_length=150, min_length=50, length_penalty=2.0)

    joined_summary = ' '.join([summ['summary_text'] for summ in all_summaries])
    txt_to_save = (joined_summary.encode('latin1', 'ignore')).decode("latin1")
    txt_to_save_prep = prep_b4_save(txt_to_save)

    # Save summarized text to a new PDF file
    summary_pdf_path = f"output_files/summary_{pdf_file.filename}.pdf"
    text_to_pdf(txt_to_save_prep, summary_pdf_path)

    return {
        "summary_text": txt_to_save_prep,
        "summary_pdf": FileResponse(summary_pdf_path, filename=f"summary_{pdf_file.filename}.pdf")
    }
