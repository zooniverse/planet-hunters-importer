import json
import math
import os

for path in ('/data/json_lightcurve/sims/', '/data/json_lightcurve/'):
    for json_file in os.listdir(path):
        if not json_file.endswith('.json'):
            continue
        with open(os.path.join(path, json_file)) as f:
            try:
                d = json.load(f)
            except:
                print "Failed to load %s" % json_file
                raise
        orig_len = len(d['x'])
        x, y = [], []
        for orig_x, orig_y in zip(d['x'], d['y']):
            if not (math.isnan(orig_x) or math.isnan(orig_y)):
                x.append(orig_x)
                y.append(orig_y)
        d['x'] = x
        d['y'] = y
        final_len = len(d['x'])
        if orig_len == final_len:
            continue
        with open(os.path.join(path, json_file), 'w') as f:
            json.dump(d, f)
        print "Processed %s: %s to %s" % (json_file, orig_len, final_len)
