import os
import sys
import subprocess
import time

def print_step(msg):
    print("=" * 60)
    print(f">>> {msg}")
    print("=" * 60)

def main():
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)

    # Step 1: Ensure directories exist
    os.makedirs("data", exist_ok=True)
    os.makedirs("backend", exist_ok=True)

    # Step 2: Set up Frontend Node dependencies
    frontend_dir = os.path.join(root_dir, "frontend")
    node_modules_dir = os.path.join(frontend_dir, "node_modules")
    
    if not os.path.exists(node_modules_dir):
        print_step("Installing Frontend Dependencies (npm install)...")
        # Run npm install
        res = subprocess.run("npm install", shell=True, cwd=frontend_dir)
        if res.returncode != 0:
            print("Error: 'npm install' failed. Please ensure Node.js and npm are installed and on your PATH.")
            sys.exit(1)
    else:
        print("Frontend dependencies (node_modules) already present. Skipping npm install.")

    # Step 3: Build Frontend assets if missing
    dist_dir = os.path.join(frontend_dir, "dist")
    if not os.path.exists(dist_dir) or "--rebuild" in sys.argv:
        print_step("Compiling Frontend Production Build (npm run build)...")
        res = subprocess.run("npm run build", shell=True, cwd=frontend_dir)
        if res.returncode != 0:
            print("Error: 'npm run build' failed.")
            sys.exit(1)
    else:
        print("Frontend production build (dist) already present. Skipping build. (Use --rebuild to rebuild)")

    # Step 4: Run Calibration if missing
    weights_path = os.path.join(root_dir, "backend", "weights.json")
    dataset_path = os.path.join(root_dir, "data", "dataset.json")
    if not os.path.exists(weights_path) or not os.path.exists(dataset_path) or "--recalibrate" in sys.argv:
        print_step("Missing calibrated weights. Running Model Calibration & Sourcing...")
        # Add root to pythonpath dynamically and execute prepare_dataset.py
        env = os.environ.copy()
        env["PYTHONPATH"] = root_dir + os.pathsep + env.get("PYTHONPATH", "")
        res = subprocess.run([sys.executable, "scripts/prepare_dataset.py"], env=env)
        if res.returncode != 0:
            print("Error: Model calibration script failed.")
            sys.exit(1)
    else:
        print("Calibrated weights and dataset already exist. Skipping calibration. (Use --recalibrate to recalibrate)")

    # Step 5: Start uvicorn server hosting API and static files
    print_step("Starting FastAPI Backend Server at http://127.0.0.1:8000 ...")
    env = os.environ.copy()
    env["PYTHONPATH"] = root_dir + os.pathsep + env.get("PYTHONPATH", "")
    
    # Run uvicorn server
    try:
        subprocess.run(["uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"], env=env)
    except KeyboardInterrupt:
        print("\nStopping server...")

if __name__ == "__main__":
    main()
