#!/usr/bin/env python3
"""Build the map's land outlines from Natural Earth 110m.

The first draft drew only a graticule. That was a defensible choice on paper -
the artifact CSP blocks every external request, and coastlines are the wrong
authority for a map of shifting historical entities - but it is wrong in
practice: bubbles floating on bare grid lines give a reader nothing to locate
them against, and the map reads as broken rather than as minimal.

Source: Natural Earth 1:110m "land" (ne_110m_land), public domain, no
permission or attribution required. Fetched once and committed, so the build
stays offline and reproducible:

  curl -o reference/ne_110m_land.geojson \\
    https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_land.geojson
  python3 scripts/build_world_land.py

Rings are stored in LON/LAT, not in screen units, so the projection can change
without refetching; the page projects them with the same px()/py() it uses for
the bubbles. Simplification is done in degrees with shapely, and everything is
clipped to the map's window, which drops Antarctica and the far Pacific
outright rather than carrying points that are never drawn.
"""
import json
from pathlib import Path
from shapely.geometry import shape, box, mapping
from shapely.ops import unary_union

SRC = Path('reference/ne_110m_land.geojson')
OUT = Path('reference/world_land_110m.json')
# must match LON/LAT in the artifact template
LON, LAT = (-135, 182), (-52, 74)
TOLERANCE = 0.25          # degrees; ~25km, below one pixel at this scale
MIN_AREA = 0.6            # deg^2; drops specks that render as a dot or less


def main():
    fc = json.loads(SRC.read_text())
    win = box(LON[0], LAT[0], LON[1], LAT[1])
    geoms = []
    for f in fc['features']:
        g = shape(f['geometry']).buffer(0)        # repair any self-intersection
        g = g.intersection(win)
        if g.is_empty:
            continue
        g = g.simplify(TOLERANCE, preserve_topology=True)
        if not g.is_empty:
            geoms.append(g)
    merged = unary_union(geoms)
    polys = getattr(merged, 'geoms', [merged])

    rings, pts = [], 0
    for poly in polys:
        if poly.area < MIN_AREA:
            continue
        for ring in [poly.exterior] + list(poly.interiors):
            coords = [[round(x, 2), round(y, 2)] for x, y in ring.coords]
            if len(coords) < 4:
                continue
            rings.append(coords)
            pts += len(coords)
    rings.sort(key=len, reverse=True)
    OUT.write_text(json.dumps(rings, separators=(',', ':')))
    print(f'{len(rings)} rings, {pts} points, {OUT.stat().st_size/1024:.0f} KB '
          f'-> {OUT}')


if __name__ == '__main__':
    main()
