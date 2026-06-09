"""LLM helper utilities for FlowDesk.

Provides wrappers around the Google Gemini API using standard HTTP client calls.
Includes fallback responses if the API key is not configured.
"""

from __future__ import annotations

import json
import os
import re

import httpx
from dotenv import load_dotenv

load_dotenv()


def call_gemini(prompt: str, response_schema: dict | None = None) -> dict:
    """Call the LLM using the Google GenAI SDK with Ollama fallback.

    If Google GenAI fails or quota is exhausted, falls back to Ollama.
    If Ollama is not configured or fails, falls back to the mock response.
    """
    api_key = os.getenv("LLM_API_KEY")
    model = os.getenv("LLM_MODEL", "gemini-2.0-flash")

    gemini_succeeded = False
    result = None

    if api_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=api_key)

            config = types.GenerateContentConfig(
                temperature=0.1,
            )
            if response_schema:
                config.response_mime_type = "application/json"
                config.response_schema = response_schema

            response = client.models.generate_content(
                model=model,
                contents=prompt,
                config=config
            )

            text = response.text
            if not text:
                raise ValueError("Empty response text from Gemini")

            if response_schema:
                result = json.loads(text)
            else:
                result = {"text": text}
            gemini_succeeded = True

        except Exception as e:
            error_msg = str(e)
            if api_key in error_msg:
                error_msg = error_msg.replace(api_key, "***REDACTED***")
            print(f"Gemini API call failed using google-genai: {error_msg}. Falling back to Ollama.")

    if not gemini_succeeded:
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        ollama_model = os.getenv("OLLAMA_MODEL", "llama3")

        try:
            # 1. Fetch available models from Ollama to pick a valid model
            available_models = []
            try:
                res = httpx.get(f"{ollama_host}/api/tags", timeout=5.0)
                if res.status_code == 200:
                    models = res.json().get("models", [])
                    available_models = [m["name"] for m in models]
            except Exception as tag_err:
                print(f"Failed to fetch models from Ollama: {tag_err}")

            # 2. Match configured model or pick first available
            chosen_model = ollama_model
            if available_models:
                if ollama_model in available_models:
                    chosen_model = ollama_model
                else:
                    # Check if there is a partial match (e.g. "llama3" matches "llama3:8b...")
                    matches = [m for m in available_models if ollama_model in m]
                    if matches:
                        chosen_model = matches[0]
                    else:
                        # If user customized OLLAMA_MODEL, respect it.
                        # Otherwise, fallback to the first available model.
                        if os.getenv("OLLAMA_MODEL") and os.getenv("OLLAMA_MODEL") != "llama3":
                            print(f"Configured Ollama model '{ollama_model}' not found in available models: {available_models}. Respecting explicit user configuration.")
                            chosen_model = ollama_model
                        else:
                            chosen_model = available_models[0]

            print(f"Attempting Ollama fallback call with model: {chosen_model}")

            payload = {
                "model": chosen_model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            }

            if response_schema:
                # Clean the schema (lowercase types)
                cleaned_schema = _clean_schema_for_ollama(response_schema)
                payload["format"] = cleaned_schema

            res = httpx.post(f"{ollama_host}/api/chat", json=payload, timeout=30.0)
            if res.status_code == 200:
                res_json = res.json()
                content = res_json.get("message", {}).get("content", "")
                if not content:
                    raise ValueError("Empty response content from Ollama")

                if response_schema:
                    result = json.loads(content)
                else:
                    result = {"text": content}
                print("Ollama call succeeded.")
            else:
                raise ValueError(f"Ollama returned status {res.status_code}: {res.text}")

        except Exception as ollama_err:
            print(f"Ollama call failed: {ollama_err}. Falling back to mock response.")

    if result is None:
        result = _get_mock_response(prompt, response_schema)

    return result


def _clean_schema_for_ollama(s):
    if isinstance(s, dict):
        new_s = {}
        for k, v in s.items():
            if k == "type" and isinstance(v, str):
                new_s[k] = v.lower()
            else:
                new_s[k] = _clean_schema_for_ollama(v)
        return new_s
    elif isinstance(s, list):
        return [_clean_schema_for_ollama(item) for item in s]
    return s





def _get_mock_response(prompt: str, response_schema: dict | None = None) -> dict:
    """Generate deterministic fallback data based on the prompt/schema."""
    prompt_lower = prompt.lower()

    if response_schema and "is_valid" in response_schema.get("properties", {}):
        from backend.complaint_validation import validate_complaint_text

        message_text = prompt
        message_match = re.search(r'student message:\s*"(.*?)"', prompt, re.DOTALL | re.IGNORECASE)
        if message_match:
            message_text = message_match.group(1).strip()

        validation = validate_complaint_text(message_text)
        return {
            "is_valid": validation.is_valid,
            "rejection_reason": validation.rejection_reason,
        }
    
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
