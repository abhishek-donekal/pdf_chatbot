import streamlit as st
import pymongo
import openai
import PyPDF2
from io import BytesIO

# Streamlit UI
st.title("PDF Text Extractor and Search with MongoDB")

# User input for OpenAI API Key
openai_api_key = st.text_input("Enter OpenAI API Key:", type="password")

# User input for MongoDB URI
mongo_uri = st.text_input("Enter MongoDB URI:", type="password")

# Upload PDF
uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])

def extract_text_from_pdf(file_bytes):
    """Extracts text from a PDF file."""
    reader = PyPDF2.PdfReader(BytesIO(file_bytes))
    text = "".join([page.extract_text() for page in reader.pages if page.extract_text()])
    return text

if openai_api_key and mongo_uri and uploaded_file:
    openai.api_key = openai_api_key
    client = pymongo.MongoClient(mongo_uri)
    db = client["pdfDB"]
    collection = db["documents"]
    
    # Extract text
    pdf_text = extract_text_from_pdf(uploaded_file.read())
    st.success("✅ Extracted text from PDF")
    st.text_area("Extracted Text (first 500 characters):", pdf_text[:500], height=150)
    
    # Generate embedding
    def get_embedding(text, model="text-embedding-ada-002"):
        response = openai.embeddings.create(
            input=text,
            model=model
        )
        return response.data[0].embedding
    
    embedding_vector = get_embedding(pdf_text)
    document = {"filename": uploaded_file.name, "text": pdf_text, "embedding": embedding_vector}
    result = collection.insert_one(document)
    st.success(f"Document inserted with ID: {result.inserted_id}")
    
    # MongoDB vector search
    results = collection.aggregate([
        {"$vectorSearch": {
            "index": "default",
            "path": "embedding",
            "queryVector": embedding_vector,
            "numCandidates": 10,
            "limit": 1
        }}
    ])
    
    # Display top matching document
    top_doc = next(results, None)
    if top_doc:
        st.subheader("Top Matching Document:")
        st.text_area("Matching Text (first 1000 characters):", top_doc["text"][:1000], height=200)
    else:
        st.warning("No matching document found.")
