from Backend.Testing.rpyc.ABexample.Node import NodeService
import rpyc

serverB = rpyc.ThreadedServer(NodeService("node B"), port = 5556)
serverB.start()