import rpyc
# c = rpyc.connect("localhost", 18861)

print(rpyc.connect("localhost", 18861).root.hey_there())
# print(c.root.get_service_name())