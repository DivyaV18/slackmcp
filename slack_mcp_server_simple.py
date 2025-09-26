#!/usr/bin/env python3
"""
Simple Slack MCP Server with SLACK_ACTIVATE_OR_MODIFY_DO_NOT_DISTURB_DURATION tool
"""

import os
import asyncio
from typing import Optional
from fastmcp import FastMCP
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastMCP
mcp = FastMCP("Slack MCP Server")

# Global Slack client
slack_client: Optional[WebClient] = None

def get_slack_client() -> WebClient:
    """Get or initialize Slack client with API token."""
    global slack_client
    if slack_client is None:
        token = os.getenv("SLACK_BOT_TOKEN")
        if not token:
            # Try to load from .env file if not set
            load_dotenv()
            token = os.getenv("SLACK_BOT_TOKEN")
            if not token:
                raise ValueError("SLACK_BOT_TOKEN environment variable is required")
        slack_client = WebClient(token=token)
    return slack_client

def get_slack_user_client() -> WebClient:
    """Get or initialize Slack client with user token for user-specific operations."""
    token = os.getenv("SLACK_USER_TOKEN")
    if not token:
        # Try to load from .env file if not set
        load_dotenv()
        token = os.getenv("SLACK_USER_TOKEN")
        if not token:
            raise ValueError("SLACK_USER_TOKEN environment variable is required for user-specific operations like DND")
    return WebClient(token=token)

# SLACK_ACTIVATE_OR_MODIFY_DO_NOT_DISTURB_DURATION
@mcp.tool()
async def slack_activate_or_modify_do_not_disturb_duration(
    num_minutes: str
) -> str:
    """
    Set snooze duration.
    
    Deprecated: turns on do not disturb mode for the current user, or changes its duration. 
    use `set dnd duration` instead.
    
    Note: This operation requires a user token (SLACK_USER_TOKEN) with dnd:write scope.
    Bot tokens cannot control DND settings.
    
    Args:
        num_minutes (str): Number of minutes for DND duration
        
    Returns:
        str: Success or error message
    """
    try:
        # Use user token for DND operations
        client = get_slack_user_client()
        
        # Convert string to integer
        minutes = int(num_minutes)
        
        # Validate minutes range (Slack allows 1-4320 minutes)
        if minutes < 1 or minutes > 4320:
            return f"Invalid duration: {minutes} minutes. Must be between 1 and 4320 minutes (72 hours)"
        
        # Set DND snooze duration
        response = client.dnd_setSnooze(num_minutes=minutes)
        
        # Check if successful
        if response.data.get("ok", False):
            return f"DND snooze set for {minutes} minutes successfully"
        else:
            return f"Failed to set DND snooze: {response.data.get('error', 'Unknown error')}"
            
    except ValueError as e:
        if "SLACK_USER_TOKEN" in str(e):
            return f"Configuration Error: {str(e)}\n\nTo fix this:\n1. Set SLACK_USER_TOKEN environment variable\n2. Use a user token (xoxp-) with dnd:write scope\n3. Bot tokens (xoxb-) cannot control DND settings"
        return f"Invalid number of minutes: {str(e)}"
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_allowed_token_type':
            return f"Token Type Error: {error_code}\n\nThis operation requires a user token (xoxp-) with dnd:write scope.\nBot tokens (xoxb-) cannot control DND settings.\n\nTo fix:\n1. Set SLACK_USER_TOKEN environment variable\n2. Use a user token with appropriate scopes"
        return f"Slack API Error: {error_code}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

# SLACK_ADD_A_CUSTOM_EMOJI_TO_A_SLACK_TEAM
@mcp.tool()
async def slack_add_a_custom_emoji_to_a_slack_team(
    name: str,
    token: str,
    url: str
) -> dict:
    """
    Add a custom emoji to a Slack team.
    
    Deprecated: adds a custom emoji to a slack workspace given a unique name and an image url. 
    use `add emoji` instead.
    
    Args:
        name (str): Unique name for the emoji
        token (str): Slack token for authentication
        url (str): URL of the image to use as emoji
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Create client with provided token
        client = WebClient(token=token)
        
        # Validate inputs
        if not name or not name.strip():
            return {
                "data": {},
                "error": "Emoji name cannot be empty",
                "successful": False
            }
        
        if not url or not url.strip():
            return {
                "data": {},
                "error": "Image URL cannot be empty",
                "successful": False
            }
        
        # Validate emoji name format (alphanumeric, hyphens, underscores only)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            return {
                "data": {},
                "error": "Emoji name can only contain letters, numbers, hyphens, and underscores",
                "successful": False
            }
        
        # Add the custom emoji
        # Note: admin.emoji.add requires Enterprise Grid
        # For regular workspaces, this will fail with "not_an_enterprise"
        response = client.admin_emoji_add(
            name=name,
            url=url
        )
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_an_enterprise':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis operation requires Slack Enterprise Grid. Regular Slack workspaces cannot add emojis via API.\n\nTo add emojis in regular workspaces:\n1. Go to workspace settings\n2. Navigate to 'Customize' → 'Add custom emoji'\n3. Upload the image manually",
                "successful": False
            }
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

# SLACK_ADD_AN_EMOJI_ALIAS_IN_SLACK
@mcp.tool()
async def slack_add_an_emoji_alias_in_slack(
    alias_for: str,
    name: str,
    token: str
) -> dict:
    """
    Add an emoji alias.
    
    Adds an alias for an existing custom emoji in a slack enterprise grid organization.
    
    Args:
        alias_for (str): Name of the existing emoji to create alias for
        name (str): Name for the new alias
        token (str): Slack token for authentication
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Create client with provided token
        client = WebClient(token=token)
        
        # Validate inputs
        if not alias_for or not alias_for.strip():
            return {
                "data": {},
                "error": "Alias target emoji name cannot be empty",
                "successful": False
            }
        
        if not name or not name.strip():
            return {
                "data": {},
                "error": "Alias name cannot be empty",
                "successful": False
            }
        
        # Validate emoji name format (alphanumeric, hyphens, underscores only)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            return {
                "data": {},
                "error": "Alias name can only contain letters, numbers, hyphens, and underscores",
                "successful": False
            }
        
        if not re.match(r'^[a-zA-Z0-9_-]+$', alias_for):
            return {
                "data": {},
                "error": "Target emoji name can only contain letters, numbers, hyphens, and underscores",
                "successful": False
            }
        
        # Add the emoji alias
        # Note: admin.emoji.addAlias requires Enterprise Grid
        response = client.admin_emoji_addAlias(
            name=name,
            alias_for=alias_for
        )
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_an_enterprise':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis operation requires Slack Enterprise Grid. Regular Slack workspaces cannot add emoji aliases via API.\n\nTo add emoji aliases in regular workspaces:\n1. Go to workspace settings\n2. Navigate to 'Customize' → 'Add custom emoji'\n3. Upload the same image with a different name",
                "successful": False
            }
        elif error_code == 'emoji_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe target emoji '{alias_for}' does not exist. Make sure the emoji exists before creating an alias.",
                "successful": False
            }
        elif error_code == 'name_taken':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe alias name '{name}' is already taken. Choose a different name for the alias.",
                "successful": False
            }
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

# SLACK_ADD_A_STAR_TO_AN_ITEM
@mcp.tool()
async def slack_add_a_star_to_an_item(
    channel: str = "",
    file: str = "",
    file_comment: str = "",
    timestamp: str = ""
) -> dict:
    """
    Add a star to an item.
    
    Stars a channel, file, file comment, or a specific message in slack.
    
    Args:
        channel (str): Channel ID to star (optional)
        file (str): File ID to star (optional)
        file_comment (str): File comment ID to star (optional)
        timestamp (str): Message timestamp to star (optional)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for starring operations)
        client = get_slack_client()
        
        # Validate that at least one parameter is provided
        provided_params = [param for param in [channel, file, file_comment, timestamp] if param and param.strip()]
        if not provided_params:
            return {
                "data": {},
                "error": "At least one parameter must be provided: channel, file, file_comment, or timestamp",
                "successful": False
            }
        
        # Validate that only one parameter is provided (Slack API limitation)
        if len(provided_params) > 1:
            return {
                "data": {},
                "error": "Only one parameter can be provided at a time. Choose either channel, file, file_comment, or timestamp",
                "successful": False
            }
        
        # Prepare the API call parameters
        api_params = {}
        if channel and channel.strip():
            api_params['channel'] = channel.strip()
        elif file and file.strip():
            api_params['file'] = file.strip()
        elif file_comment and file_comment.strip():
            api_params['file_comment'] = file_comment.strip()
        elif timestamp and timestamp.strip():
            api_params['timestamp'] = timestamp.strip()
        
        # Add the star
        response = client.stars_add(**api_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'file_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe file '{file}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'message_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe message with timestamp '{timestamp}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'already_starred':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis item is already starred.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
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

# SLACK_ADD_CALL_PARTICIPANTS
@mcp.tool()
async def slack_add_call_participants(
    id: str,
    users: str
) -> dict:
    """
    Add call participants.
    
    Registers new participants added to a slack call.
    
    Args:
        id (str): Call ID to add participants to
        users (str): Comma-separated list of user IDs to add to the call
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for call operations)
        client = get_slack_client()
        
        # Validate inputs
        if not id or not id.strip():
            return {
                "data": {},
                "error": "Call ID cannot be empty",
                "successful": False
            }
        
        if not users or not users.strip():
            return {
                "data": {},
                "error": "Users list cannot be empty",
                "successful": False
            }
        
        # Parse and validate user IDs
        user_list = [user.strip() for user in users.split(',') if user.strip()]
        if not user_list:
            return {
                "data": {},
                "error": "No valid user IDs provided. Provide comma-separated user IDs.",
                "successful": False
            }
        
        # Validate user ID format (should start with 'U')
        for user_id in user_list:
            if not user_id.startswith('U'):
                return {
                    "data": {},
                    "error": f"Invalid user ID format: '{user_id}'. User IDs should start with 'U'.",
                    "successful": False
                }
        
        # Add participants to the call
        response = client.calls_participants_add(
            id=id.strip(),
            users=user_list
        )
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'call_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe call with ID '{id}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more user IDs in the list do not exist or are invalid.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'calls:write' scope.",
                "successful": False
            }
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

