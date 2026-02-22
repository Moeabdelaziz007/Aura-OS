"""
Synaptic Bonds: API Executors for Aether Forge.
"""

import httpx
import os
from typing import Any, Dict

class CoinGeckoExecutor:
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        coins = params.get("coins", ["bitcoin"])
        currencies = params.get("currencies", ["usd", "egp"])
        async with httpx.AsyncClient(timeout=10.0) as client:
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
            refined[coin.capitalize()] = {
                "Price_USD": f"${val.get('usd', 0):,.2f}",
                "Price_EGP": f"£{val.get('egp', 0):,.0f}",
                "24h_Change": f"{val.get('usd_24h_change', 0):+.2f}%",
                "Market_Cap": f"${val.get('usd_market_cap', 0)/1e9:.1f}B"
            }
        return refined

class GitHubExecutor:
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        query = params.get("query", "AI agent")
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token := os.environ.get("GITHUB_TOKEN"):
            headers["Authorization"] = f"Bearer {token}"
            
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://api.github.com/search/repositories",
                params={"q": query, "sort": "stars", "per_page": 5},
                headers=headers
            )
            resp.raise_for_status()
            data = resp.json()
            
        return {
            "Query": query,
            "Total": data.get("total_count", 0),
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
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # Mock weather for demo if API key is missing
        city = params.get("city", "Cairo")
        return {
            "City": city,
            "Condition": "Clear Sky",
            "Temp": "24°C",
            "Humidity": "45%",
            "Note": "OpenWeather API key placeholder active."
        }
