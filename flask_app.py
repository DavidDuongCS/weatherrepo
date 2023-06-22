from flask import Flask, render_template, request
from datetime import datetime
import requests, string, os

class APIKeyException(Exception):
    pass

app = Flask(__name__)

@app.route('/', methods=["POST", "GET"])
def home():
    if request.method == "POST":
        city = request.form["city"]
        vars = getData(city)
        if "message" in vars:
            return render_template("error.html", message=vars["message"])
        else:
            return render_template("weather.html", vars=vars)
    else:
        return render_template("index.html")

def timestampConvert(timestamp, shift):
    # returns string
    adjustedTime = float(timestamp) + shift
    UTCTime = datetime.utcfromtimestamp(adjustedTime)
    return UTCTime.strftime("%A, %B %d %Y, %I:%M:%S %p")

def signedNumber(num):
    # returns string
    if num >= 0:
        return f"+{num}"
    return str(num)

def getData(city):
    # returns dictionary
    diction = {}
    try:
        apiKey = os.environ.get("OPEN_WEATHER_KEY")
        query = requests.get("https://api.openweathermap.org/geo/1.0/direct", params={"q":city, "appid":apiKey}).json()
        if type(query) == dict:
            cod = query["cod"]
            # Error code 401 means that the API key is either invalid or missing
            if cod == 401:
                raise APIKeyException
        (lat, lon) = (query[0]["lat"], query[0]["lon"])
        diction["name"] = query[0]["name"]
        diction["country"] = query[0]["country"]
    except APIKeyException:
        diction["message"] = "Sorry, there seems to be an invalid API key. Please see https://openweathermap.org/faq#error401 for more info."
    except IndexError:
        diction["message"] = "Sorry, we could not find a city based on your query. Please try again."
    else:
        current = requests.get("https://api.openweathermap.org/data/2.5/weather", params={"lat":lat, "lon":lon, "units":"metric", "appid":apiKey}).json()
        secShift = current["timezone"]
        icon = current["weather"][0]["icon"]
        diction["iconLink"] = f"https://openweathermap.org/img/wn/{icon}@2x.png"
        diction["hourShift"] = signedNumber(int(secShift / 3600))
        diction["description"] = string.capwords(current["weather"][0]["description"])
        diction["temp"] = current["main"]["temp"]
        diction["feelsLike"] = current["main"]["feels_like"]
        diction["min"] = current["main"]["temp_min"]
        diction["max"] = current["main"]["temp_max"]
        diction["pressure"] = current["main"]["pressure"] / 10
        diction["humidity"] = current["main"]["humidity"]
        diction["visibility"] = current["visibility"] / 1000
        diction["windSpeed"] = current["wind"]["speed"] * 3600 / 1000
        diction["cloudiness"] = current["clouds"]["all"]
        diction["dataCalculation"] = timestampConvert(current["dt"], secShift)
        diction["sunrise"] = timestampConvert(current["sys"]["sunrise"], secShift)
        diction["sunset"] = timestampConvert(current["sys"]["sunset"], secShift)
    finally:
        return diction

if __name__ == "__main__":
    app.run(debug=True)