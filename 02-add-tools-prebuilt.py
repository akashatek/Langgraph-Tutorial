#
# 1. Install the search engine
#

# pip install -U langchain-tavily

#
# 2. Configure your environment
#

import os
import dotenv

dotenv.load_dotenv()
openai_api_key = os.environ["OPENAI_API_KEY"]
tavily_api_key = os.environ.get("TAVILY_API_KEY")

#
# 3. Define the tool
#

from langchain.chat_models import init_chat_model

llm = init_chat_model("openai:gpt-4.1", openai_api_key=openai_api_key)

from langchain_tavily import TavilySearch

tool = TavilySearch(max_results=2, tavily_api_key=tavily_api_key)
tools = [tool]

if __debug__:
    print(tool.invoke("What's a 'node' in LangGraph?"))

#
# 4. Define the graph
#

from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

# Modification: tell the LLM which tools it can call
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)

#
# 5. Use prebuilts
#
from langgraph.prebuilt import ToolNode, tools_condition

tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

#
# 6. Define the conditional_edges
#

# The `tools_condition` function returns "tools" if the chatbot asks to use a tool, and "END" if
# it is fine directly responding. This conditional routing defines the main agent loop.
graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition
)

# Any time a tool is called, we return to the chatbot to decide the next step
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile()

#
# 7 - Visualize the graph (optional)
#
try:
    # Use the correct function to get a bytes-like object
    filename="02-add-tools-prebuilt.png"
    png_data = graph.get_graph().draw_mermaid_png()
    with open(filename, "wb") as f:
        f.write(png_data)
    print(f"Successfully saved the graph to {filename}")

except Exception as e:
        print(f"An error occurred while saving the graph: {e}")

#
# 8 - Ask the bot questions
#

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)

while True:
    try:
        user_input = input("User: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        stream_graph_updates(user_input)
    except:
        # fallback if input() is not available
        user_input = "What do you know about LangGraph?"
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break