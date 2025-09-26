# 🚀 Slack MCP Server - Simple Version

A lightweight Model Context Protocol (MCP) server for Slack integration with essential tools for Do Not Disturb (DND) management and basic Slack operations.

## ✨ Features

- **🎯 Single Focus**: Streamlined server with core Slack functionality
- **🔧 Easy Setup**: Minimal configuration required
- **🛡️ Error Handling**: Robust error handling with user-friendly messages
- **📱 DND Management**: Set and modify Do Not Disturb duration
- **🔌 MCP Compatible**: Full Model Context Protocol support
- **🧪 Tested**: Includes comprehensive test suite

## 🛠️ Available Tools

### `slack_activate_or_modify_do_not_disturb_duration`
Set or modify the Do Not Disturb duration for your Slack workspace.

**Parameters:**
- `num_minutes` (string, required): Number of minutes for DND duration

**Example Usage:**
- Set DND for 30 minutes: `num_minutes = "30"`
- Set DND for 2 hours: `num_minutes = "120"`

**Returns:**
- ✅ Success message with emoji indicators
- ❌ Error message with specific details

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install fastmcp slack-sdk python-dotenv
```

### 2. Set Up Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps)
2. Click "Create New App" → "From scratch"
3. Enter app name and select your workspace
4. Go to "OAuth & Permissions" and add these scopes:
   ```
   dnd:read
   dnd:write
   users:read
   ```
5. Click "Install to Workspace"
6. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### 3. Configure Environment

Create a `.env` file in your project directory:

```env
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_USER_TOKEN=xoxp-your-user-token-here
```

**Note:** For DND operations, you need a user token (`xoxp-`) in addition to the bot token.

### 4. Run the Server

```bash
python slack_mcp_server_simple.py
```

### 5. Test the Setup

```bash
python test_simple_tool.py
```

## 🔧 MCP Inspector Configuration

For use with MCP Inspector, configure as follows:

**Command:** `python`  
**Arguments:** `slack_mcp_server_simple.py`  
**Environment Variables:** 
```
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_USER_TOKEN=xoxp-your-token-here
```

## 📋 Requirements

- Python 3.10+
- Slack Bot Token (xoxb-)
- Slack User Token (xoxp-) for DND operations
- Required OAuth scopes

## 🧪 Testing

The project includes a comprehensive test suite:

```bash
# Test the DND tool
python test_simple_tool.py

# Expected output:
# 🧪 Testing SLACK_ACTIVATE_OR_MODIFY_DO_NOT_DISTURB_DURATION tool...
# Result: ✅ DND set for 30 minutes
# Invalid input result: ❌ Invalid input: 'invalid' is not a valid number
```

## 🔍 Troubleshooting

### Common Issues:

1. **"SLACK_BOT_TOKEN environment variable is required"**
   ```bash
   # Set your token in .env file or environment
   export SLACK_BOT_TOKEN=xoxb-your-token-here
   ```

2. **"SLACK_USER_TOKEN environment variable is required"**
   ```bash
   # DND operations require a user token
   export SLACK_USER_TOKEN=xoxp-your-token-here
   ```

3. **"ModuleNotFoundError: No module named 'slack_sdk'"**
   ```bash
   pip install slack-sdk
   ```

4. **Permission denied errors**
   - Ensure your Slack app has the required OAuth scopes
   - Verify your tokens are correct and not expired

## 📁 Project Structure

```
slack-mcp/
├── slack_mcp_server_simple.py    # Main server file
├── test_simple_tool.py           # Test script
├── requirements.txt              # Dependencies
├── .env                          # Environment variables (create this)
└── README.md                     # This file
```

## 🔄 Adding More Tools

To extend the server with additional tools:

1. Add new `@mcp.tool()` decorated functions
2. Follow the existing pattern for error handling
3. Include proper type hints and documentation
4. Add tests for new functionality

Example:
```python
@mcp.tool()
async def slack_send_message(
    channel: str,
    text: str
) -> dict:
    """Send a message to a Slack channel."""
    try:
        client = get_slack_client()
        response = client.chat_postMessage(channel=channel, text=text)
        return {"success": True, "message": "Message sent successfully"}
    except SlackApiError as e:
        return {"success": False, "error": f"Slack API error: {e.response['error']}"}
```

## 📄 License

This project is open source and available under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📞 Support

For issues and questions:
- Check the troubleshooting section above
- Review Slack API documentation
- Open an issue on GitHub

---

**Made with ❤️ for the Slack and MCP community**
