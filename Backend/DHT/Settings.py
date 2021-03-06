# debugging small case (if True hash of songs is name of the song
# please note that in this case NAME OF SONG MUST BE INTEGER,
# else is big hash)
DEBUG_MODE = True

# log of SIZE of DHT, if not DEBUG MODE you should put 160 one common choice is 160 (using each node SHA1 encryption)
LOG_LEN = 4

if not DEBUG_MODE:
    LOG_LEN = 160

# SIZE of DHT
SIZE = 2 ** LOG_LEN

# len of successor list, note that SUCC_LIST_LEN < SIZE
SUCC_LIST_LEN = LOG_LEN

# timing of jobs
JOIN_NODES_TIME = 1
MAINTENANCE_JOBS_TIME = 2
DISTRIBUTE_SONGS_TIME = 7
SHOW_CURRENT_STATUS_TIME = 4

# how much time each chunk of song has (in miliseconds),
# for client streaming
CHUNK_LENGTH_CLIENT = 100

# how much time each chunk of song has (in miliseconds),
# for server file transfer
CHUNK_LENGTH_SERVER = 30000

THREADPOOL = 1000