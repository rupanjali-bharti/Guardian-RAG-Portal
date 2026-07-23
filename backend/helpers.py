import pandas as pd

def parse_questions(csv_file):
    """Reads the uploaded CSV and extracts questions from the first column."""
    try:
        df = pd.read_csv(csv_file)
        # Assumes questions are in the first column
        questions = df.iloc[:, 0].dropna().tolist()
        return [str(q).strip() for q in questions if str(q).strip()]
    except Exception as e:
        print(f"Error parsing CSV: {e}")
        return []

def load_reference_docs(files):
    """
    Optional helper if you want to process files before indexing.
    Currently, app.py handles the direct reading.
    """
    all_text = ""
    for f in files:
        all_text += f.read().decode("utf-8") + "\n\n"
    return all_text