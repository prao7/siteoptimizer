import os
import pandas as pd
import geopandas as gpd
import numpy as np
from shapely.geometry import Point
from shapely.ops import unary_union
import matplotlib.pyplot as plt
from matplotlib import cm
import contextily as ctx


def calculate_zone_lcoe_trans_distances(
    potential_sites_df: pd.DataFrame,
    zones: dict[str, object],
    transmission_distances: pd.DataFrame,
    hub_zone: str,
    is_wind: bool = True
) -> pd.DataFrame:
    """
    Adds:
      - zone_project (by spatial test against zones)
      - zone_lcoe = total_lcoe + transmission surcharge to hub_zone

    where surcharge = distance(km) * 1500 * (1/1000) * CRF(4%,60y),
    except if zone_project == hub_zone, surcharge is zero.
    """

    df = potential_sites_df.copy()
    td = transmission_distances.copy()

    # ensure index is first column
    first_col = td.columns[0]
    if first_col not in td.index:
        td = td.set_index(first_col)

    # build geometry and assign zone_project
    gdf = gpd.GeoDataFrame(
        df,
        geometry=[Point(x, y) for x, y in zip(df.longitude, df.latitude)],
        crs="EPSG:4326"
    )
    gdf["zone_project"] = None
    for zname, geom in zones.items():
        gdf.loc[gdf.geometry.within(geom), "zone_project"] = zname

    cf_col = "mean_cf" if is_wind else "mean_cf_ac"

    # capital recovery factor
    r, n = 0.04, 60
    crf = r * (1 + r) ** n / ((1 + r) ** n - 1)

    def _compute(row):
        zone = row.zone_project
        cf = row.get(cf_col, 0.0)
        base = row.get("total_lcoe", 0.0)

        if zone is None or cf <= 0:
            return float('inf')

        if zone == hub_zone:
            return base

        try:
            dist = td.at[zone, hub_zone]
            if pd.isna(dist):
                dist = 0.0
        except KeyError:
            dist = 0.0

        to_cost = dist * 1500 * (1 / 1000) * crf  # $/kW-yr
        return base + (to_cost * 1000) / (cf * 8760)

    gdf["zone_lcoe"] = gdf.apply(_compute, axis=1)

    return gdf.drop(columns="geometry")


def load_zone_geometries(shapefiles: dict[str, str]) -> dict[str, object]:
    zones = {}
    for zone, path in shapefiles.items():
        gdf = gpd.read_file(path)
        # reproject to lat/lon to match your point GeoDataFrame
        gdf = gdf.to_crs("EPSG:4326")
        zones[zone] = gdf.geometry.unary_union
    return zones


def multi_zone_filter_and_select_sites(
    csv_file_path: str,
    shapefiles: dict[str, str],
    system: dict[str, dict[str, float]],
    distances_csv_path: str,
    output_dir: str,
    region: str,
    is_wind: bool = True
) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    # load inputs
    base_df = pd.read_csv(csv_file_path)
    dist_df = pd.read_csv(distances_csv_path, index_col=0)

    cf_col = "mean_cf" if is_wind else "mean_cf_ac"
    cap_col = "capacity_mw" if is_wind else "capacity_mw_dc"
    final_cols = ["sc_point_gid", "latitude", "longitude", cf_col, cap_col,
                  "energy_amw", "zone_lcoe", "total_lcoe", "class", "area_sq_km", "zone_project"]

    zones = load_zone_geometries(shapefiles)
    results = {}

    for curr_zone, constraints in system.items():
        # apply LCOE + surcharge
        zone_df = calculate_zone_lcoe_trans_distances(
            base_df, zones, dist_df, curr_zone, is_wind=is_wind
        )
        zone_df = zone_df[zone_df.zone_lcoe <= 150]

        # spatial filter against all zones
        gdf = gpd.GeoDataFrame(
            zone_df,
            geometry=[Point(x, y) for x, y in zip(zone_df.longitude, zone_df.latitude)],
            crs="EPSG:4326"
        )
        boundary = unary_union(list(zones.values()))
        filtered = gdf[gdf.geometry.within(boundary)]

        # compute energy and sort
        filtered["energy_amw"] = filtered[cf_col] * filtered[cap_col]
        filtered.sort_values(by=["zone_lcoe", cf_col], ascending=[True, False], inplace=True)

        # select sites under per-zone and system thresholds
        unique_zones = filtered["zone_project"].unique()
        shadow_df = pd.DataFrame(0, index=[0], columns=unique_zones)
        total_energy = 0.0
        selected = pd.DataFrame(columns=final_cols)

        for _, site in filtered.iterrows():
            zone = site.zone_project
            energy = site.energy_amw
            regional_ok = shadow_df.at[0, zone] + energy <= constraints["region_amw_threshold"]
            if regional_ok and total_energy + energy <= constraints["min_amw"]:
                selected = pd.concat([selected, pd.DataFrame([site])], ignore_index=True)
                if not (is_wind and zone == "PH"):
                    shadow_df.at[0, zone] += energy
                total_energy += energy
            if total_energy >= constraints["min_amw"]:
                break

        results[curr_zone] = selected[final_cols]
        if is_wind:
            selected[final_cols].to_csv(os.path.join(output_dir, f"{curr_zone}_wind.csv"), index=False)
        else:
            selected[final_cols].to_csv(os.path.join(output_dir, f"{curr_zone}_pv.csv"), index=False)

    # aggregate final
    final_sites = filter_best_sites(results)
    if is_wind:
        final_sites.to_csv(os.path.join(output_dir, f"{region}_wind.csv"), index=False)
    else:
        final_sites.to_csv(os.path.join(output_dir, f"{region}_pv.csv"), index=False)

    return results, final_sites


