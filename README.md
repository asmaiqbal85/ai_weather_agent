# Weather Agent ☂️  

A chatbot assistant that provides real-time weather updates using **Chainlit**, **OpenAI Agents**, and **OpenWeatherMap API**.  

---

## 🚀 Features  
- 🌍 Fetches live weather data for any city
- 🤖 Uses OpenAI Agents for AI-powered interactions  
- 🔧 Built with Chainlit for an interactive chat experience  

---

## 🛠 Installation  

### 1️⃣ Set Up the Project  
```bash
uv init --package weather_agent
cd weather_agent
```

### 2️⃣ Install Dependencies  
```bash
uv add chainlit
uv add openai-agents
uv add python-dotenv
uv add requests
uv sync
```

### 3️⃣ Configure Environment Variables  
Create a `.env` file in the project root and add:  
```ini
GEMINI_API_KEY=your_gemini_api_key
WEATHER_API_KEY=your_openweather_api_key
```

### 4️⃣ Run the Chatbot  
```bash
uv run dev
```

---

## 📍 Usage  
1. Start the chatbot and interact with it through the **Chainlit UI**.  
2. Ask for the weather using a city name (e.g., **"Find the weather in Islamabad"**).  
3. Enjoy using your AI-powered weather assistant! ☀️🌎  

---

