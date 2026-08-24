"""
Figure 4 regeneration, step 2 of 2 (Jul 2026 revision).

Composites, per city, the confirmed risk RGB composite over the open-licensed
Sentinel-2 basemap (replacing the Google/NASA basemap that cannot be published
under CC BY). Adds the reviewer-requested in-map legend, a scale bar, and the
city-center marker to each panel, then assembles the 2x2 figure.

Risk composite (confirmed by the author, matching submitted Fig 4):
  bands   R = exInunD (IR-AED), G = exDmg (FD-AED), B = exDmg_pros (FD-AED-P)
  stretch min = 0.1, max = 0.01 (GEE inverted stretch), gamma = 1
Where the risk layer is masked (NaN, ~half of pixels outside floodplains/
buildings) the Sentinel-2 basemap shows through, exactly as in the original.

Sentinel-2 basemap: bands B4,B3,B2; stretch min 0, max 2500, gamma 1.2.
"""

import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from pathlib import Path

import paths

TIF_DIR = paths.FIG4_TIFFS
OUT_DIR = paths.OUTPUT

# Fallback for panels whose (very large) Sentinel-2 export is no longer on disk.
# Shanghai_s2rgb_2026-7.tif (~2.1 GB) was removed during cleanup, so its finished
# panel is reused from a cached render instead of being recomposited. The cached
# panel already has its legend, scale bar, and city-center marker burned in, so
# those overlays are not redrawn for it. To rebuild such a panel from scratch,
# re-download the missing GeoTIFF from the Drive folder fig4_tiffs_2026-7 and
# delete the corresponding cache file.
PANEL_CACHE = paths.DATA / "fig4_panel_cache"

CITIES = ["Shanghai", "Guangzhou", "Bangkok", "Dhaka"]
PANEL_LABEL = {"Shanghai": "(a) Shanghai", "Guangzhou": "(b) Guangzhou",
               "Bangkok": "(c) Bangkok", "Dhaka": "(d) Dhaka"}
CITY_CENTER = {  # lon, lat of the yellow triangle
    "Shanghai": (121.47, 31.23), "Guangzhou": (113.26, 23.13),
    # Bangkok nudged ~one marker width (0.05 deg lon) east per author check
    "Bangkok": (100.55, 13.75), "Dhaka": (90.41, 23.81),
}
# all four panels are rendered to this identical pixel grid so they share height and
# width; each city's extent is cropped (centered) to the common display aspect first
COMMON_ASPECT = 1.40   # display width / height (mean of the four city extents)
OUT_W, OUT_H = 1400, 1000  # 1400/1000 = 1.40

# risk stretch (inverted) and basemap stretch
R_MIN, R_MAX = 0.1, 0.01
S2_MIN, S2_MAX, S2_GAMMA = 0.0, 2500.0, 1.2


def stretch_risk(band):
    """GEE inverted linear stretch -> [0,1]; NaN preserved."""
    return np.clip((band - R_MIN) / (R_MAX - R_MIN), 0, 1)


def crop_to_aspect(bounds):
    """Crop (left, bottom, right, top) centered to COMMON_ASPECT in display units."""
    l, b, r, t = bounds
    cosphi = np.cos(np.radians((t + b) / 2))
    disp_w = (r - l) * cosphi
    disp_h = t - b
    if disp_w / disp_h > COMMON_ASPECT:      # too wide -> trim longitude
        new_lon = (COMMON_ASPECT * disp_h) / cosphi
        cx = (l + r) / 2
        l, r = cx - new_lon / 2, cx + new_lon / 2
    else:                                     # too tall -> trim latitude
        new_lat = disp_w / COMMON_ASPECT
        cy = (t + b) / 2
        b, t = cy - new_lat / 2, cy + new_lat / 2
    return l, b, r, t


def build_grid(risk_path, s2_path):
    """Crop to the common aspect, then reproject risk/S2 onto the fixed OUT_W x OUT_H grid."""
    with rasterio.open(risk_path) as rsrc:
        l, b, r, t = crop_to_aspect(tuple(rsrc.bounds))
        dst_transform = rasterio.transform.from_bounds(l, b, r, t, OUT_W, OUT_H)
        risk = np.full((3, OUT_H, OUT_W), np.nan, np.float32)
        reproject(rsrc.read(), risk, src_transform=rsrc.transform, src_crs=rsrc.crs,
                  dst_transform=dst_transform, dst_crs=rsrc.crs,
                  src_nodata=np.nan, dst_nodata=np.nan, resampling=Resampling.nearest)

    with rasterio.open(s2_path) as ssrc:
        s2 = np.zeros((3, OUT_H, OUT_W), np.float32)
        reproject(ssrc.read(), s2, src_transform=ssrc.transform, src_crs=ssrc.crs,
                  dst_transform=dst_transform, dst_crs=ssrc.crs,
                  resampling=Resampling.bilinear)
    return risk, s2, dst_transform, (l, r, b, t)