# SLACK_ADD_EMOJI
@mcp.tool()
async def slack_add_emoji(
    name: str,
    token: str,
    url: str
) -> dict:
    """
    Add emoji.
    
    Adds a custom emoji to a slack workspace given a unique name and an image url; 
    subject to workspace emoji limits.
    
    Args:
        name (str): Unique name for the emoji
        token (str): Slack token for authentication
        url (str): URL of the image to use as emoji
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Create client with provided token
        client = WebClient(token=token)
        
        # Validate inputs
        if not name or not name.strip():
            return {
                "data": {},
                "error": "Emoji name cannot be empty",
                "successful": False
            }
        
        if not url or not url.strip():
            return {
                "data": {},
                "error": "Image URL cannot be empty",
                "successful": False
            }
        
        # Validate emoji name format (alphanumeric, hyphens, underscores only)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', name):
            return {
                "data": {},
                "error": "Emoji name can only contain letters, numbers, hyphens, and underscores",
                "successful": False
            }
        
        # Validate URL format
        if not url.startswith(('http://', 'https://')):
            return {
                "data": {},
                "error": "Image URL must start with http:// or https://",
                "successful": False
            }
        
        # Add the custom emoji
        # Note: admin.emoji.add requires Enterprise Grid
        response = client.admin_emoji_add(
            name=name,
            url=url
        )
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_an_enterprise':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis operation requires Slack Enterprise Grid. Regular Slack workspaces cannot add emojis via API.\n\nTo add emojis in regular workspaces:\n1. Go to workspace settings\n2. Navigate to 'Customize' → 'Add custom emoji'\n3. Upload the image manually",
                "successful": False
            }
        elif error_code == 'name_taken':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe emoji name '{name}' is already taken. Choose a different name.",
                "successful": False
            }
        elif error_code == 'invalid_name':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe emoji name '{name}' is invalid. Use letters, numbers, hyphens, and underscores only.",
                "successful": False
            }
        elif error_code == 'bad_image':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe image at URL '{url}' is invalid or cannot be processed. Ensure the URL points to a valid image file.",
                "successful": False
            }
        elif error_code == 'emoji_limit_reached':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe workspace has reached its emoji limit. Remove some emojis before adding new ones.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your token format and validity.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nToken lacks required scopes. Ensure the token has 'admin.emoji:write' scope.",
                "successful": False
            }
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

# SLACK_ADD_REACTION_TO_AN_ITEM
@mcp.tool()
async def slack_add_reaction_to_an_item(
    channel: str,
    name: str,
    timestamp: str
) -> dict:
    """
    Add reaction to message.
    
    Adds a specified emoji reaction to an existing message in a slack channel, 
    identified by its timestamp; does not remove or retrieve reactions.
    
    Args:
        channel (str): Channel ID where the message is located
        name (str): Emoji name to add as reaction (without colons)
        timestamp (str): Message timestamp to add reaction to
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for reaction operations)
        client = get_slack_client()
        
        # Validate inputs
        if not channel or not channel.strip():
            return {
                "data": {},
                "error": "Channel ID cannot be empty",
                "successful": False
            }
        
        if not name or not name.strip():
            return {
                "data": {},
                "error": "Emoji name cannot be empty",
                "successful": False
            }
        
        if not timestamp or not timestamp.strip():
            return {
                "data": {},
                "error": "Message timestamp cannot be empty",
                "successful": False
            }
        
        # Validate channel ID format (should start with 'C' for channels)
        if not channel.startswith('C'):
            return {
                "data": {},
                "error": f"Invalid channel ID format: '{channel}'. Channel IDs should start with 'C'.",
                "successful": False
            }
        
        # Validate emoji name format (remove colons if present)
        emoji_name = name.strip()
        if emoji_name.startswith(':') and emoji_name.endswith(':'):
            emoji_name = emoji_name[1:-1]  # Remove colons
        
        # Validate emoji name format (alphanumeric, hyphens, underscores only)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', emoji_name):
            return {
                "data": {},
                "error": "Emoji name can only contain letters, numbers, hyphens, and underscores",
                "successful": False
            }
        
        # Add the reaction
        response = client.reactions_add(
            channel=channel.strip(),
            name=emoji_name,
            timestamp=timestamp.strip()
        )
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'message_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe message with timestamp '{timestamp}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'invalid_name':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe emoji name '{name}' is invalid or does not exist in this workspace.",
                "successful": False
            }
        elif error_code == 'already_reacted':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nYou have already added this reaction to the message.",
                "successful": False
            }
        elif error_code == 'no_reaction':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe emoji '{name}' is not available in this workspace.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'reactions:write' scope.",
                "successful": False
            }
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

# SLACK_ARCHIVE_A_PUBLIC_OR_PRIVATE_CHANNEL
@mcp.tool()
async def slack_archive_a_public_or_private_channel(
    channel_id: str
) -> dict:
    """
    Archive a public or private channel.
    
    Archives a slack public or private channel, making it read-only; 
    the primary 'general' channel cannot be archived.
    
    Args:
        channel_id (str): Channel ID to archive
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for channel operations)
        client = get_slack_client()
        
        # Validate inputs
        if not channel_id or not channel_id.strip():
            return {
                "data": {},
                "error": "Channel ID cannot be empty",
                "successful": False
            }
        
        # Validate channel ID format (should start with 'C' for channels)
        if not channel_id.startswith('C'):
            return {
                "data": {},
                "error": f"Invalid channel ID format: '{channel_id}'. Channel IDs should start with 'C'.",
                "successful": False
            }
        
        # Archive the channel
        response = client.conversations_archive(
            channel=channel_id.strip()
        )
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel_id}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'is_archived':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel_id}' is already archived.",
                "successful": False
            }
        elif error_code == 'cant_archive_general':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe 'general' channel cannot be archived.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'channels:manage' (for public channels) and 'groups:write' (for private channels) scopes.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'channels:manage' (for public channels) and 'groups:write' (for private channels) scopes and reinstall the app.",
                "successful": False
            }
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

# SLACK_ARCHIVE_A_SLACK_CONVERSATION
@mcp.tool()
async def slack_archive_a_slack_conversation(
    channel: str
) -> dict:
    """
    Archive a Slack conversation.
    
    Archives a slack conversation by its id, rendering it read-only and hidden while 
    retaining history, ideal for cleaning up inactive channels; be aware that some 
    channels (like #general or certain dms) cannot be archived and this may impact 
    connected integrations.
    
    Args:
        channel (str): Channel ID to archive
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for conversation operations)
        client = get_slack_client()
        
        # Validate inputs
        if not channel or not channel.strip():
            return {
                "data": {},
                "error": "Channel ID cannot be empty",
                "successful": False
            }
        
        # Validate channel ID format (should start with 'C' for channels or 'D' for DMs)
        if not channel.startswith(('C', 'D', 'G')):
            return {
                "data": {},
                "error": f"Invalid channel ID format: '{channel}'. Channel IDs should start with 'C' (channels), 'D' (DMs), or 'G' (private channels).",
                "successful": False
            }
        
        # Archive the conversation
        response = client.conversations_archive(
            channel=channel.strip()
        )
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe conversation '{channel}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'is_archived':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe conversation '{channel}' is already archived.",
                "successful": False
            }
        elif error_code == 'cant_archive_general':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe 'general' channel cannot be archived.",
                "successful": False
            }
        elif error_code == 'cant_archive_this_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis channel cannot be archived. Some channels (like #general) or certain DMs cannot be archived.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of the conversation '{channel}'. Add the bot to the channel first.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'channels:manage' (for public channels) and 'groups:write' (for private channels) scopes.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'channels:manage' (for public channels) and 'groups:write' (for private channels) scopes and reinstall the app.",
                "successful": False
            }
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

