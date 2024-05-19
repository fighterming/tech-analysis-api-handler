import os
import uvicorn
import argparse
import socket
import time

HOST = "localhost"
PORT = 8000

filedir = os.path.dirname(os.path.realpath(__file__))
ENV_FILE = os.path.join(filedir, ".env")


class utils:
    def retry(times, exceptions):
        """
        Retry Decorator
        Retries the wrapped function/method `times` times if the exceptions listed
        in ``exceptions`` are thrown
        :param times: The number of times to repeat the wrapped function/method
        :type times: Int
        :param Exceptions: Lists of exceptions that trigger a retry attempt
        :type Exceptions: Tuple of Exceptions
        """

        def decorator(func):
            def newfn(*args, **kwargs):
                attempt = 0
                while attempt < times:
                    try:
                        return func(*args, **kwargs)
                    except exceptions:
                        print(
                            "Exception thrown when attempting to run %s, attempt "
                            "%d of %d" % (func, attempt, times)
                        )
                        attempt += 1
                return func(*args, **kwargs)

            return newfn

        return decorator


def main():
    parser = argparse.ArgumentParser(
        description="""Manage the usage or PY_TradeD api with FastAPI""",
    )
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    @utils.retry(times=5, exceptions=ConnectionError)
    def run():
        print("initializing: ")
        result = sock.connect_ex((HOST, PORT))
        print(result)
        if result == 0:
            raise ConnectionError()
        else:
            sock.close()
            time.sleep(0.5)
            uvicorn.run(
                "tech_analysis_api_handler.main:app", port=PORT, env_file=ENV_FILE
            )

    run()


if __name__ == "__main__":

    main()
