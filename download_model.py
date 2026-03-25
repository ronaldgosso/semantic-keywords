from sentence_transformers import SentenceTransformer

    # Choose any model you want to download from here
    # "fast":     "all-MiniLM-L6-v2",    # 90MB  — default
    # "balanced": "all-MiniLM-L12-v2",   # 120MB — more layers, slightly better
    # "accurate": "all-mpnet-base-v2",   # 420MB — best quality, slower on CPU

print("Downloading all-MiniLM-L6-v2 (~90MB)...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("Done. Model cached at:", model._model_card_vars.get("_name_or_path", "~/.cache/huggingface"))
print("You can now disconnect from the internet — the model is offline.")