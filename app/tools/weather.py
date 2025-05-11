from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field
import requests
import os

class WeatherInput(BaseModel):
    location: str = Field(description="The location to get weather for")

class WeatherTool(BaseTool):
    name: str = "Weather"
    description: str = "Get current weather for a location"
    args_schema: Type[BaseModel] = WeatherInput
    return_direct: bool = False
    
    def _run(self, location: str) -> str:
        """Get current weather for a location using OpenWeatherMap API"""
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            return "OpenWeather API key not found"
        
        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "appid": api_key,
            "units": "metric"
        }
        
        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            
            if response.status_code == 200:
                weather = data["weather"][0]["description"]
                temp = data["main"]["temp"]
                humidity = data["main"]["humidity"]
                return f"Weather in {location}: {weather}, Temperature: {temp}°C, Humidity: {humidity}%"
            else:
                return f"Error: {data.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error fetching weather: {str(e)}"
    
    async def _arun(self, location: str) -> str:
        return self._run(location)

weather_tool = WeatherTool() 