# SLACK_SEND_MESSAGE
@mcp.tool()
async def slack_send_message(
    channel: str,
    text: str = "",
    as_user: bool = False,
    attachments: str = "",
    blocks: str = "",
    icon_emoji: str = "",
    icon_url: str = "",
    link_names: bool = False,
    markdown_text: str = "",
    mrkdwn: bool = False,
    parse: str = "",
    reply_broadcast: bool = False,
    thread_ts: str = "",
    unfurl_links: bool = True,
    unfurl_media: bool = True,
    username: str = ""
) -> dict:
    """
    Send a message to a Slack channel.
    
    Sends a message to a Slack channel with various formatting and attachment options.
    
    Args:
        channel (str): Channel ID to send message to (required)
        text (str): Message text content
        as_user (bool): Send message as the bot user
        attachments (str): JSON string of attachments
        blocks (str): JSON string of blocks
        icon_emoji (str): Emoji to use as icon
        icon_url (str): URL to use as icon
        link_names (bool): Whether to link @mentions and #channels
        markdown_text (str): Markdown formatted text
        mrkdwn (bool): Whether to parse markdown
        parse (str): How to parse the message ('full', 'none')
        reply_broadcast (bool): Whether to broadcast reply to channel
        thread_ts (str): Timestamp of parent message for threading
        unfurl_links (bool): Whether to unfurl links
        unfurl_media (bool): Whether to unfurl media
        username (str): Username to display
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for message operations)
        client = get_slack_client()
        
        # Validate required inputs
        if not channel or not channel.strip():
            return {
                "data": {},
                "error": "Channel ID is required",
                "successful": False
            }
        
        # Validate channel ID format
        if not channel.startswith(('C', 'D', 'G')):
            return {
                "data": {},
                "error": f"Invalid channel ID format: '{channel}'. Channel IDs should start with 'C' (channels), 'D' (DMs), or 'G' (private channels).",
                "successful": False
            }
        
        # Prepare message parameters
        message_params = {
            "channel": channel.strip()
        }
        
        # Add optional parameters if provided
        if text and text.strip():
            message_params["text"] = text.strip()
        
        if as_user:
            message_params["as_user"] = as_user
        
        if attachments and attachments.strip():
            try:
                import json
                message_params["attachments"] = json.loads(attachments)
            except json.JSONDecodeError:
                return {
                    "data": {},
                    "error": "Invalid JSON format for attachments parameter",
                    "successful": False
                }
        
        if blocks and blocks.strip():
            try:
                import json
                message_params["blocks"] = json.loads(blocks)
            except json.JSONDecodeError:
                return {
                    "data": {},
                    "error": "Invalid JSON format for blocks parameter",
                    "successful": False
                }
        
        if icon_emoji and icon_emoji.strip():
            message_params["icon_emoji"] = icon_emoji.strip()
        
        if icon_url and icon_url.strip():
            message_params["icon_url"] = icon_url.strip()
        
        if link_names:
            message_params["link_names"] = link_names
        
        if markdown_text and markdown_text.strip():
            message_params["markdown_text"] = markdown_text.strip()
        
        if mrkdwn:
            message_params["mrkdwn"] = mrkdwn
        
        if parse and parse.strip():
            if parse.strip() in ['full', 'none']:
                message_params["parse"] = parse.strip()
            else:
                return {
                    "data": {},
                    "error": "Parse parameter must be 'full' or 'none'",
                    "successful": False
                }
        
        if reply_broadcast:
            message_params["reply_broadcast"] = reply_broadcast
        
        if thread_ts and thread_ts.strip():
            message_params["thread_ts"] = thread_ts.strip()
        
        if not unfurl_links:
            message_params["unfurl_links"] = unfurl_links
        
        if not unfurl_media:
            message_params["unfurl_media"] = unfurl_media
        
        if username and username.strip():
            message_params["username"] = username.strip()
        
        # Send the message
        response = client.chat_postMessage(**message_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of the channel '{channel}'. Add the bot to the channel first.",
                "successful": False
            }
        elif error_code == 'msg_too_long':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe message is too long. Slack has a 40,000 character limit for messages.",
                "successful": False
            }
        elif error_code == 'no_text':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMessage must contain text, attachments, or blocks.",
                "successful": False
            }
        elif error_code == 'rate_limited':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nRate limit exceeded. Please wait before sending another message.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'chat:write' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'chat:write' scope and reinstall the app.",
                "successful": False
            }
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

# SLACK_CLOSE_DM_OR_MULTI_PERSON_DM
@mcp.tool()
async def slack_close_dm_or_multi_person_dm(
    channel: str
) -> dict:
    """
    Close conversation channel.
    
    Closes a slack direct message (dm) or multi-person direct message (mpdm) channel, 
    removing it from the user's sidebar without deleting history; this action affects 
    only the calling user's view.
    
    Args:
        channel (str): Channel ID to close (DM or MPDM)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for conversation operations)
        client = get_slack_client()
        
        # Validate inputs
        if not channel or not channel.strip():
            return {
                "data": {},
                "error": "Channel ID cannot be empty",
                "successful": False
            }
        
        # Validate channel ID format (should start with 'D' for DMs or 'G' for MPDMs)
        if not channel.startswith(('D', 'G')):
            return {
                "data": {},
                "error": f"Invalid channel ID format: '{channel}'. Channel IDs should start with 'D' (DMs) or 'G' (MPDMs).",
                "successful": False
            }
        
        # Close the conversation
        response = client.conversations_close(
            channel=channel.strip()
        )
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe conversation '{channel}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of the conversation '{channel}'. Add the bot to the conversation first.",
                "successful": False
            }
        elif error_code == 'cant_close_general':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe 'general' channel cannot be closed.",
                "successful": False
            }
        elif error_code == 'cant_close_mpim':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis multi-person direct message cannot be closed.",
                "successful": False
            }
        elif error_code == 'method_not_supported_for_channel_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis channel type cannot be closed. Only DMs and MPDMs can be closed.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'im:write' scope for DMs and 'mpim:write' scope for MPDMs.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'im:write' scope for DMs and 'mpim:write' scope for MPDMs and reinstall the app.",
                "successful": False
            }
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

# SLACK_CREATE_A_REMINDER
@mcp.tool()
async def slack_create_a_reminder(
    text: str,
    time: str,
    user: str = ""
) -> dict:
    """
    Create a reminder.
    
    Creates a slack reminder with specified text and time; time accepts unix timestamps, 
    seconds from now, or natural language (e.g., 'in 15 minutes', 'every thursday at 2pm').
    
    Note: This operation requires a user token (SLACK_USER_TOKEN) with reminders:write scope.
    Bot tokens cannot create reminders.
    
    Args:
        text (str): Reminder text content (required)
        time (str): When to trigger the reminder (required)
        user (str): User ID to create reminder for (optional, defaults to user token owner)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use user token for reminder operations)
        client = get_slack_user_client()
        
        # Validate required inputs
        if not text or not text.strip():
            return {
                "data": {},
                "error": "Reminder text is required",
                "successful": False
            }
        
        if not time or not time.strip():
            return {
                "data": {},
                "error": "Reminder time is required",
                "successful": False
            }
        
        # Prepare reminder parameters
        reminder_params = {
            "text": text.strip(),
            "time": time.strip()
        }
        
        # Add user parameter if provided
        if user and user.strip():
            # Validate user ID format (should start with 'U')
            if not user.startswith('U'):
                return {
                    "data": {},
                    "error": f"Invalid user ID format: '{user}'. User IDs should start with 'U'.",
                    "successful": False
                }
            reminder_params["user"] = user.strip()
        
        # Create the reminder
        response = client.reminders_add(**reminder_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe user '{user}' does not exist or is not accessible.",
                "successful": False
            }
        elif error_code == 'invalid_time':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe time '{time}' is invalid. Use unix timestamps, seconds from now, or natural language like 'in 15 minutes' or 'tomorrow at 2pm'.",
                "successful": False
            }
        elif error_code == 'time_in_past':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified time '{time}' is in the past. Please choose a future time.",
                "successful": False
            }
        elif error_code == 'too_far_in_future':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified time '{time}' is too far in the future. Slack reminders are limited to 1 year ahead.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'not_allowed_token_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis operation requires a user token (xoxp-) with reminders:write scope.\nBot tokens (xoxb-) cannot create reminders.\n\nTo fix:\n1. Set SLACK_USER_TOKEN environment variable\n2. Use a user token with reminders:write scope",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser token lacks required scopes. Ensure the user token has 'reminders:write' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser token lacks required scopes. Ensure the user token has 'reminders:write' scope and reinstall the app.",
                "successful": False
            }
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

# SLACK_CREATE_A_SLACK_USER_GROUP
@mcp.tool()
async def slack_create_a_slack_user_group(
    name: str,
    channels: str = "",
    description: str = "",
    handle: str = "",
    include_count: bool = False
) -> dict:
    """
    Create a Slack user group.
    
    Creates a new user group (often referred to as a subteam) in a slack workspace.
    
    Args:
        name (str): Name of the user group (required)
        channels (str): Comma-separated list of channel IDs to add to the user group
        description (str): Description of the user group
        handle (str): Handle for the user group (without @)
        include_count (bool): Whether to include member count in the response
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for user group operations)
        client = get_slack_client()
        
        # Validate required inputs
        if not name or not name.strip():
            return {
                "data": {},
                "error": "User group name is required",
                "successful": False
            }
        
        # Prepare user group parameters
        usergroup_params = {
            "name": name.strip(),
            "include_count": include_count
        }
        
        # Add optional parameters if provided
        if channels and channels.strip():
            # Parse and validate channel IDs
            channel_list = [ch.strip() for ch in channels.split(',') if ch.strip()]
            if channel_list:
                # Validate channel ID format (should start with 'C')
                for channel_id in channel_list:
                    if not channel_id.startswith('C'):
                        return {
                            "data": {},
                            "error": f"Invalid channel ID format: '{channel_id}'. Channel IDs should start with 'C'.",
                            "successful": False
                        }
                usergroup_params["channels"] = channel_list
        
        if description and description.strip():
            usergroup_params["description"] = description.strip()
        
        if handle and handle.strip():
            # Remove @ if present
            clean_handle = handle.strip()
            if clean_handle.startswith('@'):
                clean_handle = clean_handle[1:]
            usergroup_params["handle"] = clean_handle
        
        # Create the user group
        response = client.usergroups_create(**usergroup_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'name_taken':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe user group name '{name}' is already taken. Choose a different name.",
                "successful": False
            }
        elif error_code == 'handle_taken':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe handle '{handle}' is already taken. Choose a different handle.",
                "successful": False
            }
        elif error_code == 'invalid_handle':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe handle '{handle}' is invalid. Use letters, numbers, hyphens, and underscores only.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more channels in the list do not exist or you don't have access to them.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'usergroups:write' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'usergroups:write' scope and reinstall the app.",
                "successful": False
            }
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

