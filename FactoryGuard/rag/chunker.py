def chunk_pages(pages, chunk_size=900, overlap=120):
    chunks = []
    for page in pages:
        text = " ".join(str(page.get("text", "")).split())
        if not text:
            continue
        start = 0
        while start < len(text):
            end = min(len(text), start + chunk_size)
            piece = text[start:end].strip()
            if piece:
                chunks.append({
                    "text": piece,
                    "page": page.get("page", 1),
                    "section": page.get("section", "Document content"),
                })
            if end >= len(text):
                break
            start = max(0, end - overlap)
    return chunks
