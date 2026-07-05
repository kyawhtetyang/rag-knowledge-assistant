from src.db import init_db
from src.ingest import ingest_default_docs


if __name__ == '__main__':
    init_db()
    result = ingest_default_docs()
    print(result)
