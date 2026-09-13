ALLOWED = {
    "SOP Review": ["pdf", "docx", "txt"],
    "HACCP Review": ["pdf", "docx", "txt"],
    "Cleaning Records": ["csv", "xlsx", "xls"],
    "Temperature Records": ["csv", "xlsx", "xls"],
    "Inspection Report": ["pdf", "docx", "txt"],
    "Laboratory Report": ["pdf", "docx", "txt", "csv", "xlsx", "xls"],
    "Visual Inspection": ["jpg", "jpeg", "png", "webp"],
}

def validate_upload(analysis_type, name):
    ext = name.lower().rsplit(".", 1)[-1] if "." in name else ""
    return ext in ALLOWED.get(analysis_type, [])
