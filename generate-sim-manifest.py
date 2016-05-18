import json
import os

DATA_PATH = '/data/json_lightcurve/sims/'

subject_data = []

for file_name in os.listdir(DATA_PATH):
    if not file_name.endswith(".json"):
        continue
    with open(os.path.join(DATA_PATH, file_name)) as f:
        file_data = json.load(f)
    subject_data.append({
        'type': 'subject',
        'metadata': file_data['metadata'],
        'light_curves': [{
            'location': 'http://www.planethunters.org/subjects/%s' % file_name,
            'quarter': '1-1',
            'start_time': file_data['metadata'].get('start_time')
        }],
        'coords': [
        ],
    })

with open('manifest.json', 'w') as f_out:
    json.dump(subject_data, f_out)
