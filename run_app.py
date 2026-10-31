import subprocess
import sys
import os
import time
import shutil
import urllib.request
import webbrowser

def wait_for_service(url: str, service_name: str, max_retries: int = 30, delay: float = 1.0) -> bool:
    """Poll URL until service responds HTTP 200 or timeout."""
    print(f"[*] Waiting for {service_name} to be ready at {url}...")
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'DataNexus-Startup-Probe'})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status in (200, 304):
                    print(f"[+] {service_name} is online! (ready in {attempt * delay:.1f}s)")
                    return True
        except Exception:
            pass
        time.sleep(delay)
    print(f"[-] Warning: {service_name} did not respond within {max_retries * delay:.0f}s.")
    return False

def terminate_process(proc: subprocess.Popen, name: str):
    """Safely terminate a process and its children on Windows/Unix."""
    if proc is None or proc.poll() is not None:
        return
    print(f"[*] Stopping {name} (PID: {proc.pid})...")
    if os.name == 'nt':
        try:
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            proc.kill()
    else:
        try:
            proc.terminate()
            proc.wait(timeout=3)
        except Exception:
            proc.kill()

def main():
    print("=" * 70)
    print("  DataNexus – Enterprise Interactive Analytics & Intelligence Platform")
    print("=" * 70)

    # Locate directories
    current_dir = os.path.abspath(os.path.dirname(__file__))
    if os.path.exists(os.path.join(current_dir, "backend")):
        root_dir = current_dir
    elif os.path.exists(os.path.join(current_dir, "data lens", "backend")):
        root_dir = os.path.join(current_dir, "data lens")
    else:
        root_dir = current_dir

    backend_dir = os.path.join(root_dir, "backend")
    frontend_dir = os.path.join(root_dir, "frontend")

    # Verify python dependencies
    try:
        import fastapi
        import uvicorn
        import pandas
        import numpy
        import sklearn
    except ImportError as e:
        print(f"\n[!] Missing Python dependency: {e.name}")
        print("    Please install requirements: pip install -r requirements.txt\n")
        sys.exit(1)

    # Verify npm
    npm_bin = shutil.which("npm.cmd") or shutil.which("npm")
    if not npm_bin:
        print("\n[!] Error: 'npm' was not found in PATH.")
        print("    Please install Node.js (v18+) from https://nodejs.org/\n")
        sys.exit(1)

    # Verify frontend node_modules
    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        print("\n[*] Installing frontend dependencies (one-time setup)...")
        install_res = subprocess.run([npm_bin, "install"], cwd=frontend_dir)
        if install_res.returncode != 0:
            print("[!] Failed to run npm install in frontend directory.")
            sys.exit(1)

    backend_proc = None
    frontend_proc = None

    try:
        # 1. Start FastAPI Backend
        print("\n[1/2] Starting FastAPI Backend on http://127.0.0.1:8000...")
        backend_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=root_dir
        )

        # 2. Start Vite Frontend
        print("[2/2] Starting React 19 / Vite Frontend on http://localhost:5173...")
        frontend_proc = subprocess.Popen(
            [npm_bin, "run", "dev"],
            cwd=frontend_dir
        )

        # 3. Check health and readiness
        backend_ready = wait_for_service("http://127.0.0.1:8000/api/health", "Backend API", max_retries=25, delay=0.8)
        frontend_ready = wait_for_service("http://localhost:5173", "Frontend UI", max_retries=25, delay=0.8)

        print("\n" + "=" * 70)
        print("  DataNexus is running successfully!")
        print("  -> Application UI:   http://localhost:5173")
        print("  -> Backend API:      http://127.0.0.1:8000")
        print("  -> API Health:       http://127.0.0.1:8000/api/health")
        print("  -> Interactive Docs: http://127.0.0.1:8000/docs")
        print("=" * 70)

        # 4. Open browser automatically once ready
        if frontend_ready:
            print("\n[*] Opening DataNexus in your default browser: http://localhost:5173")
            webbrowser.open("http://localhost:5173")

        print("\n[Press Ctrl+C to cleanly stop both DataNexus servers]\n")

        # Monitor loop
        while True:
            if backend_proc.poll() is not None:
                print("\n[!] Backend process exited unexpectedly.")
                break
            if frontend_proc.poll() is not None:
                print("\n[!] Frontend process exited unexpectedly.")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[*] Shutting down DataNexus...")
    finally:
        terminate_process(backend_proc, "FastAPI Backend")
        terminate_process(frontend_proc, "Vite Frontend")
        print("[+] All DataNexus processes stopped cleanly. Goodbye!\n")

if __name__ == '__main__':
    main()
