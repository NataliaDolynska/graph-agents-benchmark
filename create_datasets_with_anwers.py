import os

import pandas as pd

from graph_agents_benchmark.src.infrastucture.neo4jdocker import Neo4jComposeRunner
from graph_agents_benchmark.src.models import Column
from graph_agents_benchmark.src.utils.data_loaders import HuggingFaceDataLoader
from graph_agents_benchmark.src.utils.qa_enricher import QAEnricher

DUMPS = [
    "twitch-50",
    "movies-50",
    "fincen-50",
    "northwind-50",
    "recommendations-50",
]

DATABASES = [db_name.split("-")[0] for db_name in DUMPS]

print(f"GOING TO CREATE DATASET FOR DUMPS {DUMPS} ( DATABASES : {DATABASES} )")

ds_name = "neo4j/text2cypher-2025v1"
neo = HuggingFaceDataLoader(dataset_name=ds_name, columns=[Column(path="train.question", alias="question"),
                                                           Column(path="train.schema", alias="schema"),
                                                           Column(path="train.database_reference_alias",
                                                                  alias="database", map_fn=lambda x: x.split("_")[-1]),
                                                           Column(path="train.cypher", alias="cypher"),
                                                           ])

#
dictionaries = neo.get_dataset_dictionaries()

print("")
print("*" * 100)
print(f"#### TOTAL ROWS IN Q&Cypher DATASET : {len(dictionaries)}")
print("*" * 100)
print("_" * 100)

filtered_datasets_list = []
unfiltered_datasets_list = []

for dump_name, database_name in list(zip(DUMPS, DATABASES)):
    print("*" * 100)
    print(
        f"GOING TO CREATE QUESTION AND ANSWERS DATASET FOR DATABASE NAME: {database_name} WHERE DUMP NAME: {dump_name}")
    questions_and_cypher_ds = list(filter(lambda d: database_name in d['database'], dictionaries))
    print()
    print(f"Size of questions and cypher ds {len(questions_and_cypher_ds)} rows")
    n4j = Neo4jComposeRunner(dump_name)
    print(f"Starting Neo4j in docker for dataset [{dump_name}] and dump [{dump_name}]")
    n4j.start()
    print(f"Database has [{str(n4j.count_nodes())}]")
    print()
    print(f"Creating questions and answers enricher for database [{database_name}] dataset [{dump_name}]")
    qae = QAEnricher(dump_name)
    # 
    print()
    print("Starting Q&Cypher enrichment")
    print("*" * 100)
    ds_with_questions_and_answers = qae.enrich(questions_and_cypher_ds)
    print()
    print("*" * 100)
    print(f"Stopping Neo4j in docker for database [{database_name}] and dump [{dump_name}]")
    n4j.stop()
    print()
    print("*" * 100)
    print(f"Enriched dataset size is  {len(ds_with_questions_and_answers)}")
    print()
    ds_with_questions_and_answers_filtered = list(
        filter(lambda item: item['answer'] is not None, ds_with_questions_and_answers))
    print(f"Filtered dataset with answers size is  {len(ds_with_questions_and_answers_filtered)}")
    print()

    filtered_datasets_list.extend(ds_with_questions_and_answers_filtered)
    unfiltered_datasets_list.extend(ds_with_questions_and_answers)

    output_dir = f"./datasets/{database_name}"
    os.makedirs(output_dir, exist_ok=True)

    df = pd.DataFrame(ds_with_questions_and_answers_filtered)
    df.to_json(f"./datasets/{database_name}/questions_and_answers_{database_name}_filtered.jsonl", orient="records",
               lines=True, force_ascii=False)

    df = pd.DataFrame(ds_with_questions_and_answers)
    df.to_json(f"./datasets/{database_name}/questions_and_answers_{database_name}_unfiltered.jsonl", orient="records",
               lines=True, force_ascii=False)
# 
# 
filtered_df = pd.DataFrame(filtered_datasets_list)
filtered_df.to_json(f"./datasets/full_questions_and_answers_filtered.jsonl", orient="records",
                    lines=True, force_ascii=False)

unfiltered_df = pd.DataFrame(unfiltered_datasets_list)
unfiltered_df.to_json(f"./datasets/full_questions_and_answers_unfiltered.jsonl", orient="records",
                      lines=True, force_ascii=False)

print("*" * 100)
print("*" * 100)
print("*" * 100)
print(f"UNFILTERED DATASET SIZE IS: {len(unfiltered_df)}")
print(f"FILTERED DATASET SIZE IS: {len(filtered_df)}")
print("*" * 100)
print("*" * 100)
