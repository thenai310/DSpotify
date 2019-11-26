import rpyc

class MyService(rpyc.Service):
    # def on_connect(self, conn):
    #     pass
    #
    # def on_disconnect(self, conn):
    #     pass

    def exposed_get_answer(self):
        return 42

    def exposed_hey_there(self):
        print("calling from inside", self.exposed_get_answer())
        return "hi there!"

    exposed_x = 5

t = rpyc.ThreadedServer(MyService, port=18861)
t.start()