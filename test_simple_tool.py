#!/usr/bin/env python3
"""
Test script for the simple Slack MCP server
"""

import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_dnd_tool():
    """Test the DND tool function directly"""
    try:
        # Import the function
        from slack_mcp_server_simple import slack_activate_or_modify_do_not_disturb_duration
        
        print("🧪 Testing SLACK_ACTIVATE_OR_MODIFY_DO_NOT_DISTURB_DURATION tool...")
        
        # Test with 30 minutes
        result = await slack_activate_or_modify_do_not_disturb_duration("30")
        print(f"Result: {result}")
        
        # Test with invalid input
        result2 = await slack_activate_or_modify_do_not_disturb_duration("invalid")
        print(f"Invalid input result: {result2}")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")

if __name__ == "__main__":
    # Check if SLACK_BOT_TOKEN is set
    if not os.getenv("SLACK_BOT_TOKEN"):
        print("❌ SLACK_BOT_TOKEN environment variable not set!")
        print("Please set your Slack bot token in .env file or environment variable")
    else:
        print("✅ SLACK_BOT_TOKEN found, running test...")
        asyncio.run(test_dnd_tool())
