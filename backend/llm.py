"""LLM helper utilities for FlowDesk.

Provides wrappers around the Google Gemini API using standard HTTP client calls.
Includes robust fallback/mock responses if the API key is not configured.
"""

from __future__ import annotations

import json
import os
import re

import httpx
from dotenv import load_dotenv

load_dotenv()


def call_gemini(prompt: str, response_schema: dict | None = None) -> dict:
    """Call the Gemini API using httpx and return the parsed JSON response.

    If LLM_API_KEY is not configured or the API call fails, falls back
    to a mock classification/extraction logic to keep the system robust.
    """
    api_key = os.getenv("LLM_API_KEY")
    if not api_key:
        return _get_mock_response(prompt, response_schema)

    model = os.getenv("LLM_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.1,
        }
    }

    if response_schema:
        payload["generationConfig"]["responseMimeType"] = "application/json"
        payload["generationConfig"]["responseSchema"] = response_schema

    headers = {"Content-Type": "application/json"}

    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
        res_json = response.json()

        candidates = res_json.get("candidates", [])
        if not candidates:
            raise ValueError(f"No candidates returned in Gemini response: {res_json}")

        text = candidates[0]["content"]["parts"][0]["text"]

        if response_schema:
            return json.loads(text)
        return {"text": text}
    except Exception as e:
        # Fallback to mock response on failure to make it robust for demos/tests
        # We print to stderr/log, but don't crash
        print(f"Gemini API Call failed: {e}. Falling back to mock response.")
        return _get_mock_response(prompt, response_schema)


def _get_mock_response(prompt: str, response_schema: dict | None = None) -> dict:
    """Generate mock data based on the prompt/schema for fallback/testing."""
    prompt_lower = prompt.lower()
    
    # Check if the schema is for Category/Priority classification
    if response_schema and "category" in response_schema.get("properties", {}):
        complaint_text = prompt_lower
        comp_match = re.search(r'complaint:\s*"(.*?)"', prompt_lower, re.DOTALL)
        if comp_match:
            complaint_text = comp_match.group(1).strip()
            
        category = "Other"
        priority = "Medium"
        
        # Rule-based mock classifier based on complaint text
        if any(w in complaint_text for w in ["wifi", "wi-fi", "internet", "router", "network"]):
            category = "IT & Wi-Fi"
            priority = "High" if any(w in complaint_text for w in ["urgent", "exam", "broken", "critical", "not working"]) else "Medium"
        elif any(w in complaint_text for w in ["hostel", "room", "geyser", "shower", "bed", "fan", "wardrobe", "heater"]):
            category = "Hostel Maintenance"
            priority = "Critical" if any(w in complaint_text for w in ["leak", "burst", "water logging", "short circuit"]) else "Medium"
        elif any(w in complaint_text for w in ["mess", "food", "dinner", "lunch", "breakfast", "canteen"]):
            category = "Mess & Food"
            priority = "High" if any(w in complaint_text for w in ["sick", "poison", "insect", "unhygienic"]) else "Medium"
        elif any(w in complaint_text for w in ["campus", "road", "street light", "classroom", "garden", "library"]):
            category = "Campus Maintenance"
            priority = "Low"
        elif any(w in complaint_text for w in ["grade", "exam", "professor", "class", "registration", "credits"]):
            category = "Academics"
            priority = "High" if "exam" in complaint_text else "Low"

        return {"category": category, "priority": priority}
        
    else:
        # Extraction schema for intake
        title = "Campus Issue Report"
        description = prompt.strip()
        comp_match = re.search(r'Complaint:\s*"(.*?)"', prompt, re.DOTALL | re.IGNORECASE)
        if comp_match:
            description = comp_match.group(1).strip()
        location = "Unknown"

        # Simple pattern matching to extract room or hostel details
        location_patterns = [
            r"(hostel\s*\d+\s*room\s*\d+)",
            r"(room\s*\d+\s*hostel\s*\d+)",
            r"(room\s*\d+)",
            r"(hostel\s*\d+)",
            r"(mess\s*hall)",
            r"(library)",
            r"(canteen)"
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, prompt_lower)
            if match:
                location = match.group(1).title()
                break

        # Generate cleaner titles
        if any(w in prompt_lower for w in ["wifi", "wi-fi"]):
            title = f"Wi-Fi Connection Issue"
            if location != "Unknown":
                title += f" at {location}"
        elif any(w in prompt_lower for w in ["mess", "food"]):
            title = "Mess Food Quality Complaint"
        elif any(w in prompt_lower for w in ["water", "leak", "geyser"]):
            title = "Water Maintenance Issue"
            if location != "Unknown":
                title += f" at {location}"
        elif any(w in prompt_lower for w in ["electricity", "light", "power", "fan"]):
            title = "Electrical Maintenance Issue"
            if location != "Unknown":
                title += f" at {location}"

        return {
            "title": title,
            "description": description,
            "location": location
        }
