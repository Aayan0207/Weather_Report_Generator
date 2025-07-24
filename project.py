import datetime
import sys
import re
import os
import shutil
from matplotlib.pyplot import (
    close,
    tick_params,
    subplots,
    savefig,
    plot,
    xticks,
    yticks,
    imshow,
    figure,
    xlim,
    ylim,
    text,
    title,
    xlabel,
    ylabel,
)
from numpy import array
from io import BytesIO
from PIL import Image
from termcolor import colored
from emoji import emojize
from time import sleep
from requests import get
from fpdf import FPDF


API_KEY = rf"{open("key.txt", "r").read().strip('\n').strip()}"


class Day:
    def __init__(self, date, **kwargs):
        self.date = date
        for kwarg in kwargs:
            setattr(self, kwarg, kwargs[kwarg])

    def display(self):
        for attr in self.__dict__:
            yield (attr, self.__dict__[attr])

    @classmethod
    def generate_current_report(cls, response):
        try:
            snowfall = response["currrent"]["snow_cm"]
        except KeyError:
            snowfall = 0.0
        astro_info = {}
        for forecast_day in response["forecast"]["forecastday"]:
            if forecast_day["date"] == Day.get_date(
                response["current"]["last_updated"]
            ):
                astro_info["sun_rise"] = forecast_day["astro"]["sunrise"]
                astro_info["sun_set"] = forecast_day["astro"]["sunset"]
                astro_info["moon_rise"] = forecast_day["astro"]["moonrise"]
                astro_info["moon_set"] = forecast_day["astro"]["moonset"]
                astro_info["moon_phase"] = forecast_day["astro"]["moon_phase"]
                astro_info["moon_illumination"] = forecast_day["astro"][
                    "moon_illumination"
                ]
        return cls(
            date=Day.get_date(response["current"]["last_updated"]),
            name=response["location"]["name"],
            country=response["location"]["country"],
            latitude=response["location"]["lat"],
            longitude=response["location"]["lon"],
            localtime=response["location"]["localtime"],
            last_updated=response["current"]["last_updated"],
            temp_c=response["current"]["temp_c"],
            temp_f=response["current"]["temp_f"],
            condition_text=response["current"]["condition"]["text"],
            condition_image=response["current"]["condition"]["icon"],
            wind_mph=response["current"]["wind_mph"],
            wind_kph=response["current"]["wind_kph"],
            wind_dir=response["current"]["wind_dir"],
            pressure_mb=response["current"]["pressure_mb"],
            precip_mm=response["current"]["precip_mm"],
            snow_cm=snowfall,
            humidity_percentage=response["current"]["humidity"],
            cloud_cover_percentage=response["current"]["cloud"],
            feelslike_c=response["current"]["feelslike_c"],
            feelslike_f=response["current"]["feelslike_f"],
            windchill_c=response["current"]["windchill_c"],
            windchill_f=response["current"]["windchill_f"],
            heatindex_c=response["current"]["heatindex_c"],
            heatindex_f=response["current"]["heatindex_f"],
            dewpoint_c=response["current"]["dewpoint_c"],
            dewpoint_f=response["current"]["dewpoint_f"],
            vis_km=response["current"]["vis_km"],
            vis_miles=response["current"]["vis_miles"],
            uv=response["current"]["uv"],
            gust_kph=response["current"]["gust_kph"],
            gust_mph=response["current"]["gust_mph"],
            aqi_index=response["current"]["air_quality"]["gb-defra-index"],
            co=round(response["current"]["air_quality"]["co"], 2),
            o3=round(response["current"]["air_quality"]["o3"], 2),
            no2=round(response["current"]["air_quality"]["no2"], 2),
            so2=round(response["current"]["air_quality"]["so2"], 2),
            pm2_5=round(response["current"]["air_quality"]["pm2_5"], 2),
            pm_10=round(response["current"]["air_quality"]["pm10"], 2),
            astro=astro_info,
        )

    @classmethod
    def generate_forecast_for_day(cls, date, response):
        astro_info = {}
        for forecast_day in response["forecast"]["forecastday"]:
            if forecast_day["date"] == Day.get_date(date):
                astro_info["sun_rise"] = forecast_day["astro"]["sunrise"]
                astro_info["sun_set"] = forecast_day["astro"]["sunset"]
                astro_info["moon_rise"] = forecast_day["astro"]["moonrise"]
                astro_info["moon_set"] = forecast_day["astro"]["moonset"]
                astro_info["moon_phase"] = forecast_day["astro"]["moon_phase"]
                astro_info["moon_illumination"] = forecast_day["astro"][
                    "moon_illumination"
                ]
        hour_reports = {}
        for forecast_day in response["forecast"]["forecastday"]:
            if forecast_day["date"] == date:
                for hour in forecast_day["hour"]:
                    hour_reports[Day.get_hour(hour["time"])] = {
                        "temp_c": hour["temp_c"],
                        "temp_f": hour["temp_f"],
                        "is_day": hour["is_day"],
                        "condition_text": hour["condition"]["text"].strip(),
                        "condition_image": hour["condition"]["icon"],
                        "wind_mph": hour["wind_mph"],
                        "wind_kph": hour["wind_kph"],
                        "wind_dir": hour["wind_dir"],
                        "pressure_mb": hour["pressure_mb"],
                        "precip_mm": hour["precip_mm"],
                        "snow_cm": hour["snow_cm"],
                        "humidity_percentage": hour["humidity"],
                        "cloud_cover_percentage": hour["cloud"],
                        "dewpoint_c": hour["dewpoint_c"],
                        "dewpoint_f": hour["dewpoint_f"],
                        "chance_of_rain": hour["chance_of_rain"],
                        "chance_of_snow": hour["chance_of_snow"],
                        "vis_km": hour["vis_km"],
                        "vis_miles": hour["vis_miles"],
                        "uv": hour["uv"],
                        "gust_kph": hour["gust_kph"],
                        "gust_mph": hour["gust_mph"],
                        "aqi_index": hour["air_quality"]["gb-defra-index"],
                    }
        (
            gust_kph_max,
            gust_mph_max,
            pressure_avg,
            cloud_cover_avg,
            dewpoint_c_avg,
            dewpoint_f_avg,
        ) = (0, 0, 0, 0, 0, 0)
        for hour in hour_reports:
            if hour_reports[hour]["gust_kph"] > gust_kph_max:
                gust_kph_max = hour_reports[hour]["gust_kph"]
            if hour_reports[hour]["gust_mph"] > gust_mph_max:
                gust_mph_max = hour_reports[hour]["gust_mph"]
            pressure_avg += hour_reports[hour]["pressure_mb"]
            cloud_cover_avg += hour_reports[hour]["cloud_cover_percentage"]
            dewpoint_c_avg += hour_reports[hour]["dewpoint_c"]
            dewpoint_f_avg += hour_reports[hour]["dewpoint_f"]
        pressure_avg = round(pressure_avg / 24, 2)
        cloud_cover_avg = round(cloud_cover_avg / 24, 2)
        dewpoint_c_avg = round(dewpoint_c_avg / 24, 2)
        dewpoint_f_avg = round(dewpoint_f_avg / 24, 2)
        for forecast_day in response["forecast"]["forecastday"]:
            if forecast_day["date"] == date:
                return cls(
                    date=forecast_day["date"],
                    name=response["location"]["name"],
                    country=response["location"]["country"],
                    latitude=response["location"]["lat"],
                    longitude=response["location"]["lon"],
                    localtime=response["location"]["localtime"],
                    temp_c=forecast_day["day"]["avgtemp_c"],
                    temp_f=forecast_day["day"]["avgtemp_f"],
                    condition_text=forecast_day["day"]["condition"]["text"],
                    condition_image=forecast_day["day"]["condition"]["icon"],
                    wind_mph=forecast_day["day"]["maxwind_mph"],
                    wind_kph=forecast_day["day"]["maxwind_kph"],
                    gust_kph=gust_kph_max,
                    gust_mph=gust_mph_max,
                    precip_mm=forecast_day["day"]["totalprecip_mm"],
                    pressure_mb=pressure_avg,
                    snow_cm=forecast_day["day"]["totalsnow_cm"],
                    humidity_percentage=forecast_day["day"]["avghumidity"],
                    cloud_cover_percentage=cloud_cover_avg,
                    dewpoint_c=dewpoint_c_avg,
                    dewpoint_f=dewpoint_f_avg,
                    vis_km=forecast_day["day"]["avgvis_km"],
                    vis_miles=forecast_day["day"]["avgvis_miles"],
                    uv=forecast_day["day"]["uv"],
                    aqi_index=forecast_day["day"]["air_quality"]["gb-defra-index"],
                    co=round(forecast_day["day"]["air_quality"]["co"], 2),
                    o3=round(forecast_day["day"]["air_quality"]["o3"], 2),
                    no2=round(forecast_day["day"]["air_quality"]["no2"], 2),
                    so2=round(forecast_day["day"]["air_quality"]["so2"], 2),
                    pm2_5=round(forecast_day["day"]["air_quality"]["pm2_5"], 2),
                    pm_10=round(forecast_day["day"]["air_quality"]["pm10"], 2),
                    astro=astro_info,
                    hourly_reports=hour_reports,
                )

    @classmethod
    def generate_historical_for_day(cls, date, response):
        astro_info = {}
        for forecast_day in response["forecast"]["forecastday"]:
            if forecast_day["date"] == Day.get_date(date):
                astro_info["sun_rise"] = forecast_day["astro"]["sunrise"]
                astro_info["sun_set"] = forecast_day["astro"]["sunset"]
                astro_info["moon_rise"] = forecast_day["astro"]["moonrise"]
                astro_info["moon_set"] = forecast_day["astro"]["moonset"]
                astro_info["moon_phase"] = forecast_day["astro"]["moon_phase"]
                astro_info["moon_illumination"] = forecast_day["astro"][
                    "moon_illumination"
                ]
        hour_reports = {}
        for forecast_day in response["forecast"]["forecastday"]:
            if forecast_day["date"] == date:
                for hour in forecast_day["hour"]:
                    hour_reports[Day.get_hour(hour["time"])] = {
                        "temp_c": hour["temp_c"],
                        "temp_f": hour["temp_f"],
                        "is_day": hour["is_day"],
                        "condition_text": hour["condition"]["text"].strip(),
                        "condition_image": hour["condition"]["icon"],
                        "wind_mph": hour["wind_mph"],
                        "wind_kph": hour["wind_kph"],
                        "wind_dir": hour["wind_dir"],
                        "pressure_mb": hour["pressure_mb"],
                        "precip_mm": hour["precip_mm"],
                        "snow_cm": hour["snow_cm"],
                        "humidity_percentage": hour["humidity"],
                        "cloud_cover_percentage": hour["cloud"],
                        "dewpoint_c": hour["dewpoint_c"],
                        "dewpoint_f": hour["dewpoint_f"],
                        "chance_of_rain": hour["chance_of_rain"],
                        "chance_of_snow": hour["chance_of_snow"],
                        "vis_km": hour["vis_km"],
                        "vis_miles": hour["vis_miles"],
                        "uv": hour["uv"],
                        "gust_kph": hour["gust_kph"],
                        "gust_mph": hour["gust_mph"],
                    }
        (
            gust_kph_max,
            gust_mph_max,
            pressure_avg,
            cloud_cover_avg,
            dewpoint_c_avg,
            dewpoint_f_avg,
        ) = (0, 0, 0, 0, 0, 0)
        for hour in hour_reports:
            if hour_reports[hour]["gust_kph"] > gust_kph_max:
                gust_kph_max = hour_reports[hour]["gust_kph"]
            if hour_reports[hour]["gust_mph"] > gust_mph_max:
                gust_mph_max = hour_reports[hour]["gust_mph"]
            pressure_avg += hour_reports[hour]["pressure_mb"]
            cloud_cover_avg += hour_reports[hour]["cloud_cover_percentage"]
            dewpoint_c_avg += hour_reports[hour]["dewpoint_c"]
            dewpoint_f_avg += hour_reports[hour]["dewpoint_f"]
        pressure_avg = round(pressure_avg / 24, 2)
        cloud_cover_avg = round(cloud_cover_avg / 24, 2)
        dewpoint_c_avg = round(dewpoint_c_avg / 24, 2)
        dewpoint_f_avg = round(dewpoint_f_avg / 24, 2)
        for forecast_day in response["forecast"]["forecastday"]:
            if forecast_day["date"] == date:
                return cls(
                    date=forecast_day["date"],
                    name=response["location"]["name"],
                    country=response["location"]["country"],
                    latitude=response["location"]["lat"],
                    longitude=response["location"]["lon"],
                    localtime=response["location"]["localtime"],
                    temp_c=forecast_day["day"]["avgtemp_c"],
                    temp_f=forecast_day["day"]["avgtemp_f"],
                    condition_text=forecast_day["day"]["condition"]["text"],
                    condition_image=forecast_day["day"]["condition"]["icon"],
                    wind_mph=forecast_day["day"]["maxwind_mph"],
                    wind_kph=forecast_day["day"]["maxwind_kph"],
                    gust_kph=gust_kph_max,
                    gust_mph=gust_mph_max,
                    precip_mm=forecast_day["day"]["totalprecip_mm"],
                    pressure_mb=pressure_avg,
                    snow_cm=forecast_day["day"]["totalsnow_cm"],
                    humidity_percentage=forecast_day["day"]["avghumidity"],
                    cloud_cover_percentage=cloud_cover_avg,
                    dewpoint_c=dewpoint_c_avg,
                    dewpoint_f=dewpoint_f_avg,
                    vis_km=forecast_day["day"]["avgvis_km"],
                    vis_miles=forecast_day["day"]["avgvis_miles"],
                    uv=forecast_day["day"]["uv"],
                    astro=astro_info,
                    hourly_reports=hour_reports,
                )

    @staticmethod
    def get_date(string):
        if match := re.search(r"^(\d{4}-\d{2}-\d{2})(?: \d{2}:\d{2})?$", string):
            return match.group(1)
        return None

    @staticmethod
    def get_hour(string):
        if match := re.search(r"^(?:\d{4}-\d{2}-\d{2} )?(\d{2})(?::\d{2})?$", string):
            return int(match.group(1))
        return None


