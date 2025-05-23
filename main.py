import sys

from graph_agents_benchmark.src.solutions.base import Solution
from graph_agents_benchmark.src.utils.neo4j_data_population import (
    populate_neo4j_from_huggingface,
)

print(sys.path)

import csv
import os
import time
import json
from pathlib import Path
from typing import List, Tuple

from nltk.translate.bleu_score import sentence_bleu

from graph_agents_benchmark.src.executor import Executor
from graph_agents_benchmark.src.utils.benchmark_data_loader import BenchmarkDataLoader
from graph_agents_benchmark.src.utils.neo4j_integration import Neo4jConnectionManager

NEO4J_USER = "neo4j"
# NEO4J_USER = "twitter"
NEO4J_PASSWORD = "test_password"
# NEO4J_PASSWORD = "twitter"
NEO4J_URL = "bolt://0.0.0.0:7687"  # Use docker-compose service name


# NEO4J_URL = "neo4j+s://demo.neo4jlabs.com:7687"  # Use docker-compose service name


def get_solution(
        solution_name: str,
        model: str,
        db_user: str,
        db_password: str,
        db_url: str,
        db_name: str,
) -> Solution:
    """
    Retrieves a solution based on the provided name.

    Args:
        solution_name (str): The name of the solution to retrieve (e.g., "langchain", "llamaindex", "custom").
        model (str): The LLM model to use for the solution.
        db_user (str): The database user.
        db_password (str): The database password.
        db_url (str): The database URL.
        db_name (str): The database name.

    Returns:
        Solution: An instance of the requested solution.

    Raises:
        ValueError: If an unknown solution name is provided.
    """
    if solution_name == "langchain":
        from graph_agents_benchmark.src.solutions.langchain import LangChainSolution

        lch = LangChainSolution(
            config={
                "model_name": model,
                "db_user": db_user,
                "db_password": db_password,
                "db_url": db_url,
                "db_name": db_name,
                "db_user": db_user,
                "db_password": db_password,
                "db_url": db_url,
                "db_name": db_name,
            }
        )
        lch.initialize()
        return lch
    elif solution_name == "llamaindex":
        from graph_agents_benchmark.src.solutions.llamaindex import LlamaIndexSolution

        return LlamaIndexSolution()

    elif solution_name == "custom":
        from graph_agents_benchmark.src.solutions.text2neo import Text2NeoSolution

        return Text2NeoSolution(model_name="test")
    else:
        raise ValueError(f"Unknown solution: {solution_name}")


def calculate_accuracy(question, expected, actual):
    """
    Stub accuracy function.

    Args:
        question (str): The question asked.
        expected (str): The expected answer.
        actual (str): The actual answer.

    Returns:
        float: A stubbed accuracy score (always 0.5).
    """
    return 0.5


def benchmark_solutions(
        solution_name: str,
        qa_pairs: List[Tuple[str, str]],
        model: str,
        db_user: str,
        db_password: str,
        db_url: str,
        db_name: str,
):
    """
    Benchmarks a given solution.

    Args:
        solution_name (str): Name of the solution being benchmarked.
        qa_pairs (List[Tuple[str, str]]): List of question/answer tuples.
        model (str): The LLM model to use for the solution.
        db_user (str): The database user.
        db_password (str): The database password.
        db_url (str): The database URL.
        db_name (str): The database name.

    Returns:
        List[Dict[str, Any]]: A list of dictionaries containing the benchmark results.
    """
    print(f"Benchmarking solution: {solution_name}")

    results = []

    try:
        solution = get_solution(
            solution_name=solution_name,
            model=model,
            db_user=db_user,
            db_password=db_password,
            db_url=db_url,
            db_name=db_name,
        )

        # solution.populate(benchmark_data_file)

        def predictor(question):
            return solution.predict(question)

        executor = Executor(predictor, qa_pairs)
        results = executor.execute(calculate_accuracy)
    except Exception as e:
        print(f"Error during benchmarking: {repr(e)}")
        return []  # Return empty list on error

    # finally:
    # if neo4j_conn:
    # neo4j_conn.close()

    return results


def create_file_if_not_exists(file_path):
    """
    Creates a file if it does not already exist.

    Args:
        file_path (str): The path to the file to create.
    """
    file = Path(file_path)
    if not file.exists():
        file.touch()
        print(f"File '{file_path}' created.")
    else:
        print(f"File '{file_path}' already exists.")


def create_dir_if_not_exists(directory_path):
    """
    Creates a directory if it does not already exist.

    Args:
        directory_path (str): The path to the directory to create.
    """
    file = Path(directory_path)
    if not file.is_dir():
        file.mkdir(parents=True)
        print(f"Directory '{directory_path}' created.")
    else:
        print(f"Directory '{directory_path}' already exists.")


def main():
    """
    Main function to benchmark different text-to-Cypher solutions.

    Parses command-line arguments to determine the solution and model to use,
    then benchmarks the specified solution and prints the results.
    """
    # Load data using BenchmarkDataLoader, using the first and last columns for Q&A
    # qa_loader = BenchmarkDataLoader(
    #     "datasets/synthetic_opus_demodbs/questions_and_answers.csv"
    # )
    # qa_pairs = qa_loader.get_qa_pairs(
    #     question_column=qa_loader.data.columns[0],
    #     answer_column=qa_loader.data.columns[-1],
    # )

    import argparse

    parser = argparse.ArgumentParser(
        description="Benchmark different text-to-Cypher solutions."
    )
    parser.add_argument(
        "solution",
        choices=["langchain", "llamaindex", "custom"],
        help="The solution to benchmark.",
    )

    parser.add_argument(
        "model",
        help="LLM model to use for benchmark. [vertex/gemini-1.5-pro-002, ollama/deepseek-r1:32b, etc]",
    )
    args = parser.parse_args()

    results = benchmark_solutions(
        solution_name=args.solution,
        qa_pairs=[("What  database I have in graph db?", "The answer")],
        model=args.model,
        db_user=NEO4J_USER,
        db_password=NEO4J_PASSWORD,
        db_url=NEO4J_URL,
        db_name="neo4j",
    )

    # Aggregate and print results
    if results:
        avg_time = sum(r["time_taken"] for r in results) / len(results)
        avg_accuracy = sum(r["accuracy"] for r in results) / len(results)
        avg_bleu = sum(r["blue_score"] for r in results) / len(results)

        print(f"\nBenchmark Results for {args.solution}:")
        print(f"Avg time: {avg_time:.4f}s")
        print(f"Avg accuracy: {avg_accuracy:.2f}")
        print(f"Avg BLEU score: {avg_bleu:.2f}")

        provider = args.model.split("/")[0]
        file_name = f"results/{provider}/{args.solution}_benchmark_results.json"

        create_dir_if_not_exists(f"results/{provider}/")
        create_file_if_not_exists(file_name)

        with open(
                f"results/{provider}/{args.solution}_benchmark_results.json", "w"
        ) as f:
            json.dump(results, f, indent=4)


if __name__ == "__main__":
    """
    Entry point for the benchmark script.
    """
    main()
