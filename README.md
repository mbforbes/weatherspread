# weatherspread

## usage

```bash
# create new python virtual env. I recommend `pyenv`. then:
pip install -r requirements.txt
# edit main.py for places as desired. then:
python main.py
# output written to output/tester-ms.html. open, e.g., on macOS:
open output/tester-ms.html
```

## APIs

From this [list of public APIs](https://github.com/public-apis/public-apis#weather), four candidates listed as providing historical data:

1. apilayer weatherstack
2. Micro Weather
3. Oikolab
4. Visual Crossing

They all require an API key.

### 1. apilayer weatherstack

250 calls/month for free

### 2. Micro Weather

Looks like they preivously had a free tier (their "solo" tier refers to it), but it's now called "dev" and wording is unclear whether it includes anything for free.

### 3. Oikolab

Free 1500 "units" / month (unclear if amt of data for a unit is entirety of a requested month's data, or just one request)

### 4. Visual Crossing

1000 records / day in free tier. Enough to get started!

Update: woof, this gets burned quick, when 1 record = 1 day.


## Display

- Temp: TODO: What is "feelslike"? Is it standardized? Should I use it instead?
- Precipitation: might want to show as well.
- Averages: could do, but honestly might not be worth it


## Free API alternatives

Since weather data is collected by governments and released for free (as far as I can tell, granted with no extra research and just reading between the lines), it's kind of lame a bunch of near-duplicate web services have sprung up to sell you access to this free data behind their own paid APIs.

Searching a bit, there's a Python interface to some weather data dumps. It requires (lat, lon) coordinates, so using another library that interfaces w/ OpenStreetMap (I think) to resolve names. NB: Looks like this kind of name resolution, where you go from place name to geo coordinate, is called _geocoding._ Cool.

- [`meteostat`](https://dev.meteostat.net/python/) provides access to historical weather data
- [`geopy`](https://github.com/geopy/geopy) w/ [`Nominatim`](https://nominatim.org/) does geocoding
