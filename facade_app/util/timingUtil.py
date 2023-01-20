import time, os
from functools import wraps


def timeit(func):
    @wraps(func)
    def timeit_wrapper(*args, **kwargs):

        logLevel = os.getenv("LOG_LEVEL", "")
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        end_time = time.perf_counter()
        total_time = end_time - start_time
        if logLevel == "BENCHMARK":
            print(f"Function {func.__name__} Took {total_time:.4f} seconds", flush=True)
        return result

    return timeit_wrapper
