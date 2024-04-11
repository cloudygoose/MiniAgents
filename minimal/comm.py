import time
import os, json

import logging
logger = logging.getLogger()

class Comm:

    def __init__(self, args):
        self.args = args
        self.comm_path = args.comm_path
        self.next_idx = 0
        self.responded = True

    def waitAndGetNextMessage(self, sleep_interval = 0.1):
        assert(self.responded); args = self.args;
        fn = args.comm_path + '/comm_front_req_{}.json'.format(self.next_idx)

        logger.info('[comm] waiting and loading {} with sleep_interval {}...'.format(fn, sleep_interval))
        while True:
            if os.path.isfile(fn):
                logger.info('[comm] found!')
                with open(fn) as f:
                    ld = json.load(f)
                logger.info('[comm] message: %s', str(ld))
                break
            time.sleep(sleep_interval);

        self.responded = False
        return ld

    def respondMessage(self, rd):
        assert(not self.responded); args = self.args;

        fn = args.comm_path + '/comm_back_res_{}.json'.format(self.next_idx)
        assert(not os.path.isfile(fn))

        with open(fn, 'w', encoding='utf-8') as f:
            json.dump(rd, f, ensure_ascii=False, indent=4)
        self.next_idx += 1;
        self.responded = True;
