from threading import Thread
import time


class MyException(Exception):
    pass


stop_thread = False


def show_cur_time():
    while True:
        print(time.asctime())
        time.sleep(1)


def play_audio():
    def check_stop_cond():
        while True:
            global stop_thread

            if stop_thread:
                break

    t = Thread(target=check_stop_cond)
    t.start()

    print("playing audio 20 secs")

    for i in range(20):
        time.sleep(1)

        if not t.is_alive():
            print("Stopping.....")
            break


t = Thread(target=play_audio)
t.start()

q = Thread(target=show_cur_time)
q.start()

time.sleep(7)

print("Ok 7s have passed stopping the thread")
stop_thread = True
