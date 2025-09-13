#
# Install the search engine
#

# pip install -U langchain-tavily

#
# Configure your environment
#

import os
import dotenv

dotenv.load_dotenv()
openai_api_key = os.environ["OPENAI_API_KEY"]
tavily_api_key = os.environ.get("TAVILY_API_KEY")

#
# Define the tool
#

from langchain.chat_models import init_chat_model

llm = init_chat_model("openai:gpt-4.1", openai_api_key=openai_api_key)

from langchain_tavily import TavilySearch

tool = TavilySearch(max_results=2, tavily_api_key=tavily_api_key)
tools = [tool]

if __debug__:
    print(tool.invoke("What's a 'node' in LangGraph?"))

#
# 1. Create a MemorySaver checkpointer
#

from langgraph.checkpoint.memory import InMemorySaver

memory = InMemorySaver()

#
# Define the graph
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
# Use prebuilts
#
from langgraph.prebuilt import ToolNode, tools_condition

tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

#
# 2. Compile the graph
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
graph = graph_builder.compile(checkpointer=memory)

#
# 7 - Visualize the graph (optional)
#
if __debug__:
    try:
        # Use the correct function to get a bytes-like object
        filename="03-add-memory.png"
        png_data = graph.get_graph().draw_mermaid_png()
        with open(filename, "wb") as f:
            f.write(png_data)
        print(f"Successfully saved the graph to {filename}")

    except Exception as e:
            print(f"An error occurred while saving the graph: {e}")

#
# 3. Interact with your chatbot
#
config = {"configurable": {"thread_id": "1"}}

if __debug__:
    user_input = "Hi there! My name is Will."

    # The config is the **second positional argument** to stream() or invoke()!
    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values",
    )
    for event in events:
        event["messages"][-1].pretty_print()
    
#
# 4. Ask a follow up question
#
if __debug__:
    user_input = "Remember my name?"

    # The config is the **second positional argument** to stream() or invoke()!
    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values",
    )
    for event in events:
        event["messages"][-1].pretty_print()

    # The only difference is we change the `thread_id` here to "2" instead of "1"
    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        {"configurable": {"thread_id": "2"}},
        stream_mode="values",
    )
    snapshot = graph.get_state(config)

    for event in events:
        event["messages"][-1].pretty_print()

    print("Snapshot:", snapshot)
    print("Snapshot Next Node:", snapshot.next)


#
# Run the chatbot
#
config = {"configurable": {"thread_id": "2"}}

def stream_graph_updates(user_input: str):
    events = graph.stream(
        {"messages": [{"role": "user", "content": user_input}]},
        config,
        stream_mode="values",
    )

    for event in events:
        event["messages"][-1].pretty_print()

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