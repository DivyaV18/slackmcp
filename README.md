# 🚀 Slack MCP Server - Complete Integration

A comprehensive Model Context Protocol (MCP) server for Slack integration with 117+ tools covering all major Slack operations including messaging, channels, users, calls, user groups, and more.

## ✨ Features

- **🎯 Comprehensive Coverage**: 117+ Slack tools for complete workspace management
- **🔧 Easy Setup**: Minimal configuration required
- **🛡️ Robust Error Handling**: Detailed error messages with troubleshooting guidance
- **📱 Full Slack Integration**: Messaging, channels, users, calls, user groups, and more
- **🔌 MCP Compatible**: Full Model Context Protocol support
- **🧪 Well Tested**: Comprehensive error handling and validation
- **📊 Real-time Support**: RTM and Socket Mode integration
- **👥 User Management**: Complete user and user group operations
- **📞 Call Management**: Full Slack call lifecycle management

## 🛠️ Available Tools (117+ Tools)

### 📱 Do Not Disturb & Presence Management
- `slack_activate_or_modify_do_not_disturb_duration` - Set/modify DND duration
- `slack_end_user_do_not_disturb_session` - End DND session
- `slack_end_snooze` - End snooze mode
- `slack_end_user_snooze_mode_immediately` - End snooze immediately
- `slack_set_dnd_duration` - Set DND duration
- `slack_set_user_presence` - Set user presence status
- `slack_get_user_presence_info` - Get user presence information
- `slack_retrieve_current_user_dnd_status` - Get current user DND status
- `slack_fetch_dnd_status_for_multiple_team_members` - Get DND status for multiple users
- `slack_get_team_dnd_status` - Get team DND status

### 💬 Messaging & Communication
- `slack_send_message` - Send message to channel
- `slack_sends_a_message_to_a_slack_channel` - Send message with options
- `slack_send_ephemeral_message` - Send ephemeral message
- `slack_sends_ephemeral_messages_to_channel_users` - Send ephemeral to multiple users
- `slack_share_a_me_message_in_a_channel` - Share "me" message
- `slack_schedule_message` - Schedule message
- `slack_schedules_a_message_to_a_channel_at_a_specified_time` - Schedule with timestamp
- `slack_delete_a_scheduled_message_in_a_chat` - Delete scheduled message
- `slack_deletes_a_message_from_a_chat` - Delete message
- `slack_updates_a_slack_message` - Update existing message
- `slack_search_messages` - Search messages
- `slack_search_for_messages_with_query` - Search with query
- `slack_fetch_conversation_history` - Get conversation history
- `slack_fetch_message_thread_from_a_conversation` - Get message thread
- `slack_retrieve_message_permalink_url` - Get message permalink

### 📢 Reactions & Stars
- `slack_add_reaction_to_an_item` - Add reaction to message
- `slack_remove_reaction_from_item` - Remove reaction
- `slack_fetch_item_reactions` - Get item reactions
- `slack_list_user_reactions` - List user reactions
- `slack_add_a_star_to_an_item` - Star an item
- `slack_remove_a_star_from_an_item` - Remove star
- `slack_list_starred_items` - List starred items
- `slack_lists_user_s_starred_items_with_pagination` - List user starred items

### 📌 Pins & Bookmarks
- `slack_pins_an_item_to_a_channel` - Pin item to channel
- `slack_unpin_item_from_channel` - Unpin item from channel
- `slack_lists_pinned_items_in_a_channel` - List pinned items

