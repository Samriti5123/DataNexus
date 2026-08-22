import subprocess
import sys
import os
import time

def main():
    print("=" * 65)
    print("  DataLens – Interactive Data Analysis & BI Platform")
    print("=" * 65)
    
    root_dir = os.path.abspath(os.path.dirname(__file__))
    backend_dir = os.path.join(root_dir, "backend")
    frontend_dir = os.path.join(root_dir, "frontend")

    print("\n[1/2] Starting FastAPI Backend on http://127.0.0.1:8000...")
    backend_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000", "--reload"],
        cwd=root_dir
    )

    print("[2/2] Starting Vite Frontend on http://localhost:5173...")
    frontend_proc = subprocess.Popen(
        ["npm.cmd", "run", "dev"],
        cwd=frontend_dir
    )

    print("\n" + "=" * 65)
    print("  DataLens is running!")
    print("  -> Frontend UI:     http://localhost:5173")
    print("  -> Backend API:     http://127.0.0.1:8000")
    print("  -> Interactive Docs: http://127.0.0.1:8000/docs")
    print("=" * 65)
    print("\nPress Ctrl+C to stop both servers...\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down DataLens servers...")
        backend_proc.terminate()
        frontend_proc.terminate()
        print("Goodbye!")

if __name__ == '__main__':
    main()
