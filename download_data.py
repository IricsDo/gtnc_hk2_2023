import requests
from pathlib import Path

# Local data in drive
url = "https://docs.google.com/spreadsheets/d/0Ie4d-RdhZKUVsSSzjtxOFStAHY3d2HJY/edit?usp=sharing&ouid=110624032640162369931&rtpof=true&sd=true"
path = 'data/data.xls'


def check_data_exists():
    return Path(path).exists()

def pull_data():
    try:
        resp = requests.get(url)
        with open('data/data.xls', 'wb') as output:
            output.write(resp.content)
    except Exception as e:
        return False
    return True