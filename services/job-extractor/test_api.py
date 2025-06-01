import requests
import json

url = "http://host.docker.internal:5001/api/job-extractor/extract"
payload = {
    "job_url": "https://careers.greencrosshealth.co.nz/jobdetails/ajid/oLmC8/Registered-Nurses-Medplus,50220.html"
}
headers = {
    "Content-Type": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers)
    print("Status Code:", response.status_code)
    print("\nResponse:\n", json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")

