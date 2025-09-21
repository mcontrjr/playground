#!/usr/bin/env python3
"""
Simple test script to discover what DuckDuckGo tools are available
in the Docker MCP Gateway.
"""

import subprocess
import json
import sys
import time

def test_mcp_tools():
    """Test MCP tools by running docker mcp gateway commands."""
    
    print("🔍 Testing MCP Gateway tools...")
    
    # Start the gateway in a subprocess and capture its output
    try:
        print("Starting MCP Gateway...")
        process = subprocess.Popen(
            ["docker", "mcp", "gateway", "run"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1  # Line buffered
        )
        
        # Wait a bit for initialization
        time.sleep(15)
        
        # Check if the process is still running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            print(f"❌ Gateway exited: {stderr}")
            return
        
        print("✅ MCP Gateway appears to be running")
        
        # Try to send an initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "test-client",
                    "version": "1.0.0"
                }
            }
        }
        
        print("📤 Sending initialize request...")
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()
        
        # Read response
        response_line = process.stdout.readline()
        if response_line:
            try:
                response = json.loads(response_line.strip())
                print(f"📥 Initialize response: {response}")
                
                # Send initialized notification
                init_notification = {
                    "jsonrpc": "2.0",
                    "method": "initialized",
                    "params": {}
                }
                
                print("📤 Sending initialized notification...")
                process.stdin.write(json.dumps(init_notification) + "\n")
                process.stdin.flush()
                
                # Wait a bit for the initialization to complete
                print("⏳ Waiting for initialization to complete...")
                time.sleep(3)
                
                # Now try to list tools
                tools_request = {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/list",
                    "params": {}
                }
                
                print("📤 Requesting tools list...")
                process.stdin.write(json.dumps(tools_request) + "\n")
                process.stdin.flush()
                
                # Read tools response
                tools_response_line = process.stdout.readline()
                if tools_response_line:
                    try:
                        tools_response = json.loads(tools_response_line.strip())
                        print(f"🔧 Tools response: {json.dumps(tools_response, indent=2)}")
                        
                        if "result" in tools_response and "tools" in tools_response["result"]:
                            tools = tools_response["result"]["tools"]
                            print(f"\\n🎯 Found {len(tools)} tools:")
                            for tool in tools:
                                print(f"  - {tool.get('name', 'unknown')}: {tool.get('description', 'no description')}")
                                
                            # Try to find and test DuckDuckGo tools
                            ddg_tools = [t for t in tools if 'duckduckgo' in t.get('name', '').lower()]
                            if ddg_tools:
                                print(f"\\n🦆 Found {len(ddg_tools)} DuckDuckGo tools:")
                                for tool in ddg_tools:
                                    print(f"  - {tool['name']}")
                                    print(f"    Description: {tool.get('description', 'N/A')}")
                                    if 'inputSchema' in tool:
                                        schema = tool['inputSchema']
                                        if 'properties' in schema:
                                            print(f"    Parameters: {list(schema['properties'].keys())}")
                                    print()
                                
                                # Try to call one of the tools
                                if ddg_tools:
                                    tool_name = ddg_tools[0]['name']
                                    print(f"🧪 Testing tool: {tool_name}")
                                    
                                    call_request = {
                                        "jsonrpc": "2.0",
                                        "id": 3,
                                        "method": "tools/call",
                                        "params": {
                                            "name": tool_name,
                                            "arguments": {
                                                "query": "test search",
                                                "max_results": 3
                                            }
                                        }
                                    }
                                    
                                    process.stdin.write(json.dumps(call_request) + "\n")
                                    process.stdin.flush()
                                    
                                    # Read call response
                                    call_response_line = process.stdout.readline()
                                    if call_response_line:
                                        try:
                                            call_response = json.loads(call_response_line.strip())
                                            print(f"🔍 Search result: {json.dumps(call_response, indent=2)}")
                                        except json.JSONDecodeError as e:
                                            print(f"❌ Failed to parse call response: {e}")
                                            print(f"Raw response: {call_response_line}")
                            else:
                                print("❌ No DuckDuckGo tools found")
                                
                    except json.JSONDecodeError as e:
                        print(f"❌ Failed to parse tools response: {e}")
                        print(f"Raw response: {tools_response_line}")
                else:
                    print("❌ No tools response received")
                    
            except json.JSONDecodeError as e:
                print(f"❌ Failed to parse initialize response: {e}")
                print(f"Raw response: {response_line}")
        else:
            print("❌ No initialize response received")
            
    except KeyboardInterrupt:
        print("\\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'process' in locals():
            process.terminate()
            process.wait()
            print("🔚 MCP Gateway process terminated")

if __name__ == "__main__":
    test_mcp_tools()