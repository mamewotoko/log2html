#! /bin/sh
mkdir -p result

for FILENAME in $*; do
    BASENAME=$(basename $FILENAME)

    zcat -f $FILENAME | docker-compose run --rm log2html ./display_log.py --threads 2 - > result/${BASENAME}.html
done
