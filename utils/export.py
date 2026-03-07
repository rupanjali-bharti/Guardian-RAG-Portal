import pandas as pd

def export_answers(results):

    df = pd.DataFrame(results)

    file_path = "answers.csv"

    df.to_csv(file_path, index=False)

    return file_path