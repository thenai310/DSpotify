import rpyc

c1 = rpyc.connect("localhost", 5555)
c1.root.call_hello()

c2 = rpyc.connect("localhost", 5556)
c2.root.call_hello()