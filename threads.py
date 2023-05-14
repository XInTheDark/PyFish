import threading

STOP_SEARCH = False

def init():
    global STOP_SEARCH
    STOP_SEARCH = False

def stop_search():
    global STOP_SEARCH
    STOP_SEARCH = True
    
def stopped():
    return STOP_SEARCH


def set_time_limit(secs: float):
    threading.Timer(secs, stop_search).start()