def filter_best_sites(results: dict[str, pd.DataFrame]) -> pd.DataFrame:
    combined = pd.concat(results.values(), ignore_index=True)
    combined.sort_values(by=["zone_lcoe", "energy_amw"], ascending=[True, False], inplace=True)

    total_energy = combined.energy_amw.sum()
    threshold = total_energy * 1.5
    alloc = 0.0
    final = pd.DataFrame()

    for _, site in combined.iterrows():
        if alloc + site.energy_amw <= threshold:
            final = pd.concat([final, pd.DataFrame([site])], ignore_index=True)
            alloc += site.energy_amw
        if alloc >= threshold:
            break
    return final


def plot_filtered_data_on_map(filtered_df, boundary, title, is_wind=True):
    # Create a GeoDataFrame from the filtered data
    geometry = [Point(xy) for xy in zip(filtered_df['longitude'], filtered_df['latitude'])]
    gdf = gpd.GeoDataFrame(filtered_df, geometry=geometry, crs="EPSG:4326")

    # Plot the boundary and the filtered data points
    fig, ax = plt.subplots(figsize=(10, 10))
    boundary.to_crs(epsg=3857).plot(ax=ax, color='none', edgecolor='black')

    capacity_col = 'capacity_mw' if is_wind else 'capacity_mw_dc'

    # Set the marker size proportional to the capacity (scaled)
    marker_sizes = gdf[capacity_col] / gdf[capacity_col].max() * 100  # Scale marker sizes based on max capacity

    # Plot sites with circle size based on capacity
    gdf.to_crs(epsg=3857).plot(ax=ax, color='red', markersize=marker_sizes)

    # Add basemap
    ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, zoom=6)

    plt.title(title)
    plt.show()


