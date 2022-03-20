from connection import Connection
from engine import Engine


def main():
    engine = Engine()
    conn = Connection(engine, debug=True)
    conn.start()


if __name__ == "__main__":
    main()
