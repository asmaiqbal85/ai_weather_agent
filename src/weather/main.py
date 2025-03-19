import os
import requests
from dotenv import load_dotenv
import chainlit as cl
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel
from agents.run import RunConfig
from agents.tool import function_tool

# Load environment variables
load_dotenv()

# Load API keys securely from .env
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Validate API keys
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY is missing in the .env file.")
if not WEATHER_API_KEY:
    raise ValueError("WEATHER_API_KEY is missing in the .env file.")

# OpenWeatherMap API URL
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"

# Chat starters
@cl.set_starters
async def set_starts():
    return [
        cl.Starter(label="Greetings", message="Hello! How can I assist you today?"),
        cl.Starter(label="Weather", message="Find the weather in Karachi."),
    ]

# Weather fetching function
@function_tool
@cl.step(type="weather tool")
def get_weather(location: str, unit: str = "metric") -> str:
    """
    Fetches real-time weather data for a given location.
    
    Args:
        location (str): City name (e.g., "Karachi").
        unit (str): Measurement unit ("metric" for Celsius, "imperial" for Fahrenheit).

    Returns:
        str: A formatted weather description.
    """
    try:
        params = {
            "q": location,
            "appid": WEATHER_API_KEY,
            "units": unit,
        }
        response = requests.get(WEATHER_API_URL, params=params)
        response.raise_for_status()
        data = response.json()

        # Validate API response
        if data.get("cod") != 200:
            return f"Error fetching weather: {data.get('message', 'Unknown error')}"

        weather_desc = data["weather"][0]["description"]
        temperature = data["main"]["temp"]
        return f"The weather in {location} is {weather_desc} with a temperature of {temperature}°C."

    except requests.RequestException as e:
        return f"Failed to fetch weather: {e}"

# Chat session setup
@cl.on_chat_start
async def start():
    """Initializes the assistant when a user starts a chat session."""

    # Create an AI client dynamically
    external_client = AsyncOpenAI(
        api_key=GEMINI_API_KEY,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    model = OpenAIChatCompletionsModel(
        model="gemini-2.0-flash",
        openai_client=external_client,
    )

    config = RunConfig(
        model=model,
        model_provider=external_client,
        tracing_disabled=True,
    )

    # Store configurations in session
    cl.user_session.set("chat_history", [])
    cl.user_session.set("config", config)

    # Create and register agent dynamically
    agent = Agent(name="Assistant", instructions="You are a helpful assistant", model=model)
    agent.tools.extend([get_weather])
    cl.user_session.set("agent", agent)

    await cl.Message(content="Welcome to the AI Assistant! How can I help you today?").send()

# Handle incoming messages
@cl.on_message
async def main(message: cl.Message):
    """Processes user messages and generates responses dynamically."""

    # Temporary thinking response
    msg = cl.Message(content="Thinking...")
    await msg.send()

    # Retrieve session data
    agent = cl.user_session.get("agent")
    config = cl.user_session.get("config")
    history = cl.user_session.get("chat_history") or []

    # Append user message to history
    history.append({"role": "user", "content": message.content})

    try:
        print("\n[CALLING AGENT]\n", history, "\n")
        result = Runner.run_sync(agent, history, run_config=config)

        response_content = result.final_output

        # Update message with response
        msg.content = response_content
        await msg.update()

        # Append AI response to history
        history.append({"role": "assistant", "content": response_content})
        cl.user_session.set("chat_history", history)

        # Log interaction
        print(f"User: {message.content}")
        print(f"Assistant: {response_content}")

    except Exception as e:
        msg.content = f"Error: {str(e)}"
        await msg.update()
        print(f"Error: {str(e)}")