import requests

API_KEY = "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6ImMzYjhhNDI3ZTdjNDRkOGJiZjZhMmRkZjY4YWZjYTYyIiwiaCI6Im11cm11cjY0In0="

url = "https://api.openrouteservice.org/v2/directions/driving-car"

headers = {
    "Authorization": API_KEY,
    "Content-Type": "application/json"
}

# Coordinates format: [longitude, latitude]
data = {
    "coordinates": [
        [73.8567, 18.5204],  # Pune
        [72.8777, 19.0760]   # Mumbai
    ]
}

response = requests.post(url, json=data, headers=headers)

if response.status_code == 200:
    result = response.json()
    
    summary = result["routes"][0]["summary"]
    distance = summary["distance"]      # in meters
    duration = summary["duration"]      # in seconds

    print(f"Distance: {distance/1000:.2f} km")
    print(f"Duration: {duration/60:.2f} minutes")
else:
    print("Error:", response.status_code, response.text)