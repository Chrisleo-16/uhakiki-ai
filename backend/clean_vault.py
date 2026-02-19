#!/usr/bin/env python3
"""
Sovereign Vault Cleanup Script
Removes sovereign_vault.db and ALL related Milvus-Lite artifacts including:
  - .db files
  - .lock files
  - .sock Unix socket files (kills the holding process first)
  - WAL files (-shm, -wal)
  - /tmp socket files created by milvus-lite

Usage:
    python clean_vault.py              # dry run — shows what would be deleted
    python clean_vault.py --confirm    # actually deletes everything
"""

import os
import sys
import shutil
import glob
import stat
import subprocess

# ── Patterns to target ─────────────────────────────────────────────────────────
VAULT_PATTERNS = [
    "./sovereign_vault.db",
    "./sovereign_vault.db.lock",
    "./.sovereign_vault.db.lock",
    "./sovereign_vault.db-shm",
    "./sovereign_vault.db-wal",
    "./milvus_data",
    "./milvus.log",
    "./.milvus*",
]

SEARCH_DIRS     = [".", "./backend", "./app", "/tmp"]
SEARCH_KEYWORDS = ["sovereign_vault", "milvus_vault", "student_records"]


def find_all_vault_files() -> list:
    """Find every vault artifact — files, dirs, and socket files."""
    found = []

    # Pattern-based
    for pattern in VAULT_PATTERNS:
        for m in glob.glob(pattern, recursive=True):
            if os.path.exists(m) or stat.S_ISSOCK(os.stat(m).st_mode if os.path.exists(m) else 0):
                if m not in found:
                    found.append(m)

    # Recursive search
    for search_dir in SEARCH_DIRS:
        if not os.path.exists(search_dir):
            continue
        for root, dirs, files in os.walk(search_dir):
            dirs[:] = [d for d in dirs if d not in (".venv", "venv", "node_modules", ".git")]
            for filename in files:
                if any(kw in filename for kw in SEARCH_KEYWORDS):
                    full_path = os.path.join(root, filename)
                    if full_path not in found:
                        found.append(full_path)

    return found


def get_pid_holding_socket(sock_path: str) -> list:
    """Return list of PIDs holding a socket file open (Linux only)."""
    try:
        result = subprocess.run(
            ["fuser", sock_path],
            capture_output=True, text=True
        )
        pids = result.stdout.strip().split()
        return [int(p) for p in pids if p.strip().isdigit()]
    except Exception:
        return []


def kill_process(pid: int) -> bool:
    """Kill a process by PID."""
    try:
        import signal
        os.kill(pid, signal.SIGTERM)
        print(f"  🔪 Sent SIGTERM to PID {pid}")
        return True
    except ProcessLookupError:
        return True  # already dead
    except PermissionError:
        print(f"  ❌ No permission to kill PID {pid} — try running with sudo")
        return False


def delete_path(path: str) -> bool:
    """Delete a file, directory, or socket file."""
    try:
        if not os.path.exists(path):
            # Might be a dead socket — try removing anyway
            try:
                os.unlink(path)
                print(f"  ✅ Removed dead socket: {path}")
                return True
            except Exception:
                return True  # already gone

        path_stat = os.stat(path)

        # Handle Unix socket files
        if stat.S_ISSOCK(path_stat.st_mode):
            pids = get_pid_holding_socket(path)
            if pids:
                print(f"  ⚠️  Socket held by PID(s): {pids}")
                for pid in pids:
                    kill_process(pid)
            os.unlink(path)
            print(f"  ✅ Removed socket:        {path}")
            return True

        # Handle regular files and symlinks
        elif os.path.isfile(path) or os.path.islink(path):
            os.remove(path)
            size_kb = path_stat.st_size / 1024
            print(f"  ✅ Deleted file:          {path}  ({size_kb:.1f} KB)")
            return True

        # Handle directories
        elif os.path.isdir(path):
            shutil.rmtree(path)
            print(f"  ✅ Deleted directory:     {path}")
            return True

    except PermissionError:
        print(f"  ❌ Permission denied:     {path}  (try sudo)")
        return False
    except Exception as e:
        print(f"  ❌ Failed:                {path}  ({e})")
        return False

    return False


def describe_path(path: str) -> str:
    """Human-readable description of a path for dry-run output."""
    try:
        s = os.stat(path)
        if stat.S_ISSOCK(s.st_mode):
            return "  [SOCKET — will kill holding process]"
        elif os.path.isdir(path):
            return "  [DIRECTORY]"
        else:
            return f"  ({s.st_size / 1024:.1f} KB)"
    except Exception:
        return "  [unknown]"


def main():
    confirm = "--confirm" in sys.argv

    print("=" * 62)
    print("  Sovereign Vault Cleanup")
    print("=" * 62)

    found = find_all_vault_files()

    if not found:
        print("\n✅ Nothing to clean — vault is already clear.\n")
        return

    print(f"\nFound {len(found)} artifact(s):\n")
    for f in found:
        print(f"  • {f}{describe_path(f)}")

    if not confirm:
        print("\n⚠️  Dry run — nothing deleted.")
        print("    Run with --confirm to delete:\n")
        print("    python clean_vault.py --confirm\n")
        return

    print("\nCleaning...\n")
    success = sum(1 for path in found if delete_path(path))

    print(f"\n{'=' * 62}")
    print(f"  Done. {success}/{len(found)} artifact(s) removed.")

    remaining = find_all_vault_files()
    if remaining:
        print(f"\n⚠️  {len(remaining)} could not be removed (may need sudo):")
        for r in remaining:
            print(f"  • {r}")
        print("\n  Try:  sudo python clean_vault.py --confirm")
    else:
        print("\n✅ Vault fully cleared.")
        print("   Milvus will recreate it fresh on next startup.")
    print("=" * 62 + "\n")


if __name__ == "__main__":
    main()