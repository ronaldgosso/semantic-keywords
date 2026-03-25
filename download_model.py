from sentence_transformers import SentenceTransformer

print("Downloading all-MiniLM-L6-v2 (~90MB)...")
model = SentenceTransformer("all-MiniLM-L6-v2")
print("Done. Model cached at:", model._model_card_vars.get("_name_or_path", "~/.cache/huggingface"))
print("You can now disconnect from the internet — the model is offline.")