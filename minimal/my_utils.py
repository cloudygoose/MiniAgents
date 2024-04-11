import time
import os

import logging
logger = logging.getLogger()


def helper_clear_path(args):
    logger.info("Attention, will clear backend json files in path {}, wating 2 second...".format(args.path))
    time.sleep(2)
    for f in os.listdir(args.path):
        if (not f.endswith(".json")) or (not f.startswith("backend")):
            continue
        os.remove(os.path.join(args.path, f))

    if args.online:
        logger.info("Attention, will clear all json files in comm_path {}, wating 2 second...".format(args.comm_path))
        time.sleep(2)
        for f in os.listdir(args.comm_path):
            if (not f.endswith(".json")):
                continue
            os.remove(os.path.join(args.comm_path, f))

class MyTimer:

    def __init__(self, name = None, do_print = True):
        self.name = name
        self.do_print = do_print

    def __enter__(self):
        self.tstart = time.time()

    def __exit__(self, type, value, traceback):
        time_elapse = time.time() - self.tstart
        if self.do_print:
            if self.name:
                print('[%s]' % self.name,)
            print('Elapsed: %s' % (time_elapse))

class MyStruct(object):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)
