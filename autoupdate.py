import requests
import hashlib
import os
import subprocess

GITHUB_RAW_URL = "https://raw.githubusercontent.com/lerechard/Fiscon-Animatronic-Gadget/main/animatronic.py"
LOCAL_FILE = "animatronic.py"
HASH_FILE = ".animatronic_hash"

def get_remote_file():
    response = requests.get(GITHUB_RAW_URL)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch file: HTTP {response.status_code}")
    return response.text

def compute_hash(content):
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def read_local_hash():
    if os.path.exists(HASH_FILE):
        with open(HASH_FILE, 'r') as f:
            return f.read().strip()
    return None

def write_local_hash(hash_val):
    with open(HASH_FILE, 'w') as f:
        f.write(hash_val)

def save_file(content):
    with open(LOCAL_FILE, 'w', encoding='utf-8') as f:
        f.write(content)

def run_file():
    subprocess.run(["python", LOCAL_FILE], check=False)

def main():
    try:
        remote_content = get_remote_file()
        remote_hash = compute_hash(remote_content)
        local_hash = read_local_hash()

        if remote_hash != local_hash:
            print("New version found. Updating...")
            save_file(remote_content)
            write_local_hash(remote_hash)
        else:
            print("Already up to date.")

        print("Running animatronic.py...")
        run_file()

    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
