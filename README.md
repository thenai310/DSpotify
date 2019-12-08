## DSpotify

### To run the Chord implementation:
- Install the dependencies in requirements.txt

- First of all start Pyro4 name server, you do this executing from a terminal the bash file start_nameserver.sh
You can specify as a parameter the ip of the name server, default is 127.0.0.1

- Check configuration file ./Backend/Settings.py for setting variables for DHT

- Use Node.py script to start a Node this can be found in the Node class.
You use the script the following way open a terminal and go to the root
of the project folder, then execute:

    python3 -m Backend.DHT.Node
    
    These will create/start the node, start a socket on the node, and the maintenance jobs
    will start automatically.

Please check --help option of the command for more information.