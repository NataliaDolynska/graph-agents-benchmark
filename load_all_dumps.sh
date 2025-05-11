#!/bin/bash

set -e

DUMP_DIR="./neo4j/dumps"
DATA_DIR="./neo4j/data"

mkdir -p "$DUMP_DIR"
mkdir -p "$DATA_DIR"
chmod -R 777 "$DATA_DIR"

# List of dump files and corresponding GitHub raw URLs
DUMP_FILES=(
  "fincen-50.dump https://github.com/neo4j-graph-examples/fincen/raw/refs/heads/main/data/fincen-50.dump"
  "movies-50.dump https://github.com/neo4j-graph-examples/movies/raw/refs/heads/main/data/movies-50.dump"
  "northwind-50.dump https://github.com/neo4j-graph-examples/northwind/raw/refs/heads/main/data/northwind-50.dump"
  "recommendations-50.dump https://github.com/neo4j-graph-examples/recommendations/raw/refs/heads/main/data/recommendations-50.dump"
  "twitch-50.dump https://github.com/neo4j-graph-examples/twitch/raw/refs/heads/main/data/twitch-50.dump"
)

echo "Downloading dump files from GitHub if not already present..."
for entry in "${DUMP_FILES[@]}"; do
  FILE_NAME=$(echo "$entry" | awk '{print $1}')
  FILE_URL=$(echo "$entry" | awk '{print $2}')

  if [[ ! -f "$DUMP_DIR/$FILE_NAME" ]]; then
    echo "Downloading $FILE_NAME..."
    curl -L "$FILE_URL" -o "$DUMP_DIR/$FILE_NAME"
  else
    echo "$FILE_NAME already exists, skipping download."
  fi
done
echo "Download step completed."

# Continue with Neo4j logic
NEO4J_TAG=2025-community

docker pull neo4j/neo4j-admin:$NEO4J_TAG

for dump_file in "$DUMP_DIR"/*.dump; do
    db_name=$(basename "$dump_file" .dump)

    echo "Loading database: $db_name"

    if [[ "$NEO4J_TAG" == "4.4.42-community-debian-arm" ]]; then
      docker run --rm \
          --volume="$DATA_DIR":/data \
          --volume="$DUMP_DIR":/backups \
          neo4j/neo4j-admin:$NEO4J_TAG \
          neo4j-admin load \
          --database="$db_name" \
          --verbose \
          --force \
          --from=/backups/$db_name.dump
    else
      docker run --rm \
          --volume="$DATA_DIR":/data \
          --volume="$DUMP_DIR":/backups \
          neo4j/neo4j-admin:$NEO4J_TAG \
          neo4j-admin database load "$db_name" \
          --verbose \
          --overwrite-destination=true \
          --from-path=/backups
    fi

    echo "Done loading: $db_name"
done

echo "Changing permissions of restored database folders for later docker usage.."
chmod -R 777 "$DATA_DIR/databases/"
chmod -R 777 "$DATA_DIR/transactions/"
echo "Done. Restored databases from dumps in: [$DUMP_DIR/*.dump]"
