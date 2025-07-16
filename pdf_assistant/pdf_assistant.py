import typer
from typing import Optional,List
from phi.assistant import Assistant
from phi.storage.assistant.postgres import PgAssistantStorage
from phi.knowledge.pdf import PDFUrlKnowledgeBase
from phi.vectordb.pgvector import PgVector

import os
from dotenv import load_dotenv
load_dotenv()

os.environ["GROQ_API_KEY"]=os.getenv("GROQ_API_KEY")
db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge_base=PDFUrlKnowledgeBase(
    urls=["https://phi-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"],
    vector_db=PgVector(table_name="recipes",db_url=db_url,)
)

knowledge_base.load()

storage=PgAssistantStorage(table_name="pdf_assistant",db_url=db_url)

def pdf_assistant(new: bool = False, user: str = "user"):
    run_id: Optional[str] = None

    if not new:
        existing_run_ids: List[str] = storage.get_all_run_ids(user)
        if len(existing_run_ids) > 0:
            run_id = existing_run_ids[0]

    assistant = Assistant(
        run_id=run_id,
        user_id=user,
        knowledge_base=knowledge_base,
        storage=storage,
        # Show tool calls in the response
        show_tool_calls=True,
        # Enable the assistant to search the knowledge base
        search_knowledge=True,
        # Enable the assistant to read the chat history
        read_chat_history=True,
    )
    if run_id is None:
        run_id = assistant.run_id
        print(f"Started Run: {run_id}\n")
    else:
        print(f"Continuing Run: {run_id}\n")

    assistant.cli_app(markdown=True)

if __name__=="__main__":
    typer.run(pdf_assistant)



# 1. Ensure your Docker container 'pgvector' is already running with PostgreSQL.
# 2. Attach to the running container to get a shell inside it.
# 3. Launch the 'psql' command-line interface to connect to your 'ai' database as user 'ai'.
# 4. Switch to the correct schema/table if needed (e.g., schema 'ai', table 'recipes').
# 5. Remove any existing default from the 'id' column so there is no conflict.
# 6. Convert the 'id' column to a bigger integer type, ensuring existing values can be cast.
# 7. Create a sequence to generate new ID values automatically.
# 8. Attach the new sequence to the 'id' column by setting it as the default.
# 9. Mark the 'id' column as NOT NULL to avoid null inserts.
# 10. Check the table description to confirm everything is correct.
# 11. Exit psql and the container, then re-run your Python script. 
#    Now, the 'id' column will auto-increment instead of failing on NOT NULL.

# -- Attach to the running container named "pgvector"
# docker exec -it pgvector bash  # Enters the container's shell

# -- Inside the container, connect to Postgres as user=ai and database=ai
# psql -U ai -d ai  # Opens the psql CLI for database 'ai'

# -- Remove any default on the 'id' column (if present)
# ALTER TABLE ai.recipes
#     ALTER COLUMN id DROP DEFAULT;  -- Drops old default to avoid conflicts

# -- Convert the existing 'id' column to BIGINT using an explicit cast
# ALTER TABLE ai.recipes
#     ALTER COLUMN id TYPE BIGINT USING id::bigint;  -- Ensures existing ids are cast to bigint

# -- Create a new sequence to provide unique integers for the 'id' column
# CREATE SEQUENCE ai.recipes_id_seq START 1;  -- Sequence starts at 1

# -- Set the 'id' column to use the newly created sequence, and disallow NULL
# ALTER TABLE ai.recipes
#     ALTER COLUMN id SET DEFAULT nextval('ai.recipes_id_seq'::regclass),
#     ALTER COLUMN id SET NOT NULL;  -- 'NOT NULL' ensures 'id' can't be empty

# -- (Optional) Make 'id' a PRIMARY KEY if desired
# -- ALTER TABLE ai.recipes
# --     ADD PRIMARY KEY (id);

# -- Verify the table structure
# \d ai.recipes  -- Lists column info to confirm 'id' is bigint, not null, and has the default sequence

# -- Exit the psql CLI
# \q

# -- Exit the container shell
# exit

# -- (Outside container) Re-run your script
# python pdf_assistant.py  # Now inserts will auto-generate 'id' values