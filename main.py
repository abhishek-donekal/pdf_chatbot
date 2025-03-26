import streamlit as st
import pymongo
import openai
import PyPDF2
from io import BytesIO

# Streamlit UI
st.title("📄 PDF-Based Chatbot with OpenAI & MongoDB")

# User input for OpenAI API Key
openai_api_key = st.text_input("🔑 Enter OpenAI API Key:", type="password")

# User input for MongoDB URI
mongo_uri = st.text_input("🗄️ Enter MongoDB URI:", type="password")

# Upload PDF
uploaded_file = st.file_uploader("📂 Upload a PDF file", type=["pdf"])

def extract_text_from_pdf(file_bytes):
    """Extracts text from a PDF file."""
    try:
        reader = PyPDF2.PdfReader(BytesIO(file_bytes))
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        return text.strip() if text else "No text extracted."
    except Exception as e:
        return f"Error extracting text: {e}"

if openai_api_key and mongo_uri and uploaded_file:
    # Initialize OpenAI Client (Latest API)
    client = openai.OpenAI(api_key=openai_api_key)

    # Connect to MongoDB
    mongo_client = pymongo.MongoClient(mongo_uri)
    db = mongo_client["pdfDB"]
    collection = db["documents"]

    with st.spinner("🔍 Extracting text from PDF..."):
        pdf_text = extract_text_from_pdf(uploaded_file.read())

    if not pdf_text or pdf_text.startswith("Error"):
        st.error(f"⚠️ {pdf_text}")
    else:
        st.success("✅ Successfully extracted text!")
        st.text_area("📜 Extracted Text (First 500 characters):", pdf_text[:500], height=150)

        # Store document in MongoDB
        document = {"filename": uploaded_file.name, "text": pdf_text}
        collection.insert_one(document)
        st.success("✅ Document stored in MongoDB!")

        # Chatbot interface
        st.subheader("🤖 Ask Questions About the Document")

        # Store chat history
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        user_query = st.text_input("💬 You: ")

        if user_query.lower() == "stop":
            st.write("🛑 Chatbot session ended. Upload another document or restart.")
            st.session_state.chat_history = []  # Clear chat history
        elif user_query:
            st.session_state.chat_history.append({"role": "user", "content": user_query})

            # OpenAI Chat Completion
            system_prompt = f"You are an AI assistant answering questions based on this document:\n{pdf_text[:3000]}..."  # Truncate for length

            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    *st.session_state.chat_history
                ]
            )

            bot_reply = response.choices[0].message.content
            st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})

            st.text_area("🤖 Chatbot:", bot_reply, height=200)
