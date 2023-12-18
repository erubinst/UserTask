import requests
import json

json_file_name = "example.json"
url = "http://127.0.0.1:8050/task"  # Replace with the correct address if needed
with open(json_file_name, "r") as json_file:
            data = json.load(json_file)



headers = {'Content-type': 'application/json'}
response = requests.post(url,data=json.dumps(data), headers=headers)
print(response.text)