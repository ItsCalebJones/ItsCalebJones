import jinja2
import time
import requests
import json
import os
import html

LL2_ENDPOINT = "https://ll.thespacedevs.com/2.2.0/launch/upcoming/?mode=detailed&hide_recent_previous=true"
SNAPI_ENDPOINT = "https://api.spaceflightnewsapi.net/v3/articles"
BASE_TIME_URL = "https://www.timeanddate.com/worldclock/fixedtime.html?iso={iso}"
CACHE_DIR = "../cache"
ISO3_JSON = "http://country.io/iso3.json"
BASE_GOOGLE_CALENDAR_URL = "https://www.google.com/calendar/render?action=TEMPLATE&text={text}&location={location}&dates={date1}%2F{date2}"

STATUS_MAP = {
    "Go": "🟩 ",
    "TBC": "🟨 ",
    "TBD": "🟧 ",
    "Hold": "🟪 "
}

# create cache dir if it doesnt exist
os.makedirs(CACHE_DIR, exist_ok=True)


def first_letter_lower(s):
    return s[0].lower() + s[1:]


def status_emoji(status):
    return STATUS_MAP[status]


def make_google_calender_url(launch):
    return BASE_GOOGLE_CALENDAR_URL.format(
        text=html.escape(launch["name"]),
        location=html.escape(launch["pad"]["location"]["name"]),
        date1=time.strftime("%Y%m%dT%H%M%SZ", time.strptime(launch["window_start"],
                                                            "%Y-%m-%dT%H:%M:%SZ")),
        date2=time.strftime("%Y%m%dT%H%M%SZ", time.strptime(launch["window_end"],
                                                            "%Y-%m-%dT%H:%M:%SZ")),
    )


def make_google_calender_href_icon(launch):
    """
    create a google calendar href icon
    """
    return f'<a href="{make_google_calender_url(launch)}"><img border="0" width="15" src="https://upload.wikimedia.org/wikipedia/commons/a/a5/Google_Calendar_icon_%282020%29.svg"></a>'


def make_time_and_date_link(timestamp):
    """
    create a link to a time and date
    """
    # convert the timestamp to a string in iso format
    iso = time.strftime("%Y%m%dT%H%M%S", timestamp)
    return BASE_TIME_URL.format(iso=iso)


def get_iso3_to_iso2_country_map():
    """
    get a map from iso3 to iso2
    """
    # get the json
    r = requests.get(ISO3_JSON)
    data = r.json()

    # create a map from iso3 to iso2
    iso3_to_iso2 = {}
    for k, v in data.items():
        iso3_to_iso2[v] = k

    return iso3_to_iso2


ISO3_2_ISO2 = get_iso3_to_iso2_country_map()


def make_datetime_human_readable(timestamp):
    """
    make a timestamp human readable
    """
    # get the timestamp
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S UTC", timestamp)
    # timestamp = time.strftime("%B %d, %Y UTC", timestamp)
    return timestamp


def make_markdown_linked_time(timestamp):
    """
    create a link to a time and date
    """
    # convert the timestamp to a string in iso format
    s = make_datetime_human_readable(timestamp)
    url = make_time_and_date_link(timestamp)
    return f"[{s}]({url})"


def make_html_linked_time(timestamp):
    """
    create a link to a time and date
    """
    # convert the timestamp to a string in iso format
    s = make_datetime_human_readable(timestamp)
    url = make_time_and_date_link(timestamp)
    return f'<a href="{url}">{s}</a>'


