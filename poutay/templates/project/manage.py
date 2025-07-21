import os
from poutay import main

if __name__ == "__main__":
    os.environ.setdefault("poutay_setting", "settings")
    main()
