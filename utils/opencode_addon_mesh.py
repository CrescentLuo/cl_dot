#!/usr/bin/env python3
import argparse
import base64
import getpass
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HEADER = "OCADDON-BLOB-V1"
REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_DIR = REPO_ROOT / "addons"
DEFAULT_BUNDLE_NAME = "mesh.addon"


def fail(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    sys.exit(1)


def require_openssl() -> None:
    if shutil.which("openssl") is None:
        fail("openssl is required but not found in PATH")


def run_git(repo_path: Path, args: list[str]) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo_path), *args],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.strip() or "unknown git error"
        fail(f"git command failed: {stderr}")
    return result.stdout


def resolve_git_root(source: Path) -> Path:
    output = run_git(source, ["rev-parse", "--show-toplevel"]).strip()
    if not output:
        fail("unable to resolve git repository root")
    return Path(output).resolve()


def tracked_files(repo_root: Path) -> list[str]:
    output = run_git(repo_root, ["ls-files", "-z"])
    parts = output.split("\0")
    return sorted([p for p in parts if p])


def build_payload(repo_root: Path, rel_paths: list[str]) -> tuple[bytes, str, int, int]:
    files: list[dict[str, object]] = []
    total_bytes = 0

    for rel_path in rel_paths:
        abs_path = repo_root / rel_path
        if not abs_path.exists() or abs_path.is_dir():
            continue

        raw = abs_path.read_bytes()
        total_bytes += len(raw)
        files.append(
            {
                "path": rel_path,
                "size": len(raw),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "data": base64.b64encode(raw).decode("ascii"),
            }
        )

    payload = {
        "format": "ocaddon.payload.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "repo_root": str(repo_root),
        "file_count": len(files),
        "files": files,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    digest = hashlib.sha256(payload_bytes).hexdigest()
    return payload_bytes, digest, len(files), total_bytes


def encrypt_payload(payload_bytes: bytes, password: str) -> bytes:
    result = subprocess.run(
        ["openssl", "enc", "-aes-256-cbc", "-pbkdf2", "-salt", "-pass", f"pass:{password}"],
        input=payload_bytes,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        stderr = result.stderr.decode("utf-8", errors="replace").strip() or "openssl failed"
        fail(f"encryption failed: {stderr}")
    return result.stdout


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create an addon artifact from tracked files in a git repository."
    )
    parser.add_argument(
        "--source",
        default=".",
        help="Path to source repository (must be a git repo). Default: current directory",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for artifact output. Default: cl_dot/addons",
    )
    parser.add_argument(
        "--name",
        default=DEFAULT_BUNDLE_NAME,
        help=f"Artifact file name. Default: {DEFAULT_BUNDLE_NAME}",
    )
    parser.add_argument(
        "--password",
        default=None,
        help="Artifact password. If omitted, prompt interactively.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite output file if it already exists.",
    )
    return parser.parse_args()


def resolve_password(password_arg: str | None) -> str:
    if password_arg:
        return password_arg

    first = getpass.getpass("Artifact password: ")
    second = getpass.getpass("Confirm password: ")
    if first != second:
        fail("passwords do not match")
    if not first:
        fail("password cannot be empty")
    return first


def main() -> None:
    args = parse_args()
    require_openssl()

    source_path = Path(args.source).expanduser().resolve()
    if not source_path.exists():
        fail(f"source path not found: {source_path}")

    repo_root = resolve_git_root(source_path)
    rel_paths = tracked_files(repo_root)
    if not rel_paths:
        fail("no tracked files found in source repository")

    payload_bytes, payload_sha, file_count, total_bytes = build_payload(repo_root, rel_paths)
    if file_count == 0:
        fail("source repository has no regular tracked files to include")

    password = resolve_password(args.password)
    encrypted = encrypt_payload(payload_bytes, password)

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / args.name

    if output_path.exists() and not args.force:
        fail(f"output already exists: {output_path} (use --force to overwrite)")

    metadata = {
        "format": "ocaddon.bundle.v1",
        "cipher": "aes-256-cbc",
        "kdf": "pbkdf2",
        "payload_sha256": payload_sha,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_repo": str(repo_root),
    }
    encoded = base64.b64encode(encrypted).decode("ascii")

    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{HEADER}\n")
        handle.write(json.dumps(metadata, separators=(",", ":"), ensure_ascii=True))
        handle.write("\n")
        handle.write(encoded)
        handle.write("\n")

    print(f"Artifact written: {output_path}")
    print(f"Tracked files: {file_count}")
    print(f"Total bytes: {total_bytes}")


if __name__ == "__main__":
    main()