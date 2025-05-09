import pandas as pd


class BenchmarkDataLoader:

    def __init__(
            self,
            file_path,
            file_type="csv",
            question_column="question",
            answer_column="answer",
    ):
        self.file_path = file_path
        self.file_type = file_type
        self.data = self._load_data()
        self.question_column = question_column
        self.answer_column = answer_column

    def _load_data(self):
        if self.file_type == "csv":
            return pd.read_csv(self.file_path)
        elif self.file_type == "json":
            return pd.read_json(self.file_path)
        else:
            raise ValueError(
                f"Unsupported file type '{self.file_type}'. Must be 'csv', 'json', or 'tsv'."
            )

    def get_data(self):
        return self.data.copy()  # Return a copy to avoid modification of original data

    def get_questions(self, column_name=None):
        if column_name in self.data.columns:
            if column_name:
                return self.data[column_name].tolist()
            else:
                return self.get_questions(self.question_column)
        else:
            raise KeyError(f"Column '{column_name}' not found in data.")

    def get_answers(self, index: int, column_name=None):
        if column_name in self.data.columns:
            if column_name:
                return self.data[column_name].tolist()
            else:
                return self.get_answers(self.answer_column)
        else:
            raise KeyError(f"Column '{column_name}' not found in data.")

    def get_qa_pairs(self, question_column=None, answer_column=None):
        if question_column not in self.data.columns:
            raise KeyError(f"Column '{question_column}' not found in data.")

        if answer_column not in self.data.columns:
            raise KeyError(f"Column '{answer_column}' not found in data.")

        return list(
            zip(self.get_questions(question_column), self.get_answers(answer_column))
        )
