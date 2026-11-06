"""Download the pinned AADR v66.p1 1240K annotation file and check its md5."""
import hashlib
import sys
from pathlib import Path

import requests

BASE = "https://dataverse.harvard.edu/api/access/datafile/"
ANNO_ID, MD5_ID = 13994515, 13995422
ANNO_NAME = "v66.p1_1240K.aadr.PUB.anno"
OUT = Path("data/raw")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    md5s = requests.get(BASE + str(MD5_ID), timeout=60).text
    # the hosted md5 file has a leading line-number column, so take the token before the filename
    expected = next(l.split()[-2] for l in md5s.splitlines() if l.split()[-1] == ANNO_NAME)
    body = requests.get(BASE + str(ANNO_ID), timeout=300).content
    got = hashlib.md5(body).hexdigest()
    if got != expected:
        sys.exit(f"md5 mismatch: {got} != {expected}")
    (OUT / ANNO_NAME).write_bytes(body)
    print(f"saved {ANNO_NAME} ({len(body)} bytes, md5 ok)")


if __name__ == "__main__":
    main()
