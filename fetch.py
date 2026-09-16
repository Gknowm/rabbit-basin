#!/usr/bin/env python3
"""
Fills in everything the map needs. Run it once:

    python3 fetch.py

It downloads four datasets straight from the agencies that publish them,
plus the mapping library the page uses, and drops them into data/ and
vendor/. Nothing here touches Land Matters or any other third party site.

To check the sources are alive without downloading anything:

    python3 fetch.py --check

To cover different ground, change BBOX below and run it again.
Needs Python 3.8 or newer. No extra packages.
"""

import json
import os
import ssl
import sys
import urllib.parse
import urllib.request

# ----------------------------------------------------------------------
# The ground you want, as west, south, east, north in degrees.
# This box covers the Rabbit Basin area north of Plush, Lake County,
# Oregon. Widen it and the files get bigger; that is the only cost.
# ----------------------------------------------------------------------
BBOX = (-119.95, 42.55, -119.30, 42.95)

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
VENDOR = os.path.join(HERE, "vendor")

MAPLIBRE = "4.7.1"
VENDOR_FILES = [
    (f"https://cdn.jsdelivr.net/npm/maplibre-gl@{MAPLIBRE}/dist/maplibre-gl.js",
     "maplibre-gl.js"),
    (f"https://cdn.jsdelivr.net/npm/maplibre-gl@{MAPLIBRE}/dist/maplibre-gl.css",
     "maplibre-gl.css"),
]

# ----------------------------------------------------------------------
# The four layers. Each one is a public ArcGIS service run by the agency
# that owns the data.
#
# If a source ever moves, the script will tell you which one failed.
# Search the agency's REST directory for the new address and change the
# "url" line here — nothing else needs to change.
# ----------------------------------------------------------------------
SOURCES = [
    {
        "name": "Geology",
        "out": "geology.geojson",
        "who": "Oregon Dept. of Geology and Mineral Industries (OGDC)",
        "url": "https://gis.dogami.oregon.gov/arcgis/rest/services/Public/OGDC6/MapServer/2/query",
        "where": "1=1",
        "page": 1000,
        "keep": ["MAP_UNIT_L","MAP_UNIT_N","FORMATION","G_MRG_U_L","AGE_NAME","G_ROCK_TYP",
                 "LTH_RK_TYP","LITH_GEN_U","LITH_M_U_L","CR_GRN_SIZ","TERRANE_GR","MEMBER",
                 "des","Citation","Link"],
    },
    {
        "name": "Mining claims",
        "out": "claims.geojson",
        "who": "BLM Mineral and Land Records System, cases not closed",
        "url": "https://gis.blm.gov/nlsdb/rest/services/HUB/BLM_Natl_MLRS_Mining_Claims_Not_Closed/FeatureServer/0/query",
        "where": "1=1",
        "page": 2000,
        "keep": ["OBJECTID","CSE_NAME","CSE_NR","CSE_TYPE_NR","CSE_DISP","QLTY",
                 "RCRD_ACRS","LEG_CSE_NR"],
    },
    {
        "name": "Land manager",
        "out": "ownership.geojson",
        "who": "BLM Surface Management Agency",
        "url": "https://gis.blm.gov/arcgis/rest/services/lands/BLM_Natl_SMA_LimitedScale/MapServer/1/query",
        "where": "1=1",
        "page": 1000,
    },
    {
        "name": "Survey grid",
        "out": "plss.geojson",
        "who": "BLM PLSS CadNSDI, sections and aliquot parts",
        "url": "https://gis.blm.gov/arcgis/rest/services/Cadastral/BLM_Natl_PLSS_CadNSDI/MapServer/2/query",
        "where": "1=1",
        "page": 1000,
        "keep": ["FRSTDIVNO","FRSTDIVID","PLSSID","TWNSHPLAB","FRSTDIVTYP"],
    },
]

CTX = ssl.create_default_context()
UA = {"User-Agent": "rabbit-basin-field-map/1.0 (personal offline map)"}


def get(url, timeout=90):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        return r.read()


def query_url(src, offset, count, geometry_only=True):
    params = {
        "where": src["where"],
        "outFields": "*",
        "f": "geojson",
        "returnGeometry": "true",
        "outSR": "4326",
        "resultOffset": offset,
        "resultRecordCount": count,
    }
    if geometry_only:
        params.update({
            "geometry": ",".join(str(v) for v in BBOX),
            "geometryType": "esriGeometryEnvelope",
            "inSR": "4326",
            "spatialRel": "esriSpatialRelIntersects",
        })
    return src["url"] + "?" + urllib.parse.urlencode(params)


