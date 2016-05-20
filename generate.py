import astropy.io.fits as fits
import copy
import csv
import numpy
import os
import re
import sys
import json

# Load metadata from CSV

try:
    METADATA_FILE = sys.argv[1]
except IndexError:
    print "Please specify the name of the file containing lightcurve URLs"
    sys.exit(1)

DATAPATH = os.environ.get('DATAPATH', os.path.join('/', 'data'))
OUTPATH = os.environ.get('OUTPATH', os.path.join(DATAPATH, 'out'))

if not os.path.isdir(DATAPATH):
    os.mkdir(DATAPATH)

if not os.path.isdir(OUTPATH):
    os.mkdir(OUTPATH)

metadata_f = open(METADATA_FILE, 'r')
metadata_r = csv.reader(metadata_f)

def split_append(q, x, y, dy):
    q['x'].append(x)
    q['y'].append(y)
    q['dy'].append(dy)

# Put all fits filenames into dict of lists indexed by kepler ID
fits_files = {}

for fits_file_name in os.listdir(DATAPATH):
    kepler_id_match = re.match(
        r'kplr(?P<keplerid>[0-9]{9})-[0-9]{13}_llc\.fits$',
        fits_file_name
    )
    if not kepler_id_match:
        continue
    kepler_id = int(kepler_id_match.group('keplerid'))
    fits_files.setdefault(kepler_id, []).append(fits_file_name)

headers = metadata_r.next()

unknown_ids = set()

for row in metadata_r:
    row = dict(zip(headers, row))
    row['kepid'] = int(row['kepid'])

    if row['kepid'] not in fits_files:
        unknown_ids.add(row['kepid'])
        continue

    print "Processing %s" % row['kepid']

    # match files to Qx where Qx = 1
    quarters = []
    for quarter, present in enumerate([
        row['Q1'], row['Q2'], row['Q3'], row['Q4'], row['Q5'], row['Q6'],
        row['Q7'], row['Q8'], row['Q9'], row['Q10'], row['Q11'], row['Q12'],
        row['Q13'], row['Q14'], row['Q15'], row['Q16'], row['Q17']
    ], start=1):
        if present == '1':
            quarters.append(quarter)

    # Load lightcurve data from FITS
    for fits_file, quarter in zip(sorted(fits_files[row['kepid']]), quarters):
        print "\tProcessing %s" % fits_file
        with fits.open(os.path.join(DATAPATH, fits_file)) as hdu_list:
            lc_data = hdu_list['LIGHTCURVE'].data
            metadata_fields = (
                'rowid',
                'st_delivname',
                'kepid',
                'tm_designation',
                'ra',
                'dec',
                'kepmag',
                'activity',
                'teff',
                'teff_err1',
                'teff_err2',
                'teff_prov',
                'logg',
                'logg_err1',
                'logg_err2',
                'logg_prov',
                'feh',
                'feh_err1',
                'feh_err2',
                'feh_prov',
                'radius',
                'radius_err1',
                'radius_err2',
                'mass',
                'mass_err1',
                'mass_err2',
                'dens',
                'dens_err1',
                'dens_err2',
                'prov_sec',
                'nconfp',
                'nkoi',
                'ntce',
                'st_quarters',
                'st_vet_date',
                'ra_str',
                'dec_str'
            )
            default_output = {
                'x': [],
                'y': [],
                'dy': [],
                'metadata': {},
            }
            for field in metadata_fields:
                default_output[field] = row[field]

            xs, ys, dys = [], [], []
            for lc_row in lc_data:
                if not numpy.isnan(lc_row['TIME']):
                    xs.append(float(lc_row['TIME']))
                    # TODO: Check if we should use SAP_FLUX or PDCSAP_FLUX
                    ys.append(float(lc_row['PDCSAP_FLUX']))
                    dys.append(None)

            # Split lightcurve quarters into 30-day chunks
            # Unless this is quarter 17
            if quarter != 17:
                split_size = 30
                q1_upper_bound = xs[0] + split_size
                q3_lower_bound = xs[-1] - split_size

                q2_middle = numpy.mean(xs)
                q2_lower_bound = q2_middle - split_size/2
                q2_upper_bound = q2_middle + split_size/2

                splits = {
                    1: copy.deepcopy(default_output),
                    2: copy.deepcopy(default_output),
                    3: copy.deepcopy(default_output)
                }
                for x, y, dy in zip(xs, ys, dys):
                    if x <= q1_upper_bound:
                        split_append(splits[1], x, y, dy)

                    if x >= q2_lower_bound and x <= q2_upper_bound:
                        split_append(splits[2], x, y, dy)

                    if x >= q3_lower_bound:
                        split_append(splits[3], x, y, dy)

                splits[1]['metadata']['start_time'] = splits[1]['x'][0]
                splits[2]['metadata']['start_time'] = splits[2]['x'][0]
                splits[3]['metadata']['start_time'] = splits[3]['x'][0]
            else:
                splits = {
                    1: copy.deepcopy(default_output)
                }
                splits[1]['metadata']['start_time'] = xs[0]
                splits[1]['x'] = xs
                splits[1]['y'] = ys
                splits[1]['dys'] = dys

            # Write lightcurve data and metadata to JSON
            for split, json_out in splits.items():
                out_file_name = os.path.join(OUTPATH, 'kdwarf-%s-%s-%s.json' % (
                    row['kepid'], quarter, split
                ))

                print "\t\tWriting %s" % out_file_name
                with open(out_file_name, "w") as out_file:
                    json.dump(json_out, out_file)

if unknown_ids:
    print "Warning: Skipped the following unknown kepler IDs"
    for unknown_id in unknown_ids:
        print "\t%s" % unknown_id
