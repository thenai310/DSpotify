# debugging small case (if True hash of songs is name, else is big hash)
DEBUG_MODE = True

# log of SIZE of DHT, one common choice is 160 (using each node SHA1 encryption)
LOG_LEN = 3

# SIZE of DHT
SIZE = 2 ** LOG_LEN

# len of succesor list, note that SUCC_LIST_LEN < SIZE
SUCC_LIST_LEN = 3

# timing of jobs
JOIN_NODES_TIME = 1
MAINTENANCE_JOBS_TIME = 1
DISTRIBUTE_SONGS_TIME = 7
SHOW_CURRENT_STATUS_TIME = 4

# directory of songs
SONGS_DIRECTORY = "./songs_small"

# how much time each chunk of song has (in miliseconds)
CHUNK_LENGTH = 500

# size of blocks (in bytes) for socket comunication
BLOCK_SIZE = 1024
