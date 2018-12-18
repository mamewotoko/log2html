#! /bin/sh
mkdir -p result

for FILENAME in $*; do
    BASENAME=$(basename $FILENAME)

    $SUDO zcat -f $FILENAME | docker-compose run --rm log2html ./display_log.py --threads 3 - > result/${BASENAME}.html
done
./generate_index.py
