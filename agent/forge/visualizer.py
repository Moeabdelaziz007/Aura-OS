"""
AetherOS — ASCII Micro-Visualizer
===================================
Instead of plain text responses, generate instant visual context
that makes data immediately understandable.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────
# ANSI Color Support
# ─────────────────────────────────────────────

class Colors:
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RESET  = "\033[0m"

    @classmethod
    def green(cls, s: str)  -> str: return f"{cls.GREEN}{s}{cls.RESET}"
    @classmethod
    def red(cls, s: str)    -> str: return f"{cls.RED}{s}{cls.RESET}"
    @classmethod
    def yellow(cls, s: str) -> str: return f"{cls.YELLOW}{s}{cls.RESET}"
    @classmethod
    def cyan(cls, s: str)   -> str: return f"{cls.CYAN}{s}{cls.RESET}"
    @classmethod
    def bold(cls, s: str)   -> str: return f"{cls.BOLD}{s}{cls.RESET}"
    @classmethod
    def dim(cls, s: str)    -> str: return f"{cls.DIM}{s}{cls.RESET}"


# ─────────────────────────────────────────────
# Sparkline Engine
# ─────────────────────────────────────────────

SPARK_CHARS = " ▂▃▄▅▆▇█"

def sparkline(data: List[float]) -> str:
    """
    يرسم خط اتجاه (Sparkline) بسيط باستخدام أحرف Unicode Block Elements.
    """
    if not data:
        return ""

    # إذا كانت كل القيم متساوية
    if min(data) == max(data):
        return SPARK_CHARS[3] * len(data)

    # تطبيع البيانات (Normalization)
    min_val = min(data)
    max_val = max(data)
    range_val = max_val - min_val

    max_idx = len(SPARK_CHARS) - 1
    factor = max_idx / range_val

    result_chars = []
    for val in data:
        idx = math.floor((val - min_val) * factor)
        if idx > max_idx:
            idx = max_idx
        result_chars.append(SPARK_CHARS[idx])

    return "".join(result_chars)


# ─────────────────────────────────────────────
# Price Chart (2D ASCII)
# ─────────────────────────────────────────────

def price_chart(
    prices: List[float],
    asset: str,
    width: int = 40,
    height: int = 6,
    labels: Optional[List[str]] = None,
) -> str:
    """Render a 2D ASCII price chart."""
    if not prices or len(prices) < 2:
        return f"  {asset}: insufficient data"

    min_p = min(prices)
    max_p = max(prices)
    rng   = max_p - min_p or 1.0

    def to_row(p: float) -> int:
        return int((p - min_p) / rng * (height - 1))

    grid = [[" "] * width for _ in range(height)]
    step = max(1, len(prices) // width)
    sampled = prices[::step][:width]

    prev_row = None
    for x, price in enumerate(sampled):
        if x >= width:
            break
        row = height - 1 - to_row(price)
        row = max(0, min(height - 1, row))

        grid[row][x] = "╮" if (prev_row is not None and row < prev_row) else \
                       "╰" if (prev_row is not None and row > prev_row) else "─"

        if prev_row is not None and abs(row - prev_row) > 1:
            lo = min(row, prev_row) + 1
            hi = max(row, prev_row)
            for fill_row in range(lo, hi):
                grid[fill_row][x] = "│"
        prev_row = row

    last_row = height - 1 - to_row(prices[-1])
    last_row = max(0, min(height - 1, last_row))
    if len(sampled) > 0 and len(sampled) - 1 < width:
        grid[last_row][len(sampled) - 1] = "●"

    lines = []
    price_step = rng / (height - 1) if height > 1 else rng
    header = Colors.bold(f"  {asset}/USD ") + Colors.dim("─" * 30)
    lines.append(header)

    for row_idx, row in enumerate(grid):
        price_at_row = max_p - row_idx * price_step
        label = f"{price_at_row:6.1f} ┤" if row_idx < height - 1 else " " * 7 + "└"
        lines.append(Colors.dim(label) + "".join(row))

    time_labels = labels or ["─8h", "─6h", "─4h", "─2h", "now"]
    x_axis = "         " + "  ".join(f"{lbl:>5}" for lbl in time_labels[:5])
    lines.append(Colors.dim(x_axis))
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Crypto Card
# ─────────────────────────────────────────────

def crypto_card(data: Dict[str, Any]) -> str:
    asset   = data.get("asset", "unknown").upper()
    price   = data.get("price_usd", 0.0)
    change  = data.get("change_24h", 0.0)
    volume  = data.get("volume_24h", 0.0)
    mktcap  = data.get("market_cap", 0.0)

    if change > 0:
        arrow  = Colors.green(f"▲ +{change:.2f}%")
        trend  = Colors.green("BULLISH ✅")
    elif change < 0:
        arrow  = Colors.red(f"▼ {change:.2f}%")
        trend  = Colors.red("BEARISH ⚠️")
    else:
        arrow  = Colors.yellow("━  0.00%")
        trend  = Colors.yellow("NEUTRAL ─")

    def fmt_large(n: float) -> str:
        if n >= 1e9: return f"${n/1e9:.1f}B"
        if n >= 1e6: return f"${n/1e6:.1f}M"
        return f"${n:,.0f}"

    spark = sparkline([price * (1 + i * change / 800) for i in range(-8, 1)])

    lines = [
        "  ╔" + "═" * 40 + "╗",
        f"  ║  🪙 {Colors.bold(asset):30s}       ║",
        f"  ║  Price:  {Colors.bold(f'${price:,.2f}'):20s}  {arrow}  ║",
        f"  ║  Volume: {fmt_large(volume):12s}   Cap: {fmt_large(mktcap):10s} ║",
        f"  ║  Trend:  {Colors.cyan(spark):20s}  {trend}  ║",
        "  ╚" + "═" * 40 + "╝",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Weather Card
# ─────────────────────────────────────────────

WEATHER_ICONS = {
    0:  "☀️",   1:  "🌤️",  2: "⛅", 3: "☁️",
    45: "🌫️",  48: "🌫️",
    51: "🌦️",  53: "🌦️",  55: "🌧️",
    61: "🌧️",  63: "🌧️",  65: "🌧️",
    71: "🌨️",  73: "🌨️",  75: "❄️",
    80: "🌦️",  81: "🌧️",  82: "⛈️",
    95: "⛈️",  99: "⛈️",
}

def weather_card(data: Dict[str, Any]) -> str:
    city    = data.get("city", "unknown").title()
    temp    = data.get("temp_c", 0.0)
    wind    = data.get("wind_kmh", 0.0)
    w_code  = data.get("weather_code", 0)
    icon    = WEATHER_ICONS.get(w_code, "🌡️")

    feel = "🥵 Hot" if temp > 35 else "☀️ Warm" if temp > 20 else "🧥 Cool" if temp > 10 else "🥶 Cold"

    lines = [
        "  ╔" + "═" * 36 + "╗",
        f"  ║  {icon}  {Colors.bold(city):28s}      ║",
        f"  ║  🌡️  Temp:  {Colors.bold(f'{temp:.1f}°C'):15s}  {feel:10s}  ║",
        f"  ║  💨  Wind:  {wind:.1f} km/h                   ║",
        "  ╚" + "═" * 36 + "╝",
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────
# GitHub Card
# ─────────────────────────────────────────────

def github_card(data: Dict[str, Any]) -> str:
    query = data.get("query", "")
    total = data.get("total_count", 0)
    repos = data.get("Top_Repos", [])

    lines = [
        f"  🔍 GitHub: '{query}' — {total:,} نتائج",
        "  " + "─" * 46,
    ]
    for r in repos[:4]:
        stars_str = r.get("Stars", "⭐ 0").replace("⭐ ", "").replace(",", "")
        try: stars = int(stars_str)
        except: stars = 0
            
        name  = r.get("Name", "")[:35]
        lang  = r.get("Language", "Unknown")
        
        # Hype Level from stars
        hype_level = min(5, stars // 5000) if stars > 100 else 0
        hype_bar = "🔥" * hype_level + "🌑" * (5 - hype_level)
        
        lines.append(f"  ⭐{stars:6,}  {Colors.bold(name)}")
        lines.append(f"  {Colors.dim(hype_bar)}        {Colors.dim(lang)}")
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Forge Metrics
# ─────────────────────────────────────────────

def metrics_dashboard(metrics_data: Dict[str, Any]) -> str:
    total    = metrics_data.get("total_requests", 0)
    success  = metrics_data.get("success_rate", 0.0)
    avg_lat  = metrics_data.get("avg_latency_ms", 0.0)
    cache    = metrics_data.get("cache_hit_rate", 0.0)

    bar_len  = 20
    s_int    = int(success * bar_len)
    suc_bar  = "█" * s_int + "░" * (bar_len - s_int)
    
    c_int    = int(cache * bar_len)
    cache_bar= "█" * c_int + "░" * (bar_len - c_int)

    lines = [
        "",
        Colors.bold("  📊 AetherOS Forge Metrics"),
        "  " + "─" * 44,
        f"  Total Requests : {total:,}",
        f"  Success Rate   : {Colors.green(suc_bar) if success > 0.9 else Colors.yellow(suc_bar)} {success:.0%}",
        f"  Avg Latency    : {avg_lat:.0f}ms",
        f"  Cache Hit Rate : {Colors.cyan(cache_bar)} {cache:.0%}",
        "  " + "─" * 44,
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────
# Dispatcher
# ─────────────────────────────────────────────

class MicroVisualizer:
    def render(self, service: str, data: Dict[str, Any]) -> str:
        try:
            if service == "coingecko":
                return self._render_crypto(data)
            elif service == "weather":
                return weather_card(data)
            elif service == "github":
                return github_card(data)
            else:
                return self._render_generic(service, data)
        except Exception as e:
            return f"  [{service}] Error rendering: {e}"

    def _render_crypto(self, data: Dict[str, Any]) -> str:
        # Coingecko data structure fix
        # It's a dict per coin from executors.py
        output = []
        for coin_id, val in data.items():
            if coin_id == "trend_data": continue
            if not isinstance(val, dict): continue
            
            price_str = val.get("Price_USD", "$0").replace("$", "").replace(",", "")
            change_str = val.get("Trend_24h", "0%").split(" ")[1].replace("%", "")
            
            card_data = {
                "asset": coin_id,
                "price_usd": float(price_str),
                "change_24h": float(change_str),
                "volume_24h": 0.0, # Placeholder
                "market_cap": 0.0  # Placeholder
            }
            output.append(crypto_card(card_data))
            
            if "trend_data" in val:
                output.append(price_chart(val["trend_data"], coin_id))
            elif "trend_data" in data:
                output.append(price_chart(data["trend_data"], coin_id))
                
        return "\n\n".join(output)

    def _render_generic(self, service: str, data: Dict[str, Any]) -> str:
        lines = [f"  🌌 {service.upper()}"]
        for k, v in list(data.items())[:6]:
            lines.append(f"  {Colors.dim(k):20s}: {v}")
        return "\n".join(lines)