# SLACK_CREATE_CHANNEL
@mcp.tool()
async def slack_create_channel(
    name: str,
    is_private: bool = False,
    team_id: str = ""
) -> dict:
    """
    Create channel.
    
    Initiates a public or private channel-based conversation.
    
    Args:
        name (str): Name of the channel to create (required)
        is_private (bool): Whether to create a private channel (default: False)
        team_id (str): Team ID to create the channel in (optional)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for channel operations)
        client = get_slack_client()
        
        # Validate required inputs
        if not name or not name.strip():
            return {
                "data": {},
                "error": "Channel name is required",
                "successful": False
            }
        
        # Validate channel name format
        import re
        channel_name = name.strip()
        if not re.match(r'^[a-z0-9][a-z0-9._-]*$', channel_name):
            return {
                "data": {},
                "error": "Invalid channel name format. Channel names must be lowercase, start with a letter or number, and contain only letters, numbers, periods, hyphens, and underscores.",
                "successful": False
            }
        
        # Prepare channel parameters
        channel_params = {
            "name": channel_name,
            "is_private": is_private
        }
        
        # Add team_id if provided
        if team_id and team_id.strip():
            channel_params["team_id"] = team_id.strip()
        
        # Create the channel
        response = client.conversations_create(**channel_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'name_taken':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel name '{name}' is already taken. Choose a different name.",
                "successful": False
            }
        elif error_code == 'invalid_name':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel name '{name}' is invalid. Use lowercase letters, numbers, periods, hyphens, and underscores only.",
                "successful": False
            }
        elif error_code == 'restricted_action':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nChannel creation is restricted in this workspace. Check workspace settings or contact your admin.",
                "successful": False
            }
        elif error_code == 'channel_limit_reached':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe workspace has reached its channel limit. Delete some channels before creating new ones.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'channels:write' scope for public channels or 'groups:write' scope for private channels.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'channels:write' scope for public channels or 'groups:write' scope for private channels and reinstall the app.",
                "successful": False
            }
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

# SLACK_CREATE_CHANNEL_BASED_CONVERSATION
@mcp.tool()
async def slack_create_channel_based_conversation(
    name: str,
    is_private: bool,
    description: str = "",
    org_wide: bool = False,
    team_id: str = ""
) -> dict:
    """
    Create a channel-based conversation.
    
    Creates a new public or private slack channel with a unique name; the channel can be 
    org-wide, or team-specific if `team id` is given (required if `org wide` is false or not provided).
    
    Args:
        name (str): Name of the channel to create (required)
        is_private (bool): Whether to create a private channel (required)
        description (str): Description of the channel (optional)
        org_wide (bool): Whether to create an org-wide channel (default: False)
        team_id (str): Team ID to create the channel in (required if org_wide is False)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for channel operations)
        client = get_slack_client()
        
        # Validate required inputs
        if not name or not name.strip():
            return {
                "data": {},
                "error": "Channel name is required",
                "successful": False
            }
        
        # Validate team_id requirement when org_wide is False
        if not org_wide and (not team_id or not team_id.strip()):
            return {
                "data": {},
                "error": "Team ID is required when org_wide is False",
                "successful": False
            }
        
        # Validate channel name format
        import re
        channel_name = name.strip()
        if not re.match(r'^[a-z0-9][a-z0-9._-]*$', channel_name):
            return {
                "data": {},
                "error": "Invalid channel name format. Channel names must be lowercase, start with a letter or number, and contain only letters, numbers, periods, hyphens, and underscores.",
                "successful": False
            }
        
        # Prepare channel parameters
        channel_params = {
            "name": channel_name,
            "is_private": is_private
        }
        
        # Add optional parameters if provided
        if description and description.strip():
            channel_params["description"] = description.strip()
        
        if org_wide:
            channel_params["org_wide"] = org_wide
        
        if team_id and team_id.strip():
            channel_params["team_id"] = team_id.strip()
        
        # Create the channel
        response = client.conversations_create(**channel_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'name_taken':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel name '{name}' is already taken. Choose a different name.",
                "successful": False
            }
        elif error_code == 'invalid_name':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel name '{name}' is invalid. Use lowercase letters, numbers, periods, hyphens, and underscores only.",
                "successful": False
            }
        elif error_code == 'restricted_action':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nChannel creation is restricted in this workspace. Check workspace settings or contact your admin.",
                "successful": False
            }
        elif error_code == 'channel_limit_reached':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe workspace has reached its channel limit. Delete some channels before creating new ones.",
                "successful": False
            }
        elif error_code == 'team_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe team ID '{team_id}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'channels:write' scope for public channels or 'groups:write' scope for private channels.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'channels:write' scope for public channels or 'groups:write' scope for private channels and reinstall the app.",
                "successful": False
            }
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

