import streamlit as st
import requests
import pandas as pd
import re
import os

# Configuration
API_BASE_URL = "http://localhost:8000/api"
STORAGE_PATH = "storage"

st.set_page_config(page_title="Smart Data Q&A", layout="wide")

# --- Helper Functions ---
def get_all_jobs():
    try:
        response = requests.get(f"{API_BASE_URL}/jobs")
        response.raise_for_status()
        return response.json().get('jobs', [])
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting jobs: {e}")
        return []

def get_job_details(job_id):
    try:
        response = requests.get(f"{API_BASE_URL}/job/{job_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting job details: {e}")
        return None

def ingest_file(kb_name, uploaded_file):
    if uploaded_file is not None:
        files = {'file': (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
        params = {'kb_name': kb_name}
        try:
            response = requests.post(f"{API_BASE_URL}/ingest", params=params, files=files)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error during ingestion: {e}")
            return None
    return None

def get_ingestion_status(job_id):
    try:
        response = requests.get(f"{API_BASE_URL}/ingest/status/{job_id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error getting status: {e}")
        return None

def retrieve_answer(query, collection_name):
    try:
        payload = {"query": query, "collection_name": collection_name}
        response = requests.post(f"{API_BASE_URL}/retrieve", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error during retrieval: {e}")
        return None

# --- Sidebar for Ingestion and Status ---
st.sidebar.title("Knowledge Base Management")

st.sidebar.header("1. Create Knowledge Base")
kb_name_input = st.sidebar.text_input("Enter a name for the new Knowledge Base", key="kb_name_input")
uploaded_file = st.sidebar.file_uploader("Upload a PDF document", type=["pdf"])

if st.sidebar.button("Create KB", key="create_kb_button"):
    if kb_name_input and uploaded_file:
        with st.spinner("Processing document... This may take a moment."):
            ingest_result = ingest_file(kb_name_input, uploaded_file)
            if ingest_result:
                st.session_state.job_id = ingest_result.get('job_id')
                st.session_state.kb_name = kb_name_input
                st.sidebar.success(f"Ingestion started for KB '{st.session_state.kb_name}'.")
                st.sidebar.info(f"Job ID: {st.session_state.job_id}")
                st.sidebar.info("You can now check the status below or see the list of all KBs.")
    else:
        st.sidebar.warning("Please provide a name and upload a PDF file.")

st.sidebar.markdown("---")
st.sidebar.header("2. Existing Knowledge Bases")
if st.sidebar.button("Refresh List", key="refresh_jobs"):
    st.cache_data.clear()

# Fetch and display jobs
jobs_list = get_all_jobs()
if jobs_list:
    df = pd.DataFrame(jobs_list)
    df = df[['kb_name', 'job_id', 'status', 'timestamp']]
    df['timestamp'] = pd.to_datetime(df['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S')
    st.sidebar.dataframe(df, hide_index=True)
else:
    st.sidebar.info("No knowledge bases found.")

st.sidebar.markdown("---")
st.sidebar.header("3. Check Ingestion Status")
job_id_input = st.sidebar.text_input("Enter Job ID to check status", key="job_id_input")

if st.sidebar.button("Check Status", key="check_status_button"):
    if job_id_input:
        with st.spinner("Checking status..."):
            status_result = get_ingestion_status(job_id_input)
            if status_result:
                st.sidebar.metric(label=f"Status for {job_id_input}", value=status_result.get('status', 'Unknown').capitalize())
    else:
        st.sidebar.warning("Please enter a Job ID.")


# --- Main Content for Q&A ---
st.title("🧠 Smart Data Q&A")
st.markdown("Ask questions to your knowledge base.")

# Use session state to pre-fill the collection name if a KB was just created
if 'job_id' in st.session_state:
    st.info(f"Now querying knowledge base: **{st.session_state.job_id}** (from job '{st.session_state.kb_name}')")
    collection_name = st.text_input("Knowledge Base Name (Job ID)", value=st.session_state.job_id)
else:
    collection_name = st.text_input("Knowledge Base Name (Job ID)")

query = st.text_area("Enter your question here", height=150)

if st.button("Get Answer", key="get_answer_button"):
    if collection_name and query:
        with st.spinner("Searching for answers..."):
            retrieval_result = retrieve_answer(query, collection_name)
            if retrieval_result and 'response' in retrieval_result:
                st.success("Answer Found!")
                response_text = retrieval_result['response']
                
                with st.expander("Show Raw LLM Response"):
                    st.code(response_text)
                
                # Look for both [Fig: ...] and [figure: ...] patterns
                figure_matches = list(re.finditer(r'\[Fig: (.*?)\]', response_text, re.IGNORECASE))
                figure_matches.extend(re.finditer(r'\[figure: (.*?)\]', response_text, re.IGNORECASE))
                
                if figure_matches:
                    job_details = get_job_details(collection_name)
                    if job_details:
                        kb_name = job_details.get('kb_name')
                        displayed_figures = set() # Keep track of displayed figures
                        for match in figure_matches:
                            unique_id = match.group(1)
                            if unique_id not in displayed_figures:
                                image_path = os.path.join(STORAGE_PATH, kb_name, "processed", "images", f"{unique_id}.png")
                                if os.path.exists(image_path):
                                    st.image(image_path, caption=f"Figure: {unique_id}")
                                else:
                                    st.warning(f"Could not find image: {image_path}")
                                displayed_figures.add(unique_id)

                        # Clean the response text - remove both formats
                        response_text = re.sub(r'\[Fig: (.*?)\]', "", response_text, flags=re.IGNORECASE)
                        response_text = re.sub(r'\[figure: (.*?)\]', "", response_text, flags=re.IGNORECASE).strip()

                st.markdown(response_text)

            else:
                st.error("Could not retrieve an answer.")
    else:
        st.warning("Please provide the Knowledge Base Name and a question.")