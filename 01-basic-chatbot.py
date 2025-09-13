#
# 1. Install packages
#

# pip install -U langchain-openai langgraph dotenv

#
# 2. Create a StateGraph¶
#
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

#
# 3. Add a node
#
import os
from langchain.chat_models import init_chat_model
import dotenv

dotenv.load_dotenv()

openai_api_key = os.environ["OPENAI_API_KEY"]
llm = init_chat_model("openai:gpt-4.1", openai_api_key=openai_api_key)

def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

graph_builder.add_node("chatbot", chatbot)


#
# 4. Add an entry point¶
#
graph_builder.add_edge(START, "chatbot")

#
# 5. Add an exit point
#
graph_builder.add_edge("chatbot", END)

#
# 6 - Compile the graph
#
graph = graph_builder.compile()

#
# 7 - Visualize the graph (optional)
#
if __debug__:
    try:
        # Use the correct function to get a bytes-like object
        filename="01-basic-chatbot.png"
        png_data = graph.get_graph().draw_mermaid_png()
        with open(filename, "wb") as f:
            f.write(png_data)
        print(f"Successfully saved the graph to {filename}")

    except Exception as e:
            print(f"An error occurred while saving the graph: {e}")

#
# 8 - Run the chatbot
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