# SLACK_CUSTOMIZE_URL_UNFURL
@mcp.tool()
async def slack_customize_url_unfurl(
    channel: str,
    ts: str,
    unfurls: str,
    user_auth_message: str = "",
    user_auth_required: bool = False,
    user_auth_url: str = ""
) -> dict:
    """
    Customize URL unfurl.
    
    Customizes url previews (unfurling) in a specific slack message using a url-encoded json 
    in `unfurls` to define custom content or remove existing previews.
    
    Args:
        channel (str): Channel ID where the message is located (required)
        ts (str): Message timestamp to customize unfurls for (required)
        unfurls (str): URL-encoded JSON defining custom unfurl content (required)
        user_auth_message (str): Message to show when user authentication is required
        user_auth_required (bool): Whether user authentication is required
        user_auth_url (str): URL to redirect users for authentication
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for unfurl operations)
        client = get_slack_client()
        
        # Validate required inputs
        if not channel or not channel.strip():
            return {
                "data": {},
                "error": "Channel ID is required",
                "successful": False
            }
        
        if not ts or not ts.strip():
            return {
                "data": {},
                "error": "Message timestamp is required",
                "successful": False
            }
        
        if not unfurls or not unfurls.strip():
            return {
                "data": {},
                "error": "Unfurls JSON is required",
                "successful": False
            }
        
        # Validate channel ID format
        if not channel.startswith(('C', 'D', 'G')):
            return {
                "data": {},
                "error": f"Invalid channel ID format: '{channel}'. Channel IDs should start with 'C' (channels), 'D' (DMs), or 'G' (private channels).",
                "successful": False
            }
        
        # Validate and parse unfurls JSON
        try:
            import json
            import urllib.parse
            # Decode URL-encoded JSON
            decoded_unfurls = urllib.parse.unquote(unfurls)
            # Parse JSON to validate format
            unfurls_data = json.loads(decoded_unfurls)
            # Re-encode for API call
            encoded_unfurls = urllib.parse.quote(json.dumps(unfurls_data))
        except json.JSONDecodeError:
            return {
                "data": {},
                "error": "Invalid JSON format in unfurls parameter. Ensure it's valid JSON.",
                "successful": False
            }
        except Exception as e:
            return {
                "data": {},
                "error": f"Error processing unfurls parameter: {str(e)}",
                "successful": False
            }
        
        # Prepare unfurl parameters
        unfurl_params = {
            "channel": channel.strip(),
            "ts": ts.strip(),
            "unfurls": encoded_unfurls
        }
        
        # Add optional parameters if provided
        if user_auth_message and user_auth_message.strip():
            unfurl_params["user_auth_message"] = user_auth_message.strip()
        
        if user_auth_required:
            unfurl_params["user_auth_required"] = user_auth_required
        
        if user_auth_url and user_auth_url.strip():
            unfurl_params["user_auth_url"] = user_auth_url.strip()
        
        # Customize the unfurls
        response = client.chat_unfurl(**unfurl_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'message_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe message with timestamp '{ts}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'invalid_unfurls':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe unfurls JSON is invalid. Check the format and structure of your unfurl data.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'links:write' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'links:write' scope and reinstall the app.",
                "successful": False
            }
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

# SLACK_CUSTOMIZE_URL_UNFURLING_IN_MESSAGES
@mcp.tool()
async def slack_customize_url_unfurling_in_messages(
    channel: str,
    ts: str,
    unfurls: str,
    user_auth_message: str = "",
    user_auth_required: bool = False,
    user_auth_url: str = ""
) -> dict:
    """
    Customize URL unfurling in messages.
    
    Deprecated: customizes url previews (unfurling) in a specific slack message. 
    use `customize url unfurl` instead.
    
    Args:
        channel (str): Channel ID where the message is located (required)
        ts (str): Message timestamp to customize unfurls for (required)
        unfurls (str): URL-encoded JSON defining custom unfurl content (required)
        user_auth_message (str): Message to show when user authentication is required
        user_auth_required (bool): Whether user authentication is required
        user_auth_url (str): URL to redirect users for authentication
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for unfurl operations)
        client = get_slack_client()
        
        # Validate required inputs
        if not channel or not channel.strip():
            return {
                "data": {},
                "error": "Channel ID is required",
                "successful": False
            }
        
        if not ts or not ts.strip():
            return {
                "data": {},
                "error": "Message timestamp is required",
                "successful": False
            }
        
        if not unfurls or not unfurls.strip():
            return {
                "data": {},
                "error": "Unfurls JSON is required",
                "successful": False
            }
        
        # Validate channel ID format
        if not channel.startswith(('C', 'D', 'G')):
            return {
                "data": {},
                "error": f"Invalid channel ID format: '{channel}'. Channel IDs should start with 'C' (channels), 'D' (DMs), or 'G' (private channels).",
                "successful": False
            }
        
        # Validate and parse unfurls JSON
        try:
            import json
            import urllib.parse
            # Decode URL-encoded JSON
            decoded_unfurls = urllib.parse.unquote(unfurls)
            # Parse JSON to validate format
            unfurls_data = json.loads(decoded_unfurls)
            # Re-encode for API call
            encoded_unfurls = urllib.parse.quote(json.dumps(unfurls_data))
        except json.JSONDecodeError:
            return {
                "data": {},
                "error": "Invalid JSON format in unfurls parameter. Ensure it's valid JSON.",
                "successful": False
            }
        except Exception as e:
            return {
                "data": {},
                "error": f"Error processing unfurls parameter: {str(e)}",
                "successful": False
            }
        
        # Prepare unfurl parameters
        unfurl_params = {
            "channel": channel.strip(),
            "ts": ts.strip(),
            "unfurls": encoded_unfurls
        }
        
        # Add optional parameters if provided
        if user_auth_message and user_auth_message.strip():
            unfurl_params["user_auth_message"] = user_auth_message.strip()
        
        if user_auth_required:
            unfurl_params["user_auth_required"] = user_auth_required
        
        if user_auth_url and user_auth_url.strip():
            unfurl_params["user_auth_url"] = user_auth_url.strip()
        
        # Customize the unfurls (using deprecated method)
        response = client.chat_unfurl(**unfurl_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'message_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe message with timestamp '{ts}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'invalid_unfurls':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe unfurls JSON is invalid. Check the format and structure of your unfurl data.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'links:write' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'links:write' scope and reinstall the app.",
                "successful": False
            }
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

# SLACK_DELETE_A_PUBLIC_OR_PRIVATE_CHANNEL
@mcp.tool()
async def slack_delete_a_public_or_private_channel(
    channel_id: str
) -> dict:
    """
    Delete a public or private channel.
    
    Permanently and irreversibly deletes a specified public or private channel, 
    including all its messages and files, within a slack enterprise grid organization.
    
    Args:
        channel_id (str): Channel ID to delete (required)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for channel operations)
        client = get_slack_client()
        
        # Validate required inputs
        if not channel_id or not channel_id.strip():
            return {
                "data": {},
                "error": "Channel ID is required",
                "successful": False
            }
        
        # Validate channel ID format (should start with 'C' for channels)
        if not channel_id.startswith('C'):
            return {
                "data": {},
                "error": f"Invalid channel ID format: '{channel_id}'. Channel IDs should start with 'C'.",
                "successful": False
            }
        
        # Delete the channel
        response = client.admin_conversations_delete(
            channel_id=channel_id.strip()
        )
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel_id}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'not_an_enterprise':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis operation requires Slack Enterprise Grid. Regular Slack workspaces cannot delete channels via API.\n\nTo delete channels in regular workspaces:\n1. Go to the channel\n2. Click the channel name\n3. Select 'Settings' → 'Delete channel'",
                "successful": False
            }
        elif error_code == 'cant_delete_general':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe 'general' channel cannot be deleted.",
                "successful": False
            }
        elif error_code == 'restricted_action':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nChannel deletion is restricted in this workspace. Check workspace settings or contact your admin.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'admin.conversations:write' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'admin.conversations:write' scope and reinstall the app.",
                "successful": False
            }
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

# SLACK_DELETE_A_SCHEDULED_MESSAGE_IN_A_CHAT
@mcp.tool()
async def slack_delete_a_scheduled_message_in_a_chat(
    channel: str,
    scheduled_message_id: str,
    as_user: bool = False
) -> dict:
    """
    Delete scheduled chat message.
    
    Deletes a pending, unsent scheduled message from the specified slack channel, 
    identified by its `scheduled message id`.
    
    Args:
        channel (str): Channel ID where the scheduled message is located (required)
        scheduled_message_id (str): ID of the scheduled message to delete (required)
        as_user (bool): Whether to delete the message as the bot user (default: False)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for scheduled message operations)
        client = get_slack_client()
        
        # Validate required inputs
        if not channel or not channel.strip():
            return {
                "data": {},
                "error": "Channel ID is required",
                "successful": False
            }
        
        if not scheduled_message_id or not scheduled_message_id.strip():
            return {
                "data": {},
                "error": "Scheduled message ID is required",
                "successful": False
            }
        
        # Validate channel ID format
        if not channel.startswith(('C', 'D', 'G')):
            return {
                "data": {},
                "error": f"Invalid channel ID format: '{channel}'. Channel IDs should start with 'C' (channels), 'D' (DMs), or 'G' (private channels).",
                "successful": False
            }
        
        # Prepare deletion parameters
        delete_params = {
            "channel": channel.strip(),
            "scheduled_message_id": scheduled_message_id.strip()
        }
        
        # Add as_user parameter if specified
        if as_user:
            delete_params["as_user"] = as_user
        
        # Delete the scheduled message
        response = client.chat_deleteScheduledMessage(**delete_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'scheduled_message_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe scheduled message '{scheduled_message_id}' does not exist or has already been sent.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'chat:write' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'chat:write' scope and reinstall the app.",
                "successful": False
            }
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

