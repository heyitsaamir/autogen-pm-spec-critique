"""
Copyright (c) Microsoft Corporation. All rights reserved.
Licensed under the MIT License.

Description: initialize the app and listen for `message` activitys
"""

import os
import sys
import traceback
from typing import Dict, Any, Tuple, Annotated, List
from autogen import AssistantAgent, GroupChat, Agent

llm_config = {"model": "gpt-4o", "api_key": os.environ["OPENAI_KEY"]}

from botbuilder.core import TurnContext
from teams import Application, ApplicationOptions, TeamsAdapter
from teams.ai import AIOptions
from autogen_planner import AutoGenPlanner
from JSONStorage import JSONStorage
import nest_asyncio
nest_asyncio.apply()

from config import Config
from state import AppTurnState

config = Config()

if config.OPENAI_KEY is None and config.AZURE_OPENAI_KEY is None:
    raise RuntimeError(
        "Missing environment variables - please check that OPENAI_KEY or AZURE_OPENAI_KEY is set."
    )


storage = JSONStorage()

location_finder_assistant = AssistantAgent(
    name="LocationFinder",
    llm_config=llm_config,
    system_message="You are a location finder.",
)
def find_lat_long(location: Annotated[str, "A string version of a location. It must be in city, state format"]) -> Annotated[Tuple[int, int], "A tuple of the latitude and longitude for the given location"]:
    return (102, 204)
location_finder_assistant.register_for_llm(name="find_lat_long", description="Find the latitude and longitude for a given string location")(find_lat_long)
location_finder_assistant.register_for_execution('find_lat_long')(find_lat_long)

weather_assistant = AssistantAgent(
    name="WeatherAssistant",
    llm_config=llm_config,
    system_message="You are weather assistant. You are able to provide weather information for a user. You do not know how to find the latitude and longitude for a location. Do NOT predict the latitude and longitude for a location. Use evidence from the chat to determine the lat and long of a location",
)
def get_weather(lat: Annotated[int, "latitude for a location"], long: Annotated[int, "longitude for a location"]) -> Annotated[Dict[str, Any], "A json object containing weather information"]:
    return {
    "location": {
        "city": "Renton, WA",
        "country": "US",
        "latitude": lat,
        "longitude": long
    },
    "current_weather": {
        "temperature": 20,
        "humidity": 80,
        "pressure": 1013,
        "weather_description": "clear sky",
        "wind_speed": 3.1,
        "wind_direction": 210
    },
    "forecast": [
        {
            "date": "2022-12-01",
            "temperature": 18,
            "humidity": 70,
            "pressure": 1012,
            "weather_description": "few clouds",
            "wind_speed": 3.5,
            "wind_direction": 220
        },
        {
            "date": "2022-12-02",
            "temperature": 19,
            "humidity": 75,
            "pressure": 1011,
            "weather_description": "scattered clouds",
            "wind_speed": 3.2,
            "wind_direction": 230
        }
    ]
}
weather_assistant.register_for_llm(name='get_weather', description='Get the weather information for a given location.')(get_weather)
weather_assistant.register_for_execution('get_weather')(get_weather)

def build_group_chat(context: TurnContext, state: AppTurnState, agents: List[Agent]):
    group_chat_agents = agents.copy()
    group_chat_agents.append(location_finder_assistant)
    group_chat_agents.append(weather_assistant)
    return GroupChat(messages=[], agents=group_chat_agents)
    
app = Application[AppTurnState](
    ApplicationOptions(
        bot_app_id=config.APP_ID,
        storage=storage,
        adapter=TeamsAdapter(config),
        ai=AIOptions(planner=AutoGenPlanner(llm_config=llm_config, buildConversableAgents=build_group_chat)),
    ),
)

@app.turn_state_factory
async def turn_state_factory(context: TurnContext):
    return await AppTurnState.load(context, storage)

@app.error
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
