import logging
from openai import OpenAI
from qdrant_client import QdrantClient
from app.config import settings

logger = logging.getLogger(__name__)

class RetrievalService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)

    def retrieve(self, query: str, collection_name: str) -> str:
        try:
            # 1. Embed the query
            query_embedding = self.openai_client.embeddings.create(
                input=query,
                model="text-embedding-3-large"
            ).data[0].embedding

            # 2. Perform similarity search in Qdrant
            search_results = self.qdrant_client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=5  # Return top 5 results
            )

            # 3. Format the context
            context = "\n---\n".join([
                hit.payload['content'] for hit in search_results
            ])

            # 4. Prepare the prompt for the LLM
            prompt = f"""
            You are a knowledgeable and helpful AI assistant. 
            Use the provided context to answer the user’s query as accurately and concisely as possible. 

            Instructions:
            1. Only use information from the given context. If the answer is not present, explicitly say: "I don't know based on the provided context."
            2. If the user requests to display an image and the context contains that image, return the corresponding figure ID in the format: [figure: figure_id].
            3. If the user requests to show a table and the context contains that table, render it in **Markdown table format**.
            4. Do not fabricate information or make assumptions beyond the given context.
            5. Keep your response clear, structured, and user-friendly.

            Context:
            {context}

            User Query:
            {query}

            Answer:
            """


            # 5. Send context and query to LLM
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error during retrieval from collection {collection_name}: {e}", exc_info=True)
            # Check if the collection exists and provide a specific error message
            try:
                self.qdrant_client.get_collection(collection_name=collection_name)
            except Exception:
                return f"Error: Collection '{collection_name}' not found."
            return "An error occurred during retrieval."

