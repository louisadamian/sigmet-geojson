import urllib.request
import json
import os
import datetime
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat(timespec="minutes")


def noaa_coords_to_geojson(coords: [dict]) -> [[float]]:
    new_coords = []
    for coord in coords:
        new_coords.append([coord.get("lon"), coord.get("lat")])

    return new_coords


def noaa_sigmet2geojson(noaa_json: dict) -> dict:
    features = []
    for met in noaa_json:
        met_geojson = {"type": "Feature"}
        coords = noaa_coords_to_geojson(met.get("coords"))
        if datetime.fromtimestamp(met.get("validTimeTo")) is not None:
            valid_to_time = datetime.fromtimestamp(met.get("validTimeTo"))
            if valid_to_time.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                continue
        if len(coords) < 1 or met.get("airSigmetType") == "AIRMET":
            continue

        properties = {
            "airSigmetId": met.get("airSigmetId"),
            "airportIcao": met.get("icaoId"),
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
        if met.get("ValidFromTime") is not None:
            properties["validTimeFrom"] = (
                datetime.fromtimestamp(met.get("validTimeFrom")).isoformat(
                    timespec="minutes"
                ),
            )
        if met.get("validTimeTo") is not None:
            properties["validTimeTo"] = (
                met.get("validTimeTo").isoformat(timespec="minutes"),
            )
        geometry = {
            "type": "Polygon",
            "coordinates": [coords],
        }
        met_geojson["geometry"] = geometry
        met_geojson["properties"] = properties
        features.append(met_geojson)

    geojson_dict = {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {"creationTime": utcnow()},
    }
    return geojson_dict


def noaa_airmet2geojson(noaa_json: dict) -> dict:
    features = []
    for met in noaa_json:
        met_geojson = {"type": "Feature"}
        coords = noaa_coords_to_geojson(met.get("coords"))
        if met.get("validTimeTo") is not None:
            valid_to_time = datetime.fromtimestamp(met.get("validTimeTo"))
            if valid_to_time.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                continue
        if len(coords) < 1:
            continue
        properties = {
            "forecastId": met.get("icaoId"),
            "geometryId": met.get("geometryId"),
            "tag": met.get("tag"),
            "forecastHour": met.get("forecastHour"),
            "hazard": met.get("hazard"),
            "frequency": met.get("frequency"),
            "severity": met.get("severity"),
            "status": met.get("status"),
            "base": met.get("base"),
            "top": met.get("top"),
            "fzlBase": met.get("fzlbase"),
            "fzlTop": met.get("fzltop"),
            "level": met.get("level"),
            "product": met.get("product"),
            "rawAirSigmet": met.get("due_to"),
        }
        if met.get("validTime") is not None:
            properties["validTimeTo"] = met.get("validTime").replace("Z", "")
        else:
            properties["validTimeTo"] = None
        if met.get("issueTime") is not None:
            properties["validTimeFrom"] = (
                datetime.fromtimestamp(met.get("issueTime")).isoformat(
                    timespec="minutes"
                ),
            )
        geotype = met.get("geometryType")
        if geotype == "AREA":
            geometry = {
                "type": "Polygon",
                "coordinates": [coords],
            }
        elif geotype == "LINE":
            geometry = {
                "type": "LineString",
                "coordinates": coords,
            }
        else:
            continue
        met_geojson["geometry"] = geometry
        met_geojson["properties"] = properties
        features.append(met_geojson)
    return {
        "type": "FeatureCollection",
        "features": features,
        "metadata": {"creationTime": utcnow()},
    }


def move_old_file(filename, new_name_prefix, archive_dir):
    if os.path.isfile(filename):
        with open(filename) as oldfile:
            old_geojson = json.loads(oldfile.read())
            new_name_prefix += old_geojson["metadata"]["creationTime"] + ".geojson"
        if not os.path.isdir("./data/archive"):
            os.mkdir("./data/archive")
        if not os.path.isdir("./data/archive/" + archive_dir):
            os.mkdir("./data/archive/" + archive_dir)
        os.rename(filename, "./data/archive/" + archive_dir + "/" + new_name_prefix)


if __name__ == "__main__":
    usa_sigmet_url = (
        "https://aviationweather.gov/api/data/airsigmet?format=json&type=sigmet&date="
        + utcnow().replace(":", "%3A")
        + "Z"
    )
    usa_sigmet_filename = "./data/usa_sigmets_current.geojson"
    move_old_file(usa_sigmet_filename, "usa_sigmets_", "usa")
    contents = urllib.request.urlopen(usa_sigmet_url).read().decode()
    met_json = json.loads(contents)
    geojson = json.dumps(noaa_sigmet2geojson(met_json), indent=4)
    if not os.path.exists("./data"):
        os.mkdir("./data")
    with open(usa_sigmet_filename, "x") as geojson_file:
        geojson_file.write(geojson)

    usa_airmet_url = (
        "https://aviationweather.gov/api/data/gairmet?format=json&date="
        + utcnow().replace(":", "%3A")
        + "Z"
    )
    usa_airmet_filename = "./data/usa_airmets_current.geojson"
    move_old_file(usa_airmet_filename, "usa_airmets_", "airmet")
    contents = urllib.request.urlopen(usa_airmet_url).read().decode()
    met_json = json.loads(contents)
    geojson = json.dumps(noaa_airmet2geojson(met_json), indent=4)
    with open(usa_airmet_filename, "x") as geojson_file:
        geojson_file.write(geojson)
