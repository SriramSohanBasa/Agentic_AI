# Multimodal RAG Document Processing with CLIP

This project demonstrates the foundational data processing pipeline for a Multimodal Retrieval-Augmented Generation (RAG) system. It reads a PDF file containing both text and images, and uses the OpenAI CLIP model to generate semantically rich vector embeddings for all content.

This allows for powerful semantic search capabilities where a query can retrieve the most relevant text chunks and images from the document.

## Workflow Diagram

```
📄 Input: multimodal_sample.pdf
│
├───🚀 Step 1: Initialization
│    │
│    ├───🧠 Load CLIP Model & Processor
│    └───🔑 Load Environment Variables (API Keys)
│
├───⚙️ Step 2: PDF Processing (Loop per Page)
│    │
│    ├───📝 Text Processing
│    │    │
│    │    ├─── Extract Text from Page
│    │    ├─── Split Text into Chunks
│    │    └─── Embed each Text Chunk -> [Vector]
│    │
│    └───🖼️ Image Processing
│         │
│         ├─── Extract Image from Page
│         ├─── Convert to PIL Image
│         ├─── Encode to Base64 (for LLM)
│         └─── Embed Image -> [Vector]
│
└───📦 Step 3: Aggregation & Storage
     │
     ├───📚 all_docs: List of [Text Chunks, Image Placeholders]
     ├───#️⃣ all_embeddings: List of [Vectors]
     └───🖼️ image_data_store: Dict of {ImageID: Base64 Data}

```

## How It Works

The core logic resides in the `model.ipynb` Jupyter Notebook, which executes the following steps:

1.  **Initialization**: It loads the pre-trained `openai/clip-vit-base-patch32` model and its associated processor from the Hugging Face `transformers` library. It also loads the necessary API keys from a `.env` file.

2.  **Embedding Functions**: Two key functions are defined:
    *   `embed_text(text)`: Takes a string of text and returns a 512-dimensional vector embedding.
    *   `embed_image(image_data)`: Takes a PIL Image object and returns a 512-dimensional vector embedding.
    These functions ensure that both text and images are mapped into the same vector space.

3.  **PDF Processing**: The script opens a PDF file (`multimodal_sample.pdf`) and iterates through it page by page.
    *   **Text Extraction**: It extracts all text from a page, and uses `RecursiveCharacterTextSplitter` from LangChain to break it into smaller, semantically coherent chunks.
    *   **Image Extraction**: It finds and extracts all images on a page. Each image is converted into a PIL Image object for embedding and also encoded into `base64`. The base64 version is stored for potential use with vision-enabled LLMs like GPT-4V.

4.  **Embedding and Storage**:
    *   Each text chunk and each image is passed to its respective embedding function.
    *   The resulting embeddings are stored in a list (`all_embeddings`).
    *   The source content (text chunks and special image placeholders) are stored as LangChain `Document` objects in a parallel list (`all_docs`).

## Setup and Installation

Follow these steps to run the project yourself.

### 1. Prerequisites
*   Python 3.8+
*   A virtual environment (recommended)

### 2. Clone the Repository
```bash
git clone <your-repo-url>
cd <your-repo-directory>
```

### 3. Create a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

### 4. Install Dependencies
Create a `requirements.txt` file with the following content:
```
pymupdf
langchain
langchain-core
langchain-community
transformers
torch
Pillow
scikit-learn
python-dotenv
faiss-cpu
```
Then, install the packages:
```bash
pip install -r requirements.txt
```

### 5. Set Up Environment Variables
Create a file named `.env` in the root of the project directory and add your OpenAI API key:
```
OPENAI_API_KEY="sk-..."
```

### 6. Add a Sample PDF
Place a PDF file in the project directory and name it `multimodal_sample.pdf`.

## Usage

The entire data processing workflow is contained within the `model.ipynb` notebook.

1.  **Launch Jupyter**: Make sure you have Jupyter Notebook or JupyterLab installed (`pip install jupyterlab`).
2.  **Start the Server**:
    ```bash
    jupyter lab
    ```
3.  **Run the Notebook**: Open `model.ipynb` and run the cells sequentially from top to bottom.

After running the notebook, the `all_docs` and `all_embeddings` lists will be populated in memory, ready for the next step, which is typically loading them into a vector database like FAISS or Chroma for efficient retrieval.
