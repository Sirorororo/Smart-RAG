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
                limit=10
            )

            # 3. Format the context
            context = "\n---\n".join([
                hit.payload['content'] for hit in search_results
            ])

            # print(context)
            # 4. Prepare the prompt for the LLM
            sys_prompt = f"""
            You are a helpful AI assistant. Your task is to answer the user's query based *STRICTLY AND EXCLUSIVELY* on the provided context below.

            **CRITICAL RULES - VIOLATION WILL RESULT IN INCORRECT OUTPUT:**

            1. **FIGURE REFERENCES - ZERO TOLERANCE FOR HALLUCINATION:**
            - You may ONLY reference figures using IDs that appear EXACTLY as `<!-- figure: pg_X_fig_Y -->` in the context
            - **MANDATORY:** Before outputting any figure reference, you MUST verify that the figure's description or content is relevant to your answer
            - **Input Format in Context:** `<!-- figure: pg_X_fig_Y -->`
            - **Output Format in Answer:** `[Fig: pg_X_fig_Y]`
            - **PROCESS:** 1) Find `<!-- figure: pg_X_fig_Y -->` tag → 2) Read the preceding description in encapsulated in ![...] → 3) Verify relevance → 4) Only then reference if appropriate
            - **FORBIDDEN:** Referencing figures without understanding their content or relevance
            - **IF NO FIGURE TAGS EXIST IN CONTEXT:** Do not reference any figures at all

            2. **STRICT CONTEXT ADHERENCE:**
            - Answer ONLY based on information explicitly stated in the context
            - Do not add external knowledge, assumptions, or inferences
            - If information is not in the context, state: "This information is not available in the provided context."

            3. **FIGURE REFERENCE VALIDATION CHECKLIST:**
            Before using ANY figure reference, verify ALL of these:
            - [ ] Does `<!-- figure: pg_X_fig_Y -->` appear in the context?
            - [ ] Have I read the text/description around this figure tag?
            - [ ] Is this figure's content relevant to answering the user's query?
            - [ ] Am I copying the pg_X_fig_Y part exactly as written?
            - [ ] Am I using the correct output format `[Fig: pg_X_fig_Y]`?
            
            **If you cannot check ALL five boxes, DO NOT include the figure reference.**

            4. **TABLE HANDLING:**
            - If context contains tabular data, render it in proper Markdown table format
            - Only include tables that are explicitly present in the context

            **EXAMPLE OF CORRECT BEHAVIOR:**
            - Context: "The network topology shows three layers. <!-- figure: pg_1_fig_1 --> This diagram illustrates the hierarchical structure."
            - Query: "What does the network topology look like?"
            - Correct Process: 1) Find tag → 2) Read description ("three layers", "hierarchical structure") → 3) Verify relevance (matches query) → 4) Reference
            - Correct Answer: "The network topology shows three layers with a hierarchical structure [Fig: pg_1_fig_1]"
            - WRONG: Referencing [Fig: pg_1_fig_1] for a query about "database performance" when the figure is about network topology

            **REMEMBER:** Your accuracy depends on following these rules precisely. When in doubt, omit figure references rather than guess.

            ---
            **Context:**
            {context}
            ---
            """

            prompt = f"""
            **User Query:**
            {query}

            **Instructions Reminder:**
            - Answer based ONLY on the provided context above
            - Use figure references ONLY if they exist as `<!-- figure: pg_X_fig_Y -->` in the context
            - **CRITICAL:** Read and understand the figure's description/context before referencing it
            - Only reference figures that are relevant to answering the user's specific query
            - Transform figure references from `<!-- figure: pg_X_fig_Y -->` to `[Fig: pg_X_fig_Y]`
            - Copy the pg_X_fig_Y part EXACTLY as it appears
            - If uncertain about any information, state that it's not available in the context

            **Answer:**
            """

            # 5. Send context and query to LLM
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Error during retrieval from collection {collection_name}: {e}", exc_info=True)
            try:
                self.qdrant_client.get_collection(collection_name=collection_name)
            except Exception:
                return f"Error: Collection '{collection_name}' not found."
            return "An error occurred during retrieval."