# SLACK_DELETES_A_MESSAGE_FROM_A_CHAT
@mcp.tool()
async def slack_deletes_a_message_from_a_chat(
    channel: str,
    ts: str,
    as_user: bool = False
) -> dict:
    """
    Delete a message from a chat.
    
    Deletes a message, identified by its channel id and timestamp, from a slack channel, 
    private group, or direct message conversation; the authenticated user or bot must be the original poster.
    
    Args:
        channel (str): Channel ID where the message is located (required)
        ts (str): Message timestamp to delete (required)
        as_user (bool): Whether to delete the message as the bot user (default: False)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for message operations)
        client = get_slack_client()
        
        # Validate required inputs
        if not channel or not channel.strip():
            return {
                "data": {},
                "error": "Channel ID is required",
                "successful": False
            }
        
        if not ts or not ts.strip():
            return {
                "data": {},
                "error": "Message timestamp is required",
                "successful": False
            }
        
        # Validate channel ID format
        if not channel.startswith(('C', 'D', 'G')):
            return {
                "data": {},
                "error": f"Invalid channel ID format: '{channel}'. Channel IDs should start with 'C' (channels), 'D' (DMs), or 'G' (private channels).",
                "successful": False
            }
        
        # Prepare deletion parameters
        delete_params = {
            "channel": channel.strip(),
            "ts": ts.strip()
        }
        
        # Add as_user parameter if specified
        if as_user:
            delete_params["as_user"] = as_user
        
        # Delete the message
        response = client.chat_delete(**delete_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'message_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe message with timestamp '{ts}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'cant_delete_message':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nYou cannot delete this message. Only the original poster can delete their messages.",
                "successful": False
            }
        elif error_code == 'edit_window_closed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe message is too old to delete. Messages can only be deleted within a certain time window.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of the channel '{channel}'. Add the bot to the channel first.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'chat:write' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'chat:write' scope and reinstall the app.",
                "successful": False
            }
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

# SLACK_DELETE_USER_PROFILE_PHOTO
@mcp.tool()
async def slack_delete_user_profile_photo(
    token: str
) -> dict:
    """
    Delete user profile photo.
    
    Deletes the slack profile photo for the user identified by the token, reverting them to the default avatar; 
    this action is irreversible and succeeds even if no custom photo was set.
    
    Args:
        token (str): Slack user token for authentication (required)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Validate required inputs
        if not token or not token.strip():
            return {
                "data": {},
                "error": "Token is required",
                "successful": False
            }
        
        # Validate token format
        if not token.startswith(('xoxp-', 'xoxb-')):
            return {
                "data": {},
                "error": f"Invalid token format: '{token}'. Token should start with 'xoxp-' (user token) or 'xoxb-' (bot token).",
                "successful": False
            }
        
        # Create client with provided token
        client = WebClient(token=token.strip())
        
        # Delete the user profile photo
        response = client.users_profile_set(
            profile={
                "image_24": "",
                "image_32": "",
                "image_48": "",
                "image_72": "",
                "image_192": "",
                "image_512": "",
                "image_1024": ""
            }
        )
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your token format and validity.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe user account associated with this token is inactive.",
                "successful": False
            }
        elif error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe user associated with this token was not found.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nToken lacks required scopes. Ensure the token has 'users.profile:write' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nToken lacks required scopes. Ensure the token has 'users.profile:write' scope and reinstall the app.",
                "successful": False
            }
        elif error_code == 'not_allowed_token_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis operation requires a user token (xoxp-) with users.profile:write scope.\nBot tokens (xoxb-) cannot modify user profiles.\n\nTo fix:\n1. Use a user token (xoxp-)\n2. Ensure the token has 'users.profile:write' scope",
                "successful": False
            }
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

# SLACK_DISABLE_AN_EXISTING_SLACK_USER_GROUP
@mcp.tool()
async def slack_disable_an_existing_slack_user_group(
    usergroup: str,
    include_count: bool = False
) -> dict:
    """
    Disable a Slack user group.
    
    Disables a specified, currently enabled slack user group by its unique id, effectively archiving it 
    by setting its 'date delete' timestamp; the group is not permanently deleted and can be re-enabled.
    
    Args:
        usergroup (str): User group ID to disable (required)
        include_count (bool): Whether to include member count in the response (default: False)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for user group operations)
        client = get_slack_client()
        
        # Validate required inputs
        if not usergroup or not usergroup.strip():
            return {
                "data": {},
                "error": "User group ID is required",
                "successful": False
            }
        
        # Validate user group ID format (should start with 'S' for subteams)
        if not usergroup.startswith('S'):
            return {
                "data": {},
                "error": f"Invalid user group ID format: '{usergroup}'. User group IDs should start with 'S'.",
                "successful": False
            }
        
        # Prepare disable parameters
        disable_params = {
            "usergroup": usergroup.strip(),
            "include_count": include_count
        }
        
        # Disable the user group
        response = client.usergroups_disable(**disable_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'subteam_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe user group '{usergroup}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'usergroups:write' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'usergroups:write' scope and reinstall the app.",
                "successful": False
            }
        elif error_code == 'permission_denied':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nYou don't have permission to disable this user group. Only workspace admins or user group managers can disable user groups.",
                "successful": False
            }
        elif error_code == 'already_disabled':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe user group '{usergroup}' is already disabled.",
                "successful": False
            }
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

# SLACK_ENABLE_A_SPECIFIED_USER_GROUP
@mcp.tool()
async def slack_enable_a_specified_user_group(
    usergroup: str,
    include_count: bool = False
) -> dict:
    """
    Enable a user group.
    
    Enables a disabled user group in slack using its id, reactivating it for mentions and permissions; 
    this action only changes the enabled status and cannot create new groups or modify other properties.
    
    Args:
        usergroup (str): User group ID to enable (required)
        include_count (bool): Whether to include member count in the response (default: False)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for user group operations)
        client = get_slack_client()
        
        # Validate required inputs
        if not usergroup or not usergroup.strip():
            return {
                "data": {},
                "error": "User group ID is required",
                "successful": False
            }
        
        # Validate user group ID format (should start with 'S' for subteams)
        if not usergroup.startswith('S'):
            return {
                "data": {},
                "error": f"Invalid user group ID format: '{usergroup}'. User group IDs should start with 'S'.",
                "successful": False
            }
        
        # Prepare enable parameters
        enable_params = {
            "usergroup": usergroup.strip(),
            "include_count": include_count
        }
        
        # Enable the user group
        response = client.usergroups_enable(**enable_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'subteam_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe user group '{usergroup}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'usergroups:write' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'usergroups:write' scope and reinstall the app.",
                "successful": False
            }
        elif error_code == 'permission_denied':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nYou don't have permission to enable this user group. Only workspace admins or user group managers can enable user groups.",
                "successful": False
            }
        elif error_code == 'already_enabled':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe user group '{usergroup}' is already enabled.",
                "successful": False
            }
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

# SLACK_END_A_CALL_WITH_DURATION_AND_ID
@mcp.tool()
async def slack_end_a_call_with_duration_and_id(
    id: str,
    duration: int = None
) -> dict:
    """
    End a call.
    
    Ends an ongoing slack call, identified by its id (obtained from `calls.add`), 
    optionally specifying the call's duration.
    
    Args:
        id (str): Call ID to end (required)
        duration (int): Call duration in seconds (optional)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for call operations)
        client = get_slack_client()
        
        # Validate required inputs
        if not id or not id.strip():
            return {
                "data": {},
                "error": "Call ID is required",
                "successful": False
            }
        
        # Validate duration if provided
        if duration is not None and duration < 0:
            return {
                "data": {},
                "error": "Duration must be a positive number (seconds)",
                "successful": False
            }
        
        # Prepare end call parameters
        end_params = {
            "id": id.strip()
        }
        
        # Add duration if provided
        if duration is not None:
            end_params["duration"] = duration
        
        # End the call
        response = client.calls_end(**end_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'call_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe call with ID '{id}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'call_already_ended':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe call with ID '{id}' has already ended.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'calls:write' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'calls:write' scope and reinstall the app.",
                "successful": False
            }
        elif error_code == 'permission_denied':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nYou don't have permission to end this call. Only call participants or workspace admins can end calls.",
                "successful": False
            }
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

# SLACK_END_SNOOZE
@mcp.tool()
async def slack_end_snooze() -> dict:
    """
    End snooze.
    
    Ends the current user's snooze mode immediately.
    
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use user token for DND operations)
        try:
            client = get_slack_user_client()
        except ValueError as e:
            return {
                "data": {},
                "error": f"Configuration Error: {str(e)}\n\nTo fix this:\n1. Set SLACK_USER_TOKEN environment variable\n2. Use a user token (xoxp-) with dnd:write scope\n3. Bot tokens (xoxb-) cannot control DND settings",
                "successful": False
            }
        
        # End the snooze
        response = client.dnd_endSnooze()
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'not_allowed_token_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis operation requires a user token (xoxp-) with dnd:write scope.\nBot tokens (xoxb-) cannot control DND settings.\n\nTo fix:\n1. Set SLACK_USER_TOKEN environment variable\n2. Use a user token with dnd:write scope",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser token lacks required scopes. Ensure the user token has 'dnd:write' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser token lacks required scopes. Ensure the user token has 'dnd:write' scope and reinstall the app.",
                "successful": False
            }
        elif error_code == 'not_snoozing':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe user is not currently in snooze mode.",
                "successful": False
            }
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

