def normalize_source_label(label: object) -> str:
    return str(label).strip().strip("[]").lower()
