import astropy.io.fits as fits
import copy
import csv
import numpy
import os
import re
import json

# Load metadata from CSV

metadata_f = open('/data/KDwarfs-batch1-fixed.csv', 'r')
metadata_r = csv.reader(metadata_f)

# Put all fits filenames into dict of lists indexed by kepler ID
fits_files = {}

def split_append(q, x, y, dy):
    q['x'].append(x)
    q['y'].append(y)
    q['dy'].append(dy)

DATA_PATH_PREFIX = os.path.join('/', 'data', 'kdwarf')

for fits_file_name in os.listdir('/data/kdwarf'):
    kepler_id_match = re.match(
        r'kplr(?P<keplerid>[0-9]{9})-[0-9]{13}_llc\.fits$',
        fits_file_name
    )
    if not kepler_id_match:
        continue
    kepler_id = int(kepler_id_match.group('keplerid'))
    fits_files.setdefault(kepler_id, []).append(fits_file_name)

metadata_r.next()

unknown_ids = set()

for row in metadata_r:
    rowid,st_delivname,kepid,tm_designation,ra,dec,kepmag,activity,teff,teff_err1,teff_err2,teff_prov,logg,logg_err1,logg_err2,logg_prov,feh,feh_err1,feh_err2,feh_prov,radius,radius_err1,radius_err2,mass,mass_err1,mass_err2,dens,dens_err1,dens_err2,prov_sec,nconfp,nkoi,ntce,st_quarters,Q1,Q2,Q3,Q4,Q5,Q6,Q7,Q8,Q9,Q10,Q11,Q12,Q13,Q14,Q15,Q16,Q17,NumQobserved,st_vet_date,ra_str,dec_str = row
    kepid = int(kepid)

    if kepid not in fits_files:
        unknown_ids.add(kepid)
        continue

    print "Processing %s" % kepid

    # match files to Qx where Qx = 1
    quarters = []
    for quarter, present in enumerate([
        Q1, Q2, Q3, Q4, Q5, Q6, Q7, Q8, Q9, Q10, Q11, Q12, Q13, Q14, Q15, Q16,
        Q17
    ], start=1):
        if present == '1':
            quarters.append(quarter)

    # Load lightcurve data from FITS
    for fits_file, quarter in zip(sorted(fits_files[kepid]), quarters):
        print "\tProcessing %s" % fits_file
        with fits.open(os.path.join(DATA_PATH_PREFIX, fits_file)) as hdu_list:
            lc_data = hdu_list['LIGHTCURVE'].data
            default_output = {
                'x': [],
                'y': [],
                'dy': [],
                'metadata': {
                    "rowid": rowid,
                    "st_delivname": st_delivname,
                    "kepid": kepid,
                    "tm_designation": tm_designation,
                    "ra": ra,
                    "dec": dec,
                    "kepmag": kepmag,
                    "activity": activity,
                    "teff": teff,
                    "teff_err1": teff_err1,
                    "teff_err2": teff_err2,
                    "teff_prov": teff_prov,
                    "logg": logg,
                    "logg_err1": logg_err1,
                    "logg_err2": logg_err2,
                    "logg_prov": logg_prov,
                    "feh": feh,
                    "feh_err1": feh_err1,
                    "feh_err2": feh_err2,
                    "feh_prov": feh_prov,
                    "radius": radius,
                    "radius_err1": radius_err1,
                    "radius_err2": radius_err2,
                    "mass": mass,
                    "mass_err1": mass_err1,
                    "mass_err2": mass_err2,
                    "dens": dens,
                    "dens_err1": dens_err1,
                    "dens_err2": dens_err2,
                    "prov_sec": prov_sec,
                    "nconfp": nconfp,
                    "nkoi": nkoi,
                    "ntce": ntce,
                    "st_quarters": st_quarters,
                    "st_vet_date": st_vet_date,
                    "ra_str": ra_str,
                    "dec_str": dec_str
                },
            }
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
                out_file_name = "/data/json_lightcurve/kdwarf-%s-%s-%s.json" % (
                    kepid, quarter, split
                )

                print "\t\tWriting %s" % out_file_name
                with open(out_file_name, "w") as out_file:
                    json.dump(json_out, out_file)

if unknown_ids:
    print "Warning: Skipped the following unknown kepler IDs"
    for unknown_id in unknown_ids:
        print "\t%s" % unknown_id
