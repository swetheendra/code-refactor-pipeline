

import asyncio
import os

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from typing import List, Dict, TypedDict, Annotated
from langchain_core.tools import tool

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

from fastmcp import Client
from langchain_mistralai import ChatMistralAI

from langchain_core.messages import SystemMessage, HumanMessage
from mcp.client.sse import sse_client
from mcp import ClientSession
from langchain_mcp_adapters.tools import load_mcp_tools

import os
import certifi

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

class State(TypedDict):
    messages: Annotated[List[HumanMessage], add_messages]


@tool
def query_policies(query: str) -> List[Dict]:
    """
    Query the Pinecone vector store for code refactoring policies based on the provided query.
    Returns a list of relevant policy documents.
    """

    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
    vectorstore = PineconeVectorStore(
        index_name="code-refactor-policies", 
        embedding=embeddings
    )

    results = vectorstore.similarity_search(query, k=3)
    if not results:
        return []

    formatted_results = []
    for result in results:
        rule = result.metadata.get("rule_id", "Unknown Rule ID")
        category = result.metadata.get("category", "Unknown Category")
    
        formatted_results.append(f"Rule: {rule}, Category: {category}, Content: {result.page_content}")

    return formatted_results

async def get_all_tools(session):
    mcp_tools = await load_mcp_tools(session)
    
    return mcp_tools + [query_policies]

async def build_graph(session):
    tools = await get_all_tools(session)

    model = ChatMistralAI(
        model="mistral-small-latest",
        mistral_api_key=os.environ["MISTRAL_API_KEY"],
        temperature=0,
    )

    llm = model.bind_tools(tools)

    def reason_node(state: State):
        system_prompt = SystemMessage(
            content=(
                "You are an autonomous AI Code Refactoring & Security Audit Agent.\n"
                "Your objective is to inspect target files, run linters and unit tests, "
                "consult security/style policies in Pinecone when errors are found, "
                "and apply code patches until all tests pass.\n\n"
                "Available Actions:\n"
                "- Run linter/security/pytest tools using FastMCP.\n"
                "- Query Pinecone policy rules (`query_policies`) for context.\n"
                "- Apply fixes directly to disk (`apply_code_patch`).\n\n"
                "Always verify your changes by re-running tests before giving your final answer."
            )
        )
        response = llm.invoke([system_prompt] + state["messages"])
        return {"messages": [response]}

    builder = StateGraph(State)
    builder.add_node("reason", reason_node)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "reason")
    builder.add_edge("tools", "reason")
    builder.add_conditional_edges("reason", tools_condition)

    return builder.compile()

async def main():
    server_url = "http://localhost:8000/sse"
    
    # Keep the SSE connection open during graph execution
    async with sse_client(server_url) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            path = r"C:\Users\swtallamraju\temp\ai-code-agent\workspace\script.py"
            graph = await build_graph(session)
            prompt = HumanMessage(content=f"Inspect the file at {path}, run linters and tests, and apply fixes until all tests pass.")

            async for event in graph.astream({"messages": [prompt]}, stream_mode="values"):
                last_msg = event["messages"][-1]

                if "tool_calls" in last_msg and last_msg.tool_calls:
                    for tc in last_msg.tool_calls:
                        print(f"Tool Call: {tc.tool_name} with arguments {tc.arguments}")
                elif last_msg.type == "tool":
                    print(f"Tool Output: {last_msg.name} -> {last_msg.content}")
                elif last_msg.type == "message":
                    print(f"Agent Message: {last_msg.content}")

if __name__ == "__main__":
    asyncio.run(main())
