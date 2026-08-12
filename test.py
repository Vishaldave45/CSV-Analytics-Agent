from functools import wraps


def retry(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        for _ in range(3):
            try:
                return func(*args, **kwargs)
            except Exception:
                pass

        raise RuntimeError("Failed after 3 attempts")

    return wrapper

@retry
def fetch_data():
    raise ConnectionError("Server unavailable")


fetch_data()