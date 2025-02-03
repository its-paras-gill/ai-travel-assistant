import json, googlemaps, requests, openai
#from datetime import datetime, timedelta
from typing import Dict, List
from config import GOOGLE_MAPS_API_KEY, OPENAI_API_KEY, OPENWEATHER_API_KEY

class TravelAssistant:
    def __init__(self):
        self.gmaps_client = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
        self.openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
        self.weather_api_key = OPENWEATHER_API_KEY
        self.travel_data = {
            "route_details": None,
            "weather_forecast": {},
            "traffic_conditions": {}
        }

    def extract_travel_info(self, user_input: str) -> Dict:
        """
        Extracts travel details using OpenAI's NLP model.
        """
        prompt = f"""
        Extract travel information from the following text and return it in JSON format.
        The response should contain:
        - origin: The starting location
        - destination: The final destination
        - waypoints: List of locations to visit in between (can be empty)
        - departure_time: The planned start time (if mentioned, otherwise assume 'now')

        Only return the JSON object, no other text.

        Text: {user_input}
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                #model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
            )
            response_text = response.choices[0].message.content
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            return json.loads(response_text.strip())
        except Exception as e:
            return {"error": f"Failed to parse travel information: {str(e)}"}
        

    def fetch_route_info(self, origin: str, destination: str, waypoints: List[str], departure_time: str):
        """
        Fetch route, ETA, and traffic details with more granular traffic information.
        """
        departure_time = "now" if departure_time.lower() == "now" else departure_time
        try:
            route = self.gmaps_client.directions(
                origin, destination, waypoints=waypoints, departure_time=departure_time
            )
            if not route:
                return {"error": "No route found"}

            route_info = route[0]['legs']
            # Store only essential route details
            self.travel_data["route_details"] = [{
                "start_address": leg["start_address"],
                "end_address": leg["end_address"],
                "distance": leg["distance"]["text"],
                "duration": leg["duration"]["text"],
                "duration_in_traffic": leg.get("duration_in_traffic", {}).get("text", "Not available")
            } for leg in route_info]

            return route_info
        except Exception as e:
            return {"error": f"Failed to fetch route: {str(e)}"}


    def fetch_detailed_traffic(self, origin: str, destination: str):
        """
        Fetch more detailed traffic information for each route segment.
        """
        try:
            traffic_data = self.gmaps_client.directions(
                origin, destination, 
                traffic_model='best_guess',  
                departure_time='now'
            )
            
            if traffic_data:
                self.travel_data["traffic_conditions"] = [{
                    "segment_start": leg["start_address"],
                    "segment_end": leg["end_address"],
                    "traffic_duration": leg.get("duration_in_traffic", {}).get("text", "No traffic data"),
                    "traffic_delay": leg.get("duration_in_traffic", {}).get("value", 0) - 
                                     leg.get("duration", {}).get("value", 0)
                } for leg in traffic_data[0]['legs']]
        except Exception as e:
            self.travel_data["traffic_conditions"] = {"error": f"Traffic fetch failed: {str(e)}"}


    def fetch_weather(self, locations: List[str]):
        for location in locations:
            try:
                url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={self.weather_api_key}&units=metric"
                response = requests.get(url)
                data = response.json()
                
                if response.status_code == 200:
                    self.travel_data["weather_forecast"][location] = {
                        "temperature": data["main"]["temp"],
                        "feels_like": data["main"]["feels_like"],
                        "humidity": data["main"]["humidity"],
                        "description": data["weather"][0]["description"],
                        "wind_speed": data["wind"]["speed"]
                    }
                else:
                    self.travel_data["weather_forecast"][location] = {"error": data.get("message", "Weather fetch failed")}
            except Exception as e:
                self.travel_data["weather_forecast"][location] = {"error": str(e)}


    def process_travel_plan(self, user_input: str):
        """
        Compile all data: Traffic, Weather, and Route Information.
        """
        
        travel_info = self.extract_travel_info(user_input)
        if "error" in travel_info:
            return travel_info

        route_data = self.fetch_route_info(
            travel_info["origin"], 
            travel_info["destination"], 
            travel_info.get("waypoints", []), 
            travel_info.get("departure_time", "now")
        )
        if "error" in route_data:
            return route_data

        locations = [
            travel_info["origin"], 
            travel_info["destination"]
        ] + travel_info.get("waypoints", [])

        self.fetch_weather(locations)
        self.fetch_detailed_traffic(travel_info["origin"], travel_info["destination"])

        return self.travel_data


    def process_query(self, user_query: str):
        if not self.travel_data["route_details"]:
            return "Please process a travel plan first using process_travel_plan()."

        prompt = f"""
        Use {self.travel_data} to answer the user's question concisely.

        Travel Data:
        {json.dumps(self.travel_data, indent=2)}

        User Query: {user_query}
        """
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"Query processing failed: {str(e)}"