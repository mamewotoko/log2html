#! /usr/bin/env python3

import argparse
import copy
import gzip
import json
import logging
import random
import sys
import re
import time
from dateutil.parser import parse

from concurrent.futures import ProcessPoolExecutor
from difflib import SequenceMatcher

from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import select_autoescape

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


def get_time_from_log(line):
    match = re.search('\[(.*?)\]', line)
    if match is not None:
        dt = parse(match.group(1), fuzzy=True)
        epoch = time.mktime(dt.timetuple())
        return epoch
    m = re.match('(\d{2}):(\d{2}):(\d{2})', line)
    if m is not None:
        hour = int(m.group(1))
        minute = int(m.group(2))
        seconds = int(m.group(3))
        sec_from_sod = 60 * 60 * hour + 60 * minute + seconds
        return sec_from_sod
    return None


def get_ipaddress_from_log(line):
    match = re.search('^([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+) ', line)
    if match is not None:
        return match.group(1)
    return None


def main():
    parser = argparse.ArgumentParser(description='log viewer')
    parser.add_argument('--threads', type=int, default=1, help='number of threads')
    parser.add_argument('--thres', type=float, default=0.8, help='sim thres')
    # unused
    parser.add_argument('--output-context', type=argparse.FileType('w'), nargs='?')
    parser.add_argument('files', nargs='*', help='path of log file')

    args = parser.parse_args()
    thres = args.thres

    log_lines = []
    for log in args.files:
        # logger.debug("processing %s" % log)
        if log.endswith(".gz"):
            with gzip.open(log, "rt", encoding="utf-8") as f:
                log_lines += f.read().splitlines()
        else:
            if log == '-':
                log_lines += sys.stdin.read().splitlines()
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

    context = {}
    context['comps'] = []
    for comp_id in comp_group.keys():
        color = random.randint(0, 0xFFFFFF)
        red = (color >> 8) & 0xFF
        green = (color >> 4) & 0xFF
        blue = color & 0xFF
        if 186 < red * 0.299 + green * 0.587 + blue * 0.114:
            fg_color = "#000000"
        else:
            fg_color = "#ffffff"
        context['comps'].append(dict(comp_id=comp_id,
                                     comp_bg_color="#%06x" % color,
                                     comp_fg_color=fg_color))

    context['num_comps'] = len(context['comps'])
    context['num_lines'] = nlines
    context['log_lines'] = []

    start_time = None
    for i in range(0, len(log_lines)):
        line = log_lines[i]
        log_time = get_time_from_log(line)
        if start_time is None:
            start_time = log_time
        if log_time is None or start_time is None:
            delta = 0
        else:
            delta = log_time - start_time
        context['log_lines'].append(dict(log_id=i,
                                         comp_id=comp[i],
                                         log_time=log_time,
                                         delta=delta,
                                         content=line))

    env = Environment(
        loader=PackageLoader('display_log', 'templates'),
        autoescape=select_autoescape(['html'])
    )

    template = env.get_template("template.html")
    print(template.render(context))
    if args.output_context is not None:
        args.output_context.write(json.dumps(context, indent=2))


if __name__ == '__main__':
    main()