# SLACK_END_USER_DO_NOT_DISTURB_SESSION
@mcp.tool()
async def slack_end_user_do_not_disturb_session() -> dict:
    """
    End DND session.
    
    Ends the authenticated user's current do not disturb (dnd) session in slack, affecting only dnd status 
    and making them available; if dnd is not active, slack acknowledges the request without changing status.
    
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use user token for DND operations)
        try:
            client = get_slack_user_client()
        except ValueError as e:
            return {
                "data": {},
                "error": f"Configuration Error: {str(e)}\n\nTo fix this:\n1. Set SLACK_USER_TOKEN environment variable\n2. Use a user token (xoxp-) with dnd:write scope\n3. Bot tokens (xoxb-) cannot control DND settings",
                "successful": False
            }
        
        # End the DND session
        response = client.dnd_endDnd()
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'not_allowed_token_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis operation requires a user token (xoxp-) with dnd:write scope.\nBot tokens (xoxb-) cannot control DND settings.\n\nTo fix:\n1. Set SLACK_USER_TOKEN environment variable\n2. Use a user token with dnd:write scope",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser token lacks required scopes. Ensure the user token has 'dnd:write' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser token lacks required scopes. Ensure the user token has 'dnd:write' scope and reinstall the app.",
                "successful": False
            }
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

# SLACK_END_USER_SNOOZE_MODE_IMMEDIATELY
@mcp.tool()
async def slack_end_user_snooze_mode_immediately() -> dict:
    """
    End snooze mode immediately.
    
    Deprecated: ends the current user's snooze mode immediately. use `end snooze` instead.
    
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use user token for DND operations)
        try:
            client = get_slack_user_client()
        except ValueError as e:
            return {
                "data": {},
                "error": f"Configuration Error: {str(e)}\n\nTo fix this:\n1. Set SLACK_USER_TOKEN environment variable\n2. Use a user token (xoxp-) with dnd:write scope\n3. Bot tokens (xoxb-) cannot control DND settings",
                "successful": False
            }
        
        # End the snooze mode
        response = client.dnd_endSnooze()
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'not_allowed_token_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis operation requires a user token (xoxp-) with dnd:write scope.\nBot tokens (xoxb-) cannot control DND settings.\n\nTo fix:\n1. Set SLACK_USER_TOKEN environment variable\n2. Use a user token with dnd:write scope",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser token lacks required scopes. Ensure the user token has 'dnd:write' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser token lacks required scopes. Ensure the user token has 'dnd:write' scope and reinstall the app.",
                "successful": False
            }
        elif error_code == 'not_snoozing':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe user is not currently in snooze mode.",
                "successful": False
            }
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

# SLACK_FETCH_BOT_USER_INFORMATION
@mcp.tool()
async def slack_fetch_bot_user_information(
    bot: str
) -> dict:
    """
    Fetch bot user information.
    
    Fetches information for a specified, existing slack bot user; will not work for regular user accounts or other integration types.
    
    Args:
        bot (str): Bot user ID to fetch information for (required)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use bot token for bot information operations)
        client = get_slack_client()
        
        # Validate required inputs
        if not bot or not bot.strip():
            return {
                "data": {},
                "error": "Bot user ID is required",
                "successful": False
            }
        
        # Validate bot user ID format (should start with 'U' for users)
        if not bot.startswith('U'):
            return {
                "data": {},
                "error": f"Invalid bot user ID format: '{bot}'. Bot user IDs should start with 'U'.",
                "successful": False
            }
        
        # Fetch bot user information
        response = client.users_info(user=bot.strip())
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot user '{bot}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'user_not_visible':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot user '{bot}' is not visible to you or is not a bot user.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'users:read' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'users:read' scope and reinstall the app.",
                "successful": False
            }
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

# SLACK_FETCH_CONVERSATION_HISTORY
@mcp.tool()
async def slack_fetch_conversation_history(
    channel: str,
    cursor: str = None,
    inclusive: bool = None,
    latest: str = None,
    limit: int = None,
    oldest: str = None
) -> dict:
    """
    Fetch conversation history.
    
    Fetches a chronological list of messages and events from a specified slack conversation, accessible by the authenticated user/bot, with options for pagination and time range filtering.
    
    Args:
        channel (str): Channel ID to fetch history from (required)
        cursor (str, optional): Pagination cursor for fetching next page
        inclusive (bool, optional): Include messages with latest or oldest timestamp
        latest (str, optional): End of time range of messages to include (timestamp)
        limit (int, optional): Number of messages to return (1-1000, default 100)
        oldest (str, optional): Start of time range of messages to include (timestamp)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client
        client = get_slack_client()
        
        # Validate required inputs
        if not channel or not channel.strip():
            return {
                "data": {},
                "error": "Channel ID is required",
                "successful": False
            }
        
        # Validate channel ID format
        if not (channel.startswith('C') or channel.startswith('G') or channel.startswith('D')):
            return {
                "data": {},
                "error": f"Invalid channel ID format: '{channel}'. Channel IDs should start with 'C' (public), 'G' (private), or 'D' (DM).",
                "successful": False
            }
        
        # Validate limit if provided
        if limit is not None and (limit < 1 or limit > 1000):
            return {
                "data": {},
                "error": f"Invalid limit: {limit}. Limit must be between 1 and 1000.",
                "successful": False
            }
        
        # Build parameters for the API call
        history_params = {"channel": channel.strip()}
        
        # Add optional parameters if provided
        if cursor is not None:
            history_params["cursor"] = cursor.strip()
        if inclusive is not None:
            history_params["inclusive"] = inclusive
        if latest is not None:
            history_params["latest"] = latest.strip()
        if limit is not None:
            history_params["limit"] = limit
        if oldest is not None:
            history_params["oldest"] = oldest.strip()
        
        # Fetch conversation history
        response = client.conversations_history(**history_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nYou are not a member of the channel '{channel}'.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'channels:history', 'groups:history', or 'im:history' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'channels:history', 'groups:history', or 'im:history' scope and reinstall the app.",
                "successful": False
            }
        elif error_code == 'invalid_cursor':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid pagination cursor. Use a valid cursor from a previous response.",
                "successful": False
            }
        elif error_code == 'invalid_ts':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid timestamp format for 'latest' or 'oldest' parameter.",
                "successful": False
            }
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

# SLACK_FETCH_CURRENT_TEAM_INFO_WITH_OPTIONAL_TEAM_SCOPE
@mcp.tool()
async def slack_fetch_current_team_info_with_optional_team_scope(
    team: str = None
) -> dict:
    """
    Fetch team information.
    
    Deprecated: fetches comprehensive metadata about the current slack team. use `fetch team info` instead.
    
    Args:
        team (str, optional): Team ID to fetch information for (optional)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client
        client = get_slack_client()
        
        # Build parameters for the API call
        team_params = {}
        if team is not None and team.strip():
            team_params["team"] = team.strip()
        
        # Fetch team information
        response = client.team_info(**team_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'team_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe team '{team}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'team:read' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'team:read' scope and reinstall the app.",
                "successful": False
            }
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

# SLACK_FETCH_DND_STATUS_FOR_MULTIPLE_TEAM_MEMBERS
@mcp.tool()
async def slack_fetch_dnd_status_for_multiple_team_members(
    users: str
) -> dict:
    """
    Get Do Not Disturb status for users.
    
    Deprecated: retrieves a user's current do not disturb status. use `get team dnd status` instead.
    
    Args:
        users (str): Comma-separated list of user IDs to check DND status for (required)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client (use user token for DND operations)
        try:
            client = get_slack_user_client()
        except ValueError as e:
            return {
                "data": {},
                "error": f"Configuration Error: {str(e)}\n\nTo fix this:\n1. Set SLACK_USER_TOKEN environment variable\n2. Use a user token (xoxp-) with dnd:read scope\n3. Bot tokens (xoxb-) cannot read DND status",
                "successful": False
            }
        
        # Validate required inputs
        if not users or not users.strip():
            return {
                "data": {},
                "error": "Users list is required",
                "successful": False
            }
        
        # Parse and validate user IDs
        user_list = [user.strip() for user in users.split(',') if user.strip()]
        if not user_list:
            return {
                "data": {},
                "error": "No valid user IDs provided",
                "successful": False
            }
        
        # Validate user ID format (should start with 'U' for users)
        for user in user_list:
            if not user.startswith('U'):
                return {
                    "data": {},
                    "error": f"Invalid user ID format: '{user}'. User IDs should start with 'U'.",
                    "successful": False
                }
        
        # Fetch DND status for users
        response = client.dnd_teamInfo(users=','.join(user_list))
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more users in the list do not exist or you don't have access to them.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'not_allowed_token_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis operation requires a user token (xoxp-) with dnd:read scope.\nBot tokens (xoxb-) cannot read DND status.\n\nTo fix:\n1. Set SLACK_USER_TOKEN environment variable\n2. Use a user token with dnd:read scope",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser token lacks required scopes. Ensure the user token has 'dnd:read' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser token lacks required scopes. Ensure the user token has 'dnd:read' scope and reinstall the app.",
                "successful": False
            }
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

