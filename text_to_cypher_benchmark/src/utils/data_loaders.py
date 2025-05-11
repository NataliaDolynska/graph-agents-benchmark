from typing import List, Union,  Optional
import pandas as pd
from datasets import load_dataset, DatasetDict, Dataset
from text_to_cypher_benchmark.src.models import Column


class HuggingFaceDataLoader:
    def __init__(self, dataset_name: str, columns: List[Column]):
        self._data = load_dataset(dataset_name)

        self._columns: List[Column] = []
        for column in columns:
            if isinstance(column.path, str):
                path = column.path.split(".") if "." in column.path else [column.path]
            else:
                path = column.path
            self._columns.append(Column(**{**column.dict(), "path": path}))

        if not isinstance(self._data, (Dataset, DatasetDict)):
            raise TypeError(f"Unsupported dataset type: {type(self._data)}")

    def get_dataset_dictionaries(self, presents_columns_filter: Optional[List[str]] = None,
                                 order_by: Optional[Union[str, List[str]]] = None
                                 ) -> List[dict]:
        rows = self._extract_columns(self._data, self._columns)

        if presents_columns_filter:
            rows = [
                row for row in rows
                if all(row.get(col) is not None for col in presents_columns_filter)
            ]

        if order_by:
            if isinstance(order_by, str):
                order_by = [order_by]
            rows.sort(key=lambda row: tuple(row.get(col) for col in order_by))

        return rows

    def _extract_columns(self, dataset: Union[DatasetDict, Dataset], columns: List[Column]) -> List[dict]:
        datasets_dict = dataset if isinstance(dataset, DatasetDict) else {"default": dataset}

        split_names = {col.path[0] for col in columns}
        if len(split_names) > 1:
            raise ValueError(f"Multiple dataset splits referenced: {split_names}. Use only one.")

        split = split_names.pop()
        if split not in datasets_dict:
            raise KeyError(f"Split '{split}' not found in dataset.")

        ds = datasets_dict[split]

        # Build column data lookup
        column_data = {}
        for col in columns:
            try:
                column_name = col.path[1] if len(col.path) > 1 else col.path[0]
                column_data[col.alias] = ds[column_name]
            except KeyError:
                column_data[col.alias] = None
                print(f"Warning: Column '{column_name}' not found in dataset split '{split}'.")

        dataset_len = next((len(v) for v in column_data.values() if v is not None), 0)
        required_aliases = {col.alias for col in columns if col.required}
        map_fns = {col.alias: col.map_fn for col in columns if col.map_fn}

        result = []
        for i in range(dataset_len):
            row = {
                alias: values[i] if values is not None else None
                for alias, values in column_data.items()
            }
            if all(row[alias] is not None for alias in required_aliases):
                for alias, fn in map_fns.items():
                    row[alias] = fn(row[alias])
                result.append(row)

        return result


class FsDataLoader:

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
