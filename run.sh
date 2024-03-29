#! /bin/sh
set -e
mkdir -p result
docker-compose build

for FILENAME in $*; do
    BASENAME=$(basename $FILENAME)

    $SUDO zcat -f $FILENAME | docker-compose run --rm log2html ./display_log.py --threads 4 - > result/${BASENAME}.html
done
./generate_index.py
