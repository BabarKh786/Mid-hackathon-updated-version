# FactoryGuard AI

FactoryGuard AI is a modular Streamlit prototype for AI-assisted food-safety and quality auditing.

## Main workflow

1. Create a factory profile.
2. Upload the factory's SOP/HACCP/procedure documents into **Knowledge Base**.
3. FactoryGuard extracts and chunks the documents.
4. Sentence Transformers creates embeddings.
5. FAISS indexes the complete factory document set.
6. In **AI Audit**, upload operational evidence.
7. The relevant factory evidence is retrieved through RAG.
8. GPT-OSS 120B via Groq produces structured findings and corrective actions.
9. Findings can be tracked through Corrective Actions and included in the PDF report.

## Important RAG behavior

### Documents uploaded + relevant evidence retrieved
The audit is a **RAG-Based Factory Assessment**. Factory-specific requirements and recommendations must be grounded in retrieved documents.

### No SOP/HACCP documents
The audit can still run, but it is labelled **General Knowledge Assessment**. It must not claim that a factory-specific SOP requires something.

### Documents exist but relevant evidence is not retrieved
FactoryGuard does **not** silently fall back to general knowledge for a factory-specific conclusion. It tells the user that relevant factory evidence was not found.

## Knowledge Base Search

Use **Knowledge Base → Search the factory knowledge base** to ask questions about uploaded documents. The answer is restricted to retrieved factory evidence and displays the sources.

## Stack

- Streamlit
- GPT-OSS 120B through Groq
- FAISS
- Sentence Transformers (`all-MiniLM-L6-v2`)
- PyMuPDF
- python-docx
- pandas / openpyxl
- SQLite
- ReportLab

No Llama dependency is used.

## Local setup

```bash
pip install -r requirements.txt
streamlit run app.py
```

Set the API key using an environment variable or `.streamlit/secrets.toml`:

```toml
GROQ_API_KEY = "YOUR_KEY"
```

Never commit a real API key to GitHub.

## Streamlit Cloud

Use `app.py` as the main file and add `GROQ_API_KEY` under the Streamlit app Secrets.

## Important deployment note

The FAISS index and SQLite database in this prototype are stored on the app filesystem. Streamlit Cloud can reset local filesystem state when an app is rebuilt/restarted. For a hackathon prototype, re-upload/re-indexing is acceptable. For production, move persistent documents, vector indexes and database records to a persistent hosted service.

## Supported audit inputs

- Temperature Records: CSV/XLSX/XLS
- Cleaning Records: CSV/XLSX/XLS
- SOP Review: PDF/DOCX/TXT
- HACCP Review: PDF/DOCX/TXT
- Inspection Report: PDF/DOCX/TXT
- Laboratory Report: PDF/DOCX/TXT/CSV/XLSX/XLS
- Visual Inspection: image formats are accepted, but image-specific AI extraction is not implemented in this prototype.
