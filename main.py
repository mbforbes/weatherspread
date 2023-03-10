import calendar
import code
from datetime import datetime
import json
import os
from typing import List, Tuple, Dict

from geopy.geocoders import Nominatim
from jinja2 import Template
from mbforbes_python_utils import read, write
from meteostat import Point, Daily
import pandas as pd
import requests

""" (location name, [(year, [(month, [temp1, temp2, ...], [precip, precip2, ...])])]"""
Data = Tuple[str, List[Tuple[int, List[Tuple[int, List[float], List[float]]]]]]

# format {"Display Name": [lat, lon], ...}
LOCATION_CACHE_PATH = "cache/locations.json"
LocationCache = Dict[str, Tuple[float, float]]


def get_data_vc(
    location_display: str,
    temperature_key: str,
    months=[2, 3],
    years=[2020, 2021, 2022],
) -> Data:
    """Uses visualcrossing.
    temperature_key: "tempmax" or "feelslikemax"
    """
    # global settings
    api_key = read("secrets/visualcrossing_api_key.txt")
    # print(api_key)
    base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
    unit_group = "us"  # vs metric
    content_type = "json"
    include = "days"

    all_data = []
    for year in years:
        year_data = []
        for month in months:
            last_month_day = calendar.monthrange(year, month)[1]

            # request settings
            # location_display = "Tirana, Albania"  # NOTE: Try with spaces later
            location = location_display.replace(" ", "")
            start_date = f"{year}-{month}-01"  # inclusive
            end_date = f"{year}-{month}-{last_month_day}"  # inclusive

            cache_path = (
                "cache/vc/" + "_".join([location, start_date, end_date]) + ".json"
            )
            if os.path.exists(cache_path):
                print("Cached data found")
                data = json.loads(read(cache_path))
            else:
                print("Requesting data")
                url = f"{base_url}/{location}/{start_date}/{end_date}?unitGroup={unit_group}&contentType={content_type}&include={include}&key={api_key}"
                response = requests.get(url)
                assert response.status_code == 200, "Not handling bad responses rn."
                # print(response.json())
                data = response.json()
                print("Saving to cache")
                with open(cache_path, "w") as f:
                    json.dump(data, f)

            # now, weather is in obj data. type given in doc/response.py
            year_data.append(
                (
                    month,
                    [day[temperature_key] for day in data["days"]],
                    [day["precip"] for day in data["days"]],  # inches
                )
            )
        all_data.append((year, year_data))
    return (location_display, all_data)


def location2latlon(lc: LocationCache, display_name: str) -> Tuple[float, float]:
    """Cache-aware. uses Nominatim to fetch if unknown."""
    if display_name in lc:
        return lc[display_name]
    position = Nominatim(user_agent=os.getlogin()).geocode(display_name)
    lat, lon = position.latitude, position.longitude
    lc[display_name] = (lat, lon)
    return (lat, lon)


def get_data_ms(
    lc: LocationCache,
    location_display_name: str,
    months=[2, 3],
    years=[2020, 2021, 2022],
) -> Data:
    """Uses meteostat (and geopy's nominatim).
    key: "tempmax" or "feelslikemax"
    """
    lat, lon = location2latlon(lc, location_display_name)

    # check cache
    location_cache_name = location_display_name.replace(" ", "")

    all_data = []
    for year in years:
        year_data = []
        for month in months:
            last_month_day = calendar.monthrange(year, month)[1]
            start_date = f"{year}-{month}-01"  # inclusive
            end_date = f"{year}-{month}-{last_month_day}"  # inclusive

            cache_path = (
                "cache/ms/"
                + "_".join([location_cache_name, start_date, end_date])
                + ".csv"
            )
            if os.path.exists(cache_path):
                print("Cached data found")
                data = pd.read_csv(cache_path)
            else:
                print("Requesting data")
                data = Daily(
                    Point(lat, lon),
                    datetime(year, month, 1),
                    datetime(year, month, last_month_day),
                ).fetch()
                print("Saving to cache")
                data.to_csv(cache_path)

            # print(year, month)
            # code.interact(local=dict(globals(), **locals()))

            year_data.append(
                (
                    month,
                    (data.tmax.fillna(0) * 1.8 + 32).tolist(),
                    # NOTE: Not sure about unit, maybe ml? so -> inches?
                    (data.prcp.fillna(0) * 0.0610237).tolist(),
                )
            )

        all_data.append((year, year_data))
    return (location_display_name, all_data)


