import requests


log = "" #uuid ONLY no .log no logs/
id_token = ""

headers = {
    'Authorization': f"Bearer {id_token}"
}

response = requests.get(
    url=f"https://bz97lt8b1e.execute-api.eu-west-1.amazonaws.com/prod/results/tutorial/{log}",
     headers=headers
)

if __name__ == '__main__':
    print(response.json()['algo']['summary']['profit'])