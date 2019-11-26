import rpyc

class NodeService(rpyc.Service):
    def __init__(self, id):
        self.other = None
        self.id = id

    def exposed_say_hello(self):
        print("hello I'm", self.id)

    def exposed_call_hello(self):
        print("calling hello!")
        self.exposed_say_hello()
        print("------------------")