import requests
import json

url = "http://localhost:5000/api/job-enricher/enrich"
payload = {
    "id": 50220,
    "title": "Registered Nurses - Medplus",
    "summary": "Permanent Full Time Registered Nurse roles; Join our committed, fun and supportive general practice team environment. Conveniently located.",
    "department": "Medplus",
    "location": "Auckland, New Zealand",
    "jobType": "Permanent Full Time",
    "status": "Open",
    "postedAt": "2025-05-13",
    "salaryRange": None,
    "responsibilities": [
        "Work at busy clinics at Hauraki Corner, Takapuna and Anne Street, Devonport.",
        "Join our committed, fun and supportive general practice team environment."
    ],
    "qualifications": [
        "Certified vaccinator",
        "Cannulation"
    ],
    "perks": [],
    "benefitsData": [],
    "specialty": "Healthcare & Medical",
    "organization": "Green Cross Health",
    "country": "NZ",
    "isRemote": False,
    "visaSponsorship": False,
    "fullTime": True,
    "partTime": False,
    "nightShift": True
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

