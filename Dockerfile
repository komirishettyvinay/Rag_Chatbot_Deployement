FROM python:3.11-slim

WORKDIR /app

#Install dependencies
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files
COPY streamlit_app.py .
#COPY streamlit_app_tfidf.py .
#COPY main.py .

#Copy the company documents the RAG system searches through
COPY Data/ ./data/

# TF-IDF version - no model download. starts in under 2 seconds
# Switch back to streamlit_app.py to use the ChromaDB version locally
#CMD ["streamlit", "run", "streamlit_app_tfidf.py", "--server.port=10000", "--server.address=0.0.0.0"]
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=10000", "--server.address=0.0.0.0"]