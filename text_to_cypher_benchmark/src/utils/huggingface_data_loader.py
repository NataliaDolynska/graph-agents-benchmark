import datasets
from text_to_cypher_benchmark.src.utils.benchmark_data_loader import BenchmarkDataLoader


class HuggingFaceDataLoader(BenchmarkDataLoader):
    def __init__(
        self, dataset_name, question_column="question", answer_column="answer"
    ):
        self.dataset_name = dataset_name
        self.data = self._load_huggingface_data()
        self.question_column = question_column
        self.answer_column = answer_column

    def _load_huggingface_data(self):
        dataset = datasets.load_dataset(self.dataset_name)
        return dataset["train"].to_pandas()

    def get_qa_pairs(self):
        return list(zip(self.data[self.question_column], self.data[self.answer_column]))
