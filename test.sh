#! /bin/sh
ls -1 tmp/access.log* | head -n3 | xargs -P1 docker-compose run log2html ./display_log.py --threads 4  > result.html
