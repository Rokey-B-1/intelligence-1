import requests

url = "https://requests-homework.onrender.com/submit"

my_data = {
    "name": "Hyunwoo-Kim(김현우)",
    "student_number": "DR-01293"
}

res = requests.post(url, json=my_data)

print(res.status_code)
print(res.text)
