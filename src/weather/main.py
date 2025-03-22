import os
import requests
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv
import chainlit as cl
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.run import RunConfig
from agents.tool import function_tool

# Load environment variables
load_dotenv()

# API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Validate API keys
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing in the .env file.")
if not WEATHER_API_KEY:
    raise ValueError("WEATHER_API_KEY is missing in the .env file.")

# OpenWeatherMap API URL
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

@dataclass
class WeatherInfo:
    temperature: float
    feels_like: float
    humidity: int
    description: str
    wind_speed: float
    pressure: int
    location_name: str
    rain_1h: Optional[float] = None
    visibility: Optional[int] = None

@function_tool
@cl.step(type="weather tool")
def get_weather(location: str, unit: str = "metric") -> str:
    """
    Fetches real-time weather data for a given location.
    """
    try:
        normalized_location = location.strip().title()

        params = {
            "q": normalized_location,
            "appid": WEATHER_API_KEY,
            "units": unit,
        }
        response = requests.get(WEATHER_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        if data.get("cod") != 200:
            return f"Error fetching weather: {data.get('message', 'Unknown error')}"

        weather_info = WeatherInfo(
            temperature=data["main"]["temp"],
            feels_like=data["main"]["feels_like"],
            humidity=data["main"]["humidity"],
            description=data["weather"][0]["description"],
            wind_speed=data["wind"]["speed"],
            pressure=data["main"]["pressure"],
            location_name=data["name"],
            visibility=data.get("visibility"),
            rain_1h=data.get("rain", {}).get("1h"),
        )

        return (
            f"Weather in {weather_info.location_name}:\n"
            f"- Temperature: {weather_info.temperature}°C (feels like {weather_info.feels_like}°C)\n"
            f"- Conditions: {weather_info.description}\n"
            f"- Humidity: {weather_info.humidity}%\n"
            f"- Wind speed: {weather_info.wind_speed} m/s\n"
            f"- Pressure: {weather_info.pressure} hPa\n\n"
            f"Stay tuned for personalized weather suggestions!"
        )
    except requests.RequestException as e:
        return f"Failed to fetch weather: {e}"

# Create a weather assistant
weather_assistant = Agent(
   name="Weather Assistant",
   instructions="""You are a weather assistant that provides current weather information.

   When asked about the weather, use the get_weather tool to fetch accurate data.
   If the user doesn't specify a country code and ambiguity exists,
   ask for clarification (e.g., Paris, France vs. Paris, Texas).

   In addition to weather details, always generate friendly commentary,
   including clothing suggestions or activity recommendations based on conditions.
   """,
   tools=[get_weather]
)

@cl.on_chat_start
async def start():
    external_client = AsyncOpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )
    model = OpenAIChatCompletionsModel(
        model="gemini-2.0-flash",
        openai_client=external_client,
    )
    config = RunConfig(model=model, model_provider=external_client, tracing_disabled=True)
    
    # Initialize agent
    agent = Agent(
        name="Weather Assistant",
        instructions=weather_assistant.instructions,
        model=model,
        tools=[get_weather]
    )
    
    cl.user_session.set("chat_history", [])
    cl.user_session.set("config", config)
    cl.user_session.set("agent", agent)
    
    await cl.Message(content="Welcome! Check the latest weather updates for your location.").send()

@cl.on_message
async def main(message: cl.Message):
    msg = cl.Message(content="Thinking...")
    await msg.send()
    
    agent = cl.user_session.get("agent")
    config = cl.user_session.get("config")
    history = cl.user_session.get("chat_history") or []
    
    history.append({"role": "user", "content": message.content})

    try:
        result = Runner.run_sync(agent, history, run_config=config)
        response_content = result.final_output


        msg.content = response_content
        await msg.update()

        history.append({"role": "assistant", "content": response_content})
        cl.user_session.set("chat_history", history)
    except Exception as e:
        msg.content = f"Error: {str(e)}"
        await msg.update()