PRECISION = 6   # ~4 inches on the ground; source gives ~15 decimals


def trim_coords(node):
    """Round every coordinate in a nested list to PRECISION decimals."""
    if isinstance(node, list):
        if node and isinstance(node[0], (int, float)):
            return [round(v, PRECISION) for v in node]
        return [trim_coords(v) for v in node]
    return node


def slim(feature, keep):
    props = feature.get("properties") or {}
    if keep:
        props = {k: v for k, v in props.items() if k in keep and v not in (None, "", "Null")}
    else:
        props = {k: v for k, v in props.items() if v not in (None, "", "Null")}
    geom = feature.get("geometry")
    if geom and "coordinates" in geom:
        geom = dict(geom)
        geom["coordinates"] = trim_coords(geom["coordinates"])
    return {"type": "Feature", "properties": props, "geometry": geom}


def fetch_layer(src):
    features = []
    offset = 0
    page = src["page"]

    while True:
        url = query_url(src, offset, page)
        raw = get(url)
        try:
            doc = json.loads(raw)
        except json.JSONDecodeError:
            raise RuntimeError("server did not return JSON")

        if "error" in doc:
            raise RuntimeError(doc["error"].get("message", "server error"))

        batch = doc.get("features") or []
        features.extend(batch)
        sys.stdout.write(f"\r    {len(features):,} features…")
        sys.stdout.flush()

        if len(batch) < page or not doc.get("exceededTransferLimit", False):
            if len(batch) < page:
                break
        offset += page
        if offset > 200000:
            break

    sys.stdout.write("\r" + " " * 40 + "\r")
    keep = set(src.get("keep") or [])
    features = [slim(f, keep) for f in features]
    return {"type": "FeatureCollection", "features": features}


def check():
    print("Checking sources.\n")
    bad = 0
    for src in SOURCES:
        base = src["url"].rsplit("/query", 1)[0]
        try:
            doc = json.loads(get(base + "?f=json", timeout=30))
            label = doc.get("name") or doc.get("mapName") or "ok"
            print(f"  OK    {src['name']:<14} {label}")
        except Exception as exc:
            bad += 1
            print(f"  FAIL  {src['name']:<14} {exc}")
            print(f"        {base}")
    print()
    if bad:
        print(f"{bad} source(s) unreachable. If it's not your connection,")
        print("the agency moved the service — find the new address in their")
        print("REST directory and update the url in SOURCES above.")
    else:
        print("All four sources are live.")
    return 1 if bad else 0


def vendor():
    os.makedirs(VENDOR, exist_ok=True)
    for url, name in VENDOR_FILES:
        dest = os.path.join(VENDOR, name)
        if os.path.exists(dest):
            print(f"  have  {name}")
            continue
        print(f"  get   {name}")
        with open(dest, "wb") as fh:
            fh.write(get(url))


def main():
    if "--check" in sys.argv:
        return check()

    w, s, e, n = BBOX
    print(f"Area: {abs(e - w):.2f}° x {abs(n - s):.2f}°  ({w}, {s}) to ({e}, {n})\n")

    os.makedirs(DATA, exist_ok=True)

    print("Map library")
    vendor()

    print("\nData")
    failed = []
    for src in SOURCES:
        print(f"  {src['name']}")
        print(f"    {src['who']}")
        try:
            geo = fetch_layer(src)
        except Exception as exc:
            print(f"    could not download: {exc}\n")
            failed.append(src["name"])
            continue

        path = os.path.join(DATA, src["out"])
        with open(path, "w") as fh:
            json.dump(geo, fh)
        size = os.path.getsize(path) / 1048576
        count = len(geo["features"])
        if count == 0:
            print(f"    no features in this area — widen BBOX if that's unexpected\n")
        else:
            print(f"    {count:,} features, {size:.1f} MB -> data/{src['out']}\n")

    if failed:
        print("Incomplete: " + ", ".join(failed))
        print("Run  python3 fetch.py --check  to see which sources are down.")
        print("The map still opens; missing layers show as unavailable.")
    else:
        print("Done. Open index.html and everything should be there.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
