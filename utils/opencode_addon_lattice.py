#!/usr/bin/env python3
import argparse
import base64
import getpass
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

HEADER = "OCADDON-BLOB-V1"


def fail(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def require_openssl() -> None:
    if shutil.which("openssl") is None:
        fail("openssl is required but not found in PATH")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Materialize files from an addon artifact.")
    parser.add_argument("--bundle", required=True, help="Artifact file path")
    parser.add_argument("--dest", required=True, help="Destination directory")
    parser.add_argument(
        "--password",
        default=None,
        help="Artifact password. If omitted, prompt interactively.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files in destination.",
    )
    return parser.parse_args()


def resolve_password(password_arg: str | None) -> str:
    if password_arg:
        return password_arg
    password = getpass.getpass("Artifact password: ")
    if not password:
        fail("password cannot be empty")
    return password


def parse_bundle(bundle_path: Path) -> tuple[dict[str, object], bytes]:
    lines = bundle_path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 3:
        fail("artifact format is invalid or truncated")
    if lines[0].strip() != HEADER:
        fail("artifact header mismatch")

    try:
        metadata = json.loads(lines[1])
    except json.JSONDecodeError as exc:
        fail(f"invalid artifact metadata: {exc}")

    payload_b64 = "".join(lines[2:]).strip()
    if not payload_b64:
        fail("artifact payload is missing")

    try:
        encrypted = base64.b64decode(payload_b64, validate=True)
    except Exception as exc:  # noqa: BLE001
        fail(f"artifact payload is not valid base64: {exc}")

    return metadata, encrypted


def decrypt_payload(encrypted: bytes, password: str) -> bytes:
    result = subprocess.run(
        [
            "openssl",
            "enc",
            "-d",
            "-aes-256-cbc",
            "-pbkdf2",
            "-salt",
            "-pass",
            f"pass:{password}",
        ],
        input=encrypted,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip()
        fail(f"decryption failed: {stderr or 'invalid password or corrupt artifact'}")
    return result.stdout


def safe_target(dest_root: Path, rel_path: str) -> Path:
    normalized = Path(rel_path)
    if normalized.is_absolute():
        fail(f"absolute path found in payload: {rel_path}")
    target = (dest_root / normalized).resolve()
    try:
        target.relative_to(dest_root)
    except ValueError:
        fail(f"unsafe path in payload: {rel_path}")
    return target


def main() -> None:
    args = parse_args()
    require_openssl()

    bundle_path = Path(args.bundle).expanduser().resolve()
    if not bundle_path.exists() or not bundle_path.is_file():
        fail(f"artifact file not found: {bundle_path}")

    password = resolve_password(args.password)
    metadata, encrypted = parse_bundle(bundle_path)

    payload_sha = metadata.get("payload_sha256")
    if not isinstance(payload_sha, str) or not payload_sha:
        fail("artifact metadata missing payload_sha256")

    payload_bytes = decrypt_payload(encrypted, password)
    actual_sha = hashlib.sha256(payload_bytes).hexdigest()
    if actual_sha != payload_sha:
        fail("payload checksum mismatch")

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"invalid payload format: {exc}")

    if payload.get("format") != "ocaddon.payload.v1":
        fail("unsupported payload format")

    files = payload.get("files")
    if not isinstance(files, list):
        fail("payload files list is invalid")

    dest_root = Path(args.dest).expanduser().resolve()
    dest_root.mkdir(parents=True, exist_ok=True)

    planned: list[tuple[Path, bytes, str]] = []
    conflicts: list[str] = []

    for item in files:
        if not isinstance(item, dict):
            fail("payload file entry is malformed")
        rel_path = item.get("path")
        size = item.get("size")
        expected_sha = item.get("sha256")
        data_b64 = item.get("data")

        if not isinstance(rel_path, str) or not rel_path:
            fail("payload file path is invalid")
        if not isinstance(size, int) or size < 0:
            fail(f"payload size is invalid for {rel_path}")
        if not isinstance(expected_sha, str) or len(expected_sha) != 64:
            fail(f"payload checksum is invalid for {rel_path}")
        if not isinstance(data_b64, str):
            fail(f"payload data is invalid for {rel_path}")

        try:
            raw = base64.b64decode(data_b64, validate=True)
        except Exception as exc:  # noqa: BLE001
            fail(f"payload data decode failed for {rel_path}: {exc}")

        if len(raw) != size:
            fail(f"payload size mismatch for {rel_path}")
        if hashlib.sha256(raw).hexdigest() != expected_sha:
            fail(f"payload checksum mismatch for {rel_path}")

        target = safe_target(dest_root, rel_path)
        if target.exists() and not args.force:
            conflicts.append(str(target))
        planned.append((target, raw, rel_path))

    if conflicts:
        fail(
            "destination has existing files; use --force to overwrite. First conflict: "
            + conflicts[0]
        )

    for target, raw, _ in planned:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)

    print(f"Restored files: {len(planned)}")
    print(f"Destination: {dest_root}")


if __name__ == "__main__":
    main()
