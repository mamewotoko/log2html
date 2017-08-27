#! /usr/bin/env python3

import argparse
import copy
import gzip
import html
import logging
import random

from concurrent.futures import ProcessPoolExecutor
from difflib import SequenceMatcher


logger = logging.getLogger("display_log")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
# add formatter to ch
ch.setFormatter(formatter)
logger.addHandler(ch)


def sim(a, b):
    """similarity of log (text data) using difflib.SequenceMacher."""
    return SequenceMatcher(None, a, b).ratio()


def cluster_lines(log_id_list, log_lines, thres):
    comp_group = {}
    for i in log_id_list:
        line = log_lines[i]
        # if i % 1000 == 0:
        #     logger.debug("processsing %d/%d" % (i, len(log_lines)))
        for k in comp_group.keys():
            first = comp_group[k][0]
            if thres <= sim(log_lines[first], line):
                comp_group[k].append(i)
                break
            last = comp_group[k][-1]
            if thres <= sim(log_lines[last], line):
                comp_group[k].append(i)
                break
        else:
            comp_group[len(comp_group.keys())] = [i]
    return comp_group


def merge_cluster(a, b, log_lines, thres):
    result = copy.deepcopy(a)
    for b_comp_id in sorted(b.keys()):
        bfirst = b[b_comp_id][0]
        bline = log_lines[bfirst]

        for a_comp_id in sorted(a.keys()):
            afirst = a[a_comp_id][0]
            aline = log_lines[afirst]

            if thres <= sim(aline, bline):
                # logger.debug("extend %d %d" % (a_comp_id, b_comp_id))
                result[a_comp_id].extend(b[b_comp_id])
                break
            alast = a[a_comp_id][-1]
            aline = log_lines[alast]

            if thres <= sim(aline, bline):
                # logger.debug("extend %d %d" % (a_comp_id, b_comp_id))
                result[a_comp_id].extend(b[b_comp_id])
                break
        else:
            next_id = 0
            if 0 < len(a.keys()):
                next_id = max(result.keys()) + 1
            # logger.debug("add %d %d" % (next_id, b_comp_id))
            result[next_id] = b[b_comp_id]
    return result


def main():
    parser = argparse.ArgumentParser(description='log viewer')
    parser.add_argument('--threads', type=int, default=1, help='number of threads')
    parser.add_argument('--thres', type=float, default=0.8, help='sim thres')
    parser.add_argument('files', nargs='*', help='path of log file')

    args = parser.parse_args()

    thres = args.thres

    log_lines = []
    for log in args.files:
        logger.debug("processing %s" % log)
        if log.endswith(".gz"):
            with gzip.open(log, "rt", encoding="utf-8") as f:
                log_lines += f.read().splitlines()
        else:
            with open(log, "r") as f:
                log_lines += f.read().splitlines()

    nlines = len(log_lines)

    with ProcessPoolExecutor(max_workers=args.threads) as executor:
        chunksize = 1000
        clusters = []
        for i in range(0, nlines // chunksize):
            future = executor.submit(cluster_lines,
                                     range(i * chunksize, (i + 1) * chunksize),
                                     log_lines,
                                     thres)
            clusters.append(future)
        remain = nlines % chunksize
        if 0 < remain:
            future = executor.submit(cluster_lines,
                                     range(nlines - remain, nlines),
                                     log_lines,
                                     thres)
            clusters.append(future)

        count = 0
        while(1 < len(clusters)):
            fst = clusters.pop(0)
            # logger.debug("fst %d: %s" % (count, json.dumps(fst.result(), indent=2)))

            snd = clusters.pop(0)
            # logger.debug("snd %d: %s" % (count, json.dumps(snd.result(), indent=2)))

            merged = executor.submit(merge_cluster, fst.result(), snd.result(), log_lines, thres)
            # logger.debug("merged %d: %s" % (count, json.dumps(merged.result(), indent=2)))
            clusters.append(merged)
            count += 1

        # logger.debug("last: %s" % clusters)
        comp_group = clusters[0].result()

    comp = {}
    for i in range(0, max(comp_group.keys()) + 1):
        for m in comp_group[i]:
            comp[m] = i

    random.seed(a=1234)
    colors = {}
    for comp_id in comp_group.keys():
        colors[comp_id] = "#%06x" % random.randint(0, 0xFFFFFF)

    HEAD = """<html lang="ja">
<head>
<meta charset="utf-8">
<title>Log</title>
<script
  src="https://code.jquery.com/jquery-3.2.1.min.js"
  integrity="sha256-hwg4gsxgFZhOsEEamdOYGBf13FyQuiTwlAQgxVSNgt4="
   crossorigin="anonymous"></script>
<link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/1.10.15/css/jquery.dataTables.css">
<script type="text/javascript" charset="utf8" src="https://cdn.datatables.net/1.10.15/js/jquery.dataTables.js"></script>
<script>
  $(function(){
    $("#table").DataTable( {'paging': false });
  });
</script>
<style type="text/css">
    """

    print(HEAD)
    for comp_id in colors.keys():
        print(""".comp%s { background-color: %s !important; }""" % (comp_id, colors[comp_id]))

    print("""
    </style>
    </head>
    <body>
    comp %d/lines %d
    <table class="table">
    <thead>
    <tr><th>line</th><th>comp</th><th>log</th></tr>
    </thead>
    <tbody>
    """ % (len(comp_group.keys()), len(log_lines)))

    for i in range(0, nlines):
        comp_id = comp[i]
        log = html.escape(log_lines[i])
        print("""<tr class="comp%s" id="%d"><td>%d</td><td>%s</td><td class="log" data-col="log">%s</td></tr>""" % (comp_id, i, i, comp_id, log))

    print("""</tbody></table></body></html>""")


if __name__ == '__main__':
    main()
