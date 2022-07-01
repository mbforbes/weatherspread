import calendar
import code
import json
import os

from jinja2 import Template
from mbforbes_python_utils import read, write
import requests

# global settings
api_key = read("secrets/visualcrossing_api_key.txt")
# print(api_key)
base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
unit_group = "us"  # vs metric
content_type = "json"
include = "days"


def get_place_html(location_display: str, months=[8, 9, 10], years=[2019, 2020, 2021]):
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

            cache_path = "cache/" + "_".join([location, start_date, end_date]) + ".json"
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
            year_data.append((month, data))
        all_data.append((year, year_data))

    # render
    # key = "tempmax"  # alt: "feelslikemax"
    key = "feelslikemax"  # alt: "feelslikemax"

    buf = []
    buf.append(f"<h2>{location_display}</h2>")
    prev_year = None
    for year, year_data in all_data:
        buf.append("<div>")
        for month, data in year_data:
            buf.append("<div class='dib mr3'>")
            for day in data["days"]:
                temp = day[key]
                color = (
                    "dark-red"
                    if temp > 100
                    else ("red" if temp > 90 else ("yellow" if temp > 70 else "blue"))
                )
                buf.append(
                    f'<div style="width: 10px; height: {temp}px" class="bg-{color} dib"></div>'
                )
            # year, month, _ = start_date.split("-")
            buf.append(
                f"<h3 class='mt1 mb3 tc gray'>{calendar.month_name[month]}, {year}</h3>"
            )
            buf.append("</div>")
        buf.append("<div>")

    return "\n".join(buf)


buf = []

buf.append(get_place_html("Belgrade, Serbia"))
buf.append(get_place_html("Bucharest, Romania"))
buf.append(get_place_html("Sarajevo, Bosnia"))
buf.append(get_place_html("Tirana, Albania"))
# buf.append(get_place_html("Tbilisi, Georgia"))

templ_main = Template(read("templates/main.html"))
write("output/tester.html", templ_main.render(content="\n".join(buf)))
