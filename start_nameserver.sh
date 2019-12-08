export PYRO_SERIALIZERS_ACCEPTED=serpent,json,marshal,pickle
# now you have optional value, default is 127.0.0.1
pyro4-ns -n ${1-127.0.0.1}