def render_data(full_data: Data) -> str:
    location_display, all_data = full_data

    # render
    key = "tempmax"  # alt: "feelslikemax"
    # key = "feelslikemax"  # alt: "tempmax"

    buf = []
    buf.append(f"<h2 class='mt5'>{location_display}</h2>")
    prev_year = None
    for year, year_data in all_data:
        buf.append("<div>")
        for month, temps, precips in year_data:
            buf.append("<div class='dib mr3'>")
            for temp in temps:
                color = (
                    "dark-red"
                    if temp > 100
                    else ("red" if temp > 90 else ("yellow" if temp > 70 else "blue"))
                )
                buf.append(
                    f'<div style="width: 10px; height: {temp}px" class="bg-{color} dib mb0"></div>'
                )
            buf.append("<br class='mv0'>")
            for temp in temps:
                buf.append(
                    f"<span class='b dib' style='width: 10px; font-size: 7px;'>{round(temp)}</span>"
                )
            buf.append('<br><div style="height: 50px;">')
            for precip in precips:
                buf.append(
                    f'<div style="width: 10px; height: {precip * 10}px" class="bg-blue dib mb0 v-top o-80"></div>'
                )
            buf.append("</div>")

            # year, month, _ = start_date.split("-")
            buf.append(
                f"<h3 class='mt1 mb3 tc gray'>{calendar.month_name[month]}, {year}</h3>"
            )
            buf.append("</div>")
        buf.append("<div>")

    return "\n".join(buf)


def build_page_vc():
    buf = []

    buf.append(render_data(get_data_vc("Belgrade, Serbia", "tempmax")))
    buf.append(render_data(get_data_vc("Bucharest, Romania", "tempmax")))
    buf.append(render_data(get_data_vc("Sarajevo, Bosnia", "tempmax")))
    buf.append(render_data(get_data_vc("Tirana, Albania", "tempmax")))
    # buf.append(get_place_html("Tbilisi, Georgia"))

    templ_main = Template(read("templates/main.html"))
    write("output/tester-vc.html", templ_main.render(content="\n".join(buf)))


def build_page_ms(lc: LocationCache):
    buf = []

    # buf.append(render_data(get_data_ms(lc, "Zagreb, Croatia")))
    # buf.append(render_data(get_data_ms(lc, "Belgrade, Serbia")))
    # buf.append(render_data(get_data_ms(lc, "Bucharest, Romania")))
    # buf.append(render_data(get_data_ms(lc, "Sarajevo, Bosnia")))
    # buf.append(render_data(get_data_ms(lc, "Tirana, Albania")))
    # buf.append(render_data(get_data_ms(lc, "Tbilisi, Georgia")))
    # buf.append(render_data(get_data_ms(lc, "Skopje, North Macedonia")))
    # buf.append(render_data(get_data_ms(lc, "Tel Aviv, Israel")))
    # buf.append(render_data(get_data_ms(lc, "Edinburgh, Scotland")))
    # buf.append(render_data(get_data_ms(lc, "Kathmandu, Nepal")))
    # buf.append(render_data(get_data_ms(lc, "Seoul, South Korea", [8, 9, 10, 11])))
    # buf.append(render_data(get_data_ms(lc, "Sapporo, Japan", [8, 9, 10, 11])))
    # buf.append(render_data(get_data_ms(lc, "Tokyo, Japan", [8, 9, 10, 11])))
    # buf.append(render_data(get_data_ms(lc, "Miyazaki, Japan", [8, 9, 10, 11])))
    # buf.append(render_data(get_data_ms(lc, "Istanbul, Turkey")))
    # buf.append(render_data(get_data_ms(lc, "Tashkent, Uzbekistan")))
    # buf.append(render_data(get_data_ms(lc, "Montpellier, France", [7, 8, 9])))
    # buf.append(render_data(get_data_ms(lc, "Ulaanbaatar, Mongolia")))
    # buf.append(render_data(get_data_ms(lc, "Dalanzadgad, Mongolia")))

    # buf.append(render_data(get_data_ms(lc, "Hanoi, Vietnam", [11, 1])))
    # buf.append(render_data(get_data_ms(lc, "Haiphong, Vietnam", [11, 1])))
    # buf.append(render_data(get_data_ms(lc, "Sa Pa, Vietnam", [11, 1])))
    # buf.append(render_data(get_data_ms(lc, "Da Nang, Vietnam", [11, 1])))
    # buf.append(render_data(get_data_ms(lc, "Hoi An, Vietnam", [11, 1])))
    # buf.append(render_data(get_data_ms(lc, "Ho Chi Minh City, Vietnam", [11, 1])))

    # buf.append(render_data(get_data_ms(lc, "Taipei, Taiwan")))

    # buf.append(render_data(get_data_ms(lc, "Okinawa, Japan", [4, 5, 6])))
    buf.append(render_data(get_data_ms(lc, "Fukuoka, Japan", [4, 5])))
    buf.append(render_data(get_data_ms(lc, "Osaka, Japan", [4, 5, 6])))
    buf.append(render_data(get_data_ms(lc, "Tokyo, Japan", [4, 5, 6])))

    templ_main = Template(read("templates/main.html"))
    write("output/tester-ms.html", templ_main.render(content="\n".join(buf)))


def ensure_file(path: str, default_contents: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.isfile(path):
        write(path, default_contents, False)


if __name__ == "__main__":
    os.makedirs("cache/vc/", exist_ok=True)
    os.makedirs("cache/ms/", exist_ok=True)
    ensure_file(LOCATION_CACHE_PATH, "{}\n")
    lc: LocationCache = json.loads(read(LOCATION_CACHE_PATH))

    # build_page_vc()
    build_page_ms(lc)

    write(LOCATION_CACHE_PATH, json.dumps(lc), False)
