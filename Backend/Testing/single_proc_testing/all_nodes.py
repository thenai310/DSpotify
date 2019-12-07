from Backend.Testing.single_proc_testing.Node_single_process import *
from timeloop import Timeloop
from datetime import timedelta
import time
import random

random.seed(123)

a = Node(Utils.randomIp(), Utils.randomPort(), 2)
b = Node(Utils.randomIp(), Utils.randomPort(), 3)
c = Node(Utils.randomIp(), Utils.randomPort(), 1)
d = Node(Utils.randomIp(), Utils.randomPort(), 0)

a.join(b)
c.join(b)
d.join(b)

tl = Timeloop()

@tl.job(timedelta(seconds=2))
def debug_all():
    a.debug()
    b.debug()
    c.debug()
    d.debug()
    print("debugging every node, time : {}".format(time.ctime()))

@tl.job(timedelta(seconds=1))
def refresh():
    a.fix_to()
    a.stabilize()

    b.fix_to()
    b.stabilize()

    c.fix_to()
    c.stabilize()

    d.fix_to()
    d.stabilize()

    # print("finished refreshing, time : {}".format(time.ctime()))

tl.start(block=True)