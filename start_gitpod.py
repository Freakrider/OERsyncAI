import sys
import subprocess
from datetime import datetime
import os
import traceback

def log(msg: str):
    """Prints timestamped debug messages with a consistent prefix."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] 🐍 {msg}", flush=True)

def main():
    if len(sys.argv) < 2:
        print("❌ Usage: python start_gitpod.py <mbz_path>")
        sys.exit(1)

    mbz_path = os.path.abspath(sys.argv[1])
    category_id = sys.argv[2] if len(sys.argv) > 2 else "1"
    shortname = sys.argv[3] if len(sys.argv) > 3 else f"restored_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    fullname = sys.argv[4] if len(sys.argv) > 4 else f"Restored Course {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    script = "docker_image/setup-and-restore.sh"

    print(f"📦 MBZ path       : {mbz_path}")
    print(f"📁 Category ID    : {category_id}")
    print(f"🔤 Course shortname : {shortname}")
    print(f"📘 Course fullname  : {fullname}")
    print(f"🚀 Running {script}...")

    # Check if the script exists
    base_dir = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(base_dir, "docker_image", "setup-and-restore.sh")

    if not os.path.isfile(script):
        print(f"❌ Script not found at: {script}")
        sys.exit(1)

    try:
        process = subprocess.Popen(
            ["bash", script, mbz_path, category_id, shortname, fullname],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Stream live output with timestamps
        for line in process.stdout:
            log(f"🧩 {line.strip()}")

        returncode = process.wait(timeout=600)

        if returncode == 0:
            log("✅ Script completed successfully!")
        else:
            log(f"❌ Script exited with non-zero return code: {returncode}")

    except subprocess.TimeoutExpired:
        log(f"❌ {script} timed out after 600s!")
        process.kill()
    except KeyboardInterrupt:
        log("⛔ Interrupted by user.")
        process.kill()
    except Exception as e:
        log(f"❌ Unexpected error: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