def main():
    if len(sys.argv) < 2:
        place = input("Location: ").strip()
        start_date = input("Start Date: ").strip().lower()
        end_date = input("End Date (optional): ").strip().lower()
        if not end_date:
            end_date = None
    elif len(sys.argv) > 4:
        sys.exit("Usage: file_name Location Start_date End_date")
    else:
        place = sys.argv[1].strip()
        start_date = sys.argv[2].strip().lower()
        try:
            end_date = sys.argv[3].strip().lower()
        except IndexError:
            end_date = None
    print()
    prompt_parse_and_run(place, start_date, end_date)


def prompt_parse_and_run(place, start_date, end_date=None):
    if not verify_location(place):
        sys.exit(colored("Invalid location provided.", "red"))
    elif not verify_date(start_date):
        sys.exit(colored("Inavlid first date argument provided.", "red"))
    elif end_date is not None and not verify_date(end_date):
        sys.exit(colored("Inavlid second date argument provided.", "red"))
    if not end_date:
        flag = "singular"
    else:
        flag = "range"
    try:
        start_date = datetime.date(*extract_date(start_date))
        if flag == "range":
            end_date = datetime.date(*extract_date(end_date))
    except ValueError:
        sys.exit(colored("Inavlid date or date range provided.", "red"))
    if flag == "range" and start_date == end_date:
        flag = "singular"
    current_date = datetime.date.today()
    if (
        not current_date - datetime.timedelta(days=8)
        < start_date
        < current_date + datetime.timedelta(days=3)
    ):
        sys.exit(
            colored(
                "Forecast Weather functionality limited to 2 days ahead.\nHistorical Weather functionality limited to 7 days prior",
                "red",
            )
        )
    elif flag == "range" and not current_date - datetime.timedelta(
        days=8
    ) < end_date < current_date + datetime.timedelta(days=3):
        sys.exit(
            colored(
                "Forecast Weather functionality limited to 2 days ahead.\nHistorical Weather functionality limited to 7 days prior",
                "red",
            )
        )
    generate_animation(colored("Verifying user request", "green"), 1)
    print(colored(emojize("User request verified :check_mark_button:  "), "green"))
    generate_animation(colored("Requesting API", "green"), 2)
    if flag == "singular":
        if start_date < current_date:
            response = get(
                f"https://api.weatherapi.com/v1/history.json?key={API_KEY}&q={place}&dt={start_date}"
            ).json()
            response_flag = "historical"
        else:
            difference = (start_date - current_date).days
            response = get(
                f"https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={place}&days={difference+1}&aqi=yes"
            ).json()
            if difference == 0:
                response_flag = "current"
            else:
                response_flag = "forecast"
        print(colored(emojize("API Request received :desktop_computer:"), "green"))
        generate_pdf(response, flag=response_flag, date=start_date)
    else:
        if start_date > end_date:
            start_date, end_date = end_date, start_date
        for date in generate_dates(start_date, end_date):
            if date < current_date:
                response = get(
                    f"https://api.weatherapi.com/v1/history.json?key={API_KEY}&q={place}&dt={date}"
                ).json()
                response_flag = "historical"
            else:
                difference = (date - current_date).days
                response = get(
                    f"https://api.weatherapi.com/v1/forecast.json?key={API_KEY}&q={place}&days={difference+1}&aqi=yes"
                ).json()
                if difference == 0:
                    response_flag = "current"
                else:
                    response_flag = "forecast"
            print(colored(emojize("API Request received :desktop_computer:"), "green"))
            generate_pdf(response, flag=response_flag, date=date)


