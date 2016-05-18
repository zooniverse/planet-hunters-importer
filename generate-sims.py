import astropy.io.fits as fits
import copy
import csv
import numpy
import os
import re
import json

# Load metadata from CSV

metadata_f = open('/data/PHKdwarfstransittimes.txt', 'r')
metadata_r = csv.reader(metadata_f, delimiter="\t")

# Put all fits filenames into dict of lists indexed by kepler ID
fits_files = {}

def split_append(q, x, y, dy):
    q['x'].append(x)
    q['y'].append(y)
    q['dy'].append(dy)

DATA_PATH_PREFIX = os.path.join('/', 'data', 'Kdwarfsynthetics')

metadata_r.next()

unknown_ids = set()

default_output = {}

for row in metadata_r:
    kepid, origfits, synfits, period, prad, srad, kepmag, teff, syntheticid, plphase, synpixmin, synpixmax, synxmin, synxmax = row
    kepid = int(kepid)

    default_output[synfits] = {
        'x': [],
        'y': [],
        'dy': [],
        'metadata': {
            "kepid": kepid,
            "kepmag": kepmag,
            "period": period,
            "prad": prad,
            "srad": srad,
            "teff": teff,
            "syntheticid": syntheticid,
            "plphase": plphase,
            "synpixmin": synpixmin,
            "synxmin": synxmin,
            "known_transits": zip(
                map(float, synxmin.split(',')),
                map(float, synxmax.split(','))
            )
        },
    }

# Load lightcurve data from FITS
for fits_file in os.listdir(DATA_PATH_PREFIX):
    if not fits_file in default_output:
        unknown_ids.add(fits_file)
        continue

    print "Processing %s" % fits_file
    with fits.open(os.path.join(DATA_PATH_PREFIX, fits_file)) as hdu_list:
        lc_data = hdu_list[1].data
        kepler_id = hdu_list[0].header['KEPLERID']
        xs, ys, dys = [], [], []
        for lc_row in lc_data:
            if not numpy.isnan(lc_row['TIME']):
                xs.append(float(lc_row['TIME']))
                ys.append(float(lc_row['PDCSAP_FLUX']))
                dys.append(None)

        splits = {
            1: copy.deepcopy(default_output[fits_file])
        }
        splits[1]['metadata']['start_time'] = xs[0]
        splits[1]['x'] = xs
        splits[1]['y'] = ys
        splits[1]['dys'] = dys

        # Write lightcurve data and metadata to JSON
        for split, json_out in splits.items():
            out_file_name = "/data/json_lightcurve/sims/kdwarf-sim-%s-%s.json" % (
                kepler_id, json_out['metadata']['syntheticid']
            )

            print "\t\tWriting %s" % out_file_name
            with open(out_file_name, "w") as out_file:
                json.dump(json_out, out_file)

if unknown_ids:
    print "Warning: Skipped the following unknown files"
    for unknown_id in unknown_ids:
        print "\t%s" % unknown_id
