# planet-hunters-importer

Generates lightcurve JSON files and Ouroboros manifest for Planet Hunters.

Example usage:

```
docker run -it -v /data/:/data/ zooniverse/planet-hunters-importer ./generate.py /data/metadata.csv
docker run -it -v /data/:/data/ zooniverse/planet-hunters-importer ./generate-manifest.py
```
