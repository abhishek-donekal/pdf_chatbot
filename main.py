import streamlit as st
import pymongo
import openai
import PyPDF2
from io import BytesIO

# Streamlit Page Config
st.set_page_config(page_title="PDF Chatbot", page_icon="📄", layout="wide")

# UI Header
st.markdown("<h1 style='text-align: center;'>📄 PDF-Based Chatbot with OpenAI & MongoDB 🤖</h1>", unsafe_allow_html=True)

# User input for OpenAI API Key & MongoDB URI
with st.sidebar:
    openai_api_key = st.text_input("🔑 OpenAI API Key", type="password")
    mongo_uri = st.text_input("🗄️ MongoDB URI", type="password")
    uploaded_file = st.file_uploader("📂 Upload a PDF", type=["pdf"])

# Function to Extract Text from PDF
def extract_text_from_pdf(file_bytes):
    try:
        reader = PyPDF2.PdfReader(BytesIO(file_bytes))
        text = "\n".join([page.extract_text() or "" for page in reader.pages])
        return text.strip() if text else "No text extracted."
    except Exception as e:
        return f"Error extracting text: {e}"

# Chat History Initialization
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if openai_api_key and mongo_uri and uploaded_file:
    # OpenAI Client (Latest API)
    client = openai.OpenAI(api_key=openai_api_key)

    # MongoDB Connection
    mongo_client = pymongo.MongoClient(mongo_uri)
    db = mongo_client["pdfDB"]
    collection = db["documents"]

    with st.spinner("🔍 Extracting text from PDF..."):
        pdf_text = extract_text_from_pdf(uploaded_file.read())

    if not pdf_text or pdf_text.startswith("Error"):
        st.error(f"⚠️ {pdf_text}")
    else:
        st.success("✅ Successfully Extracted Text!")
        st.text_area("📜 Extracted Text (Preview)", pdf_text[:500], height=150)

        # Store in MongoDB
        document = {"filename": uploaded_file.name, "text": pdf_text}
        collection.insert_one(document)
        st.success("✅ Document stored in MongoDB!")

        # Chat UI
        st.subheader("💬 Chat with the Document")
        
        # Display Chat History
        for chat in st.session_state.chat_history:
            role = "👤" if chat["role"] == "user" else "🤖"
            st.markdown(f"**{role} {chat['role'].capitalize()}**: {chat['content']}", unsafe_allow_html=True)

        # User Input for Query
        user_query = st.chat_input("Type your question here...")

        if user_query:
            if user_query.lower() == "stop":
                st.warning("🛑 Chatbot session ended. Upload another document or restart.")
                st.session_state.chat_history = []  # Clear history
            else:
                # Store User Query
                st.session_state.chat_history.append({"role": "user", "content": user_query})

                # System Prompt for AI
                system_prompt = f"You are an AI assistant answering questions based on this document:\n{pdf_text[:3000]}..."  

                # AI Response
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[{"role": "system", "content": system_prompt}] + st.session_state.chat_history
                )

                bot_reply = response.choices[0].message.content
                st.session_state.chat_history.append({"role": "assistant", "content": bot_reply})

                # Display AI Response
                st.markdown(f"**🤖 Assistant**: {bot_reply}", unsafe_allow_html=True)
