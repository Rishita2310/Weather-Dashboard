import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import math

# ---------------- PAGE CONFIG ----------------

st.set_page_config(
    page_title="Advanced Weather Dashboard",
    page_icon="🌦️",
    layout="wide"
)

# ---------------- CSS ----------------

st.markdown("""
<style>
.block-container {
    padding-top:1rem;
}

div[data-testid="stMetric"] {
    background: rgba(255,255,255,0.05);
    padding:0.8rem;
    border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

# ---------------- HELPERS ----------------

def safe_get(data,*keys,default=None):

    current=data

    for key in keys:

        try:
            current=current[key]
        except:
            return default

    return current


def wind_direction(deg):

    dirs=["N","NNE","NE","ENE","E","ESE",
          "SE","SSE","S","SSW","SW",
          "WSW","W","WNW","NW","NNW"]

    return dirs[int((deg/22.5)+0.5)%16]


def dew_point(temp,humidity):

    a=17.62
    b=243.12

    gamma=((a*temp)/(b+temp))+math.log(humidity/100)

    return (b*gamma)/(a-gamma)


@st.cache_data(ttl=600)
def fetch_json(url):

    r=requests.get(url,timeout=15)

    r.raise_for_status()

    return r.json()


# ---------------- SIDEBAR ----------------

st.sidebar.title("⚙️ Weather Settings")

city=st.sidebar.text_input(
    "Enter City",
    "Ahmedabad"
)

api_key=st.sidebar.text_input(
    "OpenWeather API Key",
    type="password"
)

units_choice=st.sidebar.radio(
    "Units",
    ["Metric","Imperial"]
)

refresh=st.sidebar.button("🔄 Refresh")


if refresh:
    st.cache_data.clear()
    st.rerun()

# ---------------- UNIT SETUP ----------------

if units_choice=="Metric":

    units="metric"

    temp_unit="°C"
    speed_unit="m/s"
    distance_unit="km"
    pressure_unit="hPa"

else:

    units="imperial"

    temp_unit="°F"
    speed_unit="mph"
    distance_unit="mi"
    pressure_unit="hPa"


# ---------------- API CHECK ----------------

if not api_key:

    st.warning("Please enter API key")
    st.stop()


base="https://api.openweathermap.org"

weather_url=(
    f"{base}/data/2.5/weather?"
    f"q={city}"
    f"&appid={api_key}"
    f"&units={units}"
)

try:

    weather=fetch_json(weather_url)

except Exception as e:

    st.error(f"Error: {e}")
    st.stop()


if str(weather.get("cod"))!="200":

    st.error("Invalid city or API key")
    st.stop()


lat=safe_get(weather,"coord","lat")
lon=safe_get(weather,"coord","lon")

forecast_url=(
f"{base}/data/2.5/forecast?"
f"lat={lat}"
f"&lon={lon}"
f"&appid={api_key}"
f"&units={units}"
)

air_url=(
f"{base}/data/2.5/air_pollution?"
f"lat={lat}"
f"&lon={lon}"
f"&appid={api_key}"
)


try:
    forecast=fetch_json(forecast_url)
except:
    forecast=None


try:
    air=fetch_json(air_url)
except:
    air=None


# ---------------- HEADER ----------------

description=safe_get(
weather,
"weather",
0,
"description"
)

icon=safe_get(
weather,
"weather",
0,
"icon"
)

icon_url=(
f"https://openweathermap.org/img/wn/{icon}@4x.png"
)

city_name=weather["name"]

st.title("🌦 Advanced Weather Dashboard")

st.subheader(f"📍 {city_name}")

col1,col2=st.columns([1,4])

with col1:

    st.image(
        icon_url,
        width=130
    )

with col2:

    temp=safe_get(
        weather,
        "main",
        "temp"
    )

    humidity=safe_get(
        weather,
        "main",
        "humidity"
    )

    wind=safe_get(
        weather,
        "wind",
        "speed"
    )

    pressure=safe_get(
        weather,
        "main",
        "pressure"
    )

    feels=safe_get(
        weather,
        "main",
        "feels_like"
    )

    visibility=safe_get(
        weather,
        "visibility"
    )

    st.write(
        f"### {description.title()}"
    )

    st.write(
        f"Feels Like: {round(feels,1)} {temp_unit}"
    )


# ---------------- CURRENT WEATHER ----------------

st.write("## Current Weather")

a,b,c,d=st.columns(4)

a.metric(
"🌡 Temperature",
f"{round(temp,1)} {temp_unit}"
)

b.metric(
"💧 Humidity",
f"{humidity}%"
)

c.metric(
"🌬 Wind",
f"{round(wind,1)} {speed_unit}"
)

d.metric(
"⚡ Pressure",
f"{pressure} {pressure_unit}"
)


extra1,extra2,extra3=st.columns(3)

with extra1:

    deg=safe_get(
        weather,
        "wind",
        "deg",
        default=0
    )

    st.info(
        f"Direction: {wind_direction(deg)}"
    )

with extra2:

    try:

        t=temp

        if units=="imperial":
            t=(temp-32)*(5/9)

        dp=dew_point(
            t,
            humidity
        )

        if units=="imperial":
            dp=(dp*9/5)+32

        st.info(
            f"Dew Point: {round(dp,1)} {temp_unit}"
        )

    except:
        pass


with extra3:

    if visibility:

        if units=="metric":

            visibility=visibility/1000

        else:

            visibility=(visibility/1000)*0.621

        st.info(
            f"Visibility: {round(visibility,1)} {distance_unit}"
        )


# ---------------- AIR POLLUTION ----------------

st.write("## 🌍 Air Pollution")

if air:

    try:

        aqi=air["list"][0]["main"]["aqi"]
        pollutants=air["list"][0]["components"]

        status={
            1:"Good 😊",
            2:"Fair 🙂",
            3:"Moderate 😐",
            4:"Poor 😷",
            5:"Very Poor 🤢"
        }

        st.success(f"AQI: {aqi} ({status[aqi]})")

        p1,p2,p3,p4,p5=st.columns(5)

        p1.metric("PM2.5",f"{pollutants.get('pm2_5',0)} μg/m³")
        p2.metric("PM10",f"{pollutants.get('pm10',0)} μg/m³")
        p3.metric("CO",f"{pollutants.get('co',0)} μg/m³")
        p4.metric("NO₂",f"{pollutants.get('no2',0)} μg/m³")
        p5.metric("O₃",f"{pollutants.get('o3',0)} μg/m³")

        pollution_df=pd.DataFrame(
            pollutants.items(),
            columns=["Pollutant","Value"]
        )

        fig=px.bar(
            pollution_df,
            x="Pollutant",
            y="Value",
            title="Air Pollution Levels"
        )

        st.plotly_chart(fig,use_container_width=True)

    except Exception as e:

        st.warning(f"Air quality unavailable: {e}")


# ---------------- MAP ----------------

st.write("## 🗺 Location")

map_data=pd.DataFrame({

"lat":[lat],
"lon":[lon]

})

st.map(map_data)


# ---------------- FORECAST ----------------

st.write("## 📈 Forecast")

if forecast:

    rows=[]

    for item in forecast["list"]:

        rows.append({

            "Time":item["dt_txt"],

            "Temperature":
            safe_get(
                item,
                "main",
                "temp"
            ),

            "Humidity":
            safe_get(
                item,
                "main",
                "humidity"
            ),

            "Wind":
            safe_get(
                item,
                "wind",
                "speed"
            )
        })


    df=pd.DataFrame(rows)

    fig=px.line(
        df,
        x="Time",
        y="Temperature",
        title=f"Temperature ({temp_unit})"
    )

    st.plotly_chart(
        fig,
        use_container_width=True
    )


    st.dataframe(df)

    csv=df.to_csv(
        index=False
    )

    st.download_button(
        "⬇ Download Forecast CSV",
        csv,
        file_name=f"{city}.csv"
    )


# ---------------- SUNRISE/SUNSET ----------------

st.write("## 🌅 Sunrise & Sunset")

offset=weather.get(
"timezone",
0
)

sunrise=weather["sys"]["sunrise"]
sunset=weather["sys"]["sunset"]

sunrise_local=datetime.utcfromtimestamp(
sunrise+offset
)

sunset_local=datetime.utcfromtimestamp(
sunset+offset
)

x,y=st.columns(2)

x.metric(
"Sunrise",
sunrise_local.strftime("%H:%M:%S")
)

y.metric(
"Sunset",
sunset_local.strftime("%H:%M:%S")
)


st.caption(
"Powered by OpenWeather API"
)


# ---------------- WEATHER SUMMARY ----------------

st.write("## 📊 Weather Summary")

if forecast:

    max_temp = df["Temperature"].max()

    min_temp = df["Temperature"].min()

    avg_wind = df["Wind"].mean()

    col1,col2,col3 = st.columns(3)

    with col1:

        st.metric(
            "🔥 Max Temp",
            f"{round(max_temp,1)} {temp_unit}"
        )

    with col2:

        st.metric(
            "❄️ Min Temp",
            f"{round(min_temp,1)} {temp_unit}"
        )

    with col3:

        st.metric(
            "🌬 Average Wind Speed",
            f"{round(avg_wind,1)} {speed_unit}"
        )