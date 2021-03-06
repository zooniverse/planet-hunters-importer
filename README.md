# planet-hunters-importer

Generates lightcurve JSON files and Ouroboros manifest for Planet Hunters.

Example usage:

```
docker run -it --rm -v /data/:/data/ -w /data zooniverse/planet-hunters-importer /usr/src/app/wgetkdwarfs.sh
docker run -it --rm -v /data/:/data/ zooniverse/planet-hunters-importer ./generate.py /data/metadata.csv
docker run -it --rm -v /data/:/data/ zooniverse/planet-hunters-importer ./generate-manifest.py
find /data/out/ -name "kdwarf-*.json" -exec aws s3 cp {} s3://zooniverse-static/www.planethunters.org/subjects/ \;
```

Then update and run `ingest.rb` in an Ouroboros shell with `/data/out/manifest.json`.
