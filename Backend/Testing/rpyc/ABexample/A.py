from Backend.Testing.rpyc.ABexample.Node import NodeService
import rpyc

serverA = rpyc.ThreadedServer(NodeService("node A"), port = 5555)
serverA.start()