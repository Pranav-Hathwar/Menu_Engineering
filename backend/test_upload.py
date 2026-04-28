"""Manual upload smoke test for a running local backend."""

import os

import requests

base_url = os.getenv("MENUMIND_API_URL", "http://localhost:8000")
email = os.getenv("ADMIN_EMAIL")
password = os.getenv("ADMIN_PASSWORD")

if not email or not password:
    raise SystemExit("Set ADMIN_EMAIL and ADMIN_PASSWORD to run this smoke test.")

login_res = requests.post(
    f"{base_url}/api/auth/login",
    data={"username": email, "password": password},
    timeout=10,
)
login_res.raise_for_status()
token = login_res.json()["access_token"]

csv_data = "Item Name,Quantity,Revenue\nBurger,5,15.00\nFries,10,5.00"
res = requests.post(
    f"{base_url}/api/upload",
    headers={"Authorization": f"Bearer {token}"},
    data={"restaurant_name": "Smoke Test Kitchen"},
    files={"file": ("test.csv", csv_data, "text/csv")},
    timeout=10,
)

print("STATUS:", res.status_code)
print("RESPONSE:", res.text)
