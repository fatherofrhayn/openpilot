#!/usr/bin/env python3
import os
import sys

"""
Inject .venv site-packages into sys.path (for offline signing).
"""
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
venv_lib = os.path.join(project_root, '.venv', 'lib')
if os.path.isdir(venv_lib):
    for entry in os.listdir(venv_lib):
        if entry.startswith('python'):
            venv_site = os.path.join(venv_lib, entry, 'site-packages')
            if os.path.isdir(venv_site) and venv_site not in sys.path:
                sys.path.insert(0, venv_site)
                break

import struct
import hashlib
"""
Import RSA from Crypto or Cryptodome.
"""
try:
    from Crypto.PublicKey import RSA
except ImportError:
    try:
        from Cryptodome.PublicKey import RSA
    except ImportError:
        sys.stderr.write("Error: Crypto or Cryptodome missing for RSA import\n")
        sys.exit(1)
import binascii

# increment this to make new hardware not run old versions
VERSION = 2

if __name__ == "__main__":
  with open(sys.argv[3]) as k:
    rsa = RSA.importKey(k.read())

  with open(sys.argv[1], "rb") as f:
    dat = f.read()

  print("signing", len(dat), "bytes")

  with open(sys.argv[2], "wb") as f:
    if os.getenv("SETLEN") is not None:
      # add the version at the end
      dat += b"VERS" + struct.pack("I", VERSION)
      # add the length at the beginning
      x = struct.pack("I", len(dat)) + dat[4:]
      # mock signature of dat[4:]
      dd = hashlib.sha1(dat[4:]).digest()
    else:
      x = dat
      dd = hashlib.sha1(dat).digest()

    print("hash:", str(binascii.hexlify(dd), "utf-8"))
    dd = b"\x00\x01" + b"\xff" * 0x69 + b"\x00" + dd
    rsa_out = pow(int.from_bytes(dd, byteorder='big', signed=False), rsa.d, rsa.n)
    sig = (hex(rsa_out)[2:].rjust(0x100, '0'))
    x += binascii.unhexlify(sig)
    f.write(x)
