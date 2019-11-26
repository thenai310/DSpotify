import sys
import Pyro4

# ns = Pyro4.locateNS()
#
# for x, y in ns.list().items():
#     print(x, y)

sys.excepthook = Pyro4.util.excepthook

A = Pyro4.Proxy("PYRONAME:5")
B = Pyro4.Proxy("PYRONAME:185476644570504859220518713321016314985921260812")

A.debug()
B.debug()