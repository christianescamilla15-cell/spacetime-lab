#!/usr/bin/env python3
"""wg_keygen.py -- generate a WireGuard-compatible X25519 keypair.

WireGuard uses Curve25519 with base64-encoded keys.  This script
produces keys bit-compatible with `wg genkey | tee privkey | wg pubkey`
but without requiring the WireGuard CLI.

Keys are written to ~/.spacetime-bridge/ (outside the repo) with the
private key locked down.  The public key is printed so it can be
pasted into the VPS-side WireGuard config when that box comes online.

Usage:
    python .agent/_wrapper/wg_keygen.py                 # generate pc-client
    python .agent/_wrapper/wg_keygen.py --name vps      # generate vps-server keypair locally for testing
    python .agent/_wrapper/wg_keygen.py --show          # print existing public key without regenerating
"""
from __future__ import annotations

import argparse
import base64
import os
import stat
import sys
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

KEYS_DIR = Path.home() / ".spacetime-bridge"


def _priv_path(name: str) -> Path:
    return KEYS_DIR / f"wg-{name}-private.key"


def _pub_path(name: str) -> Path:
    return KEYS_DIR / f"wg-{name}-public.key"


def _meta_path(name: str) -> Path:
    return KEYS_DIR / f"wg-{name}.meta"


def _b64_key(raw: bytes) -> str:
    """WireGuard expects 32-byte keys encoded as standard base64."""
    return base64.b64encode(raw).decode("ascii")


def _windows_lock_file(path: Path) -> None:
    """Set Windows ACL so only the current user can read the private key."""
    import subprocess

    user = os.environ.get("USERNAME", "DANNY")
    try:
        subprocess.run(
            ["icacls", str(path), "/inheritance:r", "/grant:r", f"{user}:F"],
            check=False,
            capture_output=True,
        )
    except FileNotFoundError:
        pass


def generate(name: str, overwrite: bool = False) -> None:
    priv_p = _priv_path(name)
    pub_p = _pub_path(name)
    meta_p = _meta_path(name)

    if priv_p.exists() and not overwrite:
        print(f"ERROR: {priv_p} already exists. Pass --overwrite to regenerate.",
              file=sys.stderr)
        sys.exit(2)

    KEYS_DIR.mkdir(parents=True, exist_ok=True)

    priv = X25519PrivateKey.generate()
    pub = priv.public_key()

    priv_raw = priv.private_bytes(
        encoding=Encoding.Raw,
        format=PrivateFormat.Raw,
        encryption_algorithm=NoEncryption(),
    )
    pub_raw = pub.public_bytes(
        encoding=Encoding.Raw,
        format=PublicFormat.Raw,
    )

    priv_b64 = _b64_key(priv_raw)
    pub_b64 = _b64_key(pub_raw)

    priv_p.write_text(priv_b64 + "\n", encoding="ascii")
    pub_p.write_text(pub_b64 + "\n", encoding="ascii")

    if os.name == "posix":
        priv_p.chmod(stat.S_IRUSR | stat.S_IWUSR)  # 0o600
    else:
        _windows_lock_file(priv_p)

    import datetime as dt

    meta_p.write_text(
        f"name: {name}\n"
        f"generated_at: {dt.datetime.now(dt.timezone.utc).isoformat()}\n"
        f"hostname: {os.environ.get('COMPUTERNAME', os.environ.get('HOSTNAME', '?'))}\n",
        encoding="utf-8",
    )

    print(f"Generated WireGuard keypair: {name}")
    print(f"  private key  :  {priv_p}")
    print(f"  public key   :  {pub_p}")
    print(f"  meta         :  {meta_p}")
    print()
    print(f"Public key (paste into peer config):")
    print(f"  {pub_b64}")


def show(name: str) -> None:
    pub_p = _pub_path(name)
    if not pub_p.exists():
        print(f"ERROR: {pub_p} not found. Generate first.", file=sys.stderr)
        sys.exit(2)
    print(pub_p.read_text(encoding="ascii").strip())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default="pc-client",
                        help="keypair label (default: pc-client)")
    parser.add_argument("--overwrite", action="store_true",
                        help="regenerate even if keys exist")
    parser.add_argument("--show", action="store_true",
                        help="print existing public key and exit")
    args = parser.parse_args()

    if args.show:
        show(args.name)
        return 0

    generate(args.name, overwrite=args.overwrite)
    return 0


if __name__ == "__main__":
    sys.exit(main())
