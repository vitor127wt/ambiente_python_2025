from pathlib import Path

main_file = Path("main_teste.py")

main = """import os
from dotenv import load_dotenv

def main() -> None:
    load_dotenv()
    print(os.environ["GREETINGS"])

if __name__ == "__main__":
    main()"""

main_file.write_text(data=main, encoding="utf-8")
