import time

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

