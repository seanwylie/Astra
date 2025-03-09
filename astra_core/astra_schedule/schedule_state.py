"""Dynamically resolves schedule functions to avoid circular imports."""

def resolve_schedule_function(mode):
    """Returns the appropriate function for a given mode dynamically."""
    if mode == "dream":
        from astra_schedule.dream import start_dreaming
        return start_dreaming
    elif mode == "school":
        from astra_schedule.school import start_learning
        return start_learning
    elif mode == "play":
        from astra_schedule.play import start_playtime
        return start_playtime
    elif mode == "dinner":
        from astra_schedule.dinner import start_dinner_time
        return start_dinner_time
    elif mode == "sleep":
        from astra_schedule.sleep import start_sleeping
        return start_sleeping
    return None  # Default to None if mode isn't found
