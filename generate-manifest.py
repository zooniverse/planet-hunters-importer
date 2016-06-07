#!/usr/bin/env python
import copy
import os
import re
import ujson as json

DATAPATH = os.environ.get('DATAPATH', os.path.join('/', 'data'))
OUTPATH = os.environ.get('OUTPATH', os.path.join(DATAPATH, 'out'))

subject_data = {}

for file_name in os.listdir(OUTPATH):
    file_name_match = re.match(
        r'kdwarf-(?P<keplerid>[0-9]+)-(?P<quarter>[0-9]+-[0-9]+)\.json$',
        file_name
    )
    if not file_name_match:
        continue
    kepler_id = file_name_match.group('keplerid')
    with open(os.path.join(OUTPATH, file_name)) as f:
        file_data = json.load(f)
    subject_data.setdefault(
        kepler_id,
        {
            'type': 'subject',
            'metadata': copy.deepcopy(file_data['metadata']),
            'light_curves': [],
            'coords': [
                float(file_data['metadata'].get('ra')),
                float(file_data['metadata'].get('dec'))
            ]
        }
    )
    if 'start_time' in subject_data[kepler_id]['metadata']:
        del subject_data[kepler_id]['metadata']['start_time']
    subject_data[kepler_id]['light_curves'].append({
        'location': 'http://www.planethunters.org/subjects/%s' % file_name,
        'quarter': file_name_match.group('quarter'),
        'start_time': file_data['metadata'].get('start_time')
    })

with open(os.path.join(OUTPATH, 'manifest.json'), 'w') as f_out:
    json.dump(subject_data.values(), f_out)
