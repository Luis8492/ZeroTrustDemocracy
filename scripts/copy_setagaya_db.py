import shutil


def main():
    shutil.copy2("app/db/minutes.db", "app/db/setagaya.db")
    print("Copied db/minutes.db -> db/setagaya.db")


if __name__ == "__main__":
    main()