def plot_sites_on_osm(
    df,
    shapefile_dict: dict[str, str],
    is_wind: bool,
    output_dir: str,
    zoom: int = 6
) -> str:
    """
    Plot site locations on top of provided shapefile zones, on an OpenStreetMap basemap.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain columns 'longitude', 'latitude', 'capacity', 'capacity_factor'.
    shapefile_dict : dict[str, str]
        Mapping from zone name (e.g. "p48") to that zone's .shp filepath.
    is_wind : bool
        If True, wind sites are blue; if False, solar sites are red.
    output_dir : str
        Directory where the PNG will be saved.
    zoom : int
        Contextily zoom level for the basemap (default 6).

    Returns
    -------
    str
        Path to the saved plot image.
    """
    # 1) set up figure
    fig, ax = plt.subplots(figsize=(12, 8))

    # 2) plot each zone outline
    for zone_name, shp_path in shapefile_dict.items():
        try:
            zone_gdf = gpd.read_file(shp_path).to_crs(epsg=3857)
            zone_gdf.plot(
                ax=ax,
                facecolor='none',
                edgecolor='black',
                linewidth=1,
                label=zone_name
            )
        except Exception as e:
            print(f"Warning: could not read {zone_name} at {shp_path}: {e}")

    # 3) convert site DataFrame to GeoDataFrame in Web Mercator
    sites = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df.longitude, df.latitude),
        crs='EPSG:4326'
    ).to_crs(epsg=3857)

    # 4) marker sizing and coloring
    if is_wind:
        cap_col = 'capacity_mw'
    else:
        cap_col = 'capacity_mw_dc'
    cap = df[cap_col].values
    sizes = 50 + (cap / cap.max()) * 450
    cmap = cm.Blues if is_wind else cm.Reds

    if is_wind:
        capacity_factor_col = 'mean_cf'
    else:
        capacity_factor_col = 'mean_cf_ac'

    sc = ax.scatter(
        sites.geometry.x,
        sites.geometry.y,
        s=sizes,
        c=df[capacity_factor_col],
        cmap=cmap,
        alpha=0.7,
        edgecolor='k',
        linewidth=0.4,
        label='Sites'
    )

    # 5) add the OSM basemap underneath
    ctx.add_basemap(
        ax,
        source=ctx.providers.OpenStreetMap.Mapnik,
        zoom=zoom
    )

    # 6) finish styling: colorbar, legend, title, axes
    cbar = plt.colorbar(sc, ax=ax, shrink=0.6)
    cbar.set_label('Capacity Factor')

    ax.legend(loc='upper right', fontsize='small', framealpha=0.5)
    ax.set_axis_off()
    ax.set_title(f"{'Wind' if is_wind else 'Solar'} Sites on OSM", fontsize=14)

    # 7) save to disk
    os.makedirs(output_dir, exist_ok=True)
    fname = f"{'wind' if is_wind else 'solar'}_sites_osm.png"
    outpath = os.path.join(output_dir, fname)
    fig.savefig(outpath, dpi=300, bbox_inches='tight')
    plt.close(fig)

    return outpath



if __name__ == "__main__":

    region = "ERCOT"
    # ERCOT paths
    wind_output_file_path = f"site_extractions/{region}_wind.csv"
    solar_output_file_path = f"site_extractions/{region}_pv.csv"

    # Paths to the wind and solar CSVs
    wind_csv_path = 'supply_curves/wind-ons_supply_curve_raw.csv'
    solar_csv_path = 'supply_curves/upv_supply_curve_raw.csv'


    transmission_csv_path = f"centroids/{region}_zone_distances.csv"
    output_dir = "site_extractions"

    # Multiplier: 0.1141552511
    system = {"p48": {"min_amw": 46, "region_amw_threshold": 20000}, # 399368 MWh
                    "p57": {"min_amw": 11, "region_amw_threshold": 20000}, # 94744 MWh
                    "p60": {"min_amw": 822, "region_amw_threshold": 20000}, # 7193341 MWh
                    "p61": {"min_amw": 1357, "region_amw_threshold": 20000}, # 11880853 MWh
                    "p62": {"min_amw": 2249, "region_amw_threshold": 20000}, # 19694716 MWh
                    "p63": {"min_amw": 18133, "region_amw_threshold": 20000}, # 158843352 MWh
                    "p64": {"min_amw": 5589, "region_amw_threshold": 20000}, # 48959076 MWh
                    "p65": {"min_amw": 8326, "region_amw_threshold": 20000}, # 72932609 MWh
                    "p66": {"min_amw": 1310, "region_amw_threshold": 20000}, # 11484630 MWh
                    "p67": {"min_amw": 11358, "region_amw_threshold": 20000} # 99492906 MWh
    }

    shapefiles = {"p48": 'output_shapefiles/p48.shp',
                        "p57": 'output_shapefiles/p57.shp',
                        "p60": 'output_shapefiles/p60.shp',
                        "p61": 'output_shapefiles/p61.shp',
                        "p62": 'output_shapefiles/p62.shp',
                        "p63": 'output_shapefiles/p63.shp',
                        "p64": 'output_shapefiles/p64.shp',
                        "p65": 'output_shapefiles/p65.shp',
                        "p66": 'output_shapefiles/p66.shp',
                        "p67": 'output_shapefiles/p67.shp'
                        }

    solar_individual_sites, solar_filtered_sites = multi_zone_filter_and_select_sites(solar_csv_path, shapefiles, system, transmission_csv_path, output_dir, region, is_wind=False)
    wind_individual_sites, wind_filtered_sites = multi_zone_filter_and_select_sites(wind_csv_path, shapefiles, system, transmission_csv_path, output_dir, region, is_wind=True)

    # Plot the results
    plot_sites_on_osm(solar_filtered_sites, shapefiles, is_wind=False, output_dir=output_dir)
    plot_sites_on_osm(wind_filtered_sites, shapefiles, is_wind=True, output_dir=output_dir)