### 🏢 Channels & Conversations
- `slack_create_channel` - Create new channel
- `slack_create_channel_based_conversation` - Create channel-based conversation
- `slack_archive_a_public_or_private_channel` - Archive channel
- `slack_archive_a_slack_conversation` - Archive conversation
- `slack_unarchive_a_public_or_private_channel` - Unarchive public/private channel
- `slack_unarchive_channel` - Unarchive channel
- `slack_delete_a_public_or_private_channel` - Delete channel
- `slack_rename_a_slack_channel` - Rename channel
- `slack_rename_a_conversation` - Rename conversation
- `slack_set_a_conversation_s_purpose` - Set conversation purpose
- `slack_set_the_topic_of_a_conversation` - Set conversation topic
- `slack_join_an_existing_conversation` - Join conversation
- `slack_leave_a_conversation` - Leave conversation
- `slack_close_dm_or_multi_person_dm` - Close DM
- `slack_open_dm` - Open DM
- `slack_open_or_resume_direct_or_multi_person_messages` - Open/resume DM
- `slack_invite_users_to_a_slack_channel` - Invite users to channel
- `slack_invite_user_to_channel` - Invite user to channel
- `slack_remove_a_user_from_a_conversation` - Remove user from conversation
- `slack_list_all_channels` - List all channels
- `slack_list_all_slack_team_channels_with_various_filters` - List channels with filters
- `slack_find_channels` - Find channels
- `slack_retrieve_conversation_information` - Get conversation info
- `slack_retrieve_conversation_members_list` - Get conversation members
- `slack_get_channel_conversation_preferences` - Get channel preferences
- `slack_list_conversations` - List conversations
- `slack_list_accessible_conversations_for_a_user` - List user accessible conversations

### 👥 Users & User Management
- `slack_list_all_users` - List all users
- `slack_list_all_slack_team_users_with_pagination` - List users with pagination
- `slack_find_users` - Find users
- `slack_lookup_users_by_email` - Lookup users by email
- `slack_invite_user_to_workspace` - Invite user to workspace
- `slack_invite_user_to_workspace_with_optional_channel_invites` - Invite user with channel invites
- `slack_retrieve_detailed_user_information` - Get detailed user info
- `slack_retrieve_user_profile_information` - Get user profile
- `slack_retrieve_a_user_s_identity_details` - Get user identity
- `slack_set_slack_user_profile_information` - Set user profile
- `slack_set_profile_photo` - Set profile photo
- `slack_set_user_profile_photo_with_cropping_options` - Set profile photo with cropping
- `slack_delete_user_profile_photo` - Delete profile photo
- `slack_list_admin_users` - List admin users

### 👥 User Groups
- `slack_create_a_slack_user_group` - Create user group
- `slack_update_an_existing_slack_user_group` - Update user group
- `slack_update_user_group_members` - Update user group members
- `slack_disable_an_existing_slack_user_group` - Disable user group
- `slack_enable_a_specified_user_group` - Enable user group
- `slack_list_user_groups_for_team_with_options` - List user groups
- `slack_list_all_users_in_a_user_group` - List user group members

### 📞 Calls & Meetings
- `slack_start_call` - Start a call
- `slack_registers_a_new_call_with_participants` - Register new call with participants
- `slack_add_call_participants` - Add call participants
- `slack_remove_call_participants` - Remove call participants
- `slack_register_call_participants_removal` - Register participant removal
- `slack_registers_new_call_participants` - Register new participants
- `slack_retrieve_call_information` - Get call information
- `slack_update_slack_call_information` - Update call information
- `slack_end_a_call_with_duration_and_id` - End call with duration

### 🔄 Real-Time Messaging
- `slack_start_real_time_messaging_session` - Start RTM session
- `slack_set_read_cursor_in_a_conversation` - Set read cursor

### 📅 Reminders & Scheduling
- `slack_create_a_reminder` - Create reminder
- `slack_list_reminders` - List reminders
- `slack_list_user_reminders_with_details` - List user reminders with details
- `slack_get_reminder_information` - Get reminder information
- `slack_mark_reminder_as_complete` - Mark reminder complete
- `slack_list_scheduled_messages` - List scheduled messages
- `slack_list_scheduled_messages_in_a_channel` - List scheduled messages in channel

### 🎨 Emojis & Customization
- `slack_add_a_custom_emoji_to_a_slack_team` - Add custom emoji
- `slack_add_an_emoji_alias_in_slack` - Add emoji alias
- `slack_add_emoji` - Add emoji
- `slack_rename_an_emoji` - Rename emoji
- `slack_list_team_custom_emojis` - List custom emojis

### 🔗 URL & Link Management
- `slack_customize_url_unfurl` - Customize URL unfurl
- `slack_customize_url_unfurling_in_messages` - Customize URL unfurling

### 📁 Files & Remote Files
- `slack_list_remote_files` - List remote files

### 🏢 Team & Workspace
- `slack_fetch_current_team_info_with_optional_team_scope` - Get current team info
- `slack_fetch_team_info` - Get team info
- `slack_fetch_workspace_settings_information` - Get workspace settings
- `slack_retrieve_team_profile_details` - Get team profile details
- `slack_fetch_bot_user_information` - Get bot user information

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