def generate_dates(start_date, end_date):
    date = start_date
    while date != end_date + datetime.timedelta(days=1):
        yield date
        date += datetime.timedelta(days=1)


def extract_date(string):
    if match := re.search(r"^(\d{4})-(\d{1,2})-(\d{1,2})$", string):
        return int(match.group(1)), int(match.group(2)), int(match.group(3))
    return None


def verify_date(string):
    if match := re.search(r"^\d{4}-\d{1,2}-\d{1,2}$", string, re.IGNORECASE):
        return True
    return False


def verify_location(string):
    if match := re.search(r"^[a-zA-Z][a-zA-Z\s]*$", string, re.IGNORECASE):
        return True
    return False


def start_up():
    folder_path = os.path.join(os.getcwd(), "plots")
    if os.path.exists(folder_path):
        shutil.rmtree(folder_path)
    os.mkdir(folder_path)


def clean_up():
    try:
        shutil.rmtree(os.path.join(os.getcwd(), "plots"))
    except FileNotFoundError:
        pass


def generate_pdf(response, flag="current", date=None):
    start_up()
    generate_animation(colored("Starting PDF generation", "green"), 2)
    if date:
        date = str(date)
    pdf = FPDF(orientation="landscape", format="A4")
    pdf.set_display_mode(zoom="fullwidth", layout="continuous")
    print(colored(emojize("PDF generation started :bookmark_tabs:  "), "green"))
    flag = flag.lower()
    if flag == "current":
        current_response = Day.generate_current_report(response)
    elif flag == "forecast" and date is not None:
        current_response = Day.generate_forecast_for_day(date, response)
    elif flag == "historical" and date is not None:
        current_response = Day.generate_historical_for_day(date, response)
    pdf.add_page()
    pdf.set_font("helvetica", "B", 22)
    pdf.set_fill_color(0, 0, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_line_width(0.5)
    plot_current_condition(current_response)
    pdf.image("plots/Current_condition_plot.jpg", x=20, y=41)
    pdf.cell(
        275,
        24,
        f"Weather Report for {current_response.name}, {current_response.country}",
        align="C",
        fill=True,
        border=1,
    )
    pdf.set_font_size(14)
    pdf.set_xy(120, 26)
    pdf.cell(50, 8, f"Date: {current_response.date}", align="C", fill=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_xy(10, 33.5)
    if flag == "current":
        pdf.cell(
            275,
            10,
            f"Latitude: {current_response.latitude}{" "*8}Longitude: {current_response.longitude}{" "*8}Localtime: {current_response.localtime}{" "*8}Last Updated: {current_response.last_updated}",
            align="C",
            border=1,
        )
    elif flag in ("forecast", "historical"):
        pdf.cell(
            275,
            10,
            f"Latitude: {current_response.latitude}{" "*8}Longitude: {current_response.longitude}{" "*8}Localtime: {current_response.localtime}",
            align="C",
            border=1,
        )

    # Weather

    generate_animation(colored("Adding base data", "green"), 2)
    pdf.set_xy(20, 75)
    cell_width, cell_height, cell_seperation = 120, 25, 6.2
    pdf.set_font_size(16)
    pdf.set_fill_color(255, 0, 0)
    if flag == "current":
        pdf.cell(
            cell_width,
            cell_height - 10,
            f"Current Weather",
            border=1,
            align="C",
            fill=True,
        )
    elif flag == "forecast":
        pdf.cell(
            cell_width,
            cell_height - 10,
            f"Forecasted Weather",
            border=1,
            align="C",
            fill=True,
        )
    elif flag == "historical":
        pdf.cell(
            cell_width,
            cell_height - 10,
            f"Historical Weather",
            border=1,
            align="C",
            fill=True,
        )
    pdf.set_font_size(14)
    if flag == "current":
        titles = [
            f"Temperature: {current_response.temp_c} °C / {current_response.temp_f} °F",
            f"Feels like Temperature: {current_response.feelslike_c} °C / {current_response.feelslike_f} °F",
            f"Wind Speed: {current_response.wind_kph} Kph / {current_response.wind_mph} Mph",
            f"Wind Direction: {current_response.wind_dir}",
            f"Gust Speed: {current_response.gust_kph} Kph / {current_response.gust_mph} Mph",
            f"Pressure: {current_response.pressure_mb} mb",
            f"Precipitation: {current_response.precip_mm} mm",
            f"Snowfall: {current_response.snow_cm} cm",
            f"Humidity: {current_response.humidity_percentage} %",
            f"Cloud Cover: {current_response.cloud_cover_percentage} %",
            f"Dewpoint: {current_response.dewpoint_c} °C / {current_response.dewpoint_f} °F",
            f"Visibility: {current_response.vis_km} Km / {current_response.vis_miles} miles",
            f"UV Index: {current_response.uv}",
            f"AQI Index: {current_response.aqi_index}",
        ]
    elif flag == "forecast":
        titles = [
            f"Average Temperature: {current_response.temp_c} °C / {current_response.temp_f} °F",
            f"Maximum Wind Speed: {current_response.wind_kph} Kph / {current_response.wind_mph} Mph",
            f"Maximum Gust Speed: {current_response.gust_kph} Kph / {current_response.gust_mph} Mph",
            f"Average Pressure: {current_response.pressure_mb} mb",
            f"Maximum Precipitation: {current_response.precip_mm} mm",
            f"Maximum Snowfall: {current_response.snow_cm} cm",
            f"Average Humidity: {current_response.humidity_percentage} %",
            f"Average Cloud Cover: {current_response.cloud_cover_percentage} %",
            f"Average Dewpoint: {current_response.dewpoint_c} °C / {current_response.dewpoint_f} °F",
            f"Average Visibility: {current_response.vis_km} Km / {current_response.vis_miles} miles",
            f"UV Index: {current_response.uv}",
            f"AQI Index: {current_response.aqi_index}",
        ]
    elif flag == "historical":
        titles = [
            f"Average Temperature: {current_response.temp_c} °C / {current_response.temp_f} °F",
            f"Maximum Wind Speed: {current_response.wind_kph} Kph / {current_response.wind_mph} Mph",
            f"Maximum Gust Speed: {current_response.gust_kph} Kph / {current_response.gust_mph} Mph",
            f"Average Pressure: {current_response.pressure_mb} mb",
            f"Maximum Precipitation: {current_response.precip_mm} mm",
            f"Maximum Snowfall: {current_response.snow_cm} cm",
            f"Average Humidity: {current_response.humidity_percentage} %",
            f"Average Cloud Cover: {current_response.cloud_cover_percentage} %",
            f"Average Dewpoint: {current_response.dewpoint_c} °C / {current_response.dewpoint_f} °F",
            f"Average Visibility: {current_response.vis_km} Km / {current_response.vis_miles} miles",
            f"UV Index: {current_response.uv}",
        ]
    y_shift = 84
    for title in range(len(titles)):
        pdf.set_xy(20, y_shift)
        if title == len(titles) - 1:
            pdf.cell(cell_width, cell_height, titles[title], border="LRB", align="C")
        else:
            pdf.cell(cell_width, cell_height, titles[title], border="LR", align="C")
        y_shift += cell_seperation

    # Air Qualtity Data

    if flag in ("current", "forecast"):
        cell_height, cell_seperation = 19, 6.1
        pdf.set_xy(155, 75)
        pdf.set_fill_color(0, 255, 0)
        pdf.set_font_size(16)
        pdf.cell(
            cell_width,
            cell_height - 10,
            f"Air Quality Data",
            border=1,
            align="C",
            fill=True,
        )
        pdf.ln(2)
        pdf.set_font_size(14)
        titles = [
            f"Carbon Monoxide: {current_response.co} ug/m3",
            f"Ozone: {current_response.o3} ug/m3",
            f"Nitrogen Dioxide: {current_response.no2} ug/m3",
            f"Sulphur Dioxide: {current_response.so2} ug/m3",
            f"PM2.5: {current_response.pm2_5} ug/m3",
            f"PM10: {current_response.pm_10} ug/m3",
        ]
        y_shift = 82
        for title in range(len(titles)):
            pdf.set_xy(155, y_shift)
            if title == len(titles) - 1:
                pdf.cell(
                    cell_width, cell_height, titles[title], border="LRB", align="C"
                )
            else:
                pdf.cell(cell_width, cell_height, titles[title], border="LR", align="C")
            y_shift += cell_seperation

    # Astronomical Data

    if flag in ("current", "forecast"):
        pdf.set_xy(155, 135)
        y_shift = 140
    elif flag == "historical":
        pdf.set_xy(155, 75)
        y_shift = 82
    pdf.set_fill_color(25, 114, 230)
    pdf.set_font_size(16)
    pdf.cell(
        cell_width,
        cell_height - 10,
        f"Astronomical Data",
        border=1,
        align="C",
        fill=True,
    )
    pdf.ln(2)
    pdf.set_font_size(14)
    titles = [
        f"Sunrise: {current_response.astro["sun_rise"]}",
        f"Sunset: {current_response.astro["sun_set"]}",
        f"Moonrise: {current_response.astro["moon_rise"]}",
        f"Moonset: {current_response.astro["moon_set"]}",
        f"Moon Phase: {current_response.astro["moon_phase"]}",
        f"Moon Illumination: {current_response.astro["moon_illumination"]} %",
    ]
    for title in range(len(titles)):
        pdf.set_xy(155, y_shift)
        if title == len(titles) - 1:
            pdf.cell(cell_width, cell_height, titles[title], border="LRB", align="C")
        else:
            pdf.cell(cell_width, cell_height, titles[title], border="LR", align="C")
        y_shift += cell_seperation
    print(colored(emojize("Base data added :pen:   "), "green"))
    pdf.add_page()
    pdf.set_fill_color(0, 0, 0)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font_size(22)
    pdf.cell(
        275,
        20,
        f"Hourly Weather Report ({current_response.date})",
        align="C",
        fill=True,
        border=1,
    )
    generate_animation(colored("Generating graphs", "green"), 2)
    if flag in ("current", "forecast"):
        forecast_report_for_current = Day.generate_forecast_for_day(
            current_response.date, response
        )
        plot_graphs(forecast_report_for_current)
        plot_uv_aqi(forecast_report_for_current)
    elif flag == "historical":
        forecast_report_for_current = Day.generate_historical_for_day(
            current_response.date, response
        )
        plot_graphs(forecast_report_for_current)
        plot_uv(forecast_report_for_current)
    print(colored(emojize("Graphs generated :bar_chart:  "), "green"))
    pdf.image(
        rf"plots/Hourwise_Weather_plot_{current_response.date}.jpg",
        x=-20,
        y=35,
        w=325,
        h=80,
    )
    pdf.image(
        rf"plots/Hourwise_Weather_legend_plot_{current_response.date}.jpg",
        x=30,
        y=120,
        w=250,
        h=80,
    )
    pdf.add_page()
    generate_animation(colored("Adding graphs to PDF", "green"), 2)
    if flag in ("current", "forecast"):
        files = [
            rf"plots/Temperature_plot_{current_response.date}.jpg",
            rf"plots/Wind_Speed_plot_{current_response.date}.jpg",
            rf"plots/Gust_plot_{current_response.date}.jpg",
            rf"plots/Pressure_plot_{current_response.date}.jpg",
            rf"plots/Chance_plot_{current_response.date}.jpg",
            rf"plots/Precipitation_Snowfall_plot_{current_response.date}.jpg",
            rf"plots/Humidity_CloudCover_plot_{current_response.date}.jpg",
            rf"plots/Dewpoint_plot_{current_response.date}.jpg",
            rf"plots/Visibility_plot_{current_response.date}.jpg",
            rf"plots/UV_AQI_plot_{current_response.date}.jpg",
        ]
    elif flag == "historical":
        files = [
            rf"plots/Temperature_plot_{current_response.date}.jpg",
            rf"plots/Wind_Speed_plot_{current_response.date}.jpg",
            rf"plots/Gust_plot_{current_response.date}.jpg",
            rf"plots/Pressure_plot_{current_response.date}.jpg",
            rf"plots/Chance_plot_{current_response.date}.jpg",
            rf"plots/Precipitation_Snowfall_plot_{current_response.date}.jpg",
            rf"plots/Humidity_CloudCover_plot_{current_response.date}.jpg",
            rf"plots/Dewpoint_plot_{current_response.date}.jpg",
            rf"plots/Visibility_plot_{current_response.date}.jpg",
            rf"plots/UV_plot_{current_response.date}.jpg",
        ]
    for file in range(len(files)):
        pdf.image(files[file], x=-20, y=15, w=340, h=175)
        if file != len(files) - 1:
            pdf.add_page()
    print(colored(emojize("Graphs added to PDF :chart_increasing:   "), "green"))
    if date is None:
        date = Day.get_date(response["location"]["localtime"])
    file_name = f'Weather_Report_{response["location"]["name"]}_{date}.pdf'
    pdf.output(f"{file_name}")
    clean_up()
    generate_animation(colored("Finalizing PDF", "green"), 2)
    print(colored(emojize(f"{file_name} generated :slightly_smiling_face:"), "green"))
    file_path = rf"file://{os.path.join(os.getcwd(),file_name).replace(' ', '%20').replace('\\','/')}"
    print(colored(emojize(rf":right_arrow:  {file_path}")))
    print()


def plot_current_condition(response):
    figure(figsize=(8, 1))
    xticks([])
    yticks([1], array([f"{response.condition_text.title()}"]), fontweight="bold")
    image_response = get(rf"https:{response.condition_image}").content
    img = Image.open(BytesIO(image_response))
    imshow(img, extent=[-0.5, 0.5, 0.5, 1.5])
    savefig("plots/Current_condition_plot.jpg", format="jpg")
    close()


def generate_animation(word, n):
    animations = [f"{word}   ", f"{word}.", f"{word}..", f"{word}..."]
    for i in range(n):
        for animation in animations:
            print(f"{animation}\r", end="")
            sleep(0.2)


def plot_graphs(day):
    plot_hourly_weather(day)
    plot_hourly_weather_legend(day)
    plot_temperature(day)
    plot_wind_speed(day)
    plot_gust(day)
    plot_pressure(day)
    plot_chances(day)
    plot_precipitation_snowfall(day)
    plot_humidity_cloudcover(day)
    plot_dewpoint(day)
    plot_visibility(day)


(
    figure_width,
    figure_height,
    title_fontsize,
    axis_label_fontsize,
    ticks_fontsize,
    point_text_fontsize,
    rotation_value,
) = (18, 10, 20, 16, 14, 12, 50)


def plot_uv(day):
    figure(figsize=(figure_width, figure_height))
    title(
        f"Ultra-Violet records for {day.name}, {day.country}\nDate: {day.date}",
        fontsize=title_fontsize,
        weight="black",
    )
    xlabel("Hour of the day", fontsize=axis_label_fontsize, weight="black")
    ylabel("UV", fontsize=axis_label_fontsize, weight="black")
    x_axis = array([time for time in generate_time_axis()])
    xticks(rotation=rotation_value, fontsize=ticks_fontsize)
    y_axis_pres = array(
        [int(day.hourly_reports[hour]["uv"]) for hour in day.hourly_reports]
    )
    tick_params(axis="y", labelsize=ticks_fontsize)
    ylim(bottom=min(y_axis_pres) - 0.5, top=max(y_axis_pres) + 0.5)
    plot(x_axis, y_axis_pres, marker="o", linestyle="-", color="#bf2feb")
    for point in range(24):
        text(
            point,
            y_axis_pres[point] + 0.1,
            f"{y_axis_pres[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    savefig(rf"plots/UV_plot_{day.date}.jpg", format="jpg")
    close()


def plot_uv_aqi(day):
    fig, (plot_1, plot_2) = subplots(2, 1)
    fig.suptitle(
        f"Ultra-Violet and Air Quality Index records for {day.name}, {day.country}\nDate: {day.date}",
        fontsize=title_fontsize,
        weight="black",
    )
    fig.set_size_inches(figure_width, figure_height)
    x_axis = array([time for time in generate_time_axis()])
    y_axis_u = array([day.hourly_reports[hour]["uv"] for hour in day.hourly_reports])
    plot_1.plot(x_axis, y_axis_u, marker="o", linestyle="-", color="#bf2feb")
    plot_1.set_ylabel("UV", fontsize=axis_label_fontsize, weight="black")
    plot_1.set_xticks(range(24))
    plot_1.set_xticklabels(
        plot_1.get_xticklabels(), rotation=rotation_value, fontsize=ticks_fontsize
    )
    plot_1.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_1.set_ylim(top=max(y_axis_u) + 1)
    for point in range(24):
        plot_1.text(
            point,
            y_axis_u[point] + 0.25,
            f"{y_axis_u[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    y_axis_a = array(
        [day.hourly_reports[hour]["aqi_index"] for hour in day.hourly_reports]
    )
    plot_2.plot(x_axis, y_axis_a, marker="o", linestyle="-", color="green")
    plot_2.set_xlabel("Hour of the Day", fontsize=axis_label_fontsize, weight="black")
    plot_2.set_ylabel(
        "AQI Index (UK Defra Index)", fontsize=axis_label_fontsize, weight="black"
    )
    plot_2.set_xticks(range(24))
    plot_2.set_xticklabels(
        plot_2.get_xticklabels(), rotation=rotation_value, fontsize=axis_label_fontsize
    )
    plot_2.set_ylim(top=max(y_axis_a) + 1)
    plot_2.tick_params(axis="y", labelsize=ticks_fontsize)
    for point in range(24):
        plot_2.text(
            point,
            y_axis_a[point] + 0.25,
            f"{y_axis_a[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    savefig(rf"plots/UV_AQI_plot_{day.date}.jpg", format="jpg")
    close()


def plot_gust(day):
    fig, (plot_1, plot_2) = subplots(2, 1)
    fig.suptitle(
        f"Gust records for {day.name}, {day.country}\nDate: {day.date}",
        fontsize=title_fontsize,
        weight="black",
    )
    fig.set_size_inches(figure_width, figure_height)
    x_axis = array([time for time in generate_time_axis()])
    y_axis_k = array(
        [day.hourly_reports[hour]["gust_kph"] for hour in day.hourly_reports]
    )
    plot_1.plot(x_axis, y_axis_k, marker="o", linestyle="-", color="grey")
    plot_1.set_ylabel("Gust (kph)", fontsize=axis_label_fontsize, weight="black")
    plot_1.set_xticks(range(24))
    plot_1.set_xticklabels(
        plot_1.get_xticklabels(), rotation=rotation_value, fontsize=ticks_fontsize
    )
    plot_1.set_ylim(top=max(y_axis_k) + 2)
    plot_1.tick_params(axis="y", labelsize=ticks_fontsize)
    for point in range(24):
        plot_1.text(
            point,
            y_axis_k[point] + 0.5,
            f"{y_axis_k[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    y_axis_m = array(
        [day.hourly_reports[hour]["gust_mph"] for hour in day.hourly_reports]
    )
    plot_2.plot(x_axis, y_axis_m, marker="o", linestyle="-", color="grey")
    plot_2.set_xlabel("Hour of the Day", fontsize=axis_label_fontsize, weight="black")
    plot_2.set_ylabel("Gust (mph)", fontsize=axis_label_fontsize, weight="black")
    plot_2.set_xticks(range(24))
    plot_2.set_xticklabels(
        plot_2.get_xticklabels(), rotation=rotation_value, fontsize=ticks_fontsize
    )
    plot_2.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_2.set_ylim(top=max(y_axis_m) + 2)
    for point in range(24):
        plot_2.text(
            point,
            y_axis_m[point] + 0.5,
            f"{y_axis_m[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    savefig(rf"plots/Gust_plot_{day.date}.jpg", format="jpg")
    close()


def plot_visibility(day):
    fig, (plot_1, plot_2) = subplots(2, 1)
    fig.suptitle(
        f"Visibility records for {day.name}, {day.country}\nDate: {day.date}",
        fontsize=title_fontsize,
        weight="black",
    )
    fig.set_size_inches(figure_width, figure_height)
    x_axis = array([time for time in generate_time_axis()])
    y_axis_k = array(
        [day.hourly_reports[hour]["vis_km"] for hour in day.hourly_reports]
    )
    plot_1.plot(x_axis, y_axis_k, marker="o", linestyle="-", color="grey")
    plot_1.set_ylabel("Visibility (km)", fontsize=axis_label_fontsize, weight="black")
    plot_1.set_xticks(range(24))
    plot_1.set_xticklabels(
        plot_1.get_xticklabels(), rotation=rotation_value, fontsize=ticks_fontsize
    )
    plot_1.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_1.set_ylim(top=max(y_axis_k) + 2)
    for point in range(24):
        plot_1.text(
            point,
            y_axis_k[point] + 0.5,
            f"{y_axis_k[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    y_axis_m = array(
        [day.hourly_reports[hour]["vis_miles"] for hour in day.hourly_reports]
    )
    plot_2.plot(x_axis, y_axis_m, marker="o", linestyle="-", color="grey")
    plot_2.set_xlabel("Hour of the Day", fontsize=axis_label_fontsize, weight="black")
    plot_2.set_ylabel(
        "Visibility (miles)", fontsize=axis_label_fontsize, weight="black"
    )
    plot_2.set_xticks(range(24))
    plot_2.set_xticklabels(
        plot_2.get_xticklabels(), rotation=rotation_value, fontsize=ticks_fontsize
    )
    plot_2.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_2.set_ylim(top=max(y_axis_m) + 2)
    for point in range(24):
        plot_2.text(
            point,
            y_axis_m[point] + 0.5,
            f"{y_axis_m[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    savefig(rf"plots/Visibility_plot_{day.date}.jpg", format="jpg")
    close()


def plot_chances(day):
    fig, (plot_1, plot_2) = subplots(2, 1)
    fig.suptitle(
        f"Chance of rain and snow for {day.name}, {day.country}\nDate: {day.date}",
        fontsize=title_fontsize,
        weight="black",
    )
    fig.set_size_inches(figure_width, figure_height)
    x_axis = array([time for time in generate_time_axis()])
    y_axis_r = array(
        [day.hourly_reports[hour]["chance_of_rain"] for hour in day.hourly_reports]
    )
    plot_1.plot(x_axis, y_axis_r, marker="o", linestyle="-", color="#2fbceb")
    plot_1.set_ylabel(
        "Chance of rain (%)", fontsize=axis_label_fontsize, weight="black"
    )
    plot_1.set_xticks(range(24))
    plot_1.set_xticklabels(
        plot_1.get_xticklabels(), rotation=rotation_value, fontsize=ticks_fontsize
    )
    plot_1.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_1.set_ylim(top=max(y_axis_r) + 1)
    for point in range(24):
        plot_1.text(
            point,
            y_axis_r[point] + 0.2,
            f"{y_axis_r[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    y_axis_s = array(
        [day.hourly_reports[hour]["chance_of_snow"] for hour in day.hourly_reports]
    )
    plot_2.plot(x_axis, y_axis_s, marker="o", linestyle="-", color="#cbecf2")
    plot_2.set_xlabel("Hour of the Day", fontsize=axis_label_fontsize, weight="black")
    plot_2.set_ylabel(
        "Chance of snow (%)", fontsize=axis_label_fontsize, weight="black"
    )
    plot_2.set_xticks(range(24))
    plot_2.set_xticklabels(
        plot_2.get_xticklabels(), rotation=rotation_value, fontsize=ticks_fontsize
    )
    plot_2.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_2.set_ylim(top=max(y_axis_s) + 1)
    for point in range(24):
        plot_2.text(
            point,
            y_axis_s[point] + 0.2,
            f"{y_axis_s[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    savefig(rf"plots/Chance_plot_{day.date}.jpg", format="jpg")
    close()


def plot_temperature(day):
    fig, (plot_1, plot_2) = subplots(2, 1)
    fig.suptitle(
        f"Temperature records for {day.name}, {day.country}\nDate: {day.date}",
        fontsize=title_fontsize,
        weight="black",
    )
    fig.set_size_inches(figure_width, figure_height)
    x_axis = array([time for time in generate_time_axis()])
    y_axis_c = array(
        [day.hourly_reports[hour]["temp_c"] for hour in day.hourly_reports]
    )
    plot_1.plot(x_axis, y_axis_c, marker="o", linestyle="-", color="r")
    plot_1.set_ylabel("Temperature (°C)", fontsize=axis_label_fontsize, weight="black")
    plot_1.set_xticks(range(24))
    plot_1.set_xticklabels(
        plot_1.get_xticklabels(), rotation=rotation_value, fontsize=ticks_fontsize
    )
    plot_1.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_1.set_ylim(top=max(y_axis_c) + 2)
    for point in range(24):
        plot_1.text(
            point,
            y_axis_c[point] + 0.5,
            f"{y_axis_c[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    y_axis_f = array(
        [day.hourly_reports[hour]["temp_f"] for hour in day.hourly_reports]
    )
    plot_2.plot(x_axis, y_axis_f, marker="o", linestyle="-", color="r")
    plot_2.set_xlabel("Hour of the Day", fontsize=axis_label_fontsize, weight="black")
    plot_2.set_ylabel("Temperature (°F)", fontsize=axis_label_fontsize, weight="black")
    plot_2.set_xticks(range(24))
    plot_2.set_xticklabels(
        plot_2.get_xticklabels(), rotation=rotation_value, fontsize=ticks_fontsize
    )
    plot_2.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_2.set_ylim(top=max(y_axis_f) + 2)
    for point in range(24):
        plot_2.text(
            point,
            y_axis_f[point] + 0.5,
            f"{y_axis_f[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    savefig(rf"plots/Temperature_plot_{day.date}.jpg", format="jpg")
    close()


def plot_dewpoint(day):
    fig, (plot_1, plot_2) = subplots(2, 1)
    fig.suptitle(
        f"Dewpoint records for {day.name}, {day.country}\nDate: {day.date}",
        fontsize=title_fontsize,
        weight="black",
    )
    fig.set_size_inches(figure_width, figure_height)
    x_axis = array([time for time in generate_time_axis()])
    y_axis_c = array(
        [day.hourly_reports[hour]["dewpoint_c"] for hour in day.hourly_reports]
    )
    plot_1.plot(x_axis, y_axis_c, marker="o", linestyle="-", color="#91eafa")
    plot_1.set_ylabel("Dewpoint (°C)", fontsize=axis_label_fontsize, weight="black")
    plot_1.set_xticks(range(24))
    plot_1.set_xticklabels(
        plot_1.get_xticklabels(), rotation=rotation_value, fontsize=ticks_fontsize
    )
    plot_1.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_1.set_ylim(top=max(y_axis_c) + 2)
    for point in range(24):
        plot_1.text(
            point,
            y_axis_c[point] + 0.5,
            f"{y_axis_c[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    y_axis_f = array(
        [day.hourly_reports[hour]["dewpoint_f"] for hour in day.hourly_reports]
    )
    plot_2.plot(x_axis, y_axis_f, marker="o", linestyle="-", color="#91eafa")
    plot_2.set_xlabel("Hour of the Day", fontsize=axis_label_fontsize, weight="black")
    plot_2.set_ylabel("Dewpoint (°F)", fontsize=axis_label_fontsize, weight="black")
    plot_2.set_xticks(range(24))
    plot_2.set_xticklabels(
        plot_2.get_xticklabels(), rotation=rotation_value, fontsize=ticks_fontsize
    )
    plot_2.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_2.set_ylim(top=max(y_axis_f) + 2)
    for point in range(24):
        plot_2.text(
            point,
            y_axis_f[point] + 0.5,
            f"{y_axis_f[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    savefig(rf"plots/Dewpoint_plot_{day.date}.jpg", format="jpg")
    close()


def plot_humidity_cloudcover(day):
    fig, (plot_1, plot_2) = subplots(2, 1)
    fig.suptitle(
        f"Humidity and Cloud Cover records for {day.name}, {day.country}\nDate: {day.date}",
        fontsize=title_fontsize,
        weight="black",
    )
    fig.set_size_inches(figure_width, figure_height)
    x_axis = array([time for time in generate_time_axis()])
    y_axis_hum = array(
        [day.hourly_reports[hour]["humidity_percentage"] for hour in day.hourly_reports]
    )
    plot_1.plot(x_axis, y_axis_hum, marker="o", linestyle="-", color="#5ad1e6")
    plot_1.set_ylabel("Humidity (%)", fontsize=axis_label_fontsize, weight="black")
    plot_1.set_xticks(range(24))
    plot_1.set_xticklabels(
        plot_1.get_xticklabels(), rotation=rotation_value, fontsize=ticks_fontsize
    )
    plot_1.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_1.set_ylim(top=max(y_axis_hum) + 4)
    for point in range(24):
        plot_1.text(
            point,
            y_axis_hum[point] + 0.5,
            f"{y_axis_hum[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    y_axis_cloud = array(
        [
            day.hourly_reports[hour]["cloud_cover_percentage"]
            for hour in day.hourly_reports
        ]
    )
    plot_2.plot(x_axis, y_axis_cloud, marker="o", linestyle="-", color="#5ad1e6")
    plot_2.set_xlabel("Hour of the Day", fontsize=axis_label_fontsize, weight="black")
    plot_2.set_ylabel("Cloud Cover (%)", fontsize=axis_label_fontsize, weight="black")
    plot_2.set_xticks(range(24))
    plot_2.set_xticklabels(
        plot_2.get_xticklabels(), rotation=rotation_value, fontsize=ticks_fontsize
    )
    plot_2.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_2.set_ylim(top=max(y_axis_cloud) + 6.5)
    for point in range(24):
        plot_2.text(
            point,
            y_axis_cloud[point] + 0.05,
            f"{y_axis_cloud[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    savefig(rf"plots/Humidity_CloudCover_plot_{day.date}.jpg", format="jpg")
    close()


def plot_pressure(day):
    figure(figsize=(figure_width, figure_height))
    title(
        f"Pressure records for {day.name}, {day.country}\nDate: {day.date}",
        fontsize=title_fontsize,
        weight="black",
    )
    xlabel("Hour of the day", fontsize=axis_label_fontsize, weight="black")
    ylabel("Pressure (mb)", fontsize=axis_label_fontsize, weight="black")
    x_axis = array([time for time in generate_time_axis()])
    xticks(rotation=rotation_value, fontsize=ticks_fontsize)
    y_axis_pres = array(
        [int(day.hourly_reports[hour]["pressure_mb"]) for hour in day.hourly_reports]
    )
    tick_params(axis="y", labelsize=ticks_fontsize)
    ylim(bottom=min(y_axis_pres) - 0.5, top=max(y_axis_pres) + 0.5)
    plot(x_axis, y_axis_pres, marker="o", linestyle="-", color="grey")
    for point in range(24):
        text(
            point,
            y_axis_pres[point] + 0.1,
            f"{y_axis_pres[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    savefig(rf"plots/Pressure_plot_{day.date}.jpg", format="jpg")
    close()


def plot_precipitation_snowfall(day):
    fig, (plot_1, plot_2) = subplots(2, 1)
    fig.suptitle(
        f"Precipitation and Snowfall records for {day.name}, {day.country}\nDate: {day.date}",
        fontsize=title_fontsize,
        weight="black",
    )
    fig.set_size_inches(figure_width, figure_height)
    x_axis = array([time for time in generate_time_axis()])
    y_axis_prec = array(
        [day.hourly_reports[hour]["precip_mm"] for hour in day.hourly_reports]
    )
    plot_1.plot(x_axis, y_axis_prec, marker="o", linestyle="-", color="#2fbceb")
    plot_1.set_ylabel(
        "Precipitation (mm)", fontsize=axis_label_fontsize, weight="black"
    )
    plot_1.set_xticks(range(24))
    plot_1.set_xticklabels(
        plot_1.get_xticklabels(), rotation=rotation_value, fontsize=ticks_fontsize
    )
    plot_1.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_1.set_ylim(top=max(y_axis_prec) + 1)
    for point in range(24):
        plot_1.text(
            point,
            y_axis_prec[point] + 0.1,
            f"{y_axis_prec[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    y_axis_snow = array(
        [day.hourly_reports[hour]["snow_cm"] for hour in day.hourly_reports]
    )
    plot_2.plot(x_axis, y_axis_snow, marker="o", linestyle="-", color="#d3e0e8")
    plot_2.set_xlabel("Hour of the Day", fontsize=axis_label_fontsize, weight="black")
    plot_2.set_ylabel("Snowfall (cm)", fontsize=axis_label_fontsize, weight="black")
    plot_2.set_xticks(range(24))
    plot_2.set_xticklabels(
        plot_2.get_xticklabels(), rotation=rotation_value, fontsize=ticks_fontsize
    )
    plot_2.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_2.set_ylim(top=max(y_axis_snow) + 1)
    for point in range(24):
        plot_2.text(
            point,
            y_axis_snow[point] + 0.1,
            f"{y_axis_snow[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    savefig(rf"plots/Precipitation_Snowfall_plot_{day.date}.jpg", format="jpg")
    close()


def plot_wind_speed(day):
    fig, (plot_1, plot_2) = subplots(2, 1)
    fig.suptitle(
        f"Wind Speed records for {day.name}, {day.country}\nDate:{day.date}",
        fontsize=title_fontsize,
        weight="black",
    )
    fig.set_size_inches(figure_width + 1, figure_height + 1)
    x_axis = array(
        [
            f"{item[0]}\n({day.hourly_reports[item[1]]["wind_dir"]})"
            for item in zip(generate_time_axis(), day.hourly_reports)
        ]
    )
    y_axis_k = array(
        [day.hourly_reports[hour]["wind_kph"] for hour in day.hourly_reports]
    )
    plot_1.plot(x_axis, y_axis_k, marker="o", linestyle="-", color="#4293f5")
    plot_1.set_ylabel("Wind Speed (kph)", fontsize=axis_label_fontsize, weight="black")
    plot_1.set_xticks(range(24))
    plot_1.set_xticklabels(
        plot_1.get_xticklabels(), rotation=rotation_value + 40, fontsize=ticks_fontsize
    )
    plot_1.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_1.set_ylim(top=max(y_axis_k) + 2)
    for point in range(24):
        plot_1.text(
            point,
            y_axis_k[point] + 0.5,
            f"{y_axis_k[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    y_axis_m = array(
        [day.hourly_reports[hour]["wind_mph"] for hour in day.hourly_reports]
    )
    plot_2.plot(x_axis, y_axis_m, marker="o", linestyle="-", color="#4293f5")
    plot_2.set_xlabel("Hour of the Day", fontsize=axis_label_fontsize, weight="black")
    plot_2.set_ylabel("Wind Speed (mph)", fontsize=axis_label_fontsize, weight="black")
    plot_2.set_xticks(range(24))
    plot_2.set_xticklabels(
        plot_2.get_xticklabels(), rotation=rotation_value + 40, fontsize=ticks_fontsize
    )
    plot_2.tick_params(axis="y", labelsize=ticks_fontsize)
    plot_2.set_ylim(top=max(y_axis_m) + 2)
    for point in range(24):
        plot_2.text(
            point,
            y_axis_m[point] + 0.5,
            f"{y_axis_m[point]}",
            ha="center",
            va="bottom",
            weight="extra bold",
            fontsize=point_text_fontsize,
        )
    savefig(rf"plots/Wind_Speed_plot_{day.date}.jpg", format="jpg")
    close()


def plot_hourly_weather(day):
    figure(figsize=(8, 1.5))
    title(
        f"Hourly weather for {day.name}, {day.country}\nDate: {day.date}",
        weight="black",
    )
    x_axis = array([time for time in generate_time_axis()])
    xticks(range(24), x_axis, rotation=rotation_value)
    yticks([])
    y_axis_images = array(
        [day.hourly_reports[hour]["condition_image"] for hour in day.hourly_reports]
    )
    images = []
    for link in range(len(y_axis_images)):
        icon = get(f"https:{y_axis_images[link]}").content
        icon = Image.open(BytesIO(icon))
        images.append(icon)
    for position, img in enumerate(images):
        imshow(img, extent=[position - 0.5, position + 0.5, 0, 1])
    xlim(left=-1, right=24)
    savefig(rf"plots/Hourwise_Weather_plot_{day.date}.jpg", format="jpg")
    close()


def plot_hourly_weather_legend(day):
    figure(figsize=(7, 1.5))
    xticks([])
    y_axis_images = [
        day.hourly_reports[hour]["condition_image"] for hour in day.hourly_reports
    ]
    y_axis_text = [
        day.hourly_reports[hour]["condition_text"].title()
        for hour in day.hourly_reports
    ]
    y_axis_group = dict(zip(y_axis_text, y_axis_images))
    yticks(range(len(y_axis_group)), array([label for label in y_axis_group]))
    images = []
    for text in y_axis_group:
        icon = get(f"https:{y_axis_group[text]}").content
        icon = Image.open(BytesIO(icon))
        images.append(icon)
    for position, img in enumerate(images):
        imshow(img, extent=[-1, 1, position - 1, position + 1])
    ylim(bottom=-1, top=len(y_axis_group))
    savefig(rf"plots/Hourwise_Weather_legend_plot_{day.date}.jpg", format="jpg")
    close()


def generate_time_axis():
    for period in ("AM", "PM"):
        for time in range(0, 12):
            if time == 0:
                yield f"{12} {period}"
            else:
                yield f"{time} {period}"


if __name__ == "__main__":
    main()
