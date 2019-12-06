class Song:
    def __init__(self, full_path, name, hash):
        self.full_path = full_path
        self.name = name
        self.hash = hash

    def __eq__(self, other):
        return self.full_path == other.full_path and \
               self.name == other.name and \
               self.hash == other.hash

    def __hash__(self):
        return hash(tuple(sorted(self.__dict__.items())))