# SLACK_FETCH_ITEM_REACTIONS
@mcp.tool()
async def slack_fetch_item_reactions(
    channel: str = None,
    file: str = None,
    file_comment: str = None,
    full: bool = None,
    timestamp: str = None
) -> dict:
    """
    Fetch item reactions.
    
    Fetches reactions for a slack message, file, or file comment, requiring one of: channel and timestamp; file id; or file comment id.
    
    Args:
        channel (str, optional): Channel ID for message reactions (required with timestamp)
        file (str, optional): File ID for file reactions
        file_comment (str, optional): File comment ID for file comment reactions
        full (bool, optional): Include full reaction objects with user information
        timestamp (str, optional): Message timestamp for message reactions (required with channel)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": [],
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client
        client = get_slack_client()
        
        # Validate that at least one required parameter set is provided
        has_message_params = channel and timestamp
        has_file_param = file
        has_file_comment_param = file_comment
        
        if not (has_message_params or has_file_param or has_file_comment_param):
            return {
                "data": [],
                "error": "At least one of the following is required:\n1. channel + timestamp (for message reactions)\n2. file (for file reactions)\n3. file_comment (for file comment reactions)",
                "successful": False
            }
        
        # Validate message parameters if provided
        if has_message_params:
            if not channel.strip():
                return {
                    "data": [],
                    "error": "Channel ID is required when using timestamp",
                    "successful": False
                }
            if not timestamp.strip():
                return {
                    "data": [],
                    "error": "Timestamp is required when using channel",
                    "successful": False
                }
            # Validate channel ID format
            if not (channel.startswith('C') or channel.startswith('G') or channel.startswith('D')):
                return {
                    "data": [],
                    "error": f"Invalid channel ID format: '{channel}'. Channel IDs should start with 'C' (public), 'G' (private), or 'D' (DM).",
                    "successful": False
                }
        
        # Build parameters for the API call
        reaction_params = {}
        
        # Add required parameters based on what's provided
        if has_message_params:
            reaction_params["channel"] = channel.strip()
            reaction_params["timestamp"] = timestamp.strip()
        elif has_file_param:
            reaction_params["file"] = file.strip()
        elif has_file_comment_param:
            reaction_params["file_comment"] = file_comment.strip()
        
        # Add optional parameters if provided
        if full is not None:
            reaction_params["full"] = full
        
        # Fetch reactions
        response = client.reactions_get(**reaction_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data.get("message", {}).get("reactions", []) if has_message_params else response.data.get("file", {}).get("reactions", []) if has_file_param else response.data.get("comment", {}).get("reactions", []),
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": [],
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'message_not_found':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nThe message with timestamp '{timestamp}' in channel '{channel}' was not found.",
                "successful": False
            }
        elif error_code == 'file_not_found':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nThe file '{file}' was not found or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'comment_not_found':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nThe file comment '{file_comment}' was not found or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nYou are not a member of the channel '{channel}'.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'reactions:read' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'reactions:read' scope and reinstall the app.",
                "successful": False
            }
        return {
            "data": [],
            "error": f"Slack API Error: {error_code}",
            "successful": False
        }
    except Exception as e:
        return {
            "data": [],
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }

# SLACK_FETCH_MESSAGE_THREAD_FROM_A_CONVERSATION
@mcp.tool()
async def slack_fetch_message_thread_from_a_conversation(
    channel: str,
    ts: str,
    cursor: str = None,
    inclusive: bool = None,
    latest: str = None,
    limit: int = None,
    oldest: str = None
) -> dict:
    """
    Retrieve conversation replies.
    
    Retrieves replies to a specific parent message in a slack conversation, using the channel id and the parent message's timestamp (`ts`).
    
    Args:
        channel (str): Channel ID to fetch thread from (required)
        ts (str): Parent message timestamp (required)
        cursor (str, optional): Pagination cursor for fetching next page
        inclusive (bool, optional): Include messages with latest or oldest timestamp
        latest (str, optional): End of time range of messages to include (timestamp)
        limit (int, optional): Number of messages to return (1-1000, default 100)
        oldest (str, optional): Start of time range of messages to include (timestamp)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client
        client = get_slack_client()
        
        # Validate required inputs
        if not channel or not channel.strip():
            return {
                "data": {},
                "error": "Channel ID is required",
                "successful": False
            }
        
        if not ts or not ts.strip():
            return {
                "data": {},
                "error": "Parent message timestamp (ts) is required",
                "successful": False
            }
        
        # Validate channel ID format
        if not (channel.startswith('C') or channel.startswith('G') or channel.startswith('D')):
            return {
                "data": {},
                "error": f"Invalid channel ID format: '{channel}'. Channel IDs should start with 'C' (public), 'G' (private), or 'D' (DM).",
                "successful": False
            }
        
        # Validate limit if provided
        if limit is not None and (limit < 1 or limit > 1000):
            return {
                "data": {},
                "error": f"Invalid limit: {limit}. Limit must be between 1 and 1000.",
                "successful": False
            }
        
        # Build parameters for the API call
        thread_params = {
            "channel": channel.strip(),
            "ts": ts.strip()
        }
        
        # Add optional parameters if provided
        if cursor is not None:
            thread_params["cursor"] = cursor.strip()
        if inclusive is not None:
            thread_params["inclusive"] = inclusive
        if latest is not None:
            thread_params["latest"] = latest.strip()
        if limit is not None:
            thread_params["limit"] = limit
        if oldest is not None:
            thread_params["oldest"] = oldest.strip()
        
        # Fetch conversation replies
        response = client.conversations_replies(**thread_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'message_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe parent message with timestamp '{ts}' was not found in channel '{channel}'.",
                "successful": False
            }
        elif error_code == 'thread_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe message '{ts}' is not a thread parent message.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nYou are not a member of the channel '{channel}'.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'channels:history', 'groups:history', or 'im:history' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'channels:history', 'groups:history', or 'im:history' scope and reinstall the app.",
                "successful": False
            }
        elif error_code == 'invalid_cursor':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid pagination cursor. Use a valid cursor from a previous response.",
                "successful": False
            }
        elif error_code == 'invalid_ts':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid timestamp format for 'ts', 'latest', or 'oldest' parameter.",
                "successful": False
            }
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

# SLACK_FETCH_TEAM_INFO
@mcp.tool()
async def slack_fetch_team_info(
    team: str = None
) -> dict:
    """
    Fetch team info.
    
    Fetches comprehensive metadata about the current slack team, or a specified team if the provided id is accessible.
    
    Args:
        team (str, optional): Team ID to fetch information for (optional)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client
        client = get_slack_client()
        
        # Build parameters for the API call
        team_params = {}
        if team is not None and team.strip():
            team_params["team"] = team.strip()
        
        # Fetch team information
        response = client.team_info(**team_params)
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'team_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe team '{team}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'team:read' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'team:read' scope and reinstall the app.",
                "successful": False
            }
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

# SLACK_FETCH_WORKSPACE_SETTINGS_INFORMATION
@mcp.tool()
async def slack_fetch_workspace_settings_information(
    team_id: str
) -> dict:
    """
    Fetch workspace settings information.
    
    Retrieves detailed settings for a specific slack workspace, primarily for administrators in an enterprise grid organization to view or audit workspace configurations.
    
    Args:
        team_id (str): Team ID to fetch workspace settings for (required)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Test network connectivity first
        import urllib.request
        try:
            urllib.request.urlopen('https://slack.com', timeout=10)
        except Exception as network_error:
            return {
                "data": {},
                "error": f"Network Error: Cannot reach Slack servers. Check your internet connection and network settings. Details: {str(network_error)}",
                "successful": False
            }
        
        # Get client
        client = get_slack_client()
        
        # Validate required inputs
        if not team_id or not team_id.strip():
            return {
                "data": {},
                "error": "Team ID is required",
                "successful": False
            }
        
        # Fetch workspace settings information
        response = client.admin_teams_settings_info(team_id=team_id.strip())
        
        # Check if successful
        if response.data.get("ok", False):
            return {
                "data": response.data,
                "error": "",
                "successful": True
            }
        else:
            return {
                "data": response.data,
                "error": response.data.get('error', 'Unknown error'),
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'team_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe team '{team_id}' does not exist or you don't have access to it.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Check your token and permissions.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'insufficient_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'admin.teams:read' scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nBot token lacks required scopes. Ensure the bot has 'admin.teams:read' scope and reinstall the app.",
                "successful": False
            }
        elif error_code == 'not_allowed_token_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis operation requires a user token (xoxp-) with admin.teams:read scope.\nBot tokens (xoxb-) cannot access admin settings.\n\nTo fix:\n1. Set SLACK_USER_TOKEN environment variable\n2. Use a user token with admin.teams:read scope",
                "successful": False
            }
        elif error_code == 'feature_not_available':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis feature is not available for your workspace type. Admin settings are only available for Enterprise Grid organizations.",
                "successful": False
            }
        elif error_code == 'not_an_admin':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nYou must be an administrator to access workspace settings information.",
                "successful": False
            }
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

# Main server function
if __name__ == "__main__":
    mcp.run()
