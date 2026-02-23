"""
Synaptic Bonds: API Executors for Aether Forge.
"""

import httpx
import os
import logging
from typing import Any, Dict

logger = logging.getLogger("AetherForge")

class CoinGeckoExecutor:
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
                "trend_data": [0.1, 0.4, 0.3, 0.8, 0.9, 0.7, 1.0] # Mock for GIF demo
            }
        # Flat access for sparkline in models.py
        if refined:
            first_coin = list(refined.keys())[0]
            refined["trend_data"] = refined[first_coin]["trend_data"]
            
        return refined

class GitHubExecutor:
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
