import json
import re
from typing import Dict, List
from neo4j import GraphDatabase, Driver, Record
from neo4j.graph import Node, Relationship
from neo4j.time import DateTime, Date, Time, Duration

class QAEnricher:
    def __init__(
            self,
            db_name: str,
            neo4j_uri: str = "bolt://localhost:7687",
            neo4j_user: str = "neo4j",
            neo4j_password: str = "neo4j_test_password",
    ) -> None:
        self._db_name = db_name
        self._neo4j_uri = neo4j_uri
        self._neo4j_user = neo4j_user
        self._neo4j_password = neo4j_password
        self._driver: Driver = GraphDatabase.driver(
            self._neo4j_uri, auth=(self._neo4j_user, self._neo4j_password)
        )
        self._driver.verify_connectivity()

    def enrich(
            self,
            dataset: List[Dict[str, str]],
            cypher_column: str = "cypher",
            answer_key: str = "answer",
    ) -> List[Dict[str, str]]:
        enriched_dataset = []

        with self._driver.session(database=self._db_name) as session:
            for item in dataset:
                cypher_query = item.get(cypher_column)
                if not cypher_query:
                    item[answer_key] = None
                    enriched_dataset.append(item)
                    continue

                try:
                    query = QAEnricher._unescape_query(cypher_query)

                    missing_props = QAEnricher._query_has_missing_properties(session, query)
                    if missing_props:
                        print(
                            f"⚠️ Query references missing properties in database: {', '.join(missing_props)} | {cypher_query}")
                        item[answer_key] = None
                        enriched_dataset.append(item)
                        continue

                    result = session.run(query)
                    item[answer_key] = self._format_result(result)
                except Exception as e:
                    print(f"⚠️ Error executing query:\n{cypher_query}\nError: {e}")
                    item[answer_key] = None

                enriched_dataset.append(item)

        return enriched_dataset

    def close(self) -> None:
        if self._driver:
            self._driver.close()

    @staticmethod
    def _unescape_query(q: str) -> str:
        try:
            return q.encode("utf-8").decode("unicode_escape")
        except UnicodeDecodeError:
            return q

    @staticmethod
    def _parse_key(key: str) -> str:
        if "." in key:
            return key.split(".")[-1].strip()
        return key.strip()

    def _format_result(self, result_iter) -> str | None:
        lines = []

        for record in result_iter:
            if not record:
                continue
            elif QAEnricher._is_stringifies(record):
                line = self._stringify(record)
                lines.append(line)
            else:
                line = self._stringify(record.data())
                lines.append(line)
        if len(lines) > 1:
            return "\n".join(lines)
        elif len(lines) == 1:
            return lines[0]
        else:
            return None

    @staticmethod
    def _is_stringifies(val) -> bool:

        return isinstance(val, (DateTime, Date, Time, Duration, Relationship, List, Record, Node))

    def _stringify(self, val) -> str:
        if isinstance(val, (DateTime, Date, Time)):
            return val.iso_format()  # returns 'YYYY-MM-DDTHH:MM:SS' etc.
        elif isinstance(val, Duration):
            return str(val)

        elif isinstance(val, (Node, Relationship, dict, Record)):
            has_strings = False
            lines = []
            for k, v in val.items():
                if len(k) == 1 and QAEnricher._is_stringifies(v):
                    has_strings = True
                    lines.append(self._stringify(v))
                else:
                    lines.append({QAEnricher._parse_key(k): self._stringify(v)})
            if has_strings:
                return " ".join(lines)
            else:
                result = {}
                for item in lines:
                    result = {**item, **result}
                return json.dumps(result)

        elif isinstance(val, list):
            if all(isinstance(v, (str, int, float, None)) for v in val):
                str_list = ["'" + ls + "'" for ls in list(map(str, val))]
                return "[" + ",".join(str_list) + "]"
            return "\n".join(self._stringify(v) for v in val)
        return str(val)

    @staticmethod
    def _query_has_missing_properties(session, query: str) -> List[str]:
        """
        Check whether the query refers to property keys that don't exist in the DB.
        Only works for simple property references like m.foo or n.bar.
        """
        props = set(re.findall(r"\b\w+\.(\w+)", query))
        if not props:
            return []

        existing_keys = session.run("CALL db.propertyKeys()").value()
        missing = [p for p in props if p not in existing_keys]
        return missing
