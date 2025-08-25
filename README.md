# Smart-RAG

This project is a retrieval-augmented generation (RAG) application that allows you to ask questions about your documents. It uses a FastAPI backend for data ingestion and retrieval, and a Streamlit frontend for a user-friendly interface.

## Features

-   **PDF Ingestion**: Upload PDF documents to create a knowledge base.
-   **Figure Extraction**: Automatically extracts figures from documents, gets AI-generated descriptions, and saves them.
-   **Q&A Interface**: Ask questions to your knowledge bases and get answers from an LLM.
-   **Image Display**: Displays figures referenced in the LLM's response.

## Prerequisites

-   Python 3.8+
-   **uv**: A fast Python package installer. You can install it from [here](https://github.com/astral-sh/uv).

## Setup

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone https://github.com/Sirorororo/Smart-RAG.git
    cd Smart-RAG
    ```

2.  **Create and activate a virtual environment using `uv`:**
    ```bash
    # This command creates a .venv directory and activates it.
    uv venv
    ```

3.  **Install the dependencies using `uv`:**
    ```bash
    uv pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**
    -   Create a file named `.env` in the root of the project directory.
    -   Check env.example for the required parameters

5. **Set up qdrant if required**
    ```bash
    docker run -p 6333:6333 qdrant/qdrant
    ```

    Refer https://github.com/qdrant/qdrant for other installation methods.
    

## Running the Application

You need to run two processes in separate terminals: the FastAPI backend and the Streamlit frontend.

**1. Run the FastAPI Backend:**

In your first terminal, run the following command:
```bash
uvicorn app.main:app --reload
```
This will start the FastAPI server at `http://localhost:8000`.

**2. Run the Streamlit Frontend:**

In a second terminal, run the following command:
```bash
streamlit run streamlit_app.py
```
This will open the Streamlit application in your web browser, usually at `http://localhost:8501`.

## How to Use the Application

1.  **Create a Knowledge Base:**
    -   Open the Streamlit application in your browser.
    -   In the sidebar, enter a name for your knowledge base.
    -   Upload a PDF file.
    -   Click the "Create KB" button.
    -   You will see a `job_id` for the ingestion process. You can use this to track the status.

2.  **Ask Questions:**
    -   Once a knowledge base has been created, the "Knowledge Base Name (Job ID)" field will be pre-filled with the `job_id`.
    -   You can also see a list of existing knowledge bases in the sidebar and copy the `job_id` from there.
    -   Enter your question in the text area and click "Get Answer".
    -   The application will display the answer from the LLM. If the answer references any figures, they will be displayed below the text.