#### Required OAuth Scopes

**Bot Token Scopes:**
```
# Core messaging
chat:write
chat:write.public
chat:write.customize

# Channels
channels:read
channels:write
channels:manage
channels:join

# Groups (private channels)
groups:read
groups:write
groups:manage

# Users
users:read
users:read.email
users:write

# User groups
usergroups:read
usergroups:write

# Calls
calls:write
calls:read

# Files
files:read
files:write

# Pins
pins:read
pins:write

# Reactions
reactions:read
reactions:write

# Stars
stars:read
stars:write

# Reminders
reminders:read
reminders:write

# Search
search:read

# Team
team:read

# Bot
bot

# Commands
commands

# Webhooks
incoming-webhook

# App metadata
app_mentions:read

# DND (for user token)
dnd:read
dnd:write

# Presence
users:read
users:write

# Emoji
emoji:read

# Links
links:read
links:write
```

**User Token Scopes (for DND operations):**
```
dnd:read
dnd:write
users:read
users:write
```

5. Click "Install to Workspace"
6. Copy the "Bot User OAuth Token" (starts with `xoxb-`)
7. Copy the "User OAuth Token" (starts with `xoxp-`)

### 3. Configure Environment

Create a `.env` file in your project directory:

```env
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_USER_TOKEN=xoxp-your-user-token-here
```

**Note:** 
- Bot token (`xoxb-`) is required for most operations
- User token (`xoxp-`) is required for DND operations and some user-specific actions

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
- Required OAuth scopes (see above)

## 🧪 Testing

The project includes comprehensive error handling and validation:

```bash
# Test individual tools
python test_simple_tool.py

# Expected output examples:
# ✅ DND set for 30 minutes
# ✅ Message sent successfully
# ✅ Channel created successfully
# ❌ Invalid input: 'invalid' is not a valid number
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
   - Check if you have admin privileges for certain operations

5. **"missing_scope" errors**
   - Add the required scopes to your Slack app
   - Reinstall the app to your workspace after adding scopes

6. **"permission_denied" errors**
   - Some operations require workspace admin privileges
   - User group operations may require user group manager permissions
   - Check if the bot has the necessary permissions for the specific resource

## 📁 Project Structure

```
slack-mcp/
├── slack_mcp_server_simple.py    # Main server file (117+ tools)
├── test_simple_tool.py           # Test script
├── requirements.txt              # Dependencies
├── .env                          # Environment variables (create this)
├── mcp_config.json              # MCP configuration
└── README.md                     # This file
```

## 🔄 Adding More Tools

To extend the server with additional tools:

1. Add new `@mcp.tool()` decorated functions
2. Follow the existing pattern for error handling
3. Include proper type hints and documentation
4. Add comprehensive error handling for Slack API errors
5. Test the new functionality

Example:
```python
@mcp.tool()
async def slack_new_tool(
    parameter1: str,
    parameter2: str = ""
) -> dict:
    """Description of the new tool."""
    try:
        client = get_slack_client()
        response = client.slack_api_method(param1=parameter1, param2=parameter2)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            return {
                "data": {},
                "error": f"Slack API Error: {error}",
                "successful": False
            }
        
        return {
            "data": response.data,
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        return {
            "data": {},
            "error": f"Slack API Error: {error_code}",
            "successful": False
        }
    except Exception as e:
        return {
            "data": {},
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }
```

## 🎯 Tool Categories & Use Cases

### 📱 **Do Not Disturb Management**
Perfect for managing focus time and availability status across your workspace.

### 💬 **Messaging & Communication**
Complete messaging solution with support for scheduled messages, ephemeral messages, and message updates.

### 🏢 **Channel Management**
Full channel lifecycle management including creation, archiving, renaming, and member management.

### 👥 **User & User Group Management**
Comprehensive user management with user group support for team organization.

### 📞 **Call Management**
Complete Slack call integration for meeting management and participant coordination.

### 🔄 **Real-Time Features**
RTM support for real-time event streaming and live updates.

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

## 🔗 Related Resources

- [Slack API Documentation](https://api.slack.com/)
- [Model Context Protocol](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Slack SDK for Python](https://slack.dev/python-slack-sdk/)
