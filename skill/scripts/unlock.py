#!/usr/bin/env python3
"""Decrypt a password-protected PDF locally (no network, no API).

Usage: unlock.py IN.pdf OUT.pdf PASSWORD

Tries pypdf, then the qpdf CLI. Writes an unencrypted copy to OUT.pdf.
Exit codes: 0 ok (also when IN was not encrypted — OUT is still written),
2 wrong password, 3 no decryption tool available, 1 other error.
"""
import shutil
import subprocess
import sys
from pathlib import Path


def unlock_with_pypdf(src, dst, password):
    from pypdf import PdfReader, PdfWriter

    reader = PdfReader(src)
    if not reader.is_encrypted:
        shutil.copyfile(src, dst)
        return "not_encrypted"
    if not reader.decrypt(password):
        print("error: wrong password", file=sys.stderr)
        sys.exit(2)
    writer = PdfWriter(clone_from=reader)
    with open(dst, "wb") as f:
        writer.write(f)
    return "decrypted"


def unlock_with_qpdf(src, dst, password):
    if not shutil.which("qpdf"):
        return None
    result = subprocess.run(
        ["qpdf", f"--password={password}", "--decrypt", str(src), str(dst)],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        return "decrypted"
    if "invalid password" in (result.stderr or "").lower():
        print("error: wrong password", file=sys.stderr)
        sys.exit(2)
    print(f"error: qpdf failed: {result.stderr.strip()}", file=sys.stderr)
    sys.exit(1)


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    src, dst, password = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
    if not src.is_file():
        sys.exit(f"error: not found: {src}")

    try:
        status = unlock_with_pypdf(src, dst, password)
    except ImportError:
        status = unlock_with_qpdf(src, dst, password)
        if status is None:
            print("error: neither pypdf (pip install pypdf) nor qpdf "
                  "(brew install qpdf) is available", file=sys.stderr)
            sys.exit(3)

    # sanity check: output must open without a password
    try:
        from pypdf import PdfReader
        assert not PdfReader(dst).is_encrypted
    except ImportError:
        pass

    print(f"{status}: {dst}")


if __name__ == "__main__":
    main()
