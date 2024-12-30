import urllib.request
import json
import os
import datetime


def noaa_coords_to_geojson(coords: [dict]) -> [[float]]:
    new_coords = []
    for coord in coords:
        new_coords.append([coord.get("lat"), coord.get("lon")])
    return new_coords


def noaa_2geojson(noaa_json: dict) -> dict:
    features = []
    for met in noaa_json:
        met_geojson = {"type": "Feature"}
        properties = {
            "airSigmetId": met.get("airSigmetId"),
            "airportIcao": met.get("icaoId"),
            "validTimeFrom": datetime.datetime.fromtimestamp(
                met.get("validTimeFrom")
            ).isoformat(timespec="minutes"),
            "validTimeTo": datetime.datetime.fromtimestamp(
                met.get("validTimeTo")
            ).isoformat(timespec="minutes"),
            "airSigmetType": met.get("airSigmetType"),
            "hazard": met.get("hazard"),
            "severity": met.get("severity"),
            "altitudeLow1": met.get("altitudeLow1"),
            "altitudeLow2": met.get("altitudeLow2"),
            "altitudeHi1": met.get("altitudeHi1"),
            "altitudeHi2": met.get("altitudeHi2"),
            "movementDir": met.get("movementDir"),
            "movementSpd": met.get("movementSpd"),
            "rawAirSigmet": met.get("rawAirSigmet"),
        }
        geometry = {
            "type": "Polygon",
            "coordinates": noaa_coords_to_geojson(met.get("coords")),
        }
        met_geojson["geometry"] = geometry
        met_geojson["properties"] = properties
        features.append(met_geojson)

    geojson_dict = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {
            "creationTime": datetime.datetime.utcnow().isoformat(timespec="minutes")
        },
    }
    return geojson_dict


if __name__ == "__main__":
    usa_filename = "./data/usa_air_sigmets_current.geojson"
    if os.path.isfile(usa_filename):
        newname = "usa_air_sigmets_"
        with open(usa_filename) as oldfile:
            old_geojson = json.loads(oldfile.read())
            newname += old_geojson["metadata"]["creationTime"] + ".geojson"
        if not os.path.isdir("./data/archive/usa"):
            os.mkdir("./data/archive/usa")
        os.rename("./data/air_sigmets_current.geojson", "./data/archive/usa/" + newname)
    contents = (
        urllib.request.urlopen(
            "https://aviationweather.gov/api/data/airsigmet?format=json"
        )
        .read()
        .decode()
    )
    met_json = json.loads(contents)

    geojson = json.dumps(noaa_2geojson(met_json), indent=4)
    if not os.path.isdir("./data"):
        os.mkdir("./data")
    with open(usa_filename, "x") as geojson_file:
        geojson_file.write(geojson)
