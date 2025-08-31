import shutil
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from utils.logger import get_logger


logger = get_logger(__name__)


def main():
    shutil.copy2("app/db/minutes.db", "app/db/setagaya.db")
    logger.info("Copied db/minutes.db -> db/setagaya.db")


if __name__ == "__main__":
    main()
