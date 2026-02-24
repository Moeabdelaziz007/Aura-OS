"""
Synaptic Bonds: API Executors for Aether Forge.
"""

import httpx
import os
import logging
from typing import Any, Dict

logger = logging.getLogger("AetherForge")

class CoinGeckoExecutor:
    base_url = "https://api.coingecko.com/api/v3"
    intent_action = "price_check"

    async def execute(self, params: Dict[str, Any], client: httpx.AsyncClient) -> Dict[str, Any]:
        coins = params.get("coins", ["bitcoin", "ethereum", "solana"])
        currencies = params.get("currencies", ["usd"])
        
        resp = await client.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={
                "ids": ",".join(coins),
                "vs_currencies": ",".join(currencies),
                "include_24hr_change": "true",
                "include_market_cap": "true"
            }
        )
        resp.raise_for_status()
        data = resp.json()
            
        refined = {}
        for coin, val in data.items():
            change = val.get("usd_24h_change", 0)
            refined[coin.upper()] = {
                "Price_USD": f"${val.get('usd', 0):,.2f}",
                "Trend_24h": f"{'🟢' if change > 0 else '🔴'} {change:.2f}%",
                "MarketCap": f"${val.get('usd_market_cap', 0)/1e9:.1f}B",
            }
            
        return refined

class GitHubExecutor:
    base_url = "https://api.github.com"
    intent_action = "github_search"

    async def execute(self, params: Dict[str, Any], client: httpx.AsyncClient) -> Dict[str, Any]:
        query = params.get("query", "AI agent python")
        limit = params.get("limit", 3)
        headers = {"Accept": "application/vnd.github.v3+json"}
        
        if token := os.environ.get("GITHUB_TOKEN"):
            headers["Authorization"] = f"Bearer {token}"
            
        resp = await client.get(
            "https://api.github.com/search/repositories",
            params={"q": query, "sort": "stars", "per_page": limit},
            headers=headers
        )
        resp.raise_for_status()
        data = resp.json()
            
        return {
            "Query": query,
            "Total_Found": data.get("total_count", 0),
            "Top_Repos": [
                {
                    "Name": r["full_name"],
                    "Stars": f"⭐ {r['stargazers_count']:,}",
                    "Language": r.get("language", "Unknown"),
                    "URL": r["html_url"]
                } for r in data.get("items", [])
            ]
        }

class WeatherExecutor:
    base_url = "https://api.open-meteo.com/v1"
    intent_action = "weather_check"

    async def execute(self, params: Dict[str, Any], client: httpx.AsyncClient) -> Dict[str, Any]:
        city = params.get("city", "Cairo")
        # Placeholder for OpenWeather logic
        return {
            "City": city,
            "Condition": "Clear Sky",
            "Temp": "24°C",
            "Humidity": "45%",
            "Note": "OpenWeather API bridge ready for activation."
        }
