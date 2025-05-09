import time
import nltk
from pyclbr import Function

nltk.download("punkt")


class Executor:

    def __init__(self, predictor: Function, dataset):
        self.predictor = predictor
        self.dataset = dataset

    def execute(self, accuracy_function: Function):
        results = []
        for question, expected_answer in self.dataset:

            start_time = time.time()
            actual_answer = self.predictor(question)

            end_time = time.time()
            time_taken = end_time - start_time

            print("Question: " + question)
            print("Expected Answer: " + expected_answer)
            print("Actual Answer:" + actual_answer)
            accuracy = accuracy_function(question, expected_answer, actual_answer)
            blue_score = nltk.translate.bleu_score.sentence_bleu(
                [expected_answer], actual_answer
            )

            results.append(
                {
                    "question": question,
                    "expected_answer": expected_answer,
                    "actual_answer": actual_answer,
                    "accuracy": accuracy,
                    "blue_score": blue_score,
                    "time_taken": time_taken,
                }
            )

        return results
