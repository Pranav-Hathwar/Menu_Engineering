import requests

url = "http://localhost:8000/api/upload"

# Minimal CSV to simulate '9. Sales-Data-Analysis.csv'
csv_data = "Item Name,Quantity,Revenue\nBurger,5,15.00\nFries,10,5.00"
files = {
    'file': ('test.csv', csv_data, 'text/csv')
}
data = {
    'restaurant_name': 'burger shop'
}

# The user's token (we will just try without token to see if it redirects/fails differently, or bypass auth)
# Wait, the endpoint is protected! 
# We need an admin JWT.
import sqlite3
# We can bypass auth securely or just write a mock login.
# Mock login:
login_data = {
    "username": "admin@restaurant.com",
    "password": "password123"
}
try:
    login_res = requests.post("http://localhost:8000/api/auth/login", data=login_data)
    token = login_res.json()["access_token"]
    
    headers = {
        "Authorization": f"Bearer {token}"
    }

    res = requests.post(url, headers=headers, data=data, files=files)
    print("STATUS:", res.status_code)
    print("RESPONSE:", res.text)
except Exception as e:
    print("TEST FAILED:", e)