def get_upcoming_launches(cache_time=3600 // 2):
    """
    get upcoming launches from the Launch Library 2 API
    """
    # check if launches are cached
    # cache launches by the time
    # if cache is older than 1 hour, update cache

    # get the current time
    now = time.time()

    # get the time of the last update from filename
    # if the file does not exist, create it
    try:
        with open(os.path.join(CACHE_DIR, "launches_last_update.txt"), "r") as f:
            last_update = f.read()
    except FileNotFoundError:
        last_update = now

    # if the cache is older than 1 hour, update cache
    if (now - float(last_update) > cache_time) | (last_update == now):
        # get the data from the api
        r = requests.get(LL2_ENDPOINT)
        data = r.json()

        # write the data to the cache
        with open(os.path.join(CACHE_DIR, "launch_cache.json"), "w") as f:
            json.dump(data, f)

        # update the last update time
        with open(os.path.join(CACHE_DIR, "launches_last_update.txt"), "w") as f:
            f.write(str(now))

    # read the cache
    with open(os.path.join(CACHE_DIR, "launch_cache.json"), "r") as f:
        data = json.load(f)

    # return the data
    return data


# def generate_next_launch(data):
#     """
#     generate the next launch readme
#     """
#     # get the template
#
#     # render the template
#     description = """
#
#     """


def add_a_an(s):
    if s[0] in "aeiouAEIOU":
        return "an " + s
    else:
        return "a " + s


def parse_launch_windows_to_datetime(launches):
    for launch in launches:
        # get datetime from window_start string
        launch["datetime"] = time.strptime(launch["window_start"],
                                           "%Y-%m-%dT%H:%M:%SZ")
    return launches


def get_country_flag_svg(iso3_country_code, country_reassign):
    if iso3_country_code:
        if country_reassign:
            if iso3_country_code == 'KAZ':
                iso3_country_code = 'RUS'
            elif iso3_country_code == 'GUF':
                iso3_country_code = 'FRA'
        # convert iso3 to iso2
        iso2_country_code = ISO3_2_ISO2[iso3_country_code]
        return f'https://raw.githubusercontent.com/lipis/flag-icons/main/flags/4x3/{iso2_country_code.lower()}.svg'
    return f'https://upload.wikimedia.org/wikipedia/commons/e/ef/International_Flag_of_Planet_Earth.svg'


def parse_launches_within_a_month(launches):
    upcoming_launches = []
    t_now = time.mktime(time.localtime())
    for i, launch in enumerate(launches):
        t_launch = time.mktime(launch["datetime"])
        if (t_launch > t_now) & (t_launch < t_now + 2592000):
            upcoming_launches.append(launch)
    return upcoming_launches


# get readme data
def get_readme_data():
    """
    get the readme data for the readme file generation
    """
    # get timestamp and ensure tz is UTC
    # timestamp = time.gmtime()
    # timestamp = time.strftime("%Y-%m-%d %H:%M:%S", timestamp)
    launches = get_upcoming_launches()["results"]
    launches = parse_launch_windows_to_datetime(launches)
    next_launch = launches[0]
    latest_news = get_latest_news()
    launch_news = get_launch_news(next_launch["id"])
    if next_launch["mission"] is None:
        next_launch["mission"] = {}
        next_launch["mission"]["name"] = "Unknown Payload"
        next_launch["mission"]["type"] = "Unknown"
        next_launch["mission"]["orbit"] = {}
        next_launch["mission"]["orbit"]["name"] = "Unknown Orbit"
        next_launch["mission"]["orbit"]["abbrev"] = "-"
        next_launch["mission"]["description"] = "Unknown Payload"
    elif next_launch["mission"]["orbit"] is None:
        next_launch["mission"]["orbit"] = {}
        next_launch["mission"]["orbit"]["name"] = "Unknown Orbit"
        next_launch["mission"]["orbit"]["abbrev"] = "-"

    return {
        "timestamp": time.gmtime(),
        "launches": launches,
        "next_launch": next_launch,
        "make_html_linked_time": make_html_linked_time,
        "parse_launches_within_a_month": parse_launches_within_a_month,
        "get_country_flag_svg": get_country_flag_svg,
        "get_iso3_to_iso2_country_map": get_iso3_to_iso2_country_map,
        "status_emoji": status_emoji,
        "first_letter_lower": first_letter_lower,
        "add_a_an": add_a_an,
        "make_google_calender_href_icon": make_google_calender_href_icon,
        "latest_news": latest_news,
        "launch_news": launch_news
    }


def get_latest_news(cache_time=3600 // 2):
    """
    get the latest news from the Spaceflight News API
    """
    # check if news are cached
    # cache news by the time
    # if cache is older than 1 hour, update cache

    # get the current time
    now = time.time()

    # get the time of the last update from filename
    # if the file does not exist, create it
    try:
        with open(os.path.join(CACHE_DIR, "latest_news_last_update.txt"), "r") as f:
            last_update = f.read()
    except FileNotFoundError:
        last_update = now

    # if the cache is older than 1 hour, update cache
    if (now - float(last_update) > cache_time) | (last_update == now):
        # get the data from the api
        r = requests.get(SNAPI_ENDPOINT + '?_limit=5')
        data = r.json()

        # write the data to the cache
        with open(os.path.join(CACHE_DIR, "latest_news_cache.json"), "w") as f:
            json.dump(data, f)

        # update the last update time
        with open(os.path.join(CACHE_DIR, "latest_news_last_update.txt"), "w") as f:
            f.write(str(now))

    # read the cache
    with open(os.path.join(CACHE_DIR, "latest_news_cache.json"), "r") as f:
        data = json.load(f)

    # return the data
    return data


def get_launch_news(launch_ID, cache_time=3600 // 2):
    """
    get all news related to a launch from the Spaceflight News API
    """
    # check if news are cached
    # cache news by the time
    # if cache is older than 1 hour, update cache

    # get the current time
    now = time.time()

    # get the time of the last update from filename
    # if the file does not exist, create it
    try:
        with open(os.path.join(CACHE_DIR, "launch_news_last_update.txt"), "r") as f:
            last_update = f.read()
    except FileNotFoundError:
        last_update = now

    # if the cache is older than 1 hour, update cache
    if (now - float(last_update) > cache_time) | (last_update == now):
        # get the data from the api
        r = requests.get(SNAPI_ENDPOINT + '/launch/' + launch_ID)
        data = r.json()

        # write the data to the cache
        with open(os.path.join(CACHE_DIR, "launch_news_cache.json"), "w") as f:
            json.dump(data, f)

        # update the last update time
        with open(os.path.join(CACHE_DIR, "launch_news_last_update.txt"), "w") as f:
            f.write(str(now))

    # read the cache
    with open(os.path.join(CACHE_DIR, "launch_news_cache.json"), "r") as f:
        data = json.load(f)

    # return the data
    return data


# load template file
template_loader = jinja2.FileSystemLoader(searchpath="./templates")
template_env = jinja2.Environment(loader=template_loader)
template = template_env.get_template("README.md.j2")

if __name__ == "__main__":
    # # load data
    data = get_readme_data()

    # render template
    output = template.render(**data)

    # write output
    with open(os.path.join("..", "README.md"), "w", encoding="utf-8") as f:
        f.write(output)
