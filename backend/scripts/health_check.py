import requests
import sys

def check_backend():
    try:
        r = requests.get("http://localhost:8000/")
        if r.status_code == 200:
            print("BACKEND_HEALTH_OK:", r.json())
        else:
            print("BACKEND_ERROR:", r.status_code)
    except Exception as e:
        print("BACKEND_DOWN:", str(e))

if __name__ == "__main__":
    check_backend()
