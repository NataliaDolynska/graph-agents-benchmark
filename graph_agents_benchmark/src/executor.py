import time
from collections.abc import Callable

import nltk
from pyclbr import Function

nltk.download("punkt")


class Executor:
    """
    Executes a given predictor function on a dataset and calculates accuracy and BLEU score.
    """

    def __init__(self, predictor: Callable, dataset):
        """
        Initializes the Executor with a predictor function and a dataset.

        Args:
            predictor (Function): A function that takes a question as input and returns an answer.
            dataset: A list of (question, expected_answer) tuples.
        """
        self.predictor = predictor
        self.dataset = dataset

    def execute(self, accuracy_function: Function):
        """
        Executes the predictor function on the dataset and calculates accuracy and BLEU score for each question.

        Args:
            accuracy_function (Function): A function that takes a question, expected answer, and actual answer as input and returns an accuracy score.

        Returns:
            list: A list of dictionaries, where each dictionary contains the question, expected answer, actual answer, accuracy, BLEU score, and time taken for each question.
        """
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
