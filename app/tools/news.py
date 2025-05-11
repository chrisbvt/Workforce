from langchain.tools import BaseTool
from typing import Optional, Type
from pydantic import BaseModel, Field
import requests
import os

class NewsInput(BaseModel):
    query: str = Field(description="The topic to search for news articles")
    category: Optional[str] = Field(None, description="Optional news category to filter by")

class NewsTool(BaseTool):
    name: str = "News"
    description: str = "Get latest news articles on a topic"
    args_schema: Type[BaseModel] = NewsInput
    return_direct: bool = False
    
    def _run(self, query: str, category: Optional[str] = None) -> str:
        """Get news articles using NewsAPI"""
        api_key = os.getenv("NEWS_API_KEY")
        if not api_key:
            return "News API key not found"
        
        base_url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "apiKey": api_key,
            "language": "en",
            "sortBy": "publishedAt"
        }
        
        if category:
            params["category"] = category
        
        try:
            response = requests.get(base_url, params=params)
            data = response.json()
            
            if response.status_code == 200 and data["status"] == "ok":
                articles = data["articles"][:5]  # Get top 5 articles
                result = []
                for article in articles:
                    result.append(f"Title: {article['title']}\nSource: {article['source']['name']}\nURL: {article['url']}\n")
                return "\n".join(result)
            else:
                return f"Error: {data.get('message', 'Unknown error')}"
        except Exception as e:
            return f"Error fetching news: {str(e)}"
    
    async def _arun(self, query: str, category: Optional[str] = None) -> str:
        return self._run(query, category)

news_tool = NewsTool() 