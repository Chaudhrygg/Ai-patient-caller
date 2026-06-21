from dotenv import load_dotenv
load_dotenv()

import sys
sys.argv = ["main.py", "--scenario", "0", "--delay", "120"]
from main import main
main()
