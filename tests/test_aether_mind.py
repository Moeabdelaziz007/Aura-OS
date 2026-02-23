import unittest
import json

# This function simulates the Phase 3 feature: The AetherMind Parser
# It intercepts Gemini's 2.0 Spatial API response and translates it to Tauri commands.
def parse_gemini_spatial(response_text: str, screen_w: int, screen_h: int) -> dict:
    try:
        # Gemini spatial API returns coords in [y, x] format scaled to 1000x1000
        data = json.loads(response_text)
        if "point" in data:
            y_rel, x_rel = data["point"]
            # Convert 1000x1000 relative scale to absolute host resolution coordinates
            abs_x = int((x_rel / 1000.0) * screen_w)
            abs_y = int((y_rel / 1000.0) * screen_h)
            return {"action": "CLICK", "x": abs_x, "y": abs_y}
        elif "text" in data:
            return {"action": "TYPE", "text": data["text"]}
    except Exception as e:
        print(f"Error parsing spatial coords: {e}")
    return None

class TestAetherMindParser(unittest.TestCase):
    def test_click_extraction(self):
        # Gemini 2.0 Spatial API outputs [y, x] inside a 1000x1000 grid
        # y=500 (50%), x=250 (25%)
        gemini_response = '{"point": [500, 250]}' 
        screen_w, screen_h = 1920, 1080
        
        result = parse_gemini_spatial(gemini_response, screen_w, screen_h)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["action"], "CLICK")
        self.assertEqual(result["x"], 480) # 1920 * 0.25 = 480
        self.assertEqual(result["y"], 540) # 1080 * 0.50 = 540

    def test_type_extraction(self):
        gemini_response = '{"text": "AetherOS Hackathon"}'
        result = parse_gemini_spatial(gemini_response, 1920, 1080)
        
        self.assertIsNotNone(result)
        self.assertEqual(result["action"], "TYPE")
        self.assertEqual(result["text"], "AetherOS Hackathon")

if __name__ == "__main__":
    unittest.main()