def composite(risk, s2):
    # basemap RGB
    base = np.clip(s2 / S2_MAX, 0, 1) ** (1.0 / S2_GAMMA)
    base = np.moveaxis(base, 0, -1)  # h,w,3
    # risk RGB
    rr = np.stack([stretch_risk(risk[i]) for i in range(3)], axis=-1)  # h,w,3
    has = np.isfinite(risk).all(axis=0)  # data mask
    out = base.copy()
    out[has] = rr[has]
    return out


def scalebar_km(ax, extent, y_frac=0.06, x_frac=0.06):
    lon0, lon1, lat0, lat1 = extent
    latmid = (lat0 + lat1) / 2
    km_per_deg = 111.32 * np.cos(np.radians(latmid))
    span_km = (lon1 - lon0) * km_per_deg
    # nice round bar ~1/4 of width
    target = span_km / 4
    nice = min([1, 2, 5, 10, 20, 50], key=lambda v: abs(v - target))
    bar_deg = nice / km_per_deg
    x = lon0 + (lon1 - lon0) * x_frac
    y = lat0 + (lat1 - lat0) * y_frac
    ax.add_line(Line2D([x, x + bar_deg], [y, y], color="white", lw=3, solid_capstyle="butt"))
    ax.text(x + bar_deg / 2, y + (lat1 - lat0) * 0.012, f"{nice} km",
            color="white", ha="center", va="bottom", fontsize=7,
            path_effects=_stroke())


def _stroke():
    import matplotlib.patheffects as pe
    return [pe.withStroke(linewidth=1.6, foreground="black")]


def add_legend(ax):
    """In-map legend with dark background: composite color swatches + city-center marker."""
    items = [
        ("swatch", "#ff5cc8", "High IR-AED & FD-AED"),
        ("swatch", "#2f6bd6", "High FD-AED, low IR-AED"),
        ("swatch", "#9b6fd4", "Moderate risk"),
        ("tri", "#ffdd00", "City center"),
    ]
    bx, by, bw, bh = 0.02, 0.60, 0.45, 0.375
    ax.add_patch(Rectangle((bx, by), bw, bh, transform=ax.transAxes,
                           facecolor="black", alpha=0.5, edgecolor="none", zorder=5))
    ax.text(bx + 0.02, by + bh - 0.045, "Composite flood risk", transform=ax.transAxes,
            fontsize=7.2, fontweight="bold", color="white", va="center", zorder=6)
    y0 = by + bh - 0.125
    for i, (kind, c, lab) in enumerate(items):
        yy = y0 - i * 0.072
        if kind == "swatch":
            ax.add_patch(Rectangle((bx + 0.03, yy - 0.018), 0.038, 0.036, transform=ax.transAxes,
                                   facecolor=c, edgecolor="white", lw=0.5, zorder=6))
        else:
            ax.plot(bx + 0.049, yy, marker="v", ms=8, mfc=c, mec="white", mew=0.7,
                    transform=ax.transAxes, zorder=6)
        ax.text(bx + 0.085, yy, lab, transform=ax.transAxes, fontsize=6.6,
                color="white", va="center", zorder=6)


def main():
    plt.rcParams["font.family"] = ["Arial", "DejaVu Sans"]
    fig, axes = plt.subplots(2, 2, figsize=(7.2, 5.4))

    for ax, city in zip(axes.ravel(), CITIES):
        risk_p = TIF_DIR / f"{city}_risk_2026-7.tif"
        s2_p = TIF_DIR / f"{city}_s2rgb_2026-7.tif"
        cache_p = PANEL_CACHE / f"{city}_panel_rendered.png"
        burned_in = not s2_p.exists() and cache_p.exists()

        if burned_in:
            rgb = plt.imread(cache_p)
            with rasterio.open(risk_p) as rsrc:
                l, b, r, t = crop_to_aspect(tuple(rsrc.bounds))
            extent = (l, r, b, t)
        else:
            risk, s2, _, extent = build_grid(risk_p, s2_p)
            rgb = composite(risk, s2)
        # aspect="auto" makes every panel fill its equal grid cell, so all four share
        # identical height and width; extents are pre-cropped to the common aspect so
        # the maps are not distorted relative to one another
        ax.imshow(rgb, extent=extent, origin="upper", interpolation="nearest", aspect="auto")
        ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])

        if not burned_in:   # cached panels already carry these overlays
            lon, lat = CITY_CENTER[city]
            ax.plot(lon, lat, marker="v", ms=11, mfc="#ffdd00", mec="black", mew=1.0, zorder=7)
            add_legend(ax)
            scalebar_km(ax, extent)
        ax.set_title(PANEL_LABEL[city], fontsize=10, loc="left", fontweight="bold", pad=3)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_edgecolor("0.4"); s.set_linewidth(0.6)
        print(f"composed {city}: {rgb.shape[1]}x{rgb.shape[0]}" + (" [cached panel]" if burned_in else ""))

    fig.tight_layout(h_pad=1.2, w_pad=0.8)
    for ext in ("png", "pdf"):
        fig.savefig(OUT_DIR / f"Fig4_city_maps_2026-7.{ext}", dpi=300,
                    bbox_inches="tight", facecolor="white")
    print("saved", OUT_DIR / "Fig4_city_maps_2026-7.png")


if __name__ == "__main__":
    main()
