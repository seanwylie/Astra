import time
from astra_schedule.dream import start_dreaming
from astra_schedule.school import start_learning
from astra_schedule.play import start_playtime
from astra_schedule.dinner import start_dinner_time
from astra_schedule.sleep import start_sleeping

def astra_schedule():
    """Manages Astra's daily routine and switches between states."""
    while True:
        current_hour = time.localtime().tm_hour
        
        if is_dream_time(current_hour):
            start_dreaming()
        elif is_dinner_time(current_hour):
            start_dinner_time()
        elif is_learning_time(current_hour):
            start_learning()
        elif is_playtime(current_hour):
            start_playtime()
        else:
            start_sleeping()

def is_dream_time(hour): return 3 <= hour < 7
def is_dinner_time(hour): return 18 <= hour < 19
def is_learning_time(hour): return 7 <= hour < 18 or 19 <= hour < 22
def is_playtime(hour): return 22 <= hour < 23
