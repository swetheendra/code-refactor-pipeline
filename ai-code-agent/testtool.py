import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client

async def loop():
    server_url = "http://localhost:8000/sse"
    print("Starting MCP server...")
    async with sse_client(server_url) as (read,write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("MCP server started. Running tools...")
            
            file = "workspace/script.py"

            print(f"Executing linter tool on {file}")
            linter_result = await session.call_tool("run_linter", arguments={"file_path": file})
            print("Linter Result:", linter_result.content[0].text)

            print(f"Executing tests tool on {file}")
            test_result = await session.call_tool("run_tests", arguments={"test_file": file})
            print("Test Result:", test_result.content[0].text)

if __name__ == "__main__":
    asyncio.run(loop())