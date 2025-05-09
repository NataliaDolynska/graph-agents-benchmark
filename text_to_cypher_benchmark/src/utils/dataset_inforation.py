import datasets
from text_to_cypher_benchmark.src.utils.benchmark_data_loader import BenchmarkDataLoader
from text_to_cypher_benchmark.src.utils.huggingface_data_loader import HuggingFaceDataLoader


class DatasetHandler:
    def __init__(
            self,
            payload_dataset_name, payload_entity_extractor, questions_dataset_name, questions_entity_extractor
    ):
        self.payload_dataset_name = payload_dataset_name
        self.payload_entity_extractor = payload_entity_extractor
        self.questions_dataset_name = questions_dataset_name
        self.questions_entity_extractor = questions_entity_extractor

        self._payload_dataset = None
        self._payload_dataset_items = list()
        self._questions_dataset = None
        self._questions_dataset_items = list()

    def get_payload_datasets_items(self):
        if self._payload_dataset is None:
            self._payload_dataset = HuggingFaceDataLoader(self.payload_dataset_name).get_data()

        if len(self._payload_dataset_items) == 0:
            for index, row in self._payload_dataset.iterrows():
                self._payload_dataset_items.append(self.payload_entity_extractor(row))
        return self._payload_dataset_items

    def get_questions_datasets_items(self):
        if self._questions_dataset is None:
            self._questions_dataset = HuggingFaceDataLoader(self.payload_dataset_name).get_data()

        if len(self._questions_dataset_items) == 0:
            for index, row in self._questions_dataset.iterrows():
                self._questions_dataset_items.append(self.questions_entity_extractor(row))
        return self._questions_dataset_items
