import copy
import csv
import ujson as json
import math
import numpy
import os
import progressbar as pb

epic_columns = (
    'epic_number',
    'epic_ra',
    'epic_dec',
    'kepler',
    '2mass_id',
    '2mass_ra',
    '2mass_dec',
    'Jmag',
    'Hmag',
    'Kmag',
    'sdss_id',
    'sdss_ra',
    'sdss_dec',
    'Umag',
    'Gmag',
    'Rmag',
    'Imag',
    'Zmag'
)

magnitude_cols = (
    'kepler',
    'Jmag',
    'Hmag',
    'Kmag',
    'Umag',
    'Gmag',
    'Rmag',
    'Imag',
    'Zmag'
)

metadata = {}
magnitudes = {}
manifest = []

CAMPAIGN_NO = "C04"

with open('EPIC_meta_data.dat.K2C4') as epic_f:
    epic_data = csv.reader(epic_f, delimiter=" ", skipinitialspace=True)

    for md_row in epic_data:
        epic_id = int(md_row[0])
        d = metadata.setdefault(epic_id, {
            'k2': True, 'spectral_type': None
        })
        m = magnitudes.setdefault(epic_id, {})
        for head, col in zip(epic_columns[1:], md_row[1:]):
            if col == '-999':
                col = None
            elif head not in ('2mass_id', 'sdss_id'):
                col = float(col)
                if math.isnan(col):
                    col = None

            if head in magnitude_cols:
                m[head] = col
            else:
                d[head] = col

quarter_size = 30

def quarter_append(q, x, y, dy):
    q['x'].append(x)
    q['y'].append(y)
    q['dy'].append(dy)

files = [ f for f in os.listdir('lc-data')
          if f.endswith('.csv') and f.startswith('ep') ]

progress = pb.ProgressBar(
    widgets=[
        " Writing JSON: ", pb.Percentage(), ' ', pb.Bar(marker='='), ' ',
        pb.ETA()
    ], maxval=len(files)
).start()

for f_num, f_name in enumerate(files):
    epic_id = int(f_name.replace('ep', '').replace('.csv', ''))

    if not epic_id in metadata:
        print "Warning: %s not found in metadata" % epic_id
        continue

    default_output = {
        'x': [],
        'y': [],
        'dy': [],
        'metadata': {
            "EPIC_number": epic_id,
            'kepler_2_campaign_no': CAMPAIGN_NO,
        }
    }

    default_output['metadata'].update(metadata[epic_id])
    default_output['metadata'].update(magnitudes[epic_id])

    xs, ys, dys = [], [], []

    with open("lc-data/%s" % f_name) as f:
        r = csv.reader(f)
        for row in r:
            xs.append(float(row[0]))
            ys.append(float(row[1]))
            if row[2] == "":
                row[2] = None
            dys.append(row[2])

    q1_upper_bound = xs[0] + quarter_size
    q3_lower_bound = xs[-1] - quarter_size

    q2_middle = numpy.mean(xs)
    q2_lower_bound = q2_middle - quarter_size/2
    q2_upper_bound = q2_middle + quarter_size/2

    quarters = {
        1: copy.deepcopy(default_output),
        2: copy.deepcopy(default_output),
        3: copy.deepcopy(default_output)
    }

    for x, y, dy in zip(xs, ys, dys):
        if x <= q1_upper_bound:
            quarter_append(quarters[1], x, y, dy)

        if x >= q2_lower_bound and x <= q2_upper_bound:
            quarter_append(quarters[2], x, y, dy)

        if x >= q3_lower_bound:
            quarter_append(quarters[3], x, y, dy)

    quarters[1]['metadata']['start_time'] = quarters[1]['x'][0]
    quarters[2]['metadata']['start_time'] = quarters[2]['x'][0]
    quarters[3]['metadata']['start_time'] = quarters[3]['x'][0]

    light_curves = []

    for quarter, data in quarters.items():
        filename = '%s-%s-1-%s.json' % (CAMPAIGN_NO, epic_id, quarter)
        with open(
            'lc-output/%s' % filename, 'w'
        ) as json_out:
            try:
                json.dump(data, json_out)
            except Exception as e:
                print data
                raise e
        light_curves.append({
            'location': 'http://www.planethunters.org/subjects/%s' % filename,
            'quarter': '1-%s' % quarter,
            'start_time': quarters[quarter]['metadata']['start_time']
        })

    manifest_out = {
        'type': 'subject',
        'metadata': copy.deepcopy(default_output['metadata']),
        'light_curves': light_curves,
        'coords': [
            default_output['metadata'].get('2mass_ra'),
            default_output['metadata'].get('2mass_dec')
        ]
    }
    manifest_out['metadata']['magnitudes'] = magnitudes[epic_id]

    manifest.append(manifest_out)
    progress.update(f_num)

print ""

with open('manifest.json', 'w') as manifest_f:
    json.dump(manifest, manifest_f)
