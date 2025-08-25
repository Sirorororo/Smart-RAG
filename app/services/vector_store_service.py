import logging
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import OpenAI
from qdrant_client import QdrantClient, models
from app.config import settings
import uuid
import pandas as pd

logger = logging.getLogger(__name__)

class VectorStoreService:
    def __init__(self, collection_name: str):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            length_function=len,
        )
        self.openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.qdrant_client = QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = collection_name
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        try:
            self.qdrant_client.get_collection(collection_name=self.collection_name)
            logger.info(f"Collection '{self.collection_name}' already exists.")
        except Exception:
            self.qdrant_client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=3072, distance=models.Distance.COSINE), # text-embedding-3-large has 3072 dimensions
            )
            logger.info(f"Collection '{self.collection_name}' created.")

    def embed_and_store(self, df: pd.DataFrame):
        full_text = ""
        page_offsets = []
        page_metadata = []

        for _, row in df.iterrows():
            page_offsets.append(len(full_text))
            full_text += row['contents_md'] + "\n\n" # Add page separator
            page_metadata.append({
                "document": row['document'],
                "page_hash": row['page_hash'],
                "page_num": row['extra.page_num'],
            })

        chunks = self.text_splitter.split_text(full_text)
        
        chunk_points = []
        for chunk in chunks:
            # Find the page number for the chunk
            chunk_start_offset = full_text.find(chunk)
            page_index = -1
            for i, offset in enumerate(page_offsets):
                if chunk_start_offset >= offset:
                    page_index = i
                else:
                    break
            
            if page_index != -1:
                metadata = page_metadata[page_index].copy()
                metadata['content'] = chunk

                embedding = self.openai_client.embeddings.create(
                    input=chunk,
                    model="text-embedding-3-large"
                ).data[0].embedding

                chunk_points.append(
                    models.PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding,
                        payload=metadata
                    )
                )
        
        if chunk_points:
            self.qdrant_client.upsert(
                collection_name=self.collection_name,
                points=chunk_points
            )
            
        logger.info(f"Successfully embedded and stored {len(chunk_points)} chunks in Qdrant.")
