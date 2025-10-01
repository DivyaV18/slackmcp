#!/usr/bin/env python3
"""
Simple Slack MCP Server with SLACK_ACTIVATE_OR_MODIFY_DO_NOT_DISTURB_DURATION tool
"""

import os
import time
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
def slack_send_message(
    channel: str,
    text: Optional[str] = None,
    blocks: Optional[str] = None,
    attachments: Optional[str] = None,
    as_user: bool = False,
    icon_emoji: Optional[str] = None,
    icon_url: Optional[str] = None,
    link_names: bool = False,
    markdown_text: Optional[str] = None,
    mrkdwn: bool = True,
    parse: Optional[str] = None,
    reply_broadcast: bool = False,
    thread_ts: Optional[str] = None,
    unfurl_links: bool = True,
    unfurl_media: bool = True,
    username: Optional[str] = None
) -> dict:
    """
    Posts a message to a slack channel, direct message, or private group; requires content via `text`, `blocks`, or `attachments`.
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

@mcp.tool()
async def slack_find_channels(
    search_query: str,
    exact_match: bool = False,
    exclude_archived: bool = True,
    limit: int = 50,
    member_only: bool = False,
    types: str = "public_channel,private_channel"
) -> dict:
    """
    Find channels in a slack workspace by any criteria - name, topic, purpose, or description.
    
    Args:
        search_query (str): Search query to find channels by name, topic, purpose, or description
        exact_match (bool): Whether to match the search query exactly (default: False)
        exclude_archived (bool): Whether to exclude archived channels (default: True)
        limit (int): Maximum number of channels to return (default: 50)
        member_only (bool): Whether to only return channels the user is a member of (default: False)
        types (str): Comma-separated list of channel types to include (default: "public_channel,private_channel")
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Parse types parameter
        channel_types = [t.strip() for t in types.split(',')]
        
        # Prepare parameters for conversations.list
        params = {
            'types': ','.join(channel_types),
            'limit': min(limit, 1000),  # Slack API limit is 1000
            'exclude_archived': exclude_archived
        }
        
        # Add member filter if requested
        if member_only:
            params['exclude_members'] = False
        
        all_channels = []
        cursor = None
        
        # Fetch channels with pagination
        while len(all_channels) < limit:
            if cursor:
                params['cursor'] = cursor
            
            response = client.conversations_list(**params)
            
            if not response.data.get("ok", False):
                return {
                    "data": {},
                    "error": f"Failed to fetch channels: {response.data.get('error', 'Unknown error')}",
                    "successful": False
                }
            
            channels = response.data.get("channels", [])
            if not channels:
                break
                
            all_channels.extend(channels)
            
            # Check if there are more pages
            cursor = response.data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        
        # Filter channels based on search query
        filtered_channels = []
        search_lower = search_query.lower()
        
        for channel in all_channels:
            # Get channel details for search
            channel_name = channel.get("name", "").lower()
            channel_topic = channel.get("topic", {}).get("value", "").lower()
            channel_purpose = channel.get("purpose", {}).get("value", "").lower()
            
            # Create searchable text
            searchable_text = f"{channel_name} {channel_topic} {channel_purpose}"
            
            # Apply search filter
            if exact_match:
                match_found = search_lower in [channel_name, channel_topic, channel_purpose]
            else:
                match_found = search_lower in searchable_text
            
            if match_found:
                # Add channel info
                channel_info = {
                    "id": channel.get("id"),
                    "name": channel.get("name"),
                    "is_channel": channel.get("is_channel", False),
                    "is_group": channel.get("is_group", False),
                    "is_im": channel.get("is_im", False),
                    "is_mpim": channel.get("is_mpim", False),
                    "is_private": channel.get("is_private", False),
                    "is_archived": channel.get("is_archived", False),
                    "is_general": channel.get("is_general", False),
                    "created": channel.get("created"),
                    "creator": channel.get("creator"),
                    "num_members": channel.get("num_members"),
                    "topic": {
                        "value": channel.get("topic", {}).get("value", ""),
                        "creator": channel.get("topic", {}).get("creator", ""),
                        "last_set": channel.get("topic", {}).get("last_set", 0)
                    },
                    "purpose": {
                        "value": channel.get("purpose", {}).get("value", ""),
                        "creator": channel.get("purpose", {}).get("creator", ""),
                        "last_set": channel.get("purpose", {}).get("last_set", 0)
                    }
                }
                
                filtered_channels.append(channel_info)
                
                # Stop if we've reached the limit
                if len(filtered_channels) >= limit:
                    break
        
        return {
            "data": {
                "channels": filtered_channels,
                "total_found": len(filtered_channels),
                "search_query": search_query,
                "exact_match": exact_match,
                "exclude_archived": exclude_archived,
                "member_only": member_only,
                "types": types
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to access channels. The bot needs channels:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:read scope to list channels.",
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

@mcp.tool()
async def slack_lookup_users_by_email(
    email: str
) -> dict:
    """
    Retrieves the slack user object for an active user by their registered email address; 
    fails with 'users not found' if the email is unregistered or the user is inactive.
    
    Args:
        email (str): Email address of the user to lookup
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the users.lookupByEmail method
        response = client.users_lookupByEmail(email=email)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'users_not_found':
                return {
                    "data": {},
                    "error": f"User not found: No active user found with email '{email}'. The email may be unregistered or the user may be inactive.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to lookup user: {error}",
                    "successful": False
                }
        
        user = response.data.get("user", {})
        
        # Format user information
        user_info = {
            "id": user.get("id"),
            "team_id": user.get("team_id"),
            "name": user.get("name"),
            "real_name": user.get("real_name"),
            "display_name": user.get("display_name"),
            "email": user.get("profile", {}).get("email"),
            "first_name": user.get("profile", {}).get("first_name"),
            "last_name": user.get("profile", {}).get("last_name"),
            "title": user.get("profile", {}).get("title"),
            "phone": user.get("profile", {}).get("phone"),
            "skype": user.get("profile", {}).get("skype"),
            "status": user.get("profile", {}).get("status_text"),
            "status_emoji": user.get("profile", {}).get("status_emoji"),
            "image_24": user.get("profile", {}).get("image_24"),
            "image_32": user.get("profile", {}).get("image_32"),
            "image_48": user.get("profile", {}).get("image_48"),
            "image_72": user.get("profile", {}).get("image_72"),
            "image_192": user.get("profile", {}).get("image_192"),
            "image_512": user.get("profile", {}).get("image_512"),
            "is_admin": user.get("is_admin", False),
            "is_owner": user.get("is_owner", False),
            "is_primary_owner": user.get("is_primary_owner", False),
            "is_restricted": user.get("is_restricted", False),
            "is_ultra_restricted": user.get("is_ultra_restricted", False),
            "is_bot": user.get("is_bot", False),
            "is_app_user": user.get("is_app_user", False),
            "is_invited_user": user.get("is_invited_user", False),
            "has_2fa": user.get("has_2fa", False),
            "two_factor_type": user.get("two_factor_type"),
            "has_files": user.get("has_files", False),
            "presence": user.get("presence"),
            "locale": user.get("locale"),
            "tz": user.get("tz"),
            "tz_label": user.get("tz_label"),
            "tz_offset": user.get("tz_offset"),
            "updated": user.get("updated"),
            "deleted": user.get("deleted", False),
            "color": user.get("color"),
            "profile": {
                "title": user.get("profile", {}).get("title", ""),
                "phone": user.get("profile", {}).get("phone", ""),
                "skype": user.get("profile", {}).get("skype", ""),
                "real_name": user.get("profile", {}).get("real_name", ""),
                "real_name_normalized": user.get("profile", {}).get("real_name_normalized", ""),
                "display_name": user.get("profile", {}).get("display_name", ""),
                "display_name_normalized": user.get("profile", {}).get("display_name_normalized", ""),
                "status_text": user.get("profile", {}).get("status_text", ""),
                "status_emoji": user.get("profile", {}).get("status_emoji", ""),
                "status_expiration": user.get("profile", {}).get("status_expiration", 0),
                "avatar_hash": user.get("profile", {}).get("avatar_hash", ""),
                "email": user.get("profile", {}).get("email", ""),
                "first_name": user.get("profile", {}).get("first_name", ""),
                "last_name": user.get("profile", {}).get("last_name", ""),
                "image_24": user.get("profile", {}).get("image_24", ""),
                "image_32": user.get("profile", {}).get("image_32", ""),
                "image_48": user.get("profile", {}).get("image_48", ""),
                "image_72": user.get("profile", {}).get("image_72", ""),
                "image_192": user.get("profile", {}).get("image_192", ""),
                "image_512": user.get("profile", {}).get("image_512", ""),
                "image_1024": user.get("profile", {}).get("image_1024", ""),
                "image_original": user.get("profile", {}).get("image_original", ""),
                "is_custom_image": user.get("profile", {}).get("is_custom_image", False)
            }
        }
        
        return {
            "data": {
                "user": user_info,
                "email": email,
                "found": True
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'users_not_found':
            return {
                "data": {},
                "error": f"User not found: No active user found with email '{email}'. The email may be unregistered or the user may be inactive.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to lookup users. The bot needs users:read.email scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs users:read.email scope to lookup users by email.",
                "successful": False
            }
        elif error_code == 'invalid_email':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid email format: '{email}'",
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

@mcp.tool()
async def slack_find_users(
    search_query: str,
    exact_match: bool = False,
    include_bots: bool = False,
    include_deleted: bool = False,
    include_restricted: bool = True,
    limit: int = 50
) -> dict:
    """
    Find users in a slack workspace by any criteria - email, name, display name, or other text. 
    Includes optimized email lookup for exact email matches.
    
    Args:
        search_query (str): Search query to find users by email, name, display name, or other text
        exact_match (bool): Whether to match the search query exactly (default: False)
        include_bots (bool): Whether to include bot users in results (default: False)
        include_deleted (bool): Whether to include deleted users in results (default: False)
        include_restricted (bool): Whether to include restricted users in results (default: True)
        limit (int): Maximum number of users to return (default: 50)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Check if search_query looks like an email for optimized lookup
        is_email_lookup = "@" in search_query and "." in search_query
        
        if is_email_lookup and exact_match:
            # Use optimized email lookup for exact email matches
            try:
                response = client.users_lookupByEmail(email=search_query)
                if response.data.get("ok", False):
                    user = response.data.get("user", {})
                    # Apply filters
                    if not include_bots and user.get("is_bot", False):
                        return {
                            "data": {
                                "users": [],
                                "total_found": 0,
                                "search_query": search_query,
                                "exact_match": exact_match,
                                "include_bots": include_bots,
                                "include_deleted": include_deleted,
                                "include_restricted": include_restricted,
                                "optimized_email_lookup": True
                            },
                            "error": "",
                            "successful": True
                        }
                    
                    if not include_deleted and user.get("deleted", False):
                        return {
                            "data": {
                                "users": [],
                                "total_found": 0,
                                "search_query": search_query,
                                "exact_match": exact_match,
                                "include_bots": include_bots,
                                "include_deleted": include_deleted,
                                "include_restricted": include_restricted,
                                "optimized_email_lookup": True
                            },
                            "error": "",
                            "successful": True
                        }
                    
                    if not include_restricted and (user.get("is_restricted", False) or user.get("is_ultra_restricted", False)):
                        return {
                            "data": {
                                "users": [],
                                "total_found": 0,
                                "search_query": search_query,
                                "exact_match": exact_match,
                                "include_bots": include_bots,
                                "include_deleted": include_deleted,
                                "include_restricted": include_restricted,
                                "optimized_email_lookup": True
                            },
                            "error": "",
                            "successful": True
                        }
                    
                    # Format user info
                    user_info = format_user_info(user)
                    
                    return {
                        "data": {
                            "users": [user_info],
                            "total_found": 1,
                            "search_query": search_query,
                            "exact_match": exact_match,
                            "include_bots": include_bots,
                            "include_deleted": include_deleted,
                            "include_restricted": include_restricted,
                            "optimized_email_lookup": True
                        },
                        "error": "",
                        "successful": True
                    }
                else:
                    # Email not found, return empty results
                    return {
                        "data": {
                            "users": [],
                            "total_found": 0,
                            "search_query": search_query,
                            "exact_match": exact_match,
                            "include_bots": include_bots,
                            "include_deleted": include_deleted,
                            "include_restricted": include_restricted,
                            "optimized_email_lookup": True
                        },
                        "error": "",
                        "successful": True
                    }
            except SlackApiError:
                # If email lookup fails, fall back to regular user search
                pass
        
        # Regular user search using users.list
        all_users = []
        cursor = None
        
        # Fetch users with pagination
        while len(all_users) < limit * 2:  # Fetch more to account for filtering
            params = {
                'limit': min(1000, limit * 2),  # Slack API limit is 1000
                'include_locale': True
            }
            
            if cursor:
                params['cursor'] = cursor
            
            response = client.users_list(**params)
            
            if not response.data.get("ok", False):
                return {
                    "data": {},
                    "error": f"Failed to fetch users: {response.data.get('error', 'Unknown error')}",
                    "successful": False
                }
            
            users = response.data.get("members", [])
            if not users:
                break
                
            all_users.extend(users)
            
            # Check if there are more pages
            cursor = response.data.get("response_metadata", {}).get("next_cursor")
            if not cursor:
                break
        
        # Filter users based on search query and criteria
        filtered_users = []
        search_lower = search_query.lower()
        
        for user in all_users:
            # Apply inclusion filters first
            if not include_bots and user.get("is_bot", False):
                continue
            if not include_deleted and user.get("deleted", False):
                continue
            if not include_restricted and (user.get("is_restricted", False) or user.get("is_ultra_restricted", False)):
                continue
            
            # Get user details for search
            user_name = user.get("name", "").lower()
            real_name = user.get("real_name", "").lower()
            display_name = user.get("profile", {}).get("display_name", "").lower()
            first_name = user.get("profile", {}).get("first_name", "").lower()
            last_name = user.get("profile", {}).get("last_name", "").lower()
            email = user.get("profile", {}).get("email", "").lower()
            title = user.get("profile", {}).get("title", "").lower()
            
            # Create searchable text
            searchable_text = f"{user_name} {real_name} {display_name} {first_name} {last_name} {email} {title}"
            
            # Apply search filter
            if exact_match:
                match_found = search_lower in [user_name, real_name, display_name, first_name, last_name, email, title]
            else:
                match_found = search_lower in searchable_text
            
            if match_found:
                # Format user info
                user_info = format_user_info(user)
                filtered_users.append(user_info)
                
                # Stop if we've reached the limit
                if len(filtered_users) >= limit:
                    break
        
        return {
            "data": {
                "users": filtered_users,
                "total_found": len(filtered_users),
                "search_query": search_query,
                "exact_match": exact_match,
                "include_bots": include_bots,
                "include_deleted": include_deleted,
                "include_restricted": include_restricted,
                "optimized_email_lookup": False
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to search users. The bot needs users:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs users:read scope to search users.",
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

def format_user_info(user: dict) -> dict:
    """Helper function to format user information consistently."""
    return {
        "id": user.get("id"),
        "team_id": user.get("team_id"),
        "name": user.get("name"),
        "real_name": user.get("real_name"),
        "display_name": user.get("display_name"),
        "email": user.get("profile", {}).get("email"),
        "first_name": user.get("profile", {}).get("first_name"),
        "last_name": user.get("profile", {}).get("last_name"),
        "title": user.get("profile", {}).get("title"),
        "phone": user.get("profile", {}).get("phone"),
        "skype": user.get("profile", {}).get("skype"),
        "status": user.get("profile", {}).get("status_text"),
        "status_emoji": user.get("profile", {}).get("status_emoji"),
        "image_24": user.get("profile", {}).get("image_24"),
        "image_32": user.get("profile", {}).get("image_32"),
        "image_48": user.get("profile", {}).get("image_48"),
        "image_72": user.get("profile", {}).get("image_72"),
        "image_192": user.get("profile", {}).get("image_192"),
        "image_512": user.get("profile", {}).get("image_512"),
        "is_admin": user.get("is_admin", False),
        "is_owner": user.get("is_owner", False),
        "is_primary_owner": user.get("is_primary_owner", False),
        "is_restricted": user.get("is_restricted", False),
        "is_ultra_restricted": user.get("is_ultra_restricted", False),
        "is_bot": user.get("is_bot", False),
        "is_app_user": user.get("is_app_user", False),
        "is_invited_user": user.get("is_invited_user", False),
        "has_2fa": user.get("has_2fa", False),
        "two_factor_type": user.get("two_factor_type"),
        "has_files": user.get("has_files", False),
        "presence": user.get("presence"),
        "locale": user.get("locale"),
        "tz": user.get("tz"),
        "tz_label": user.get("tz_label"),
        "tz_offset": user.get("tz_offset"),
        "updated": user.get("updated"),
        "deleted": user.get("deleted", False),
        "color": user.get("color")
    }

@mcp.tool()
async def slack_get_channel_conversation_preferences(
    channel_id: str
) -> dict:
    """
    Retrieves conversation preferences (e.g., who can post, who can thread) for a specified channel, 
    primarily for use within slack enterprise grid environments.
    
    Args:
        channel_id (str): The ID of the channel to get conversation preferences for
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the conversations.getPrefs method
        response = client.api_call("conversations.getPrefs", channel=channel_id)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Channel not found: No channel found with ID '{channel_id}'",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": {},
                    "error": f"Not in channel: The bot is not a member of channel '{channel_id}'",
                    "successful": False
                }
            elif error == 'invalid_channel':
                return {
                    "data": {},
                    "error": f"Invalid channel: Channel ID '{channel_id}' is not valid",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to get channel preferences: {error}",
                    "successful": False
                }
        
        prefs = response.data.get("prefs", {})
        
        # Format conversation preferences
        preferences = {
            "channel_id": channel_id,
            "who_can_post": prefs.get("who_can_post", {}),
            "who_can_thread": prefs.get("who_can_thread", {}),
            "who_can_react": prefs.get("who_can_react", {}),
            "who_can_manage_channel": prefs.get("who_can_manage_channel", {}),
            "who_can_manage_extensions": prefs.get("who_can_manage_extensions", {}),
            "who_can_manage_guests": prefs.get("who_can_manage_guests", {}),
            "who_can_manage_integrations": prefs.get("who_can_manage_integrations", {}),
            "who_can_manage_members": prefs.get("who_can_manage_members", {}),
            "who_can_manage_retention": prefs.get("who_can_manage_retention", {}),
            "who_can_manage_topics": prefs.get("who_can_manage_topics", {}),
            "who_can_manage_workflows": prefs.get("who_can_manage_workflows", {}),
            "who_can_manage_workflows_beta": prefs.get("who_can_manage_workflows_beta", {}),
            "who_can_manage_workflows_gamma": prefs.get("who_can_manage_workflows_gamma", {}),
            "who_can_manage_workflows_delta": prefs.get("who_can_manage_workflows_delta", {}),
            "who_can_manage_workflows_epsilon": prefs.get("who_can_manage_workflows_epsilon", {}),
            "who_can_manage_workflows_zeta": prefs.get("who_can_manage_workflows_zeta", {}),
            "who_can_manage_workflows_eta": prefs.get("who_can_manage_workflows_eta", {}),
            "who_can_manage_workflows_theta": prefs.get("who_can_manage_workflows_theta", {}),
            "who_can_manage_workflows_iota": prefs.get("who_can_manage_workflows_iota", {}),
            "who_can_manage_workflows_kappa": prefs.get("who_can_manage_workflows_kappa", {}),
            "who_can_manage_workflows_lambda": prefs.get("who_can_manage_workflows_lambda", {}),
            "who_can_manage_workflows_mu": prefs.get("who_can_manage_workflows_mu", {}),
            "who_can_manage_workflows_nu": prefs.get("who_can_manage_workflows_nu", {}),
            "who_can_manage_workflows_xi": prefs.get("who_can_manage_workflows_xi", {}),
            "who_can_manage_workflows_omicron": prefs.get("who_can_manage_workflows_omicron", {}),
            "who_can_manage_workflows_pi": prefs.get("who_can_manage_workflows_pi", {}),
            "who_can_manage_workflows_rho": prefs.get("who_can_manage_workflows_rho", {}),
            "who_can_manage_workflows_sigma": prefs.get("who_can_manage_workflows_sigma", {}),
            "who_can_manage_workflows_tau": prefs.get("who_can_manage_workflows_tau", {}),
            "who_can_manage_workflows_upsilon": prefs.get("who_can_manage_workflows_upsilon", {}),
            "who_can_manage_workflows_phi": prefs.get("who_can_manage_workflows_phi", {}),
            "who_can_manage_workflows_chi": prefs.get("who_can_manage_workflows_chi", {}),
            "who_can_manage_workflows_psi": prefs.get("who_can_manage_workflows_psi", {}),
            "who_can_manage_workflows_omega": prefs.get("who_can_manage_workflows_omega", {}),
            "raw_prefs": prefs
        }
        
        return {
            "data": {
                "preferences": preferences,
                "channel_id": channel_id,
                "enterprise_grid": True
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Channel not found: No channel found with ID '{channel_id}'",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Not in channel: The bot is not a member of channel '{channel_id}'",
                "successful": False
            }
        elif error_code == 'invalid_channel':
            return {
                "data": {},
                "error": f"Invalid channel: Channel ID '{channel_id}' is not valid",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to get channel preferences. The bot needs channels:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:read scope to get channel preferences.",
                "successful": False
            }
        elif error_code == 'method_not_supported_for_channel_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis method is not supported for the specified channel type. Channel preferences are primarily available for Enterprise Grid channels.",
                "successful": False
            }
        elif error_code == 'not_enterprise_grid':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis feature is only available for Enterprise Grid workspaces. Your workspace is not an Enterprise Grid organization.",
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

@mcp.tool()
async def slack_get_reminder_information(
    reminder: str
) -> dict:
    """
    Retrieves detailed information for an existing slack reminder specified by its id; 
    this is a read-only operation.
    
    Args:
        reminder (str): The ID of the reminder to get information for
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Use user token for reminder operations (reminders require user tokens)
        client = get_slack_user_client()
        
        # Use the reminders.info method
        response = client.reminders_info(reminder=reminder)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'reminder_not_found':
                return {
                    "data": {},
                    "error": f"Reminder not found: No reminder found with ID '{reminder}'",
                    "successful": False
                }
            elif error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Authentication failed: {error}\n\nPlease check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Invalid authentication: {error}\n\nPlease check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to get reminder information: {error}",
                    "successful": False
                }
        
        reminder_data = response.data.get("reminder", {})
        
        # Format reminder information
        reminder_info = {
            "id": reminder_data.get("id"),
            "creator": reminder_data.get("creator"),
            "text": reminder_data.get("text"),
            "user": reminder_data.get("user"),
            "recurring": reminder_data.get("recurring", False),
            "time": reminder_data.get("time"),
            "complete_ts": reminder_data.get("complete_ts"),
            "channel": reminder_data.get("channel"),
            "team": reminder_data.get("team"),
            "date_created": reminder_data.get("date_created"),
            "date_updated": reminder_data.get("date_updated"),
            "recurrence": reminder_data.get("recurrence", {}),
            "is_deleted": reminder_data.get("is_deleted", False),
            "is_completed": reminder_data.get("is_completed", False),
            "raw_reminder": reminder_data
        }
        
        return {
            "data": {
                "reminder": reminder_info,
                "reminder_id": reminder,
                "found": True
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'reminder_not_found':
            return {
                "data": {},
                "error": f"Reminder not found: No reminder found with ID '{reminder}'",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to get reminder information. The bot needs reminders:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs reminders:read scope to get reminder information.",
                "successful": False
            }
        elif error_code == 'invalid_reminder_id':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid reminder ID format: '{reminder}'",
                "successful": False
            }
        elif error_code == 'not_allowed_token_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis operation requires a user token (xoxp-) with reminders:read scope.\nBot tokens (xoxb-) cannot access reminder information.\n\nTo fix this:\n1. Set SLACK_USER_TOKEN environment variable\n2. Use a user token with reminders:read scope",
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

@mcp.tool()
async def slack_get_team_dnd_status(
    users: str
) -> dict:
    """
    Retrieves a user's current do not disturb status.
    
    Args:
        users (str): Comma-separated list of user IDs to get DND status for
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Parse users parameter
        user_list = [user.strip() for user in users.split(',')]
        
        # Use the dnd.teamInfo method
        response = client.dnd_teamInfo(users=','.join(user_list))
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'users_not_found':
                return {
                    "data": {},
                    "error": f"Users not found: One or more user IDs in '{users}' were not found",
                    "successful": False
                }
            elif error == 'invalid_users':
                return {
                    "data": {},
                    "error": f"Invalid users: One or more user IDs in '{users}' are invalid",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to get DND status: {error}",
                    "successful": False
                }
        
        dnd_info = response.data.get("users", {})
        
        # Format DND status information
        dnd_statuses = []
        for user_id, user_dnd in dnd_info.items():
            dnd_status = {
                "user_id": user_id,
                "dnd_enabled": user_dnd.get("dnd_enabled", False),
                "next_dnd_start_ts": user_dnd.get("next_dnd_start_ts"),
                "next_dnd_end_ts": user_dnd.get("next_dnd_end_ts"),
                "snooze_enabled": user_dnd.get("snooze_enabled", False),
                "snooze_endtime": user_dnd.get("snooze_endtime"),
                "snooze_remaining": user_dnd.get("snooze_remaining"),
                "is_snoozed": user_dnd.get("snooze_enabled", False) and user_dnd.get("snooze_endtime", 0) > 0,
                "raw_dnd_info": user_dnd
            }
            dnd_statuses.append(dnd_status)
        
        return {
            "data": {
                "dnd_statuses": dnd_statuses,
                "users_requested": user_list,
                "total_users": len(dnd_statuses),
                "timestamp": response.data.get("response_metadata", {}).get("timestamp")
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'users_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more user IDs in '{users}' were not found",
                "successful": False
            }
        elif error_code == 'invalid_users':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more user IDs in '{users}' are invalid",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to get DND status. The bot needs dnd:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs dnd:read scope to get DND status.",
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

@mcp.tool()
async def slack_get_user_presence_info(
    user: str
) -> dict:
    """
    Retrieves a slack user's current real-time presence (e.g., 'active', 'away') to determine their availability, 
    noting this action does not provide historical data or status reasons.
    
    Args:
        user (str): User ID to get presence information for
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the users.getPresence method
        response = client.users_getPresence(user=user)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'user_not_found':
                return {
                    "data": {},
                    "error": f"User not found: No user found with ID '{user}'",
                    "successful": False
                }
            elif error == 'user_not_visible':
                return {
                    "data": {},
                    "error": f"User not visible: User '{user}' is not visible to the bot (may be in a different workspace or have restricted visibility)",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to get user presence: {error}",
                    "successful": False
                }
        
        presence_data = response.data
        
        # Format presence information
        presence_info = {
            "user_id": user,
            "presence": presence_data.get("presence", "unknown"),
            "online": presence_data.get("online", False),
            "auto_away": presence_data.get("auto_away", False),
            "manual_away": presence_data.get("manual_away", False),
            "connection_count": presence_data.get("connection_count", 0),
            "last_activity": presence_data.get("last_activity"),
            "timestamp": presence_data.get("timestamp"),
            "raw_presence": presence_data
        }
        
        # Determine availability status
        availability_status = "unknown"
        if presence_info["presence"] == "active":
            availability_status = "available"
        elif presence_info["presence"] == "away":
            availability_status = "away"
        elif presence_info["auto_away"]:
            availability_status = "auto_away"
        elif presence_info["manual_away"]:
            availability_status = "manual_away"
        
        presence_info["availability_status"] = availability_status
        
        return {
            "data": {
                "presence": presence_info,
                "user_id": user,
                "found": True,
                "note": "This is real-time presence data. Historical data and status reasons are not provided."
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nNo user found with ID '{user}'",
                "successful": False
            }
        elif error_code == 'user_not_visible':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser '{user}' is not visible to the bot. The user may be in a different workspace or have restricted visibility.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to get user presence. The bot needs users:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs users:read scope to get user presence.",
                "successful": False
            }
        elif error_code == 'invalid_user':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid user ID format: '{user}'",
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

@mcp.tool()
async def slack_initiates_channel_based_conversations(
    name: str,
    is_private: bool = False,
    team_id: str = ""
) -> dict:
    """
    Deprecated: initiates a public or private channel-based conversation. 
    use `create channel` instead.
    
    Args:
        name (str): Name of the channel to create
        is_private (bool): Whether to create a private channel (default: False)
        team_id (str): Team ID for the channel (optional)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Prepare parameters for conversations.create
        params = {
            'name': name,
            'is_private': is_private
        }
        
        # Add team_id if provided
        if team_id:
            params['team_id'] = team_id
        
        # Use the conversations.create method
        response = client.conversations_create(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'name_taken':
                return {
                    "data": {},
                    "error": f"Channel name taken: A channel with the name '{name}' already exists",
                    "successful": False
                }
            elif error == 'restricted_action':
                return {
                    "data": {},
                    "error": f"Restricted action: Creating channels is restricted in this workspace",
                    "successful": False
                }
            elif error == 'invalid_name':
                return {
                    "data": {},
                    "error": f"Invalid name: Channel name '{name}' is invalid. Channel names must be lowercase, contain no spaces or special characters except hyphens and underscores.",
                    "successful": False
                }
            elif error == 'invalid_team_id':
                return {
                    "data": {},
                    "error": f"Invalid team ID: Team ID '{team_id}' is invalid",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to create channel: {error}",
                    "successful": False
                }
        
        channel = response.data.get("channel", {})
        
        # Format channel information
        channel_info = {
            "id": channel.get("id"),
            "name": channel.get("name"),
            "is_channel": channel.get("is_channel", False),
            "is_group": channel.get("is_group", False),
            "is_im": channel.get("is_im", False),
            "is_mpim": channel.get("is_mpim", False),
            "is_private": channel.get("is_private", False),
            "is_archived": channel.get("is_archived", False),
            "is_general": channel.get("is_general", False),
            "created": channel.get("created"),
            "creator": channel.get("creator"),
            "num_members": channel.get("num_members"),
            "topic": {
                "value": channel.get("topic", {}).get("value", ""),
                "creator": channel.get("topic", {}).get("creator", ""),
                "last_set": channel.get("topic", {}).get("last_set", 0)
            },
            "purpose": {
                "value": channel.get("purpose", {}).get("value", ""),
                "creator": channel.get("purpose", {}).get("creator", ""),
                "last_set": channel.get("purpose", {}).get("last_set", 0)
            }
        }
        
        return {
            "data": {
                "channel": channel_info,
                "channel_name": name,
                "is_private": is_private,
                "team_id": team_id,
                "created": True,
                "deprecation_warning": "This tool is deprecated. Please use 'create channel' instead."
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'name_taken':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nA channel with the name '{name}' already exists",
                "successful": False
            }
        elif error_code == 'restricted_action':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nCreating channels is restricted in this workspace",
                "successful": False
            }
        elif error_code == 'invalid_name':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nChannel name '{name}' is invalid. Channel names must be lowercase, contain no spaces or special characters except hyphens and underscores.",
                "successful": False
            }
        elif error_code == 'invalid_team_id':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nTeam ID '{team_id}' is invalid",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to create channels. The bot needs channels:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:write scope to create channels.",
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

@mcp.tool()
async def slack_invite_users_to_a_slack_channel(
    channel: str,
    users: str
) -> dict:
    """
    Invites users to an existing slack channel using their valid slack user ids.
    
    Args:
        channel (str): Channel ID to invite users to
        users (str): Comma-separated list of user IDs to invite
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Parse users parameter
        user_list = [user.strip() for user in users.split(',')]
        
        # Use the conversations.invite method
        response = client.conversations_invite(channel=channel, users=','.join(user_list))
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Channel not found: No channel found with ID '{channel}'",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": {},
                    "error": f"Not in channel: The bot is not a member of channel '{channel}'",
                    "successful": False
                }
            elif error == 'cant_invite_self':
                return {
                    "data": {},
                    "error": f"Cannot invite self: The bot cannot invite itself to the channel",
                    "successful": False
                }
            elif error == 'cant_invite':
                return {
                    "data": {},
                    "error": f"Cannot invite: One or more users cannot be invited to this channel (may already be members or have restricted access)",
                    "successful": False
                }
            elif error == 'invalid_user':
                return {
                    "data": {},
                    "error": f"Invalid user: One or more user IDs in '{users}' are invalid",
                    "successful": False
                }
            elif error == 'users_not_found':
                return {
                    "data": {},
                    "error": f"Users not found: One or more user IDs in '{users}' were not found",
                    "successful": False
                }
            elif error == 'already_in_channel':
                return {
                    "data": {},
                    "error": f"Already in channel: One or more users are already members of the channel",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to invite users: {error}",
                    "successful": False
                }
        
        channel_info = response.data.get("channel", {})
        
        # Format channel information
        channel_data = {
            "id": channel_info.get("id"),
            "name": channel_info.get("name"),
            "is_channel": channel_info.get("is_channel", False),
            "is_group": channel_info.get("is_group", False),
            "is_im": channel_info.get("is_im", False),
            "is_mpim": channel_info.get("is_mpim", False),
            "is_private": channel_info.get("is_private", False),
            "is_archived": channel_info.get("is_archived", False),
            "is_general": channel_info.get("is_general", False),
            "created": channel_info.get("created"),
            "creator": channel_info.get("creator"),
            "num_members": channel_info.get("num_members"),
            "topic": {
                "value": channel_info.get("topic", {}).get("value", ""),
                "creator": channel_info.get("topic", {}).get("creator", ""),
                "last_set": channel_info.get("topic", {}).get("last_set", 0)
            },
            "purpose": {
                "value": channel_info.get("purpose", {}).get("value", ""),
                "creator": channel_info.get("purpose", {}).get("creator", ""),
                "last_set": channel_info.get("purpose", {}).get("last_set", 0)
            }
        }
        
        return {
            "data": {
                "channel": channel_data,
                "users_invited": user_list,
                "total_invited": len(user_list),
                "channel_id": channel,
                "invitation_successful": True
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nNo channel found with ID '{channel}'",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of channel '{channel}'. The bot must be a member to invite others.",
                "successful": False
            }
        elif error_code == 'cant_invite_self':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot cannot invite itself to the channel.",
                "successful": False
            }
        elif error_code == 'cant_invite':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more users cannot be invited to this channel. They may already be members or have restricted access.",
                "successful": False
            }
        elif error_code == 'invalid_user':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more user IDs in '{users}' are invalid.",
                "successful": False
            }
        elif error_code == 'users_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more user IDs in '{users}' were not found.",
                "successful": False
            }
        elif error_code == 'already_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more users are already members of the channel.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to invite users. The bot needs channels:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:write scope to invite users to channels.",
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

@mcp.tool()
async def slack_invite_user_to_channel(
    channel_id: str,
    user_ids: str
) -> dict:
    """
    Invites users to a specified slack channel; this action is restricted to enterprise grid workspaces 
    and requires the authenticated user to be a member of the target channel.
    
    Args:
        channel_id (str): Channel ID to invite users to
        user_ids (str): Comma-separated list of user IDs to invite
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Parse user_ids parameter
        user_list = [user.strip() for user in user_ids.split(',')]
        
        # Use the conversations.invite method for Enterprise Grid
        response = client.conversations_invite(channel=channel_id, users=','.join(user_list))
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Channel not found: No channel found with ID '{channel_id}'",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": {},
                    "error": f"Not in channel: The authenticated user is not a member of channel '{channel_id}'. You must be a member to invite others.",
                    "successful": False
                }
            elif error == 'cant_invite_self':
                return {
                    "data": {},
                    "error": f"Cannot invite self: Cannot invite yourself to the channel",
                    "successful": False
                }
            elif error == 'cant_invite':
                return {
                    "data": {},
                    "error": f"Cannot invite: One or more users cannot be invited to this channel (may already be members or have restricted access)",
                    "successful": False
                }
            elif error == 'invalid_user':
                return {
                    "data": {},
                    "error": f"Invalid user: One or more user IDs in '{user_ids}' are invalid",
                    "successful": False
                }
            elif error == 'users_not_found':
                return {
                    "data": {},
                    "error": f"Users not found: One or more user IDs in '{user_ids}' were not found",
                    "successful": False
                }
            elif error == 'already_in_channel':
                return {
                    "data": {},
                    "error": f"Already in channel: One or more users are already members of the channel",
                    "successful": False
                }
            elif error == 'method_not_supported_for_channel_type':
                return {
                    "data": {},
                    "error": f"Method not supported: This method is not supported for the specified channel type",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to invite users: {error}",
                    "successful": False
                }
        
        channel_info = response.data.get("channel", {})
        
        # Format channel information
        channel_data = {
            "id": channel_info.get("id"),
            "name": channel_info.get("name"),
            "is_channel": channel_info.get("is_channel", False),
            "is_group": channel_info.get("is_group", False),
            "is_im": channel_info.get("is_im", False),
            "is_mpim": channel_info.get("is_mpim", False),
            "is_private": channel_info.get("is_private", False),
            "is_archived": channel_info.get("is_archived", False),
            "is_general": channel_info.get("is_general", False),
            "created": channel_info.get("created"),
            "creator": channel_info.get("creator"),
            "num_members": channel_info.get("num_members"),
            "team_id": channel_info.get("team_id"),
            "topic": {
                "value": channel_info.get("topic", {}).get("value", ""),
                "creator": channel_info.get("topic", {}).get("creator", ""),
                "last_set": channel_info.get("topic", {}).get("last_set", 0)
            },
            "purpose": {
                "value": channel_info.get("purpose", {}).get("value", ""),
                "creator": channel_info.get("purpose", {}).get("creator", ""),
                "last_set": channel_info.get("purpose", {}).get("last_set", 0)
            }
        }
        
        return {
            "data": {
                "channel": channel_data,
                "users_invited": user_list,
                "total_invited": len(user_list),
                "channel_id": channel_id,
                "enterprise_grid": True,
                "invitation_successful": True
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nNo channel found with ID '{channel_id}'",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authenticated user is not a member of channel '{channel_id}'. You must be a member to invite others.",
                "successful": False
            }
        elif error_code == 'cant_invite_self':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nCannot invite yourself to the channel.",
                "successful": False
            }
        elif error_code == 'cant_invite':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more users cannot be invited to this channel. They may already be members or have restricted access.",
                "successful": False
            }
        elif error_code == 'invalid_user':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more user IDs in '{user_ids}' are invalid.",
                "successful": False
            }
        elif error_code == 'users_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more user IDs in '{user_ids}' were not found.",
                "successful": False
            }
        elif error_code == 'already_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more users are already members of the channel.",
                "successful": False
            }
        elif error_code == 'method_not_supported_for_channel_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis method is not supported for the specified channel type.",
                "successful": False
            }
        elif error_code == 'not_enterprise_grid':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis feature is only available for Enterprise Grid workspaces. Your workspace is not an Enterprise Grid organization.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to invite users. The bot needs channels:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:write scope to invite users to channels.",
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

@mcp.tool()
async def slack_invite_user_to_workspace(
    email: str,
    channel_ids: str,
    team_id: str,
    custom_message: str = "",
    guest_expiration_ts: str = "",
    is_restricted: bool = False,
    is_ultra_restricted: bool = False,
    real_name: str = "",
    resend: bool = False
) -> dict:
    """
    Invites a user to a slack workspace and specified channels by email; 
    use `resend=true` to re-process an existing invitation for a user not yet signed up.
    
    Args:
        email (str): Email address of the user to invite
        channel_ids (str): Comma-separated list of channel IDs to invite user to
        team_id (str): Team ID for the workspace
        custom_message (str): Custom message to include with the invitation (optional)
        guest_expiration_ts (str): Unix timestamp for guest expiration (optional)
        is_restricted (bool): Whether to create a restricted guest account (default: False)
        is_ultra_restricted (bool): Whether to create an ultra-restricted guest account (default: False)
        real_name (str): Real name of the user (optional)
        resend (bool): Whether to re-send an existing invitation (default: False)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Parse channel_ids parameter
        channel_list = [channel.strip() for channel in channel_ids.split(',')]
        
        # Prepare parameters for admin.users.invite
        params = {
            'email': email,
            'channels': ','.join(channel_list),
            'team_id': team_id,
            'resend': resend
        }
        
        # Add optional parameters if provided
        if custom_message:
            params['custom_message'] = custom_message
        if guest_expiration_ts:
            params['guest_expiration_ts'] = guest_expiration_ts
        if is_restricted:
            params['is_restricted'] = is_restricted
        if is_ultra_restricted:
            params['is_ultra_restricted'] = is_ultra_restricted
        if real_name:
            params['real_name'] = real_name
        
        # Use the admin.users.invite method
        response = client.admin_users_invite(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'invalid_email':
                return {
                    "data": {},
                    "error": f"Invalid email: Email address '{email}' is not valid",
                    "successful": False
                }
            elif error == 'already_in_team':
                return {
                    "data": {},
                    "error": f"Already in team: User with email '{email}' is already a member of the workspace",
                    "successful": False
                }
            elif error == 'already_invited':
                return {
                    "data": {},
                    "error": f"Already invited: User with email '{email}' has already been invited. Use resend=true to re-send the invitation.",
                    "successful": False
                }
            elif error == 'invalid_channels':
                return {
                    "data": {},
                    "error": f"Invalid channels: One or more channel IDs in '{channel_ids}' are invalid",
                    "successful": False
                }
            elif error == 'invalid_team_id':
                return {
                    "data": {},
                    "error": f"Invalid team ID: Team ID '{team_id}' is invalid",
                    "successful": False
                }
            elif error == 'not_an_admin':
                return {
                    "data": {},
                    "error": f"Not an admin: The authenticated user is not an administrator and cannot invite users",
                    "successful": False
                }
            elif error == 'restricted_action':
                return {
                    "data": {},
                    "error": f"Restricted action: User invitations are restricted in this workspace",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to invite user: {error}",
                    "successful": False
                }
        
        invite_data = response.data
        
        # Format invitation information
        invitation_info = {
            "email": email,
            "channels": channel_list,
            "team_id": team_id,
            "custom_message": custom_message,
            "guest_expiration_ts": guest_expiration_ts,
            "is_restricted": is_restricted,
            "is_ultra_restricted": is_ultra_restricted,
            "real_name": real_name,
            "resend": resend,
            "invitation_sent": True,
            "raw_response": invite_data
        }
        
        return {
            "data": {
                "invitation": invitation_info,
                "email": email,
                "channels_invited_to": channel_list,
                "total_channels": len(channel_list),
                "team_id": team_id,
                "invitation_successful": True
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'invalid_email':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nEmail address '{email}' is not valid.",
                "successful": False
            }
        elif error_code == 'already_in_team':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser with email '{email}' is already a member of the workspace.",
                "successful": False
            }
        elif error_code == 'already_invited':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser with email '{email}' has already been invited. Use resend=true to re-send the invitation.",
                "successful": False
            }
        elif error_code == 'invalid_channels':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more channel IDs in '{channel_ids}' are invalid.",
                "successful": False
            }
        elif error_code == 'invalid_team_id':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nTeam ID '{team_id}' is invalid.",
                "successful": False
            }
        elif error_code == 'not_an_admin':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authenticated user is not an administrator and cannot invite users.",
                "successful": False
            }
        elif error_code == 'restricted_action':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser invitations are restricted in this workspace.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to invite users. The bot needs admin.users:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs admin.users:write scope to invite users to the workspace.",
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

@mcp.tool()
async def slack_invite_user_to_workspace_with_optional_channel_invites(
    email: str,
    channel_ids: str,
    team_id: str,
    custom_message: str = "",
    guest_expiration_ts: str = "",
    is_restricted: bool = False,
    is_ultra_restricted: bool = False,
    real_name: str = "",
    resend: bool = False
) -> dict:
    """
    Deprecated: invites a user to a slack workspace and specified channels by email. 
    use `invite user to workspace` instead.
    
    Args:
        email (str): Email address of the user to invite
        channel_ids (str): Comma-separated list of channel IDs to invite user to
        team_id (str): Team ID for the workspace
        custom_message (str): Custom message to include with the invitation (optional)
        guest_expiration_ts (str): Unix timestamp for guest expiration (optional)
        is_restricted (bool): Whether to create a restricted guest account (default: False)
        is_ultra_restricted (bool): Whether to create an ultra-restricted guest account (default: False)
        real_name (str): Real name of the user (optional)
        resend (bool): Whether to re-send an existing invitation (default: False)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Parse channel_ids parameter
        channel_list = [channel.strip() for channel in channel_ids.split(',')]
        
        # Prepare parameters for admin.users.invite
        params = {
            'email': email,
            'channels': ','.join(channel_list),
            'team_id': team_id,
            'resend': resend
        }
        
        # Add optional parameters if provided
        if custom_message:
            params['custom_message'] = custom_message
        if guest_expiration_ts:
            params['guest_expiration_ts'] = guest_expiration_ts
        if is_restricted:
            params['is_restricted'] = is_restricted
        if is_ultra_restricted:
            params['is_ultra_restricted'] = is_ultra_restricted
        if real_name:
            params['real_name'] = real_name
        
        # Use the admin.users.invite method
        response = client.admin_users_invite(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'invalid_email':
                return {
                    "data": {},
                    "error": f"Invalid email: Email address '{email}' is not valid",
                    "successful": False
                }
            elif error == 'already_in_team':
                return {
                    "data": {},
                    "error": f"Already in team: User with email '{email}' is already a member of the workspace",
                    "successful": False
                }
            elif error == 'already_invited':
                return {
                    "data": {},
                    "error": f"Already invited: User with email '{email}' has already been invited. Use resend=true to re-send the invitation.",
                    "successful": False
                }
            elif error == 'invalid_channels':
                return {
                    "data": {},
                    "error": f"Invalid channels: One or more channel IDs in '{channel_ids}' are invalid",
                    "successful": False
                }
            elif error == 'invalid_team_id':
                return {
                    "data": {},
                    "error": f"Invalid team ID: Team ID '{team_id}' is invalid",
                    "successful": False
                }
            elif error == 'not_an_admin':
                return {
                    "data": {},
                    "error": f"Not an admin: The authenticated user is not an administrator and cannot invite users",
                    "successful": False
                }
            elif error == 'restricted_action':
                return {
                    "data": {},
                    "error": f"Restricted action: User invitations are restricted in this workspace",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to invite user: {error}",
                    "successful": False
                }
        
        invite_data = response.data
        
        # Format invitation information
        invitation_info = {
            "email": email,
            "channels": channel_list,
            "team_id": team_id,
            "custom_message": custom_message,
            "guest_expiration_ts": guest_expiration_ts,
            "is_restricted": is_restricted,
            "is_ultra_restricted": is_ultra_restricted,
            "real_name": real_name,
            "resend": resend,
            "invitation_sent": True,
            "raw_response": invite_data
        }
        
        return {
            "data": {
                "invitation": invitation_info,
                "email": email,
                "channels_invited_to": channel_list,
                "total_channels": len(channel_list),
                "team_id": team_id,
                "invitation_successful": True,
                "deprecation_warning": "This tool is deprecated. Please use 'invite user to workspace' instead."
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'invalid_email':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nEmail address '{email}' is not valid.",
                "successful": False
            }
        elif error_code == 'already_in_team':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser with email '{email}' is already a member of the workspace.",
                "successful": False
            }
        elif error_code == 'already_invited':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser with email '{email}' has already been invited. Use resend=true to re-send the invitation.",
                "successful": False
            }
        elif error_code == 'invalid_channels':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more channel IDs in '{channel_ids}' are invalid.",
                "successful": False
            }
        elif error_code == 'invalid_team_id':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nTeam ID '{team_id}' is invalid.",
                "successful": False
            }
        elif error_code == 'not_an_admin':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authenticated user is not an administrator and cannot invite users.",
                "successful": False
            }
        elif error_code == 'restricted_action':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser invitations are restricted in this workspace.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to invite users. The bot needs admin.users:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs admin.users:write scope to invite users to the workspace.",
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

@mcp.tool()
async def slack_join_an_existing_conversation(
    channel: str
) -> dict:
    """
    Joins an existing slack conversation (public channel, private channel, or multi-person direct message) 
    by its id, if the authenticated user has permission.
    
    Args:
        channel (str): Channel ID to join
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the conversations.join method
        response = client.conversations_join(channel=channel)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Channel not found: No channel found with ID '{channel}'",
                    "successful": False
                }
            elif error == 'already_in_channel':
                return {
                    "data": {},
                    "error": f"Already in channel: The bot is already a member of channel '{channel}'",
                    "successful": False
                }
            elif error == 'cant_join_channel':
                return {
                    "data": {},
                    "error": f"Cannot join channel: The bot cannot join channel '{channel}' (may be private or restricted)",
                    "successful": False
                }
            elif error == 'is_archived':
                return {
                    "data": {},
                    "error": f"Channel archived: Channel '{channel}' is archived and cannot be joined",
                    "successful": False
                }
            elif error == 'channel_is_private':
                return {
                    "data": {},
                    "error": f"Private channel: Channel '{channel}' is private and the bot does not have permission to join",
                    "successful": False
                }
            elif error == 'method_not_supported_for_channel_type':
                return {
                    "data": {},
                    "error": f"Method not supported: This method is not supported for the specified channel type",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to join channel: {error}",
                    "successful": False
                }
        
        channel_info = response.data.get("channel", {})
        
        # Format channel information
        channel_data = {
            "id": channel_info.get("id"),
            "name": channel_info.get("name"),
            "is_channel": channel_info.get("is_channel", False),
            "is_group": channel_info.get("is_group", False),
            "is_im": channel_info.get("is_im", False),
            "is_mpim": channel_info.get("is_mpim", False),
            "is_private": channel_info.get("is_private", False),
            "is_archived": channel_info.get("is_archived", False),
            "is_general": channel_info.get("is_general", False),
            "created": channel_info.get("created"),
            "creator": channel_info.get("creator"),
            "num_members": channel_info.get("num_members"),
            "topic": {
                "value": channel_info.get("topic", {}).get("value", ""),
                "creator": channel_info.get("topic", {}).get("creator", ""),
                "last_set": channel_info.get("topic", {}).get("last_set", 0)
            },
            "purpose": {
                "value": channel_info.get("purpose", {}).get("value", ""),
                "creator": channel_info.get("purpose", {}).get("creator", ""),
                "last_set": channel_info.get("purpose", {}).get("last_set", 0)
            }
        }
        
        return {
            "data": {
                "channel": channel_data,
                "channel_id": channel,
                "joined_successfully": True,
                "membership_status": "joined"
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nNo channel found with ID '{channel}'",
                "successful": False
            }
        elif error_code == 'already_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is already a member of channel '{channel}'",
                "successful": False
            }
        elif error_code == 'cant_join_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot cannot join channel '{channel}'. The channel may be private or restricted.",
                "successful": False
            }
        elif error_code == 'is_archived':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nChannel '{channel}' is archived and cannot be joined.",
                "successful": False
            }
        elif error_code == 'channel_is_private':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nChannel '{channel}' is private and the bot does not have permission to join.",
                "successful": False
            }
        elif error_code == 'method_not_supported_for_channel_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis method is not supported for the specified channel type.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to join channels. The bot needs channels:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:write scope to join channels.",
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

@mcp.tool()
async def slack_leave_a_conversation(
    channel: str
) -> dict:
    """
    Leaves a slack conversation given its channel id; fails if leaving as the last member of a private channel 
    or if used on a slack connect channel.
    
    Args:
        channel (str): Channel ID to leave
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the conversations.leave method
        response = client.conversations_leave(channel=channel)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Channel not found: No channel found with ID '{channel}'",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": {},
                    "error": f"Not in channel: The bot is not a member of channel '{channel}'",
                    "successful": False
                }
            elif error == 'cant_leave_general':
                return {
                    "data": {},
                    "error": f"Cannot leave general: Cannot leave the #general channel",
                    "successful": False
                }
            elif error == 'last_member':
                return {
                    "data": {},
                    "error": f"Last member: Cannot leave as the last member of a private channel '{channel}'",
                    "successful": False
                }
            elif error == 'is_archived':
                return {
                    "data": {},
                    "error": f"Channel archived: Channel '{channel}' is archived and cannot be left",
                    "successful": False
                }
            elif error == 'method_not_supported_for_channel_type':
                return {
                    "data": {},
                    "error": f"Method not supported: This method is not supported for the specified channel type (may be a Slack Connect channel)",
                    "successful": False
                }
            elif error == 'slack_connect_channel':
                return {
                    "data": {},
                    "error": f"Slack Connect channel: Cannot leave Slack Connect channel '{channel}'",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to leave channel: {error}",
                    "successful": False
                }
        
        # Format response data
        leave_data = {
            "channel_id": channel,
            "left_successfully": True,
            "not_in_channel": response.data.get("not_in_channel", False)
        }
        
        return {
            "data": {
                "leave_info": leave_data,
                "channel_id": channel,
                "left_successfully": True,
                "membership_status": "left"
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nNo channel found with ID '{channel}'",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of channel '{channel}'",
                "successful": False
            }
        elif error_code == 'cant_leave_general':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nCannot leave the #general channel.",
                "successful": False
            }
        elif error_code == 'last_member':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nCannot leave as the last member of a private channel '{channel}'.",
                "successful": False
            }
        elif error_code == 'is_archived':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nChannel '{channel}' is archived and cannot be left.",
                "successful": False
            }
        elif error_code == 'method_not_supported_for_channel_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis method is not supported for the specified channel type. This may be a Slack Connect channel.",
                "successful": False
            }
        elif error_code == 'slack_connect_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nCannot leave Slack Connect channel '{channel}'.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to leave channels. The bot needs channels:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:write scope to leave channels.",
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

@mcp.tool()
async def slack_list_accessible_conversations_for_a_user(
    user: str,
    cursor: str = "",
    exclude_archived: bool = True,
    limit: int = 50,
    types: str = "public_channel,private_channel,mpim,im"
) -> dict:
    """
    Deprecated: retrieves conversations accessible to a specified user. 
    use `list conversations` instead.
    
    Args:
        user (str): User ID to get accessible conversations for
        cursor (str): Pagination cursor for fetching additional results (optional)
        exclude_archived (bool): Whether to exclude archived conversations (default: True)
        limit (int): Maximum number of conversations to return (default: 50)
        types (str): Comma-separated list of conversation types to include (default: "public_channel,private_channel,mpim,im")
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Parse types parameter
        conversation_types = [t.strip() for t in types.split(',')]
        
        # Prepare parameters for conversations.list
        params = {
            'types': ','.join(conversation_types),
            'limit': min(limit, 1000),  # Slack API limit is 1000
            'exclude_archived': exclude_archived
        }
        
        # Add cursor if provided
        if cursor:
            params['cursor'] = cursor
        
        # Use the conversations.list method
        response = client.conversations_list(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'user_not_found':
                return {
                    "data": {},
                    "error": f"User not found: No user found with ID '{user}'",
                    "successful": False
                }
            elif error == 'invalid_user':
                return {
                    "data": {},
                    "error": f"Invalid user: User ID '{user}' is invalid",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list conversations: {error}",
                    "successful": False
                }
        
        conversations = response.data.get("channels", [])
        
        # Format conversation information
        conversation_list = []
        for conv in conversations:
            conv_info = {
                "id": conv.get("id"),
                "name": conv.get("name"),
                "is_channel": conv.get("is_channel", False),
                "is_group": conv.get("is_group", False),
                "is_im": conv.get("is_im", False),
                "is_mpim": conv.get("is_mpim", False),
                "is_private": conv.get("is_private", False),
                "is_archived": conv.get("is_archived", False),
                "is_general": conv.get("is_general", False),
                "created": conv.get("created"),
                "creator": conv.get("creator"),
                "num_members": conv.get("num_members"),
                "topic": {
                    "value": conv.get("topic", {}).get("value", ""),
                    "creator": conv.get("topic", {}).get("creator", ""),
                    "last_set": conv.get("topic", {}).get("last_set", 0)
                },
                "purpose": {
                    "value": conv.get("purpose", {}).get("value", ""),
                    "creator": conv.get("purpose", {}).get("creator", ""),
                    "last_set": conv.get("purpose", {}).get("last_set", 0)
                }
            }
            conversation_list.append(conv_info)
        
        # Get pagination info
        response_metadata = response.data.get("response_metadata", {})
        next_cursor = response_metadata.get("next_cursor", "")
        
        return {
            "data": {
                "conversations": conversation_list,
                "total_found": len(conversation_list),
                "user_id": user,
                "exclude_archived": exclude_archived,
                "types": types,
                "next_cursor": next_cursor,
                "has_more": bool(next_cursor),
                "deprecation_warning": "This tool is deprecated. Please use 'list conversations' instead."
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nNo user found with ID '{user}'",
                "successful": False
            }
        elif error_code == 'invalid_user':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nUser ID '{user}' is invalid",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list conversations. The bot needs channels:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:read scope to list conversations.",
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

@mcp.tool()
async def slack_list_all_channels(
    channel_name: str = "",
    cursor: str = "",
    exclude_archived: bool = True,
    limit: int = 1,
    types: str = "public_channel,private_channel,mpim,im"
) -> dict:
    """
    Lists conversations available to the user with various filters and search options.
    
    Args:
        channel_name (str): Filter conversations by channel name (optional)
        cursor (str): Pagination cursor for fetching additional results (optional)
        exclude_archived (bool): Whether to exclude archived conversations (default: True)
        limit (int): Maximum number of conversations to return (default: 1)
        types (str): Comma-separated list of conversation types to include (default: "public_channel,private_channel,mpim,im")
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Parse types parameter
        conversation_types = [t.strip() for t in types.split(',')]
        
        # Prepare parameters for conversations.list
        params = {
            'types': ','.join(conversation_types),
            'limit': min(limit, 1000),  # Slack API limit is 1000
            'exclude_archived': exclude_archived
        }
        
        # Add cursor if provided
        if cursor:
            params['cursor'] = cursor
        
        # Use the conversations.list method
        response = client.conversations_list(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'invalid_cursor':
                return {
                    "data": {},
                    "error": f"Invalid cursor: Pagination cursor '{cursor}' is invalid",
                    "successful": False
                }
            elif error == 'invalid_types':
                return {
                    "data": {},
                    "error": f"Invalid types: One or more conversation types in '{types}' are invalid",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list conversations: {error}",
                    "successful": False
                }
        
        conversations = response.data.get("channels", [])
        
        # Filter by channel name if provided
        if channel_name:
            channel_name_lower = channel_name.lower()
            conversations = [
                conv for conv in conversations 
                if channel_name_lower in conv.get("name", "").lower()
            ]
        
        # Format conversation information
        conversation_list = []
        for conv in conversations:
            conv_info = {
                "id": conv.get("id"),
                "name": conv.get("name"),
                "is_channel": conv.get("is_channel", False),
                "is_group": conv.get("is_group", False),
                "is_im": conv.get("is_im", False),
                "is_mpim": conv.get("is_mpim", False),
                "is_private": conv.get("is_private", False),
                "is_archived": conv.get("is_archived", False),
                "is_general": conv.get("is_general", False),
                "created": conv.get("created"),
                "creator": conv.get("creator"),
                "num_members": conv.get("num_members"),
                "topic": {
                    "value": conv.get("topic", {}).get("value", ""),
                    "creator": conv.get("topic", {}).get("creator", ""),
                    "last_set": conv.get("topic", {}).get("last_set", 0)
                },
                "purpose": {
                    "value": conv.get("purpose", {}).get("value", ""),
                    "creator": conv.get("purpose", {}).get("creator", ""),
                    "last_set": conv.get("purpose", {}).get("last_set", 0)
                }
            }
            conversation_list.append(conv_info)
        
        # Get pagination info
        response_metadata = response.data.get("response_metadata", {})
        next_cursor = response_metadata.get("next_cursor", "")
        
        return {
            "data": {
                "conversations": conversation_list,
                "total_found": len(conversation_list),
                "channel_name_filter": channel_name,
                "exclude_archived": exclude_archived,
                "types": types,
                "next_cursor": next_cursor,
                "has_more": bool(next_cursor),
                "limit_requested": limit
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'invalid_cursor':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nPagination cursor '{cursor}' is invalid.",
                "successful": False
            }
        elif error_code == 'invalid_types':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more conversation types in '{types}' are invalid.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list conversations. The bot needs channels:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:read scope to list conversations.",
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

@mcp.tool()
async def slack_list_all_slack_team_channels_with_various_filters(
    channel_name: str = "",
    cursor: str = "",
    exclude_archived: bool = True,
    limit: int = 1,
    types: str = "public_channel,private_channel,mpim,im"
) -> dict:
    """
    Deprecated: lists conversations available to the user with various filters and search options. 
    use `list channels` instead.
    
    Args:
        channel_name (str): Filter conversations by channel name (optional)
        cursor (str): Pagination cursor for fetching additional results (optional)
        exclude_archived (bool): Whether to exclude archived conversations (default: True)
        limit (int): Maximum number of conversations to return (default: 1)
        types (str): Comma-separated list of conversation types to include (default: "public_channel,private_channel,mpim,im")
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Parse types parameter
        conversation_types = [t.strip() for t in types.split(',')]
        
        # Prepare parameters for conversations.list
        params = {
            'types': ','.join(conversation_types),
            'limit': min(limit, 1000),  # Slack API limit is 1000
            'exclude_archived': exclude_archived
        }
        
        # Add cursor if provided
        if cursor:
            params['cursor'] = cursor
        
        # Use the conversations.list method
        response = client.conversations_list(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'invalid_cursor':
                return {
                    "data": {},
                    "error": f"Invalid cursor: Pagination cursor '{cursor}' is invalid",
                    "successful": False
                }
            elif error == 'invalid_types':
                return {
                    "data": {},
                    "error": f"Invalid types: One or more conversation types in '{types}' are invalid",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list conversations: {error}",
                    "successful": False
                }
        
        conversations = response.data.get("channels", [])
        
        # Filter by channel name if provided
        if channel_name:
            channel_name_lower = channel_name.lower()
            conversations = [
                conv for conv in conversations 
                if channel_name_lower in conv.get("name", "").lower()
            ]
        
        # Format conversation information
        conversation_list = []
        for conv in conversations:
            conv_info = {
                "id": conv.get("id"),
                "name": conv.get("name"),
                "is_channel": conv.get("is_channel", False),
                "is_group": conv.get("is_group", False),
                "is_im": conv.get("is_im", False),
                "is_mpim": conv.get("is_mpim", False),
                "is_private": conv.get("is_private", False),
                "is_archived": conv.get("is_archived", False),
                "is_general": conv.get("is_general", False),
                "created": conv.get("created"),
                "creator": conv.get("creator"),
                "num_members": conv.get("num_members"),
                "topic": {
                    "value": conv.get("topic", {}).get("value", ""),
                    "creator": conv.get("topic", {}).get("creator", ""),
                    "last_set": conv.get("topic", {}).get("last_set", 0)
                },
                "purpose": {
                    "value": conv.get("purpose", {}).get("value", ""),
                    "creator": conv.get("purpose", {}).get("creator", ""),
                    "last_set": conv.get("purpose", {}).get("last_set", 0)
                }
            }
            conversation_list.append(conv_info)
        
        # Get pagination info
        response_metadata = response.data.get("response_metadata", {})
        next_cursor = response_metadata.get("next_cursor", "")
        
        return {
            "data": {
                "conversations": conversation_list,
                "total_found": len(conversation_list),
                "channel_name_filter": channel_name,
                "exclude_archived": exclude_archived,
                "types": types,
                "next_cursor": next_cursor,
                "has_more": bool(next_cursor),
                "limit_requested": limit,
                "deprecation_warning": "This tool is deprecated. Please use 'list channels' instead."
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'invalid_cursor':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nPagination cursor '{cursor}' is invalid.",
                "successful": False
            }
        elif error_code == 'invalid_types':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more conversation types in '{types}' are invalid.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list conversations. The bot needs channels:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:read scope to list conversations.",
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

@mcp.tool()
async def slack_list_all_slack_team_users_with_pagination(
    cursor: str = "",
    include_locale: bool = False,
    limit: int = 1
) -> dict:
    """
    Deprecated: retrieves a paginated list of all users in a slack workspace. 
    use `list all users` instead.
    
    Args:
        cursor (str): Pagination cursor for fetching additional results (optional)
        include_locale (bool): Whether to include locale information (default: False)
        limit (int): Maximum number of users to return (default: 1)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Prepare parameters for users.list
        params = {
            'limit': min(limit, 1000),  # Slack API limit is 1000
            'include_locale': include_locale
        }
        
        # Add cursor if provided
        if cursor:
            params['cursor'] = cursor
        
        # Use the users.list method
        response = client.users_list(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'invalid_cursor':
                return {
                    "data": {},
                    "error": f"Invalid cursor: Pagination cursor '{cursor}' is invalid",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list users: {error}",
                    "successful": False
                }
        
        users = response.data.get("members", [])
        
        # Format user information
        user_list = []
        for user in users:
            user_info = {
                "id": user.get("id"),
                "team_id": user.get("team_id"),
                "name": user.get("name"),
                "real_name": user.get("real_name"),
                "display_name": user.get("display_name"),
                "email": user.get("profile", {}).get("email"),
                "first_name": user.get("profile", {}).get("first_name"),
                "last_name": user.get("profile", {}).get("last_name"),
                "title": user.get("profile", {}).get("title"),
                "phone": user.get("profile", {}).get("phone"),
                "skype": user.get("profile", {}).get("skype"),
                "status": user.get("profile", {}).get("status_text"),
                "status_emoji": user.get("profile", {}).get("status_emoji"),
                "image_24": user.get("profile", {}).get("image_24"),
                "image_32": user.get("profile", {}).get("image_32"),
                "image_48": user.get("profile", {}).get("image_48"),
                "image_72": user.get("profile", {}).get("image_72"),
                "image_192": user.get("profile", {}).get("image_192"),
                "image_512": user.get("profile", {}).get("image_512"),
                "is_admin": user.get("is_admin", False),
                "is_owner": user.get("is_owner", False),
                "is_primary_owner": user.get("is_primary_owner", False),
                "is_restricted": user.get("is_restricted", False),
                "is_ultra_restricted": user.get("is_ultra_restricted", False),
                "is_bot": user.get("is_bot", False),
                "is_app_user": user.get("is_app_user", False),
                "is_invited_user": user.get("is_invited_user", False),
                "has_2fa": user.get("has_2fa", False),
                "two_factor_type": user.get("two_factor_type"),
                "has_files": user.get("has_files", False),
                "presence": user.get("presence"),
                "locale": user.get("locale") if include_locale else None,
                "tz": user.get("tz"),
                "tz_label": user.get("tz_label"),
                "tz_offset": user.get("tz_offset"),
                "updated": user.get("updated"),
                "deleted": user.get("deleted", False),
                "color": user.get("color")
            }
            user_list.append(user_info)
        
        # Get pagination info
        response_metadata = response.data.get("response_metadata", {})
        next_cursor = response_metadata.get("next_cursor", "")
        
        return {
            "data": {
                "users": user_list,
                "total_found": len(user_list),
                "include_locale": include_locale,
                "next_cursor": next_cursor,
                "has_more": bool(next_cursor),
                "limit_requested": limit,
                "deprecation_warning": "This tool is deprecated. Please use 'list all users' instead."
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'invalid_cursor':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nPagination cursor '{cursor}' is invalid.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list users. The bot needs users:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs users:read scope to list users.",
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

@mcp.tool()
async def slack_list_all_users(
    cursor: str = "",
    include_locale: bool = False,
    limit: int = 1
) -> dict:
    """
    Retrieves a paginated list of all users, including comprehensive details, profile information, 
    status, and team memberships, in a slack workspace; data may not be real-time.
    
    Args:
        cursor (str): Pagination cursor for fetching additional results (optional)
        include_locale (bool): Whether to include locale information (default: False)
        limit (int): Maximum number of users to return (default: 1)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Prepare parameters for users.list
        params = {
            'limit': min(limit, 1000),  # Slack API limit is 1000
            'include_locale': include_locale
        }
        
        # Add cursor if provided
        if cursor:
            params['cursor'] = cursor
        
        # Use the users.list method
        response = client.users_list(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'invalid_cursor':
                return {
                    "data": {},
                    "error": f"Invalid cursor: Pagination cursor '{cursor}' is invalid",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list users: {error}",
                    "successful": False
                }
        
        users = response.data.get("members", [])
        
        # Format user information with comprehensive details
        user_list = []
        for user in users:
            user_info = {
                "id": user.get("id"),
                "team_id": user.get("team_id"),
                "name": user.get("name"),
                "real_name": user.get("real_name"),
                "display_name": user.get("display_name"),
                "email": user.get("profile", {}).get("email"),
                "first_name": user.get("profile", {}).get("first_name"),
                "last_name": user.get("profile", {}).get("last_name"),
                "title": user.get("profile", {}).get("title"),
                "phone": user.get("profile", {}).get("phone"),
                "skype": user.get("profile", {}).get("skype"),
                "status": user.get("profile", {}).get("status_text"),
                "status_emoji": user.get("profile", {}).get("status_emoji"),
                "status_expiration": user.get("profile", {}).get("status_expiration"),
                "image_24": user.get("profile", {}).get("image_24"),
                "image_32": user.get("profile", {}).get("image_32"),
                "image_48": user.get("profile", {}).get("image_48"),
                "image_72": user.get("profile", {}).get("image_72"),
                "image_192": user.get("profile", {}).get("image_192"),
                "image_512": user.get("profile", {}).get("image_512"),
                "image_1024": user.get("profile", {}).get("image_1024"),
                "image_original": user.get("profile", {}).get("image_original"),
                "is_custom_image": user.get("profile", {}).get("is_custom_image"),
                "avatar_hash": user.get("profile", {}).get("avatar_hash"),
                "is_admin": user.get("is_admin", False),
                "is_owner": user.get("is_owner", False),
                "is_primary_owner": user.get("is_primary_owner", False),
                "is_restricted": user.get("is_restricted", False),
                "is_ultra_restricted": user.get("is_ultra_restricted", False),
                "is_bot": user.get("is_bot", False),
                "is_app_user": user.get("is_app_user", False),
                "is_invited_user": user.get("is_invited_user", False),
                "has_2fa": user.get("has_2fa", False),
                "two_factor_type": user.get("two_factor_type"),
                "has_files": user.get("has_files", False),
                "presence": user.get("presence"),
                "locale": user.get("locale") if include_locale else None,
                "tz": user.get("tz"),
                "tz_label": user.get("tz_label"),
                "tz_offset": user.get("tz_offset"),
                "updated": user.get("updated"),
                "deleted": user.get("deleted", False),
                "color": user.get("color"),
                "real_name_normalized": user.get("profile", {}).get("real_name_normalized"),
                "display_name_normalized": user.get("profile", {}).get("display_name_normalized"),
                "fields": user.get("profile", {}).get("fields", {}),
                "always_active": user.get("always_active", False),
                "enterprise_user": user.get("enterprise_user", {}),
                "is_email_confirmed": user.get("is_email_confirmed", False),
                "who_can_share_contact_card": user.get("who_can_share_contact_card")
            }
            user_list.append(user_info)
        
        # Get pagination info
        response_metadata = response.data.get("response_metadata", {})
        next_cursor = response_metadata.get("next_cursor", "")
        
        return {
            "data": {
                "users": user_list,
                "total_found": len(user_list),
                "include_locale": include_locale,
                "next_cursor": next_cursor,
                "has_more": bool(next_cursor),
                "limit_requested": limit,
                "data_freshness": "Data may not be real-time"
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'invalid_cursor':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nPagination cursor '{cursor}' is invalid.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list users. The bot needs users:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs users:read scope to list users.",
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

@mcp.tool()
async def slack_list_all_users_in_a_user_group(
    usergroup: str,
    include_disabled: bool = False
) -> dict:
    """
    Retrieves a list of all user ids within a specified slack user group, with an option to include users from disabled groups.
    
    Args:
        usergroup (str): The ID of the user group to list users from (required)
        include_disabled (bool): Whether to include users from disabled groups (default: False)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Prepare parameters for usergroups.users.list
        params = {
            'usergroup': usergroup,
            'include_disabled': include_disabled
        }
        
        # Use the usergroups.users.list method
        response = client.usergroups_users_list(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'usergroup_not_found':
                return {
                    "data": {},
                    "error": f"User group not found: The user group '{usergroup}' does not exist or is not accessible",
                    "successful": False
                }
            elif error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to list user group members. The bot needs usergroups:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs usergroups:read scope to list user group members.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list user group members: {error}",
                    "successful": False
                }
        
        # Extract user IDs from the response
        user_ids = response.data.get("users", [])
        
        # Get user group information for context
        usergroup_info = response.data.get("usergroup", {})
        
        return {
            "data": {
                "usergroup_id": usergroup,
                "usergroup_name": usergroup_info.get("name", "Unknown"),
                "usergroup_handle": usergroup_info.get("handle", ""),
                "usergroup_description": usergroup_info.get("description", ""),
                "usergroup_is_active": usergroup_info.get("is_active", True),
                "usergroup_is_external": usergroup_info.get("is_external", False),
                "usergroup_created_by": usergroup_info.get("created_by", ""),
                "usergroup_updated_by": usergroup_info.get("updated_by", ""),
                "usergroup_created": usergroup_info.get("date_create", 0),
                "usergroup_updated": usergroup_info.get("date_update", 0),
                "usergroup_auto_type": usergroup_info.get("auto_type", ""),
                "usergroup_auto_value": usergroup_info.get("auto_value", ""),
                "usergroup_team_id": usergroup_info.get("team_id", ""),
                "user_ids": user_ids,
                "total_members": len(user_ids),
                "include_disabled": include_disabled,
                "membership_type": "User group members"
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'usergroup_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe user group '{usergroup}' does not exist or is not accessible.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list user group members. The bot needs usergroups:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs usergroups:read scope to list user group members.",
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

@mcp.tool()
async def slack_list_conversations(
    user: str = "",
    cursor: str = "",
    exclude_archived: bool = True,
    limit: int = 50,
    types: str = "public_channel,private_channel,mpim,im"
) -> dict:
    """
    List conversations (channels/dms) accessible to a specified user (or the authenticated user if no user id is provided), 
    respecting shared membership for non-public channels.
    
    Args:
        user (str): User ID to list conversations for (optional, defaults to authenticated user)
        cursor (str): Pagination cursor for fetching additional results (optional)
        exclude_archived (bool): Whether to exclude archived conversations (default: True)
        limit (int): Maximum number of conversations to return (default: 50)
        types (str): Comma-separated list of conversation types (default: "public_channel,private_channel,mpim,im")
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Prepare parameters for conversations.list
        params = {
            'exclude_archived': exclude_archived,
            'limit': min(limit, 1000),  # Slack API limit is 1000
            'types': types
        }
        
        # Add cursor if provided
        if cursor:
            params['cursor'] = cursor
        
        # Add user if provided
        if user:
            params['user'] = user
        
        # Use the conversations.list method
        response = client.conversations_list(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'invalid_cursor':
                return {
                    "data": {},
                    "error": f"Invalid cursor: Pagination cursor '{cursor}' is invalid",
                    "successful": False
                }
            elif error == 'user_not_found':
                return {
                    "data": {},
                    "error": f"User not found: The user '{user}' does not exist or is not accessible",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list conversations: {error}",
                    "successful": False
                }
        
        conversations = response.data.get("channels", [])
        
        # Format conversation information
        conversation_list = []
        for conv in conversations:
            conv_info = {
                "id": conv.get("id"),
                "name": conv.get("name"),
                "is_channel": conv.get("is_channel", False),
                "is_group": conv.get("is_group", False),
                "is_im": conv.get("is_im", False),
                "is_member": conv.get("is_member", False),
                "is_private": conv.get("is_private", False),
                "is_mpim": conv.get("is_mpim", False),
                "is_archived": conv.get("is_archived", False),
                "is_general": conv.get("is_general", False),
                "is_shared": conv.get("is_shared", False),
                "is_org_shared": conv.get("is_org_shared", False),
                "is_pending_ext_shared": conv.get("is_pending_ext_shared", False),
                "is_ext_shared": conv.get("is_ext_shared", False),
                "is_org_default": conv.get("is_org_default", False),
                "is_org_mandatory": conv.get("is_org_mandatory", False),
                "is_moved": conv.get("is_moved", False),
                "is_open": conv.get("is_open", False),
                "created": conv.get("created", 0),
                "creator": conv.get("creator", ""),
                "is_read_only": conv.get("is_read_only", False),
                "is_thread_only": conv.get("is_thread_only", False),
                "is_starred": conv.get("is_starred", False),
                "is_pinned": conv.get("is_pinned", False),
                "is_muted": conv.get("is_muted", False),
                "topic": conv.get("topic", {}),
                "purpose": conv.get("purpose", {}),
                "num_members": conv.get("num_members", 0),
                "locale": conv.get("locale", ""),
                "unread_count": conv.get("unread_count", 0),
                "unread_count_display": conv.get("unread_count_display", 0),
                "priority": conv.get("priority", 0),
                "conversation_host_id": conv.get("conversation_host_id", ""),
                "internal_team_ids": conv.get("internal_team_ids", []),
                "pending_shared": conv.get("pending_shared", []),
                "context_team_id": conv.get("context_team_id", ""),
                "updated": conv.get("updated", 0),
                "parent_conversation": conv.get("parent_conversation", ""),
                "shared_team_ids": conv.get("shared_team_ids", []),
                "properties": conv.get("properties", {}),
                "is_workflow_bot": conv.get("is_workflow_bot", False),
                "is_global_shared": conv.get("is_global_shared", False),
                "is_org_default": conv.get("is_org_default", False),
                "is_org_mandatory": conv.get("is_org_mandatory", False),
                "is_frozen": conv.get("is_frozen", False),
                "is_connect": conv.get("is_connect", False),
                "connect_team_id": conv.get("connect_team_id", ""),
                "enterprise_id": conv.get("enterprise_id", ""),
                "channel_email_address": conv.get("channel_email_address", ""),
                "walking_liam_variant": conv.get("walking_liam_variant", ""),
                "is_deleted": conv.get("is_deleted", False),
                "is_forgotten": conv.get("is_forgotten", False),
                "is_soft_deleted": conv.get("is_soft_deleted", False),
                "is_im": conv.get("is_im", False),
                "is_user_deleted": conv.get("is_user_deleted", False),
                "priority": conv.get("priority", 0),
                "user": conv.get("user", ""),
                "name_normalized": conv.get("name_normalized", ""),
                "previous_names": conv.get("previous_names", []),
                "conversation_type": "public_channel" if conv.get("is_channel") and not conv.get("is_private") else
                                  "private_channel" if conv.get("is_channel") and conv.get("is_private") else
                                  "im" if conv.get("is_im") else
                                  "mpim" if conv.get("is_mpim") else
                                  "group" if conv.get("is_group") else "unknown"
            }
            conversation_list.append(conv_info)
        
        # Get pagination info
        response_metadata = response.data.get("response_metadata", {})
        next_cursor = response_metadata.get("next_cursor", "")
        
        return {
            "data": {
                "conversations": conversation_list,
                "total_found": len(conversation_list),
                "user_id": user if user else "authenticated_user",
                "exclude_archived": exclude_archived,
                "types_requested": types,
                "next_cursor": next_cursor,
                "has_more": bool(next_cursor),
                "limit_requested": limit
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'invalid_cursor':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nPagination cursor '{cursor}' is invalid.",
                "successful": False
            }
        elif error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe user '{user}' does not exist or is not accessible.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list conversations. The bot needs channels:read, groups:read, im:read, mpim:read scopes.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:read, groups:read, im:read, mpim:read scopes to list conversations.",
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

@mcp.tool()
async def slack_list_reminders() -> dict:
    """
    Lists all reminders with their details for the authenticated slack user; returns an empty list if no reminders exist.
    
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Use user token for reminder operations (reminders require user tokens)
        client = get_slack_user_client()
        
        # Use the reminders.list method
        response = client.reminders_list()
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_USER_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_USER_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to list reminders. The user token needs reminders:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The user token needs reminders:read scope to list reminders.",
                    "successful": False
                }
            elif error == 'not_allowed_token_type':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nReminders require a user token (xoxp-). Please set SLACK_USER_TOKEN with a user token that has reminders:read scope.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list reminders: {error}",
                    "successful": False
                }
        
        reminders = response.data.get("reminders", [])
        
        # Format reminder information
        reminder_list = []
        for reminder in reminders:
            reminder_info = {
                "id": reminder.get("id"),
                "creator": reminder.get("creator"),
                "user": reminder.get("user"),
                "text": reminder.get("text"),
                "recurring": reminder.get("recurring", False),
                "time": reminder.get("time"),
                "complete_ts": reminder.get("complete_ts"),
                "recurrence": reminder.get("recurrence", {}),
                "created": reminder.get("created", 0),
                "updated": reminder.get("updated", 0),
                "is_complete": reminder.get("complete_ts") is not None,
                "completion_time": reminder.get("complete_ts", 0),
                "reminder_time": reminder.get("time", 0),
                "reminder_text": reminder.get("text", ""),
                "is_recurring": reminder.get("recurring", False),
                "recurrence_pattern": reminder.get("recurrence", {}),
                "status": "completed" if reminder.get("complete_ts") else "pending"
            }
            reminder_list.append(reminder_info)
        
        return {
            "data": {
                "reminders": reminder_list,
                "total_found": len(reminder_list),
                "user_id": response.data.get("user", "unknown"),
                "reminder_types": {
                    "pending": len([r for r in reminder_list if not r["is_complete"]]),
                    "completed": len([r for r in reminder_list if r["is_complete"]]),
                    "recurring": len([r for r in reminder_list if r["is_recurring"]])
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list reminders. The user token needs reminders:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The user token needs reminders:read scope to list reminders.",
                "successful": False
            }
        elif error_code == 'not_allowed_token_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nReminders require a user token (xoxp-). Please set SLACK_USER_TOKEN with a user token that has reminders:read scope.",
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

@mcp.tool()
async def slack_list_remote_files(
    channel: str = "",
    cursor: str = "",
    limit: int = 100,
    ts_from: float = None,
    ts_to: float = None
) -> dict:
    """
    Retrieve information about a team's remote files.
    
    Args:
        channel (str): Channel ID to filter files by (optional)
        cursor (str): Pagination cursor for fetching additional results (optional)
        limit (int): Maximum number of files to return (default: 100)
        ts_from (float): Start timestamp for filtering files (optional)
        ts_to (float): End timestamp for filtering files (optional)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Prepare parameters for files.remote.list
        params = {
            'limit': min(limit, 1000)  # Slack API limit is 1000
        }
        
        # Add optional parameters
        if channel:
            params['channel'] = channel
        if cursor:
            params['cursor'] = cursor
        if ts_from is not None:
            params['ts_from'] = ts_from
        if ts_to is not None:
            params['ts_to'] = ts_to
        
        # Use the files.remote.list method
        response = client.files_remote_list(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'invalid_cursor':
                return {
                    "data": {},
                    "error": f"Invalid cursor: Pagination cursor '{cursor}' is invalid",
                    "successful": False
                }
            elif error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Channel not found: The channel '{channel}' does not exist or is not accessible",
                    "successful": False
                }
            elif error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to list remote files. The bot needs files:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs files:read scope to list remote files.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list remote files: {error}",
                    "successful": False
                }
        
        files = response.data.get("files", [])
        
        # Format file information
        file_list = []
        for file in files:
            file_info = {
                "id": file.get("id"),
                "name": file.get("name"),
                "title": file.get("title"),
                "mimetype": file.get("mimetype"),
                "filetype": file.get("filetype"),
                "pretty_type": file.get("pretty_type"),
                "user": file.get("user"),
                "user_team": file.get("user_team"),
                "editable": file.get("editable", False),
                "size": file.get("size", 0),
                "mode": file.get("mode"),
                "is_external": file.get("is_external", False),
                "external_type": file.get("external_type"),
                "is_public": file.get("is_public", False),
                "public_url_shared": file.get("public_url_shared", False),
                "display_as_bot": file.get("display_as_bot", False),
                "username": file.get("username"),
                "created": file.get("created", 0),
                "updated": file.get("updated", 0),
                "timestamp": file.get("timestamp", 0),
                "original_attachment_count": file.get("original_attachment_count", 0),
                "is_starred": file.get("is_starred", False),
                "has_rich_preview": file.get("has_rich_preview", False),
                "shares": file.get("shares", {}),
                "channels": file.get("channels", []),
                "groups": file.get("groups", []),
                "ims": file.get("ims", []),
                "external_id": file.get("external_id"),
                "external_url": file.get("external_url"),
                "app_id": file.get("app_id"),
                "app_name": file.get("app_name"),
                "thumb_360": file.get("thumb_360"),
                "thumb_360_w": file.get("thumb_360_w"),
                "thumb_360_h": file.get("thumb_360_h"),
                "thumb_480": file.get("thumb_480"),
                "thumb_480_w": file.get("thumb_480_w"),
                "thumb_480_h": file.get("thumb_480_h"),
                "thumb_160": file.get("thumb_160"),
                "thumb_720": file.get("thumb_720"),
                "thumb_720_w": file.get("thumb_720_w"),
                "thumb_720_h": file.get("thumb_720_h"),
                "thumb_800": file.get("thumb_800"),
                "thumb_800_w": file.get("thumb_800_w"),
                "thumb_800_h": file.get("thumb_800_h"),
                "thumb_960": file.get("thumb_960"),
                "thumb_960_w": file.get("thumb_960_w"),
                "thumb_960_h": file.get("thumb_960_h"),
                "thumb_1024": file.get("thumb_1024"),
                "thumb_1024_w": file.get("thumb_1024_w"),
                "thumb_1024_h": file.get("thumb_1024_h"),
                "image_exif_rotation": file.get("image_exif_rotation"),
                "original_w": file.get("original_w"),
                "original_h": file.get("original_h"),
                "permalink": file.get("permalink"),
                "permalink_public": file.get("permalink_public"),
                "is_removed": file.get("is_removed", False),
                "url_private": file.get("url_private"),
                "url_private_download": file.get("url_private_download"),
                "media_display_type": file.get("media_display_type"),
                "preview": file.get("preview"),
                "preview_highlight": file.get("preview_highlight"),
                "lines": file.get("lines"),
                "lines_more": file.get("lines_more"),
                "num_stars": file.get("num_stars", 0),
                "is_public": file.get("is_public", False),
                "public_url_shared": file.get("public_url_shared", False),
                "file_access": file.get("file_access"),
                "filetype_detection": file.get("filetype_detection"),
                "thumb_video": file.get("thumb_video"),
                "thumb_video_w": file.get("thumb_video_w"),
                "thumb_video_h": file.get("thumb_video_h"),
                "duration_ms": file.get("duration_ms"),
                "thumb_tiny": file.get("thumb_tiny"),
                "hd": file.get("hd", False),
                "subtype": file.get("subtype"),
                "transcription": file.get("transcription", {}),
                "mp4": file.get("mp4"),
                "vtt": file.get("vtt"),
                "hls": file.get("hls"),
                "hls_embed": file.get("hls_embed"),
                "dash": file.get("dash"),
                "dash_embed": file.get("dash_embed"),
                "is_animated": file.get("is_animated", False),
                "is_removed": file.get("is_removed", False),
                "deanimate_gif": file.get("deanimate_gif"),
                "deanimate": file.get("deanimate"),
                "pjs": file.get("pjs"),
                "pjpeg": file.get("pjpeg"),
                "comments_count": file.get("comments_count", 0),
                "initial_comment": file.get("initial_comment", {}),
                "num_stars": file.get("num_stars", 0),
                "pinned_to": file.get("pinned_to", []),
                "reactions": file.get("reactions", []),
                "is_external": file.get("is_external", False),
                "external_type": file.get("external_type"),
                "external_id": file.get("external_id"),
                "external_url": file.get("external_url"),
                "app_id": file.get("app_id"),
                "app_name": file.get("app_name"),
                "file_access": file.get("file_access"),
                "filetype_detection": file.get("filetype_detection")
            }
            file_list.append(file_info)
        
        # Get pagination info
        response_metadata = response.data.get("response_metadata", {})
        next_cursor = response_metadata.get("next_cursor", "")
        
        return {
            "data": {
                "files": file_list,
                "total_found": len(file_list),
                "channel_filter": channel if channel else "all_channels",
                "ts_from": ts_from,
                "ts_to": ts_to,
                "next_cursor": next_cursor,
                "has_more": bool(next_cursor),
                "limit_requested": limit
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'invalid_cursor':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nPagination cursor '{cursor}' is invalid.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel}' does not exist or is not accessible.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list remote files. The bot needs files:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs files:read scope to list remote files.",
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

@mcp.tool()
async def slack_list_scheduled_messages(
    channel: str = "",
    cursor: str = "",
    latest: str = "",
    limit: int = 100,
    oldest: str = ""
) -> dict:
    """
    Retrieves a list of pending (not yet delivered) messages scheduled in a specific slack channel, 
    or across all accessible channels if no channel id is provided, optionally filtered by time and paginated.
    
    Args:
        channel (str): Channel ID to filter scheduled messages by (optional)
        cursor (str): Pagination cursor for fetching additional results (optional)
        latest (str): End of time range of messages to include (optional)
        limit (int): Maximum number of messages to return (default: 100)
        oldest (str): Start of time range of messages to include (optional)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Prepare parameters for chat.scheduledMessages.list
        params = {
            'limit': min(limit, 1000)  # Slack API limit is 1000
        }
        
        # Add optional parameters
        if channel:
            params['channel'] = channel
        if cursor:
            params['cursor'] = cursor
        if latest:
            params['latest'] = latest
        if oldest:
            params['oldest'] = oldest
        
        # Use the chat.scheduledMessages.list method
        response = client.chat_scheduledMessages_list(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'invalid_cursor':
                return {
                    "data": {},
                    "error": f"Invalid cursor: Pagination cursor '{cursor}' is invalid",
                    "successful": False
                }
            elif error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Channel not found: The channel '{channel}' does not exist or is not accessible",
                    "successful": False
                }
            elif error == 'invalid_time_range':
                return {
                    "data": {},
                    "error": f"Invalid time range: The time range from '{oldest}' to '{latest}' is invalid",
                    "successful": False
                }
            elif error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to list scheduled messages. The bot needs chat:write scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs chat:write scope to list scheduled messages.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list scheduled messages: {error}",
                    "successful": False
                }
        
        scheduled_messages = response.data.get("scheduled_messages", [])
        
        # Format scheduled message information
        message_list = []
        for msg in scheduled_messages:
            message_info = {
                "id": msg.get("id"),
                "channel": msg.get("channel"),
                "post_at": msg.get("post_at"),
                "date_created": msg.get("date_created"),
                "text": msg.get("text"),
                "user": msg.get("user"),
                "team": msg.get("team"),
                "blocks": msg.get("blocks", []),
                "attachments": msg.get("attachments", []),
                "as_user": msg.get("as_user", False),
                "icon_emoji": msg.get("icon_emoji"),
                "icon_url": msg.get("icon_url"),
                "link_names": msg.get("link_names", False),
                "mrkdwn": msg.get("mrkdwn", False),
                "parse": msg.get("parse"),
                "reply_broadcast": msg.get("reply_broadcast", False),
                "thread_ts": msg.get("thread_ts"),
                "unfurl_links": msg.get("unfurl_links", True),
                "unfurl_media": msg.get("unfurl_media", True),
                "username": msg.get("username"),
                "scheduled_message_id": msg.get("scheduled_message_id"),
                "channel_id": msg.get("channel"),
                "post_time": msg.get("post_at"),
                "created_time": msg.get("date_created"),
                "message_text": msg.get("text", ""),
                "author_user": msg.get("user"),
                "team_id": msg.get("team"),
                "is_thread_reply": bool(msg.get("thread_ts")),
                "thread_timestamp": msg.get("thread_ts"),
                "has_blocks": bool(msg.get("blocks")),
                "has_attachments": bool(msg.get("attachments")),
                "blocks_count": len(msg.get("blocks", [])),
                "attachments_count": len(msg.get("attachments", [])),
                "scheduled_for": msg.get("post_at"),
                "created_by": msg.get("user"),
                "message_type": "scheduled_message",
                "status": "pending",
                "delivery_status": "not_delivered"
            }
            message_list.append(message_info)
        
        # Get pagination info
        response_metadata = response.data.get("response_metadata", {})
        next_cursor = response_metadata.get("next_cursor", "")
        
        return {
            "data": {
                "scheduled_messages": message_list,
                "total_found": len(message_list),
                "channel_filter": channel if channel else "all_channels",
                "time_range": {
                    "oldest": oldest if oldest else "not_specified",
                    "latest": latest if latest else "not_specified"
                },
                "next_cursor": next_cursor,
                "has_more": bool(next_cursor),
                "limit_requested": limit,
                "message_status": "pending_only"
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'invalid_cursor':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nPagination cursor '{cursor}' is invalid.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel}' does not exist or is not accessible.",
                "successful": False
            }
        elif error_code == 'invalid_time_range':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe time range from '{oldest}' to '{latest}' is invalid.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list scheduled messages. The bot needs chat:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs chat:write scope to list scheduled messages.",
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

@mcp.tool()
async def slack_list_scheduled_messages_in_a_channel(
    channel: str,
    cursor: str = "",
    latest: str = "",
    limit: int = 100,
    oldest: str = ""
) -> dict:
    """
    Deprecated: retrieves a list of pending (not yet delivered) messages scheduled in a specific slack channel. 
    use `list scheduled messages` instead.
    
    Args:
        channel (str): Channel ID to filter scheduled messages by (required)
        cursor (str): Pagination cursor for fetching additional results (optional)
        latest (str): End of time range of messages to include (optional)
        limit (int): Maximum number of messages to return (default: 100)
        oldest (str): Start of time range of messages to include (optional)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Prepare parameters for chat.scheduledMessages.list
        params = {
            'channel': channel,
            'limit': min(limit, 1000)  # Slack API limit is 1000
        }
        
        # Add optional parameters
        if cursor:
            params['cursor'] = cursor
        if latest:
            params['latest'] = latest
        if oldest:
            params['oldest'] = oldest
        
        # Use the chat.scheduledMessages.list method
        response = client.chat_scheduledMessages_list(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'invalid_cursor':
                return {
                    "data": {},
                    "error": f"Invalid cursor: Pagination cursor '{cursor}' is invalid",
                    "successful": False
                }
            elif error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Channel not found: The channel '{channel}' does not exist or is not accessible",
                    "successful": False
                }
            elif error == 'invalid_time_range':
                return {
                    "data": {},
                    "error": f"Invalid time range: The time range from '{oldest}' to '{latest}' is invalid",
                    "successful": False
                }
            elif error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to list scheduled messages. The bot needs chat:write scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs chat:write scope to list scheduled messages.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list scheduled messages: {error}",
                    "successful": False
                }
        
        scheduled_messages = response.data.get("scheduled_messages", [])
        
        # Format scheduled message information
        message_list = []
        for msg in scheduled_messages:
            message_info = {
                "id": msg.get("id"),
                "channel": msg.get("channel"),
                "post_at": msg.get("post_at"),
                "date_created": msg.get("date_created"),
                "text": msg.get("text"),
                "user": msg.get("user"),
                "team": msg.get("team"),
                "blocks": msg.get("blocks", []),
                "attachments": msg.get("attachments", []),
                "as_user": msg.get("as_user", False),
                "icon_emoji": msg.get("icon_emoji"),
                "icon_url": msg.get("icon_url"),
                "link_names": msg.get("link_names", False),
                "mrkdwn": msg.get("mrkdwn", False),
                "parse": msg.get("parse"),
                "reply_broadcast": msg.get("reply_broadcast", False),
                "thread_ts": msg.get("thread_ts"),
                "unfurl_links": msg.get("unfurl_links", True),
                "unfurl_media": msg.get("unfurl_media", True),
                "username": msg.get("username"),
                "scheduled_message_id": msg.get("scheduled_message_id"),
                "channel_id": msg.get("channel"),
                "post_time": msg.get("post_at"),
                "created_time": msg.get("date_created"),
                "message_text": msg.get("text", ""),
                "author_user": msg.get("user"),
                "team_id": msg.get("team"),
                "is_thread_reply": bool(msg.get("thread_ts")),
                "thread_timestamp": msg.get("thread_ts"),
                "has_blocks": bool(msg.get("blocks")),
                "has_attachments": bool(msg.get("attachments")),
                "blocks_count": len(msg.get("blocks", [])),
                "attachments_count": len(msg.get("attachments", [])),
                "scheduled_for": msg.get("post_at"),
                "created_by": msg.get("user"),
                "message_type": "scheduled_message",
                "status": "pending",
                "delivery_status": "not_delivered"
            }
            message_list.append(message_info)
        
        # Get pagination info
        response_metadata = response.data.get("response_metadata", {})
        next_cursor = response_metadata.get("next_cursor", "")
        
        return {
            "data": {
                "scheduled_messages": message_list,
                "total_found": len(message_list),
                "channel_filter": channel,
                "time_range": {
                    "oldest": oldest if oldest else "not_specified",
                    "latest": latest if latest else "not_specified"
                },
                "next_cursor": next_cursor,
                "has_more": bool(next_cursor),
                "limit_requested": limit,
                "message_status": "pending_only",
                "deprecation_warning": "This tool is deprecated. Use 'list scheduled messages' instead for better functionality."
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'invalid_cursor':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nPagination cursor '{cursor}' is invalid.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel}' does not exist or is not accessible.",
                "successful": False
            }
        elif error_code == 'invalid_time_range':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe time range from '{oldest}' to '{latest}' is invalid.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list scheduled messages. The bot needs chat:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs chat:write scope to list scheduled messages.",
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

@mcp.tool()
async def slack_lists_pinned_items_in_a_channel(
    channel: str
) -> dict:
    """
    Retrieves all messages and files pinned to a specified channel; the caller must have access to this channel.
    
    Args:
        channel (str): Channel ID to retrieve pinned items from (required)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the pins.list method
        response = client.pins_list(channel=channel)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'channel_not_found':
                return {
                    "data": [],
                    "error": f"Channel not found: The channel '{channel}' does not exist or is not accessible",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": [],
                    "error": f"Not in channel: The bot is not a member of the channel '{channel}'",
                    "successful": False
                }
            elif error == 'not_authed':
                return {
                    "data": [],
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": [],
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": [],
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": [],
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": [],
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to list pinned items. The bot needs pins:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": [],
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs pins:read scope to list pinned items.",
                    "successful": False
                }
            else:
                return {
                    "data": [],
                    "error": f"Failed to list pinned items: {error}",
                    "successful": False
                }
        
        items = response.data.get("items", [])
        
        # Format pinned items information
        pinned_items = []
        for item in items:
            item_info = {
                "type": item.get("type"),
                "channel": item.get("channel"),
                "created": item.get("created"),
                "created_by": item.get("created_by"),
                "timestamp": item.get("timestamp"),
                "message": item.get("message", {}),
                "file": item.get("file", {}),
                "comment": item.get("comment", {}),
                "item_id": item.get("id"),
                "item_type": item.get("type"),
                "pinned_by": item.get("created_by"),
                "pinned_at": item.get("created"),
                "channel_id": item.get("channel"),
                "is_message": item.get("type") == "message",
                "is_file": item.get("type") == "file",
                "is_comment": item.get("type") == "comment"
            }
            
            # Add message-specific information if it's a message
            if item.get("type") == "message" and item.get("message"):
                message = item.get("message", {})
                item_info.update({
                    "message_text": message.get("text", ""),
                    "message_user": message.get("user", ""),
                    "message_ts": message.get("ts", ""),
                    "message_blocks": message.get("blocks", []),
                    "message_attachments": message.get("attachments", []),
                    "message_thread_ts": message.get("thread_ts", ""),
                    "message_reply_count": message.get("reply_count", 0),
                    "message_reply_users": message.get("reply_users", []),
                    "message_reply_users_count": message.get("reply_users_count", 0),
                    "message_latest_reply": message.get("latest_reply", ""),
                    "message_subtype": message.get("subtype", ""),
                    "message_hidden": message.get("hidden", False),
                    "message_edited": message.get("edited", {}),
                    "message_deleted_ts": message.get("deleted_ts", ""),
                    "message_event_ts": message.get("event_ts", ""),
                    "message_team": message.get("team", ""),
                    "message_has_blocks": bool(message.get("blocks")),
                    "message_has_attachments": bool(message.get("attachments")),
                    "message_is_thread": bool(message.get("thread_ts")),
                    "message_blocks_count": len(message.get("blocks", [])),
                    "message_attachments_count": len(message.get("attachments", []))
                })
            
            # Add file-specific information if it's a file
            elif item.get("type") == "file" and item.get("file"):
                file = item.get("file", {})
                item_info.update({
                    "file_id": file.get("id", ""),
                    "file_name": file.get("name", ""),
                    "file_title": file.get("title", ""),
                    "file_mimetype": file.get("mimetype", ""),
                    "file_filetype": file.get("filetype", ""),
                    "file_size": file.get("size", 0),
                    "file_url_private": file.get("url_private", ""),
                    "file_url_private_download": file.get("url_private_download", ""),
                    "file_thumb_360": file.get("thumb_360", ""),
                    "file_thumb_480": file.get("thumb_480", ""),
                    "file_thumb_720": file.get("thumb_720", ""),
                    "file_thumb_800": file.get("thumb_800", ""),
                    "file_thumb_960": file.get("thumb_960", ""),
                    "file_thumb_1024": file.get("thumb_1024", ""),
                    "file_thumb_160": file.get("thumb_160", ""),
                    "file_thumb_360_w": file.get("thumb_360_w", 0),
                    "file_thumb_360_h": file.get("thumb_360_h", 0),
                    "file_thumb_480_w": file.get("thumb_480_w", 0),
                    "file_thumb_480_h": file.get("thumb_480_h", 0),
                    "file_thumb_720_w": file.get("thumb_720_w", 0),
                    "file_thumb_720_h": file.get("thumb_720_h", 0),
                    "file_thumb_800_w": file.get("thumb_800_w", 0),
                    "file_thumb_800_h": file.get("thumb_800_h", 0),
                    "file_thumb_960_w": file.get("thumb_960_w", 0),
                    "file_thumb_960_h": file.get("thumb_960_h", 0),
                    "file_thumb_1024_w": file.get("thumb_1024_w", 0),
                    "file_thumb_1024_h": file.get("thumb_1024_h", 0),
                    "file_thumb_160_w": file.get("thumb_160_w", 0),
                    "file_thumb_160_h": file.get("thumb_160_h", 0),
                    "file_original_w": file.get("original_w", 0),
                    "file_original_h": file.get("original_h", 0),
                    "file_created": file.get("created", 0),
                    "file_timestamp": file.get("timestamp", 0),
                    "file_user": file.get("user", ""),
                    "file_username": file.get("username", ""),
                    "file_editable": file.get("editable", False),
                    "file_is_external": file.get("is_external", False),
                    "file_external_type": file.get("external_type", ""),
                    "file_is_public": file.get("is_public", False),
                    "file_public_url_shared": file.get("public_url_shared", False),
                    "file_display_as_bot": file.get("display_as_bot", False),
                    "file_mode": file.get("mode", ""),
                    "file_media_display_type": file.get("media_display_type", ""),
                    "file_preview": file.get("preview", ""),
                    "file_preview_highlight": file.get("preview_highlight", ""),
                    "file_lines": file.get("lines", 0),
                    "file_lines_more": file.get("lines_more", 0),
                    "file_thumb_tiny": file.get("thumb_tiny", ""),
                    "file_thumb_video": file.get("thumb_video", ""),
                    "file_thumb_video_w": file.get("thumb_video_w", 0),
                    "file_thumb_video_h": file.get("thumb_video_h", 0),
                    "file_duration_ms": file.get("duration_ms", 0),
                    "file_hd": file.get("hd", False),
                    "file_subtype": file.get("subtype", ""),
                    "file_transcription": file.get("transcription", {}),
                    "file_mp4": file.get("mp4", ""),
                    "file_vtt": file.get("vtt", ""),
                    "file_hls": file.get("hls", ""),
                    "file_hls_embed": file.get("hls_embed", ""),
                    "file_dash": file.get("dash", ""),
                    "file_dash_embed": file.get("dash_embed", ""),
                    "file_is_animated": file.get("is_animated", False),
                    "file_is_removed": file.get("is_removed", False),
                    "file_deanimate_gif": file.get("deanimate_gif", ""),
                    "file_deanimate": file.get("deanimate", ""),
                    "file_pjs": file.get("pjs", ""),
                    "file_pjpeg": file.get("pjpeg", ""),
                    "file_comments_count": file.get("comments_count", 0),
                    "file_initial_comment": file.get("initial_comment", {}),
                    "file_num_stars": file.get("num_stars", 0),
                    "file_pinned_to": file.get("pinned_to", []),
                    "file_reactions": file.get("reactions", []),
                    "file_shares": file.get("shares", {}),
                    "file_channels": file.get("channels", []),
                    "file_groups": file.get("groups", []),
                    "file_ims": file.get("ims", []),
                    "file_external_id": file.get("external_id", ""),
                    "file_external_url": file.get("external_url", ""),
                    "file_app_id": file.get("app_id", ""),
                    "file_app_name": file.get("app_name", ""),
                    "file_has_rich_preview": file.get("has_rich_preview", False),
                    "file_media_display_type": file.get("media_display_type", ""),
                    "file_thumbnails": {
                        "thumb_160": file.get("thumb_160", ""),
                        "thumb_360": file.get("thumb_360", ""),
                        "thumb_480": file.get("thumb_480", ""),
                        "thumb_720": file.get("thumb_720", ""),
                        "thumb_800": file.get("thumb_800", ""),
                        "thumb_960": file.get("thumb_960", ""),
                        "thumb_1024": file.get("thumb_1024", ""),
                        "thumb_tiny": file.get("thumb_tiny", "")
                    }
                })
            
            # Add comment-specific information if it's a comment
            elif item.get("type") == "comment" and item.get("comment"):
                comment = item.get("comment", {})
                item_info.update({
                    "comment_id": comment.get("id", ""),
                    "comment_text": comment.get("text", ""),
                    "comment_user": comment.get("user", ""),
                    "comment_created": comment.get("created", 0),
                    "comment_timestamp": comment.get("timestamp", ""),
                    "comment_reply_count": comment.get("reply_count", 0),
                    "comment_reply_users": comment.get("reply_users", []),
                    "comment_reply_users_count": comment.get("reply_users_count", 0),
                    "comment_latest_reply": comment.get("latest_reply", ""),
                    "comment_subtype": comment.get("subtype", ""),
                    "comment_hidden": comment.get("hidden", False),
                    "comment_edited": comment.get("edited", {}),
                    "comment_deleted_ts": comment.get("deleted_ts", ""),
                    "comment_event_ts": comment.get("event_ts", ""),
                    "comment_team": comment.get("team", ""),
                    "comment_blocks": comment.get("blocks", []),
                    "comment_attachments": comment.get("attachments", []),
                    "comment_has_blocks": bool(comment.get("blocks")),
                    "comment_has_attachments": bool(comment.get("attachments")),
                    "comment_blocks_count": len(comment.get("blocks", [])),
                    "comment_attachments_count": len(comment.get("attachments", []))
                })
            
            pinned_items.append(item_info)
        
        return {
            "data": pinned_items,
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'channel_not_found':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nThe channel '{channel}' does not exist or is not accessible.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of the channel '{channel}'.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list pinned items. The bot needs pins:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": [],
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs pins:read scope to list pinned items.",
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

@mcp.tool()
async def slack_list_starred_items(
    count: int = 20,
    cursor: str = "",
    limit: int = 20,
    page: int = 1
) -> dict:
    """
    Lists items starred by a user.
    
    Args:
        count (int): Number of items to return (default: 20)
        cursor (str): Pagination cursor for fetching additional results (optional)
        limit (int): Maximum number of items to return (default: 20)
        page (int): Page number for pagination (default: 1)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Use user token for starred items (stars require user tokens)
        client = get_slack_user_client()
        
        # Prepare parameters for stars.list
        params = {
            'count': min(count, 1000),  # Slack API limit is 1000
            'limit': min(limit, 1000)
        }
        
        # Add optional parameters
        if cursor:
            params['cursor'] = cursor
        if page > 1:
            params['page'] = page
        
        # Use the stars.list method
        response = client.stars_list(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'invalid_cursor':
                return {
                    "data": {},
                    "error": f"Invalid cursor: Pagination cursor '{cursor}' is invalid",
                    "successful": False
                }
            elif error == 'invalid_page':
                return {
                    "data": {},
                    "error": f"Invalid page: Page number '{page}' is invalid",
                    "successful": False
                }
            elif error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to list starred items. The user token needs stars:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The user token needs stars:read scope to list starred items.",
                    "successful": False
                }
            elif error == 'not_allowed_token_type':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nStarred items require a user token (xoxp-). Please set SLACK_USER_TOKEN with a user token that has stars:read scope.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list starred items: {error}",
                    "successful": False
                }
        
        items = response.data.get("items", [])
        
        # Format starred items information
        starred_items = []
        for item in items:
            item_info = {
                "type": item.get("type"),
                "channel": item.get("channel"),
                "message": item.get("message", {}),
                "file": item.get("file", {}),
                "comment": item.get("comment", {}),
                "item_id": item.get("id"),
                "item_type": item.get("type"),
                "channel_id": item.get("channel"),
                "is_message": item.get("type") == "message",
                "is_file": item.get("type") == "file",
                "is_comment": item.get("type") == "comment",
                "is_starred": True
            }
            
            # Add message-specific information if it's a message
            if item.get("type") == "message" and item.get("message"):
                message = item.get("message", {})
                item_info.update({
                    "message_text": message.get("text", ""),
                    "message_user": message.get("user", ""),
                    "message_ts": message.get("ts", ""),
                    "message_blocks": message.get("blocks", []),
                    "message_attachments": message.get("attachments", []),
                    "message_thread_ts": message.get("thread_ts", ""),
                    "message_reply_count": message.get("reply_count", 0),
                    "message_reply_users": message.get("reply_users", []),
                    "message_reply_users_count": message.get("reply_users_count", 0),
                    "message_latest_reply": message.get("latest_reply", ""),
                    "message_subtype": message.get("subtype", ""),
                    "message_hidden": message.get("hidden", False),
                    "message_edited": message.get("edited", {}),
                    "message_deleted_ts": message.get("deleted_ts", ""),
                    "message_event_ts": message.get("event_ts", ""),
                    "message_team": message.get("team", ""),
                    "message_has_blocks": bool(message.get("blocks")),
                    "message_has_attachments": bool(message.get("attachments")),
                    "message_is_thread": bool(message.get("thread_ts")),
                    "message_blocks_count": len(message.get("blocks", [])),
                    "message_attachments_count": len(message.get("attachments", []))
                })
            
            # Add file-specific information if it's a file
            elif item.get("type") == "file" and item.get("file"):
                file = item.get("file", {})
                item_info.update({
                    "file_id": file.get("id", ""),
                    "file_name": file.get("name", ""),
                    "file_title": file.get("title", ""),
                    "file_mimetype": file.get("mimetype", ""),
                    "file_filetype": file.get("filetype", ""),
                    "file_size": file.get("size", 0),
                    "file_url_private": file.get("url_private", ""),
                    "file_url_private_download": file.get("url_private_download", ""),
                    "file_thumb_360": file.get("thumb_360", ""),
                    "file_thumb_480": file.get("thumb_480", ""),
                    "file_thumb_720": file.get("thumb_720", ""),
                    "file_thumb_800": file.get("thumb_800", ""),
                    "file_thumb_960": file.get("thumb_960", ""),
                    "file_thumb_1024": file.get("thumb_1024", ""),
                    "file_thumb_160": file.get("thumb_160", ""),
                    "file_thumb_360_w": file.get("thumb_360_w", 0),
                    "file_thumb_360_h": file.get("thumb_360_h", 0),
                    "file_thumb_480_w": file.get("thumb_480_w", 0),
                    "file_thumb_480_h": file.get("thumb_480_h", 0),
                    "file_thumb_720_w": file.get("thumb_720_w", 0),
                    "file_thumb_720_h": file.get("thumb_720_h", 0),
                    "file_thumb_800_w": file.get("thumb_800_w", 0),
                    "file_thumb_800_h": file.get("thumb_800_h", 0),
                    "file_thumb_960_w": file.get("thumb_960_w", 0),
                    "file_thumb_960_h": file.get("thumb_960_h", 0),
                    "file_thumb_1024_w": file.get("thumb_1024_w", 0),
                    "file_thumb_1024_h": file.get("thumb_1024_h", 0),
                    "file_thumb_160_w": file.get("thumb_160_w", 0),
                    "file_thumb_160_h": file.get("thumb_160_h", 0),
                    "file_original_w": file.get("original_w", 0),
                    "file_original_h": file.get("original_h", 0),
                    "file_created": file.get("created", 0),
                    "file_timestamp": file.get("timestamp", 0),
                    "file_user": file.get("user", ""),
                    "file_username": file.get("username", ""),
                    "file_editable": file.get("editable", False),
                    "file_is_external": file.get("is_external", False),
                    "file_external_type": file.get("external_type", ""),
                    "file_is_public": file.get("is_public", False),
                    "file_public_url_shared": file.get("public_url_shared", False),
                    "file_display_as_bot": file.get("display_as_bot", False),
                    "file_mode": file.get("mode", ""),
                    "file_media_display_type": file.get("media_display_type", ""),
                    "file_preview": file.get("preview", ""),
                    "file_preview_highlight": file.get("preview_highlight", ""),
                    "file_lines": file.get("lines", 0),
                    "file_lines_more": file.get("lines_more", 0),
                    "file_thumb_tiny": file.get("thumb_tiny", ""),
                    "file_thumb_video": file.get("thumb_video", ""),
                    "file_thumb_video_w": file.get("thumb_video_w", 0),
                    "file_thumb_video_h": file.get("thumb_video_h", 0),
                    "file_duration_ms": file.get("duration_ms", 0),
                    "file_hd": file.get("hd", False),
                    "file_subtype": file.get("subtype", ""),
                    "file_transcription": file.get("transcription", {}),
                    "file_mp4": file.get("mp4", ""),
                    "file_vtt": file.get("vtt", ""),
                    "file_hls": file.get("hls", ""),
                    "file_hls_embed": file.get("hls_embed", ""),
                    "file_dash": file.get("dash", ""),
                    "file_dash_embed": file.get("dash_embed", ""),
                    "file_is_animated": file.get("is_animated", False),
                    "file_is_removed": file.get("is_removed", False),
                    "file_deanimate_gif": file.get("deanimate_gif", ""),
                    "file_deanimate": file.get("deanimate", ""),
                    "file_pjs": file.get("pjs", ""),
                    "file_pjpeg": file.get("pjpeg", ""),
                    "file_comments_count": file.get("comments_count", 0),
                    "file_initial_comment": file.get("initial_comment", {}),
                    "file_num_stars": file.get("num_stars", 0),
                    "file_pinned_to": file.get("pinned_to", []),
                    "file_reactions": file.get("reactions", []),
                    "file_shares": file.get("shares", {}),
                    "file_channels": file.get("channels", []),
                    "file_groups": file.get("groups", []),
                    "file_ims": file.get("ims", []),
                    "file_external_id": file.get("external_id", ""),
                    "file_external_url": file.get("external_url", ""),
                    "file_app_id": file.get("app_id", ""),
                    "file_app_name": file.get("app_name", ""),
                    "file_has_rich_preview": file.get("has_rich_preview", False),
                    "file_media_display_type": file.get("media_display_type", ""),
                    "file_thumbnails": {
                        "thumb_160": file.get("thumb_160", ""),
                        "thumb_360": file.get("thumb_360", ""),
                        "thumb_480": file.get("thumb_480", ""),
                        "thumb_720": file.get("thumb_720", ""),
                        "thumb_800": file.get("thumb_800", ""),
                        "thumb_960": file.get("thumb_960", ""),
                        "thumb_1024": file.get("thumb_1024", ""),
                        "thumb_tiny": file.get("thumb_tiny", "")
                    }
                })
            
            # Add comment-specific information if it's a comment
            elif item.get("type") == "comment" and item.get("comment"):
                comment = item.get("comment", {})
                item_info.update({
                    "comment_id": comment.get("id", ""),
                    "comment_text": comment.get("text", ""),
                    "comment_user": comment.get("user", ""),
                    "comment_created": comment.get("created", 0),
                    "comment_timestamp": comment.get("timestamp", ""),
                    "comment_reply_count": comment.get("reply_count", 0),
                    "comment_reply_users": comment.get("reply_users", []),
                    "comment_reply_users_count": comment.get("reply_users_count", 0),
                    "comment_latest_reply": comment.get("latest_reply", ""),
                    "comment_subtype": comment.get("subtype", ""),
                    "comment_hidden": comment.get("hidden", False),
                    "comment_edited": comment.get("edited", {}),
                    "comment_deleted_ts": comment.get("deleted_ts", ""),
                    "comment_event_ts": comment.get("event_ts", ""),
                    "comment_team": comment.get("team", ""),
                    "comment_blocks": comment.get("blocks", []),
                    "comment_attachments": comment.get("attachments", []),
                    "comment_has_blocks": bool(comment.get("blocks")),
                    "comment_has_attachments": bool(comment.get("attachments")),
                    "comment_blocks_count": len(comment.get("blocks", [])),
                    "comment_attachments_count": len(comment.get("attachments", []))
                })
            
            starred_items.append(item_info)
        
        # Get pagination info
        response_metadata = response.data.get("response_metadata", {})
        next_cursor = response_metadata.get("next_cursor", "")
        
        return {
            "data": {
                "starred_items": starred_items,
                "total_found": len(starred_items),
                "count_requested": count,
                "limit_requested": limit,
                "page_requested": page,
                "next_cursor": next_cursor,
                "has_more": bool(next_cursor),
                "pagination": {
                    "current_page": page,
                    "items_per_page": count,
                    "total_items": len(starred_items),
                    "has_next_page": bool(next_cursor)
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'invalid_cursor':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nPagination cursor '{cursor}' is invalid.",
                "successful": False
            }
        elif error_code == 'invalid_page':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nPage number '{page}' is invalid.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list starred items. The user token needs stars:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The user token needs stars:read scope to list starred items.",
                "successful": False
            }
        elif error_code == 'not_allowed_token_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nStarred items require a user token (xoxp-). Please set SLACK_USER_TOKEN with a user token that has stars:read scope.",
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

@mcp.tool()
async def slack_lists_user_s_starred_items_with_pagination(
    count: int = 20,
    cursor: str = "",
    limit: int = 20,
    page: int = 1
) -> dict:
    """
    Deprecated: lists items starred by a user. use `list starred items` instead.
    
    Args:
        count (int): Number of items to return (default: 20)
        cursor (str): Pagination cursor for fetching additional results (optional)
        limit (int): Maximum number of items to return (default: 20)
        page (int): Page number for pagination (default: 1)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Use user token for starred items (stars require user tokens)
        client = get_slack_user_client()
        
        # Prepare parameters for stars.list
        params = {
            'count': min(count, 1000),  # Slack API limit is 1000
            'limit': min(limit, 1000)
        }
        
        # Add optional parameters
        if cursor:
            params['cursor'] = cursor
        if page > 1:
            params['page'] = page
        
        # Use the stars.list method
        response = client.stars_list(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'invalid_cursor':
                return {
                    "data": {},
                    "error": f"Invalid cursor: Pagination cursor '{cursor}' is invalid",
                    "successful": False
                }
            elif error == 'invalid_page':
                return {
                    "data": {},
                    "error": f"Invalid page: Page number '{page}' is invalid",
                    "successful": False
                }
            elif error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_USER_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_USER_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to list starred items. The user token needs stars:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The user token needs stars:read scope to list starred items.",
                    "successful": False
                }
            elif error == 'not_allowed_token_type':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nStarred items require a user token (xoxp-). Please set SLACK_USER_TOKEN with a user token that has stars:read scope.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list starred items: {error}",
                    "successful": False
                }
        
        items = response.data.get("items", [])
        
        # Format starred items information
        starred_items = []
        for item in items:
            item_info = {
                "type": item.get("type"),
                "channel": item.get("channel"),
                "message": item.get("message", {}),
                "file": item.get("file", {}),
                "comment": item.get("comment", {}),
                "item_id": item.get("id"),
                "item_type": item.get("type"),
                "channel_id": item.get("channel"),
                "is_message": item.get("type") == "message",
                "is_file": item.get("type") == "file",
                "is_comment": item.get("type") == "comment",
                "is_starred": True
            }
            
            # Add message-specific information if it's a message
            if item.get("type") == "message" and item.get("message"):
                message = item.get("message", {})
                item_info.update({
                    "message_text": message.get("text", ""),
                    "message_user": message.get("user", ""),
                    "message_ts": message.get("ts", ""),
                    "message_blocks": message.get("blocks", []),
                    "message_attachments": message.get("attachments", []),
                    "message_thread_ts": message.get("thread_ts", ""),
                    "message_reply_count": message.get("reply_count", 0),
                    "message_reply_users": message.get("reply_users", []),
                    "message_reply_users_count": message.get("reply_users_count", 0),
                    "message_latest_reply": message.get("latest_reply", ""),
                    "message_subtype": message.get("subtype", ""),
                    "message_hidden": message.get("hidden", False),
                    "message_edited": message.get("edited", {}),
                    "message_deleted_ts": message.get("deleted_ts", ""),
                    "message_event_ts": message.get("event_ts", ""),
                    "message_team": message.get("team", ""),
                    "message_has_blocks": bool(message.get("blocks")),
                    "message_has_attachments": bool(message.get("attachments")),
                    "message_is_thread": bool(message.get("thread_ts")),
                    "message_blocks_count": len(message.get("blocks", [])),
                    "message_attachments_count": len(message.get("attachments", []))
                })
            
            # Add file-specific information if it's a file
            elif item.get("type") == "file" and item.get("file"):
                file = item.get("file", {})
                item_info.update({
                    "file_id": file.get("id", ""),
                    "file_name": file.get("name", ""),
                    "file_title": file.get("title", ""),
                    "file_mimetype": file.get("mimetype", ""),
                    "file_filetype": file.get("filetype", ""),
                    "file_size": file.get("size", 0),
                    "file_url_private": file.get("url_private", ""),
                    "file_url_private_download": file.get("url_private_download", ""),
                    "file_thumb_360": file.get("thumb_360", ""),
                    "file_thumb_480": file.get("thumb_480", ""),
                    "file_thumb_720": file.get("thumb_720", ""),
                    "file_thumb_800": file.get("thumb_800", ""),
                    "file_thumb_960": file.get("thumb_960", ""),
                    "file_thumb_1024": file.get("thumb_1024", ""),
                    "file_thumb_160": file.get("thumb_160", ""),
                    "file_thumb_360_w": file.get("thumb_360_w", 0),
                    "file_thumb_360_h": file.get("thumb_360_h", 0),
                    "file_thumb_480_w": file.get("thumb_480_w", 0),
                    "file_thumb_480_h": file.get("thumb_480_h", 0),
                    "file_thumb_720_w": file.get("thumb_720_w", 0),
                    "file_thumb_720_h": file.get("thumb_720_h", 0),
                    "file_thumb_800_w": file.get("thumb_800_w", 0),
                    "file_thumb_800_h": file.get("thumb_800_h", 0),
                    "file_thumb_960_w": file.get("thumb_960_w", 0),
                    "file_thumb_960_h": file.get("thumb_960_h", 0),
                    "file_thumb_1024_w": file.get("thumb_1024_w", 0),
                    "file_thumb_1024_h": file.get("thumb_1024_h", 0),
                    "file_thumb_160_w": file.get("thumb_160_w", 0),
                    "file_thumb_160_h": file.get("thumb_160_h", 0),
                    "file_original_w": file.get("original_w", 0),
                    "file_original_h": file.get("original_h", 0),
                    "file_created": file.get("created", 0),
                    "file_timestamp": file.get("timestamp", 0),
                    "file_user": file.get("user", ""),
                    "file_username": file.get("username", ""),
                    "file_editable": file.get("editable", False),
                    "file_is_external": file.get("is_external", False),
                    "file_external_type": file.get("external_type", ""),
                    "file_is_public": file.get("is_public", False),
                    "file_public_url_shared": file.get("public_url_shared", False),
                    "file_display_as_bot": file.get("display_as_bot", False),
                    "file_mode": file.get("mode", ""),
                    "file_media_display_type": file.get("media_display_type", ""),
                    "file_preview": file.get("preview", ""),
                    "file_preview_highlight": file.get("preview_highlight", ""),
                    "file_lines": file.get("lines", 0),
                    "file_lines_more": file.get("lines_more", 0),
                    "file_thumb_tiny": file.get("thumb_tiny", ""),
                    "file_thumb_video": file.get("thumb_video", ""),
                    "file_thumb_video_w": file.get("thumb_video_w", 0),
                    "file_thumb_video_h": file.get("thumb_video_h", 0),
                    "file_duration_ms": file.get("duration_ms", 0),
                    "file_hd": file.get("hd", False),
                    "file_subtype": file.get("subtype", ""),
                    "file_transcription": file.get("transcription", {}),
                    "file_mp4": file.get("mp4", ""),
                    "file_vtt": file.get("vtt", ""),
                    "file_hls": file.get("hls", ""),
                    "file_hls_embed": file.get("hls_embed", ""),
                    "file_dash": file.get("dash", ""),
                    "file_dash_embed": file.get("dash_embed", ""),
                    "file_is_animated": file.get("is_animated", False),
                    "file_is_removed": file.get("is_removed", False),
                    "file_deanimate_gif": file.get("deanimate_gif", ""),
                    "file_deanimate": file.get("deanimate", ""),
                    "file_pjs": file.get("pjs", ""),
                    "file_pjpeg": file.get("pjpeg", ""),
                    "file_comments_count": file.get("comments_count", 0),
                    "file_initial_comment": file.get("initial_comment", {}),
                    "file_num_stars": file.get("num_stars", 0),
                    "file_pinned_to": file.get("pinned_to", []),
                    "file_reactions": file.get("reactions", []),
                    "file_shares": file.get("shares", {}),
                    "file_channels": file.get("channels", []),
                    "file_groups": file.get("groups", []),
                    "file_ims": file.get("ims", []),
                    "file_external_id": file.get("external_id", ""),
                    "file_external_url": file.get("external_url", ""),
                    "file_app_id": file.get("app_id", ""),
                    "file_app_name": file.get("app_name", ""),
                    "file_has_rich_preview": file.get("has_rich_preview", False),
                    "file_media_display_type": file.get("media_display_type", ""),
                    "file_thumbnails": {
                        "thumb_160": file.get("thumb_160", ""),
                        "thumb_360": file.get("thumb_360", ""),
                        "thumb_480": file.get("thumb_480", ""),
                        "thumb_720": file.get("thumb_720", ""),
                        "thumb_800": file.get("thumb_800", ""),
                        "thumb_960": file.get("thumb_960", ""),
                        "thumb_1024": file.get("thumb_1024", ""),
                        "thumb_tiny": file.get("thumb_tiny", "")
                    }
                })
            
            # Add comment-specific information if it's a comment
            elif item.get("type") == "comment" and item.get("comment"):
                comment = item.get("comment", {})
                item_info.update({
                    "comment_id": comment.get("id", ""),
                    "comment_text": comment.get("text", ""),
                    "comment_user": comment.get("user", ""),
                    "comment_created": comment.get("created", 0),
                    "comment_timestamp": comment.get("timestamp", ""),
                    "comment_reply_count": comment.get("reply_count", 0),
                    "comment_reply_users": comment.get("reply_users", []),
                    "comment_reply_users_count": comment.get("reply_users_count", 0),
                    "comment_latest_reply": comment.get("latest_reply", ""),
                    "comment_subtype": comment.get("subtype", ""),
                    "comment_hidden": comment.get("hidden", False),
                    "comment_edited": comment.get("edited", {}),
                    "comment_deleted_ts": comment.get("deleted_ts", ""),
                    "comment_event_ts": comment.get("event_ts", ""),
                    "comment_team": comment.get("team", ""),
                    "comment_blocks": comment.get("blocks", []),
                    "comment_attachments": comment.get("attachments", []),
                    "comment_has_blocks": bool(comment.get("blocks")),
                    "comment_has_attachments": bool(comment.get("attachments")),
                    "comment_blocks_count": len(comment.get("blocks", [])),
                    "comment_attachments_count": len(comment.get("attachments", []))
                })
            
            starred_items.append(item_info)
        
        # Get pagination info
        response_metadata = response.data.get("response_metadata", {})
        next_cursor = response_metadata.get("next_cursor", "")
        
        return {
            "data": {
                "starred_items": starred_items,
                "total_found": len(starred_items),
                "count_requested": count,
                "limit_requested": limit,
                "page_requested": page,
                "next_cursor": next_cursor,
                "has_more": bool(next_cursor),
                "pagination": {
                    "current_page": page,
                    "items_per_page": count,
                    "total_items": len(starred_items),
                    "has_next_page": bool(next_cursor)
                },
                "deprecation_warning": "This tool is deprecated. Use 'list starred items' instead for better functionality."
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'invalid_cursor':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nPagination cursor '{cursor}' is invalid.",
                "successful": False
            }
        elif error_code == 'invalid_page':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nPage number '{page}' is invalid.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list starred items. The user token needs stars:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The user token needs stars:read scope to list starred items.",
                "successful": False
            }
        elif error_code == 'not_allowed_token_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nStarred items require a user token (xoxp-). Please set SLACK_USER_TOKEN with a user token that has stars:read scope.",
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

@mcp.tool()
async def slack_list_team_custom_emojis() -> dict:
    """
    Retrieves all custom emojis for the slack workspace (image urls or aliases), not standard unicode emojis; 
    does not include usage statistics or creation dates.
    
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the emoji.list method
        response = client.emoji_list()
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to list custom emojis. The bot needs emoji:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs emoji:read scope to list custom emojis.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list custom emojis: {error}",
                    "successful": False
                }
        
        emoji_data = response.data.get("emoji", {})
        
        # Format emoji information
        custom_emojis = []
        for emoji_name, emoji_url in emoji_data.items():
            # Skip standard unicode emojis (they don't have URLs)
            if emoji_url and not emoji_url.startswith('alias:'):
                emoji_info = {
                    "name": emoji_name,
                    "url": emoji_url,
                    "type": "custom_emoji",
                    "is_alias": False,
                    "is_unicode": False,
                    "is_custom": True
                }
                custom_emojis.append(emoji_info)
            elif emoji_url and emoji_url.startswith('alias:'):
                # Handle emoji aliases
                alias_target = emoji_url.replace('alias:', '')
                emoji_info = {
                    "name": emoji_name,
                    "alias_target": alias_target,
                    "type": "emoji_alias",
                    "is_alias": True,
                    "is_unicode": False,
                    "is_custom": True
                }
                custom_emojis.append(emoji_info)
        
        # Sort emojis by name for consistent ordering
        custom_emojis.sort(key=lambda x: x["name"])
        
        return {
            "data": {
                "custom_emojis": custom_emojis,
                "total_found": len(custom_emojis),
                "emoji_types": {
                    "custom_emojis": len([e for e in custom_emojis if not e["is_alias"]]),
                    "emoji_aliases": len([e for e in custom_emojis if e["is_alias"]])
                },
                "workspace_info": "Custom emojis for the Slack workspace",
                "note": "Does not include usage statistics or creation dates"
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list custom emojis. The bot needs emoji:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs emoji:read scope to list custom emojis.",
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

@mcp.tool()
async def slack_list_user_groups_for_team_with_options(
    include_count: bool = False,
    include_disabled: bool = False,
    include_users: bool = False
) -> dict:
    """
    Lists user groups in a slack workspace, including user-created and default groups; 
    results for large workspaces may be paginated.
    
    Args:
        include_count (bool): Whether to include the number of users in each group (default: False)
        include_disabled (bool): Whether to include disabled user groups (default: False)
        include_users (bool): Whether to include the list of users in each group (default: False)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Prepare parameters for usergroups.list
        params = {
            'include_count': include_count,
            'include_disabled': include_disabled,
            'include_users': include_users
        }
        
        # Use the usergroups.list method
        response = client.usergroups_list(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to list user groups. The bot needs usergroups:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs usergroups:read scope to list user groups.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list user groups: {error}",
                    "successful": False
                }
        
        usergroups = response.data.get("usergroups", [])
        
        # Format user group information
        user_group_list = []
        for group in usergroups:
            group_info = {
                "id": group.get("id"),
                "team_id": group.get("team_id"),
                "name": group.get("name"),
                "description": group.get("description", ""),
                "handle": group.get("handle", ""),
                "is_external": group.get("is_external", False),
                "date_create": group.get("date_create", 0),
                "date_update": group.get("date_update", 0),
                "date_delete": group.get("date_delete", 0),
                "auto_type": group.get("auto_type", ""),
                "auto_value": group.get("auto_value", ""),
                "created_by": group.get("created_by", ""),
                "updated_by": group.get("updated_by", ""),
                "deleted_by": group.get("deleted_by", ""),
                "prefs": group.get("prefs", {}),
                "user_count": group.get("user_count", 0) if include_count else None,
                "users": group.get("users", []) if include_users else [],
                "is_active": group.get("is_active", True),
                "is_disabled": not group.get("is_active", True),
                "is_external": group.get("is_external", False),
                "is_auto_type": bool(group.get("auto_type")),
                "auto_type_value": group.get("auto_value", ""),
                "created_timestamp": group.get("date_create", 0),
                "updated_timestamp": group.get("date_update", 0),
                "deleted_timestamp": group.get("date_delete", 0),
                "creator_user": group.get("created_by", ""),
                "updater_user": group.get("updated_by", ""),
                "deleter_user": group.get("deleted_by", ""),
                "preferences": group.get("prefs", {}),
                "member_count": group.get("user_count", 0) if include_count else None,
                "member_list": group.get("users", []) if include_users else [],
                "group_type": "external" if group.get("is_external") else "internal",
                "status": "active" if group.get("is_active") else "disabled",
                "auto_configuration": {
                    "auto_type": group.get("auto_type", ""),
                    "auto_value": group.get("auto_value", ""),
                    "is_auto_configured": bool(group.get("auto_type"))
                },
                "timestamps": {
                    "created": group.get("date_create", 0),
                    "updated": group.get("date_update", 0),
                    "deleted": group.get("date_delete", 0)
                },
                "users_info": {
                    "created_by": group.get("created_by", ""),
                    "updated_by": group.get("updated_by", ""),
                    "deleted_by": group.get("deleted_by", "")
                }
            }
            
            # Add user-specific information if include_users is True
            if include_users and group.get("users"):
                users = group.get("users", [])
                group_info.update({
                    "user_ids": users,
                    "user_count": len(users),
                    "member_list": users,
                    "has_members": len(users) > 0,
                    "member_count": len(users)
                })
            
            # Add count-specific information if include_count is True
            if include_count:
                user_count = group.get("user_count", 0)
                group_info.update({
                    "user_count": user_count,
                    "member_count": user_count,
                    "has_members": user_count > 0,
                    "is_empty": user_count == 0
                })
            
            user_group_list.append(group_info)
        
        # Sort user groups by name for consistent ordering
        user_group_list.sort(key=lambda x: x["name"])
        
        return {
            "data": {
                "user_groups": user_group_list,
                "total_found": len(user_group_list),
                "include_count": include_count,
                "include_disabled": include_disabled,
                "include_users": include_users,
                "group_types": {
                    "active": len([g for g in user_group_list if g["is_active"]]),
                    "disabled": len([g for g in user_group_list if not g["is_active"]]),
                    "external": len([g for g in user_group_list if g["is_external"]]),
                    "internal": len([g for g in user_group_list if not g["is_external"]]),
                    "auto_configured": len([g for g in user_group_list if g["is_auto_type"]])
                },
                "workspace_info": "User groups for the Slack workspace",
                "pagination_note": "Results for large workspaces may be paginated"
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list user groups. The bot needs usergroups:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs usergroups:read scope to list user groups.",
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

@mcp.tool()
async def slack_list_user_reactions(
    user: str,
    count: int = 20,
    cursor: str = "",
    full: bool = False,
    limit: int = 20,
    page: int = 1
) -> dict:
    """
    Lists all reactions added by a specific user to messages, files, or file comments in slack, 
    useful for engagement analysis when the item content itself is not required.
    
    Args:
        user (str): User ID to get reactions for
        count (int): Number of items to return per page (default: 20)
        cursor (str): Pagination cursor for next page (default: "")
        full (bool): Whether to return full item information (default: False)
        limit (int): Maximum number of items to return (default: 20)
        page (int): Page number for pagination (default: 1)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_user_client()  # Uses user token for reactions
        
        # Prepare parameters for reactions.list
        params = {
            'user': user,
            'count': count,
            'full': full,
            'limit': limit,
            'page': page
        }
        
        # Add cursor if provided
        if cursor:
            params['cursor'] = cursor
        
        # Use the reactions.list method
        response = client.reactions_list(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_USER_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_USER_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to list user reactions. The user token needs reactions:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The user token needs reactions:read scope to list user reactions.",
                    "successful": False
                }
            elif error == 'user_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified user was not found.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list user reactions: {error}",
                    "successful": False
                }
        
        items = response.data.get("items", [])
        paging = response.data.get("paging", {})
        
        # Format reaction items
        reaction_list = []
        for item in items:
            item_info = {
                "type": item.get("type", ""),
                "channel": item.get("channel", ""),
                "message": item.get("message", {}),
                "file": item.get("file", {}),
                "comment": item.get("comment", {}),
                "reactions": item.get("reactions", []),
                "timestamp": item.get("ts", ""),
                "user": item.get("user", ""),
                "text": item.get("text", ""),
                "permalink": item.get("permalink", ""),
                "is_message": item.get("type") == "message",
                "is_file": item.get("type") == "file",
                "is_comment": item.get("type") == "file_comment",
                "has_reactions": len(item.get("reactions", [])) > 0,
                "reaction_count": len(item.get("reactions", [])),
                "item_id": item.get("ts", ""),
                "channel_id": item.get("channel", ""),
                "user_id": item.get("user", ""),
                "content": item.get("text", ""),
                "link": item.get("permalink", ""),
                "reaction_details": []
            }
            
            # Add reaction details
            for reaction in item.get("reactions", []):
                reaction_info = {
                    "name": reaction.get("name", ""),
                    "count": reaction.get("count", 0),
                    "users": reaction.get("users", []),
                    "emoji": reaction.get("name", ""),
                    "user_count": reaction.get("count", 0),
                    "user_list": reaction.get("users", []),
                    "is_user_reaction": user in reaction.get("users", [])
                }
                item_info["reaction_details"].append(reaction_info)
            
            # Add message-specific information
            if item.get("type") == "message":
                message = item.get("message", {})
                item_info.update({
                    "message_ts": message.get("ts", ""),
                    "message_text": message.get("text", ""),
                    "message_user": message.get("user", ""),
                    "message_type": message.get("type", ""),
                    "message_subtype": message.get("subtype", ""),
                    "message_thread_ts": message.get("thread_ts", ""),
                    "message_reply_count": message.get("reply_count", 0),
                    "message_reply_users": message.get("reply_users", []),
                    "message_reply_users_count": message.get("reply_users_count", 0),
                    "message_is_thread": bool(message.get("thread_ts")),
                    "message_has_replies": message.get("reply_count", 0) > 0
                })
            
            # Add file-specific information
            elif item.get("type") == "file":
                file_info = item.get("file", {})
                item_info.update({
                    "file_id": file_info.get("id", ""),
                    "file_name": file_info.get("name", ""),
                    "file_title": file_info.get("title", ""),
                    "file_type": file_info.get("filetype", ""),
                    "file_size": file_info.get("size", 0),
                    "file_url": file_info.get("url_private", ""),
                    "file_thumb": file_info.get("thumb_360", ""),
                    "file_user": file_info.get("user", ""),
                    "file_created": file_info.get("created", 0),
                    "file_updated": file_info.get("updated", 0),
                    "file_is_public": file_info.get("is_public", False),
                    "file_is_external": file_info.get("is_external", False)
                })
            
            # Add comment-specific information
            elif item.get("type") == "file_comment":
                comment = item.get("comment", {})
                item_info.update({
                    "comment_id": comment.get("id", ""),
                    "comment_text": comment.get("comment", ""),
                    "comment_user": comment.get("user", ""),
                    "comment_created": comment.get("created", 0),
                    "comment_updated": comment.get("updated", 0),
                    "comment_file_id": comment.get("file", {}).get("id", "") if comment.get("file") else ""
                })
            
            reaction_list.append(item_info)
        
        # Calculate statistics
        total_reactions = sum(len(item.get("reactions", [])) for item in items)
        reaction_types = {}
        for item in items:
            for reaction in item.get("reactions", []):
                name = reaction.get("name", "")
                if name in reaction_types:
                    reaction_types[name] += 1
                else:
                    reaction_types[name] = 1
        
        return {
            "data": {
                "items": reaction_list,
                "total_items": len(reaction_list),
                "total_reactions": total_reactions,
                "user_id": user,
                "pagination": {
                    "count": paging.get("count", 0),
                    "total": paging.get("total", 0),
                    "page": paging.get("page", 1),
                    "pages": paging.get("pages", 1),
                    "per_page": paging.get("per_page", 20)
                },
                "statistics": {
                    "total_reactions": total_reactions,
                    "average_reactions_per_item": total_reactions / len(items) if items else 0,
                    "reaction_types": reaction_types,
                    "unique_reaction_types": len(reaction_types),
                    "items_with_reactions": len([item for item in items if item.get("reactions")]),
                    "items_without_reactions": len([item for item in items if not item.get("reactions")])
                },
                "item_types": {
                    "messages": len([item for item in items if item.get("type") == "message"]),
                    "files": len([item for item in items if item.get("type") == "file"]),
                    "comments": len([item for item in items if item.get("type") == "file_comment"])
                },
                "parameters": {
                    "count": count,
                    "cursor": cursor,
                    "full": full,
                    "limit": limit,
                    "page": page
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list user reactions. The user token needs reactions:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The user token needs reactions:read scope to list user reactions.",
                "successful": False
            }
        elif error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified user was not found.",
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

@mcp.tool()
async def slack_list_user_reminders_with_details() -> dict:
    """
    Deprecated: lists all reminders with their details for the authenticated slack user. 
    use `list reminders` instead.
    
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_user_client()  # Uses user token for reminders
        
        # Use the reminders.list method
        response = client.reminders_list()
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_USER_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_USER_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to list reminders. The user token needs reminders:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The user token needs reminders:read scope to list reminders.",
                    "successful": False
                }
            elif error == 'not_allowed_token_type':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis action requires a user token (xoxp-) with reminders:read scope. Bot tokens (xoxb-) are not supported for reminders.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list reminders: {error}",
                    "successful": False
                }
        
        reminders = response.data.get("reminders", [])
        
        # Format reminder information
        reminder_list = []
        for reminder in reminders:
            reminder_info = {
                "id": reminder.get("id", ""),
                "creator": reminder.get("creator", ""),
                "user": reminder.get("user", ""),
                "text": reminder.get("text", ""),
                "recurring": reminder.get("recurring", False),
                "time": reminder.get("time", 0),
                "complete_ts": reminder.get("complete_ts", 0),
                "recurrence": reminder.get("recurrence", {}),
                "is_completed": reminder.get("complete_ts", 0) > 0,
                "is_recurring": reminder.get("recurring", False),
                "reminder_id": reminder.get("id", ""),
                "creator_id": reminder.get("creator", ""),
                "user_id": reminder.get("user", ""),
                "reminder_text": reminder.get("text", ""),
                "reminder_time": reminder.get("time", 0),
                "completion_timestamp": reminder.get("complete_ts", 0),
                "recurrence_info": reminder.get("recurrence", {}),
                "status": "completed" if reminder.get("complete_ts", 0) > 0 else "pending",
                "type": "recurring" if reminder.get("recurring", False) else "one-time",
                "created_timestamp": reminder.get("time", 0),
                "completed_timestamp": reminder.get("complete_ts", 0),
                "is_overdue": reminder.get("time", 0) < int(time.time()) and reminder.get("complete_ts", 0) == 0,
                "time_until_due": reminder.get("time", 0) - int(time.time()) if reminder.get("time", 0) > int(time.time()) else 0,
                "days_until_due": (reminder.get("time", 0) - int(time.time())) // 86400 if reminder.get("time", 0) > int(time.time()) else 0,
                "hours_until_due": (reminder.get("time", 0) - int(time.time())) // 3600 if reminder.get("time", 0) > int(time.time()) else 0,
                "minutes_until_due": (reminder.get("time", 0) - int(time.time())) // 60 if reminder.get("time", 0) > int(time.time()) else 0
            }
            
            # Add recurrence information if it's a recurring reminder
            if reminder.get("recurring", False) and reminder.get("recurrence"):
                recurrence = reminder.get("recurrence", {})
                reminder_info.update({
                    "recurrence_frequency": recurrence.get("frequency", ""),
                    "recurrence_interval": recurrence.get("interval", 1),
                    "recurrence_days": recurrence.get("days", []),
                    "recurrence_weekdays": recurrence.get("weekdays", []),
                    "recurrence_monthdays": recurrence.get("monthdays", []),
                    "recurrence_years": recurrence.get("years", []),
                    "recurrence_start_time": recurrence.get("start_time", 0),
                    "recurrence_end_time": recurrence.get("end_time", 0),
                    "recurrence_count": recurrence.get("count", 0),
                    "recurrence_until": recurrence.get("until", 0),
                    "recurrence_timezone": recurrence.get("timezone", ""),
                    "recurrence_weekday_names": recurrence.get("weekday_names", []),
                    "recurrence_month_names": recurrence.get("month_names", []),
                    "recurrence_year_names": recurrence.get("year_names", [])
                })
            
            reminder_list.append(reminder_info)
        
        # Sort reminders by time (earliest first)
        reminder_list.sort(key=lambda x: x["time"])
        
        # Calculate statistics
        total_reminders = len(reminder_list)
        completed_reminders = len([r for r in reminder_list if r["is_completed"]])
        pending_reminders = len([r for r in reminder_list if not r["is_completed"]])
        recurring_reminders = len([r for r in reminder_list if r["is_recurring"]])
        one_time_reminders = len([r for r in reminder_list if not r["is_recurring"]])
        overdue_reminders = len([r for r in reminder_list if r["is_overdue"]])
        
        return {
            "data": {
                "reminders": reminder_list,
                "total_reminders": total_reminders,
                "completed_reminders": completed_reminders,
                "pending_reminders": pending_reminders,
                "recurring_reminders": recurring_reminders,
                "one_time_reminders": one_time_reminders,
                "overdue_reminders": overdue_reminders,
                "statistics": {
                    "total": total_reminders,
                    "completed": completed_reminders,
                    "pending": pending_reminders,
                    "recurring": recurring_reminders,
                    "one_time": one_time_reminders,
                    "overdue": overdue_reminders,
                    "completion_rate": (completed_reminders / total_reminders * 100) if total_reminders > 0 else 0,
                    "recurring_rate": (recurring_reminders / total_reminders * 100) if total_reminders > 0 else 0,
                    "overdue_rate": (overdue_reminders / total_reminders * 100) if total_reminders > 0 else 0
                },
                "deprecation_notice": "This tool is deprecated. Use 'list reminders' instead.",
                "recommended_tool": "slack_list_reminders"
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list reminders. The user token needs reminders:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The user token needs reminders:read scope to list reminders.",
                "successful": False
            }
        elif error_code == 'not_allowed_token_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis action requires a user token (xoxp-) with reminders:read scope. Bot tokens (xoxb-) are not supported for reminders.",
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

@mcp.tool()
async def slack_list_admin_users(
    team_id: str,
    cursor: str = "",
    limit: int = 100
) -> dict:
    """
    Retrieves a paginated list of admin users for a specified slack workspace.
    
    Args:
        team_id (str): Team ID to get admin users for
        cursor (str): Pagination cursor for next page (default: "")
        limit (int): Maximum number of admin users to return (default: 100)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Prepare parameters for admin.users.list
        params = {
            'team_id': team_id,
            'limit': limit
        }
        
        # Add cursor if provided
        if cursor:
            params['cursor'] = cursor
        
        # Use the regular users.list method (admin API not available)
        response = client.users_list(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to list users. The bot needs users:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs users:read scope to list users.",
                    "successful": False
                }
            elif error == 'team_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified team was not found.",
                    "successful": False
                }
            elif error == 'not_allowed_token_type':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis action requires a bot token with users:read scope.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to list admin users: {error}",
                    "successful": False
                }
        
        users = response.data.get("users", [])
        response_metadata = response.data.get("response_metadata", {})
        
        # Format admin user information
        admin_user_list = []
        for user in users:
            user_info = {
                "id": user.get("id", ""),
                "team_id": user.get("team_id", ""),
                "name": user.get("name", ""),
                "deleted": user.get("deleted", False),
                "color": user.get("color", ""),
                "real_name": user.get("real_name", ""),
                "tz": user.get("tz", ""),
                "tz_label": user.get("tz_label", ""),
                "tz_offset": user.get("tz_offset", 0),
                "profile": user.get("profile", {}),
                "is_admin": user.get("is_admin", False),
                "is_owner": user.get("is_owner", False),
                "is_primary_owner": user.get("is_primary_owner", False),
                "is_restricted": user.get("is_restricted", False),
                "is_ultra_restricted": user.get("is_ultra_restricted", False),
                "is_bot": user.get("is_bot", False),
                "is_app_user": user.get("is_app_user", False),
                "updated": user.get("updated", 0),
                "is_email_confirmed": user.get("is_email_confirmed", False),
                "who_can_share_contact_card": user.get("who_can_share_contact_card", ""),
                "user_id": user.get("id", ""),
                "username": user.get("name", ""),
                "display_name": user.get("real_name", ""),
                "email": user.get("profile", {}).get("email", ""),
                "phone": user.get("profile", {}).get("phone", ""),
                "title": user.get("profile", {}).get("title", ""),
                "status_text": user.get("profile", {}).get("status_text", ""),
                "status_emoji": user.get("profile", {}).get("status_emoji", ""),
                "timezone": user.get("tz", ""),
                "timezone_label": user.get("tz_label", ""),
                "timezone_offset": user.get("tz_offset", 0),
                "last_updated": user.get("updated", 0),
                "admin_status": {
                    "is_admin": user.get("is_admin", False),
                    "is_owner": user.get("is_owner", False),
                    "is_primary_owner": user.get("is_primary_owner", False),
                    "is_restricted": user.get("is_restricted", False),
                    "is_ultra_restricted": user.get("is_ultra_restricted", False)
                },
                "user_type": {
                    "is_bot": user.get("is_bot", False),
                    "is_app_user": user.get("is_app_user", False),
                    "is_human": not user.get("is_bot", False) and not user.get("is_app_user", False)
                },
                "contact_info": {
                    "email": user.get("profile", {}).get("email", ""),
                    "phone": user.get("profile", {}).get("phone", ""),
                    "title": user.get("profile", {}).get("title", "")
                },
                "profile_info": {
                    "status_text": user.get("profile", {}).get("status_text", ""),
                    "status_emoji": user.get("profile", {}).get("status_emoji", ""),
                    "avatar_hash": user.get("profile", {}).get("avatar_hash", ""),
                    "image_24": user.get("profile", {}).get("image_24", ""),
                    "image_32": user.get("profile", {}).get("image_32", ""),
                    "image_48": user.get("profile", {}).get("image_48", ""),
                    "image_72": user.get("profile", {}).get("image_72", ""),
                    "image_192": user.get("profile", {}).get("image_192", ""),
                    "image_512": user.get("profile", {}).get("image_512", ""),
                    "image_1024": user.get("profile", {}).get("image_1024", "")
                }
            }
            
            # Add profile information
            profile = user.get("profile", {})
            if profile:
                user_info.update({
                    "profile_email": profile.get("email", ""),
                    "profile_phone": profile.get("phone", ""),
                    "profile_title": profile.get("title", ""),
                    "profile_status_text": profile.get("status_text", ""),
                    "profile_status_emoji": profile.get("status_emoji", ""),
                    "profile_avatar_hash": profile.get("avatar_hash", ""),
                    "profile_image_24": profile.get("image_24", ""),
                    "profile_image_32": profile.get("image_32", ""),
                    "profile_image_48": profile.get("image_48", ""),
                    "profile_image_72": profile.get("image_72", ""),
                    "profile_image_192": profile.get("image_192", ""),
                    "profile_image_512": profile.get("image_512", ""),
                    "profile_image_1024": profile.get("image_1024", ""),
                    "profile_first_name": profile.get("first_name", ""),
                    "profile_last_name": profile.get("last_name", ""),
                    "profile_display_name": profile.get("display_name", ""),
                    "profile_display_name_normalized": profile.get("display_name_normalized", ""),
                    "profile_real_name": profile.get("real_name", ""),
                    "profile_real_name_normalized": profile.get("real_name_normalized", ""),
                    "profile_skype": profile.get("skype", ""),
                    "profile_team": profile.get("team", "")
                })
            
            admin_user_list.append(user_info)
        
        # Sort admin users by name for consistent ordering
        admin_user_list.sort(key=lambda x: x["name"])
        
        # Calculate statistics
        total_users = len(admin_user_list)
        admin_users = len([u for u in admin_user_list if u["is_admin"]])
        owner_users = len([u for u in admin_user_list if u["is_owner"]])
        primary_owner_users = len([u for u in admin_user_list if u["is_primary_owner"]])
        restricted_users = len([u for u in admin_user_list if u["is_restricted"]])
        ultra_restricted_users = len([u for u in admin_user_list if u["is_ultra_restricted"]])
        bot_users = len([u for u in admin_user_list if u["is_bot"]])
        app_users = len([u for u in admin_user_list if u["is_app_user"]])
        human_users = len([u for u in admin_user_list if not u["is_bot"] and not u["is_app_user"]])
        
        return {
            "data": {
                "admin_users": admin_user_list,
                "total_users": total_users,
                "team_id": team_id,
                "pagination": {
                    "cursor": response_metadata.get("next_cursor", ""),
                    "has_more": bool(response_metadata.get("next_cursor")),
                    "limit": limit
                },
                "statistics": {
                    "total_users": total_users,
                    "admin_users": admin_users,
                    "owner_users": owner_users,
                    "primary_owner_users": primary_owner_users,
                    "restricted_users": restricted_users,
                    "ultra_restricted_users": ultra_restricted_users,
                    "bot_users": bot_users,
                    "app_users": app_users,
                    "human_users": human_users,
                    "admin_percentage": (admin_users / total_users * 100) if total_users > 0 else 0,
                    "owner_percentage": (owner_users / total_users * 100) if total_users > 0 else 0,
                    "restricted_percentage": (restricted_users / total_users * 100) if total_users > 0 else 0
                },
                "user_types": {
                    "admins": admin_users,
                    "owners": owner_users,
                    "primary_owners": primary_owner_users,
                    "restricted": restricted_users,
                    "ultra_restricted": ultra_restricted_users,
                    "bots": bot_users,
                    "apps": app_users,
                    "humans": human_users
                },
                "parameters": {
                    "team_id": team_id,
                    "cursor": cursor,
                    "limit": limit
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to list users. The bot needs users:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs users:read scope to list users.",
                "successful": False
            }
        elif error_code == 'team_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified team was not found.",
                "successful": False
            }
        elif error_code == 'not_allowed_token_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis action requires a bot token with users:read scope.",
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

@mcp.tool()
async def slack_set_user_presence(
    presence: str
) -> dict:
    """
    Manually sets a user's slack presence, overriding automatic detection; 
    this setting persists across connections but can be overridden by user actions 
    or slack's auto-away (e.g., after 10 mins of inactivity).
    
    Args:
        presence (str): Presence status to set ('auto' or 'away')
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_user_client()  # Uses user token for presence
        
        # Validate presence parameter
        if presence not in ['auto', 'away']:
            return {
                "data": {},
                "error": f"Invalid presence value: {presence}. Must be 'auto' or 'away'.",
                "successful": False
            }
        
        # Use the users.setPresence method
        response = client.users_setPresence(presence=presence)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_USER_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_USER_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to set presence. The user token needs users:write scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The user token needs users:write scope to set presence.",
                    "successful": False
                }
            elif error == 'not_allowed_token_type':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis action requires a user token (xoxp-) with users:write scope. Bot tokens (xoxb-) are not supported for setting presence.",
                    "successful": False
                }
            elif error == 'invalid_presence':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid presence value. Must be 'auto' or 'away'.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to set presence: {error}",
                    "successful": False
                }
        
        return {
            "data": {
                "presence": presence,
                "status": "success",
                "message": f"Presence successfully set to '{presence}'",
                "presence_info": {
                    "current_presence": presence,
                    "presence_type": "manual" if presence == "away" else "automatic",
                    "description": "Manual presence setting" if presence == "away" else "Automatic presence detection",
                    "persistence": "This setting persists across connections",
                    "override_note": "Can be overridden by user actions or Slack's auto-away (after 10 mins of inactivity)",
                    "auto_away_time": "10 minutes of inactivity" if presence == "auto" else "N/A"
                },
                "api_response": response.data
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to set presence. The user token needs users:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The user token needs users:write scope to set presence.",
                "successful": False
            }
        elif error_code == 'not_allowed_token_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis action requires a user token (xoxp-) with users:write scope. Bot tokens (xoxb-) are not supported for setting presence.",
                "successful": False
            }
        elif error_code == 'invalid_presence':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid presence value. Must be 'auto' or 'away'.",
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

@mcp.tool()
async def slack_mark_reminder_as_complete(
    reminder: str
) -> dict:
    """
    Marks a specific slack reminder as complete using its `reminder` id; 
    **deprecated**: this slack api endpoint ('reminders.complete') was deprecated in march 2023 and is not recommended for new applications.
    
    Args:
        reminder (str): Reminder ID to mark as complete
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_user_client()  # Uses user token for reminders
        
        # Use the reminders.complete method (deprecated)
        response = client.reminders_complete(reminder=reminder)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_USER_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_USER_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to complete reminders. The user token needs reminders:write scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The user token needs reminders:write scope to complete reminders.",
                    "successful": False
                }
            elif error == 'not_allowed_token_type':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis action requires a user token (xoxp-) with reminders:write scope. Bot tokens (xoxb-) are not supported for reminders.",
                    "successful": False
                }
            elif error == 'reminder_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified reminder was not found or you don't have permission to access it.",
                    "successful": False
                }
            elif error == 'already_completed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe reminder is already marked as complete.",
                    "successful": False
                }
            elif error == 'api_deprecated':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis API endpoint has been deprecated and is no longer supported.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to complete reminder: {error}",
                    "successful": False
                }
        
        return {
            "data": {
                "reminder_id": reminder,
                "status": "completed",
                "message": f"Reminder '{reminder}' successfully marked as complete",
                "completion_info": {
                    "reminder_id": reminder,
                    "completion_status": "completed",
                    "completion_timestamp": int(time.time()),
                    "completion_date": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                    "deprecation_warning": "This API endpoint was deprecated in March 2023",
                    "recommendation": "Consider using alternative reminder management methods"
                },
                "deprecation_notice": {
                    "deprecated": True,
                    "deprecation_date": "March 2023",
                    "api_endpoint": "reminders.complete",
                    "status": "not_recommended",
                    "warning": "This API endpoint is deprecated and not recommended for new applications",
                    "alternative": "Consider using other reminder management approaches"
                },
                "api_response": response.data
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to complete reminders. The user token needs reminders:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The user token needs reminders:write scope to complete reminders.",
                "successful": False
            }
        elif error_code == 'not_allowed_token_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis action requires a user token (xoxp-) with reminders:write scope. Bot tokens (xoxb-) are not supported for reminders.",
                "successful": False
            }
        elif error_code == 'reminder_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified reminder was not found or you don't have permission to access it.",
                "successful": False
            }
        elif error_code == 'already_completed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe reminder is already marked as complete.",
                "successful": False
            }
        elif error_code == 'api_deprecated':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis API endpoint has been deprecated and is no longer supported.",
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

@mcp.tool()
async def slack_open_dm(
    channel: str = "",
    return_im: bool = False,
    users: str = ""
) -> dict:
    """
    Opens or resumes a slack direct message (dm) or multi-person direct message (mpim) 
    by providing either user ids or an existing channel id.
    
    Args:
        channel (str): Channel ID to open (optional)
        return_im (bool): Whether to return IM channel information (default: False)
        users (str): Comma-separated list of user IDs for MPIM (optional)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Prepare parameters for conversations.open
        params = {}
        
        # Add channel if provided
        if channel:
            params['channel'] = channel
        
        # Add return_im parameter
        if return_im:
            params['return_im'] = return_im
        
        # Add users if provided (for MPIM)
        if users:
            # Split users string into list
            user_list = [user.strip() for user in users.split(',') if user.strip()]
            params['users'] = user_list
        
        # Use the conversations.open method
        response = client.conversations_open(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to open conversations. The bot needs im:write and mpim:write scopes.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs im:write and mpim:write scopes to open conversations.",
                    "successful": False
                }
            elif error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified channel was not found.",
                    "successful": False
                }
            elif error == 'user_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nOne or more specified users were not found.",
                    "successful": False
                }
            elif error == 'invalid_users':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid user IDs provided.",
                    "successful": False
                }
            elif error == 'too_many_users':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nToo many users specified for MPIM. Maximum is 8 users.",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe bot is not a member of the specified channel.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to open conversation: {error}",
                    "successful": False
                }
        
        channel_info = response.data.get("channel", {})
        no_op = response.data.get("no_op", False)
        already_open = response.data.get("already_open", False)
        
        # Format channel information
        channel_data = {
            "id": channel_info.get("id", ""),
            "name": channel_info.get("name", ""),
            "is_channel": channel_info.get("is_channel", False),
            "is_group": channel_info.get("is_group", False),
            "is_im": channel_info.get("is_im", False),
            "is_mpim": channel_info.get("is_mpim", False),
            "is_private": channel_info.get("is_private", False),
            "is_archived": channel_info.get("is_archived", False),
            "is_general": channel_info.get("is_general", False),
            "is_member": channel_info.get("is_member", False),
            "is_muted": channel_info.get("is_muted", False),
            "is_open": channel_info.get("is_open", False),
            "created": channel_info.get("created", 0),
            "creator": channel_info.get("creator", ""),
            "num_members": channel_info.get("num_members", 0),
            "topic": channel_info.get("topic", {}),
            "purpose": channel_info.get("purpose", {}),
            "previous_names": channel_info.get("previous_names", []),
            "priority": channel_info.get("priority", 0),
            "channel_type": "channel" if channel_info.get("is_channel") else "group" if channel_info.get("is_group") else "im" if channel_info.get("is_im") else "mpim" if channel_info.get("is_mpim") else "unknown",
            "conversation_type": {
                "is_dm": channel_info.get("is_im", False),
                "is_group_dm": channel_info.get("is_mpim", False),
                "is_public_channel": channel_info.get("is_channel", False) and not channel_info.get("is_private", False),
                "is_private_channel": channel_info.get("is_group", False) or (channel_info.get("is_channel", False) and channel_info.get("is_private", False))
            },
            "membership_info": {
                "is_member": channel_info.get("is_member", False),
                "is_muted": channel_info.get("is_muted", False),
                "is_open": channel_info.get("is_open", False),
                "num_members": channel_info.get("num_members", 0)
            },
            "metadata": {
                "created": channel_info.get("created", 0),
                "creator": channel_info.get("creator", ""),
                "is_archived": channel_info.get("is_archived", False),
                "is_general": channel_info.get("is_general", False),
                "previous_names": channel_info.get("previous_names", [])
            }
        }
        
        # Add topic and purpose information
        if channel_info.get("topic"):
            topic = channel_info.get("topic", {})
            channel_data["topic_info"] = {
                "value": topic.get("value", ""),
                "creator": topic.get("creator", ""),
                "last_set": topic.get("last_set", 0)
            }
        
        if channel_info.get("purpose"):
            purpose = channel_info.get("purpose", {})
            channel_data["purpose_info"] = {
                "value": purpose.get("value", ""),
                "creator": purpose.get("creator", ""),
                "last_set": purpose.get("last_set", 0)
            }
        
        return {
            "data": {
                "channel": channel_data,
                "no_op": no_op,
                "already_open": already_open,
                "status": "opened" if not no_op else "no_change",
                "message": "Conversation opened successfully" if not no_op else "Conversation was already open",
                "conversation_info": {
                    "channel_id": channel_info.get("id", ""),
                    "channel_name": channel_info.get("name", ""),
                    "channel_type": channel_data["channel_type"],
                    "is_dm": channel_info.get("is_im", False),
                    "is_group_dm": channel_info.get("is_mpim", False),
                    "is_public_channel": channel_info.get("is_channel", False) and not channel_info.get("is_private", False),
                    "is_private_channel": channel_info.get("is_group", False) or (channel_info.get("is_channel", False) and channel_info.get("is_private", False)),
                    "is_member": channel_info.get("is_member", False),
                    "is_open": channel_info.get("is_open", False),
                    "num_members": channel_info.get("num_members", 0)
                },
                "parameters": {
                    "channel": channel,
                    "return_im": return_im,
                    "users": users
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to open conversations. The bot needs im:write and mpim:write scopes.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs im:write and mpim:write scopes to open conversations.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified channel was not found.",
                "successful": False
            }
        elif error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more specified users were not found.",
                "successful": False
            }
        elif error_code == 'invalid_users':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid user IDs provided.",
                "successful": False
            }
        elif error_code == 'too_many_users':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nToo many users specified for MPIM. Maximum is 8 users.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of the specified channel.",
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

@mcp.tool()
async def slack_open_or_resume_direct_or_multi_person_messages(
    channel: str = "",
    return_im: bool = False,
    users: str = ""
) -> dict:
    """
    Deprecated: opens or resumes a slack direct message (dm) or multi-person direct message (mpim). 
    use `open dm` instead.
    
    Args:
        channel (str): Channel ID to open (optional)
        return_im (bool): Whether to return IM channel information (default: False)
        users (str): Comma-separated list of user IDs for MPIM (optional)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Prepare parameters for conversations.open
        params = {}
        
        # Add channel if provided
        if channel:
            params['channel'] = channel
        
        # Add return_im parameter
        if return_im:
            params['return_im'] = return_im
        
        # Add users if provided (for MPIM)
        if users:
            # Split users string into list
            user_list = [user.strip() for user in users.split(',') if user.strip()]
            params['users'] = user_list
        
        # Use the conversations.open method
        response = client.conversations_open(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to open conversations. The bot needs im:write and mpim:write scopes.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs im:write and mpim:write scopes to open conversations.",
                    "successful": False
                }
            elif error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified channel was not found.",
                    "successful": False
                }
            elif error == 'user_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nOne or more specified users were not found.",
                    "successful": False
                }
            elif error == 'invalid_users':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid user IDs provided.",
                    "successful": False
                }
            elif error == 'too_many_users':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nToo many users specified for MPIM. Maximum is 8 users.",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe bot is not a member of the specified channel.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to open conversation: {error}",
                    "successful": False
                }
        
        channel_info = response.data.get("channel", {})
        no_op = response.data.get("no_op", False)
        already_open = response.data.get("already_open", False)
        
        # Format channel information
        channel_data = {
            "id": channel_info.get("id", ""),
            "name": channel_info.get("name", ""),
            "is_channel": channel_info.get("is_channel", False),
            "is_group": channel_info.get("is_group", False),
            "is_im": channel_info.get("is_im", False),
            "is_mpim": channel_info.get("is_mpim", False),
            "is_private": channel_info.get("is_private", False),
            "is_archived": channel_info.get("is_archived", False),
            "is_general": channel_info.get("is_general", False),
            "is_member": channel_info.get("is_member", False),
            "is_muted": channel_info.get("is_muted", False),
            "is_open": channel_info.get("is_open", False),
            "created": channel_info.get("created", 0),
            "creator": channel_info.get("creator", ""),
            "num_members": channel_info.get("num_members", 0),
            "topic": channel_info.get("topic", {}),
            "purpose": channel_info.get("purpose", {}),
            "previous_names": channel_info.get("previous_names", []),
            "priority": channel_info.get("priority", 0),
            "channel_type": "channel" if channel_info.get("is_channel") else "group" if channel_info.get("is_group") else "im" if channel_info.get("is_im") else "mpim" if channel_info.get("is_mpim") else "unknown",
            "conversation_type": {
                "is_dm": channel_info.get("is_im", False),
                "is_group_dm": channel_info.get("is_mpim", False),
                "is_public_channel": channel_info.get("is_channel", False) and not channel_info.get("is_private", False),
                "is_private_channel": channel_info.get("is_group", False) or (channel_info.get("is_channel", False) and channel_info.get("is_private", False))
            },
            "membership_info": {
                "is_member": channel_info.get("is_member", False),
                "is_muted": channel_info.get("is_muted", False),
                "is_open": channel_info.get("is_open", False),
                "num_members": channel_info.get("num_members", 0)
            },
            "metadata": {
                "created": channel_info.get("created", 0),
                "creator": channel_info.get("creator", ""),
                "is_archived": channel_info.get("is_archived", False),
                "is_general": channel_info.get("is_general", False),
                "previous_names": channel_info.get("previous_names", [])
            }
        }
        
        # Add topic and purpose information
        if channel_info.get("topic"):
            topic = channel_info.get("topic", {})
            channel_data["topic_info"] = {
                "value": topic.get("value", ""),
                "creator": topic.get("creator", ""),
                "last_set": topic.get("last_set", 0)
            }
        
        if channel_info.get("purpose"):
            purpose = channel_info.get("purpose", {})
            channel_data["purpose_info"] = {
                "value": purpose.get("value", ""),
                "creator": purpose.get("creator", ""),
                "last_set": purpose.get("last_set", 0)
            }
        
        return {
            "data": {
                "channel": channel_data,
                "no_op": no_op,
                "already_open": already_open,
                "status": "opened" if not no_op else "no_change",
                "message": "Conversation opened successfully" if not no_op else "Conversation was already open",
                "deprecation_notice": {
                    "deprecated": True,
                    "status": "not_recommended",
                    "warning": "This tool is deprecated. Use 'open dm' instead.",
                    "recommended_tool": "slack_open_dm",
                    "alternative": "Use the newer 'open dm' tool for better functionality"
                },
                "conversation_info": {
                    "channel_id": channel_info.get("id", ""),
                    "channel_name": channel_info.get("name", ""),
                    "channel_type": channel_data["channel_type"],
                    "is_dm": channel_info.get("is_im", False),
                    "is_group_dm": channel_info.get("is_mpim", False),
                    "is_public_channel": channel_info.get("is_channel", False) and not channel_info.get("is_private", False),
                    "is_private_channel": channel_info.get("is_group", False) or (channel_info.get("is_channel", False) and channel_info.get("is_private", False)),
                    "is_member": channel_info.get("is_member", False),
                    "is_open": channel_info.get("is_open", False),
                    "num_members": channel_info.get("num_members", 0)
                },
                "parameters": {
                    "channel": channel,
                    "return_im": return_im,
                    "users": users
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to open conversations. The bot needs im:write and mpim:write scopes.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs im:write and mpim:write scopes to open conversations.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified channel was not found.",
                "successful": False
            }
        elif error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more specified users were not found.",
                "successful": False
            }
        elif error_code == 'invalid_users':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid user IDs provided.",
                "successful": False
            }
        elif error_code == 'too_many_users':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nToo many users specified for MPIM. Maximum is 8 users.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of the specified channel.",
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

@mcp.tool()
async def slack_pins_an_item_to_a_channel(
    channel: str,
    timestamp: str
) -> dict:
    """
    Pins a message to a specified slack channel; the message must not already be pinned.
    
    Args:
        channel (str): Channel ID where the message is located
        timestamp (str): Timestamp of the message to pin
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the pins.add method to pin the message
        response = client.pins_add(channel=channel, timestamp=timestamp)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to pin messages. The bot needs pins:write scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs pins:write scope to pin messages.",
                    "successful": False
                }
            elif error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified channel was not found.",
                    "successful": False
                }
            elif error == 'message_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified message was not found in the channel.",
                    "successful": False
                }
            elif error == 'already_pinned':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe message is already pinned to the channel.",
                    "successful": False
                }
            elif error == 'cant_pin_message':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nCannot pin this message. The message may be from a bot or system message.",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe bot is not a member of the specified channel.",
                    "successful": False
                }
            elif error == 'invalid_timestamp':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid timestamp format. Please provide a valid timestamp.",
                    "successful": False
                }
            elif error == 'too_many_pins':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nToo many pins in this channel. Remove some pins before adding new ones.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to pin message: {error}",
                    "successful": False
                }
        
        # Get the pinned message details
        pinned_item = response.data.get("item", {})
        
        # Format the pinned item information
        pinned_data = {
            "type": pinned_item.get("type", ""),
            "channel": pinned_item.get("channel", ""),
            "message": pinned_item.get("message", {}),
            "file": pinned_item.get("file", {}),
            "comment": pinned_item.get("comment", {}),
            "pinned_by": pinned_item.get("pinned_by", ""),
            "pinned_at": pinned_item.get("pinned_at", 0),
            "item_type": pinned_item.get("type", "unknown"),
            "is_pinned": True
        }
        
        # Add message details if available
        if pinned_item.get("message"):
            message = pinned_item.get("message", {})
            pinned_data["message_details"] = {
                "text": message.get("text", ""),
                "user": message.get("user", ""),
                "ts": message.get("ts", ""),
                "type": message.get("type", ""),
                "subtype": message.get("subtype", ""),
                "attachments": message.get("attachments", []),
                "blocks": message.get("blocks", []),
                "reactions": message.get("reactions", []),
                "thread_ts": message.get("thread_ts", ""),
                "reply_count": message.get("reply_count", 0),
                "reply_users_count": message.get("reply_users_count", 0),
                "latest_reply": message.get("latest_reply", ""),
                "is_starred": message.get("is_starred", False),
                "pinned_to": message.get("pinned_to", []),
                "permalink": message.get("permalink", "")
            }
        
        # Add file details if available
        if pinned_item.get("file"):
            file_info = pinned_item.get("file", {})
            pinned_data["file_details"] = {
                "id": file_info.get("id", ""),
                "name": file_info.get("name", ""),
                "title": file_info.get("title", ""),
                "mimetype": file_info.get("mimetype", ""),
                "filetype": file_info.get("filetype", ""),
                "pretty_type": file_info.get("pretty_type", ""),
                "size": file_info.get("size", 0),
                "url_private": file_info.get("url_private", ""),
                "url_private_download": file_info.get("url_private_download", ""),
                "thumb_360": file_info.get("thumb_360", ""),
                "thumb_360_w": file_info.get("thumb_360_w", 0),
                "thumb_360_h": file_info.get("thumb_360_h", 0),
                "permalink": file_info.get("permalink", ""),
                "permalink_public": file_info.get("permalink_public", ""),
                "is_external": file_info.get("is_external", False),
                "is_public": file_info.get("is_public", False),
                "is_starred": file_info.get("is_starred", False),
                "is_tombstoned": file_info.get("is_tombstoned", False),
                "created": file_info.get("created", 0),
                "timestamp": file_info.get("timestamp", 0),
                "user": file_info.get("user", ""),
                "username": file_info.get("username", ""),
                "mode": file_info.get("mode", ""),
                "editable": file_info.get("editable", False),
                "is_external": file_info.get("is_external", False),
                "external_type": file_info.get("external_type", ""),
                "external_id": file_info.get("external_id", ""),
                "external_url": file_info.get("external_url", ""),
                "has_rich_preview": file_info.get("has_rich_preview", False)
            }
        
        return {
            "data": {
                "pinned_item": pinned_data,
                "channel_id": channel,
                "timestamp": timestamp,
                "pinned_by": pinned_item.get("pinned_by", ""),
                "pinned_at": pinned_item.get("pinned_at", 0),
                "item_type": pinned_item.get("type", "unknown"),
                "status": "pinned",
                "message": "Message pinned successfully",
                "pin_details": {
                    "channel": channel,
                    "timestamp": timestamp,
                    "pinned_by": pinned_item.get("pinned_by", ""),
                    "pinned_at": pinned_item.get("pinned_at", 0),
                    "item_type": pinned_item.get("type", "unknown"),
                    "is_pinned": True
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to pin messages. The bot needs pins:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs pins:write scope to pin messages.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified channel was not found.",
                "successful": False
            }
        elif error_code == 'message_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified message was not found in the channel.",
                "successful": False
            }
        elif error_code == 'already_pinned':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe message is already pinned to the channel.",
                "successful": False
            }
        elif error_code == 'cant_pin_message':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nCannot pin this message. The message may be from a bot or system message.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of the specified channel.",
                "successful": False
            }
        elif error_code == 'invalid_timestamp':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid timestamp format. Please provide a valid timestamp.",
                "successful": False
            }
        elif error_code == 'too_many_pins':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nToo many pins in this channel. Remove some pins before adding new ones.",
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

@mcp.tool()
async def slack_register_call_participants_removal(
    id: str,
    users: str
) -> dict:
    """
    Deprecated: registers participants removed from a slack call. 
    use `remove call participants` instead.
    
    Args:
        id (str): Call ID to remove participants from
        users (str): Comma-separated list of user IDs to remove from the call
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Parse users parameter
        user_list = [user.strip() for user in users.split(',') if user.strip()]
        
        # Use the calls.participants.remove method
        response = client.calls_participants_remove(id=id, users=user_list)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to remove call participants. The bot needs calls:write scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs calls:write scope to remove call participants.",
                    "successful": False
                }
            elif error == 'call_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified call was not found.",
                    "successful": False
                }
            elif error == 'invalid_call_id':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid call ID provided.",
                    "successful": False
                }
            elif error == 'user_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nOne or more specified users were not found.",
                    "successful": False
                }
            elif error == 'invalid_users':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid user IDs provided.",
                    "successful": False
                }
            elif error == 'not_in_call':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nOne or more users are not participants in the call.",
                    "successful": False
                }
            elif error == 'call_ended':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe call has already ended.",
                    "successful": False
                }
            elif error == 'insufficient_permissions':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to remove participants from this call.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to remove call participants: {error}",
                    "successful": False
                }
        
        # Get the call information
        call_info = response.data.get("call", {})
        
        # Format the call information
        call_data = {
            "id": call_info.get("id", ""),
            "date_start": call_info.get("date_start", 0),
            "external_unique_id": call_info.get("external_unique_id", ""),
            "join_url": call_info.get("join_url", ""),
            "desktop_app_join_url": call_info.get("desktop_app_join_url", ""),
            "external_display_id": call_info.get("external_display_id", ""),
            "title": call_info.get("title", ""),
            "created_by": call_info.get("created_by", ""),
            "date_end": call_info.get("date_end", 0),
            "channels": call_info.get("channels", []),
            "was_desktop_app_switching_enabled": call_info.get("was_desktop_app_switching_enabled", False),
            "was_join_url_shared": call_info.get("was_join_url_shared", False),
            "was_created_by_meeting_plugin": call_info.get("was_created_by_meeting_plugin", False),
            "was_ended": call_info.get("was_ended", False),
            "participants": call_info.get("participants", []),
            "participants_count": call_info.get("participants_count", 0),
            "participants_removed": user_list,
            "participants_removed_count": len(user_list),
            "call_status": "active" if not call_info.get("was_ended", False) else "ended",
            "call_type": "slack_call"
        }
        
        # Format participants information
        participants_data = []
        for participant in call_info.get("participants", []):
            participant_info = {
                "external_id": participant.get("external_id", ""),
                "avatar_url": participant.get("avatar_url", ""),
                "display_name": participant.get("display_name", ""),
                "slack_id": participant.get("slack_id", ""),
                "is_removed": participant.get("is_removed", False),
                "was_removed": participant.get("was_removed", False)
            }
            participants_data.append(participant_info)
        
        return {
            "data": {
                "call": call_data,
                "participants": participants_data,
                "call_id": id,
                "users_removed": user_list,
                "users_removed_count": len(user_list),
                "status": "participants_removed",
                "message": "Call participants removed successfully",
                "deprecation_notice": {
                    "deprecated": True,
                    "status": "not_recommended",
                    "warning": "This tool is deprecated. Use 'remove call participants' instead.",
                    "recommended_tool": "slack_remove_call_participants",
                    "alternative": "Use the newer 'remove call participants' tool for better functionality"
                },
                "call_info": {
                    "call_id": id,
                    "title": call_info.get("title", ""),
                    "created_by": call_info.get("created_by", ""),
                    "date_start": call_info.get("date_start", 0),
                    "date_end": call_info.get("date_end", 0),
                    "was_ended": call_info.get("was_ended", False),
                    "participants_count": call_info.get("participants_count", 0),
                    "participants_removed": user_list,
                    "participants_removed_count": len(user_list)
                },
                "removal_details": {
                    "call_id": id,
                    "users_removed": user_list,
                    "users_removed_count": len(user_list),
                    "removal_successful": True,
                    "remaining_participants": call_info.get("participants_count", 0) - len(user_list)
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to remove call participants. The bot needs calls:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs calls:write scope to remove call participants.",
                "successful": False
            }
        elif error_code == 'call_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified call was not found.",
                "successful": False
            }
        elif error_code == 'invalid_call_id':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid call ID provided.",
                "successful": False
            }
        elif error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more specified users were not found.",
                "successful": False
            }
        elif error_code == 'invalid_users':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid user IDs provided.",
                "successful": False
            }
        elif error_code == 'not_in_call':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more users are not participants in the call.",
                "successful": False
            }
        elif error_code == 'call_ended':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe call has already ended.",
                "successful": False
            }
        elif error_code == 'insufficient_permissions':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to remove participants from this call.",
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

@mcp.tool()
async def slack_registers_a_new_call_with_participants(
    external_unique_id: str,
    join_url: str,
    created_by: str = "",
    date_start: int = 0,
    desktop_app_join_url: str = "",
    external_display_id: str = "",
    title: str = "",
    users: str = ""
) -> dict:
    """
    Deprecated: registers a new call in slack using `calls.add` for third-party call integration. 
    use `start call` instead.
    
    Args:
        external_unique_id (str): External unique ID for the call (required)
        join_url (str): Join URL for the call (required)
        created_by (str): User ID who created the call (optional)
        date_start (int): Call start timestamp (optional)
        desktop_app_join_url (str): Desktop app join URL (optional)
        external_display_id (str): External display ID (optional)
        title (str): Call title (optional)
        users (str): Comma-separated list of user IDs to add to the call (optional)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Prepare parameters for calls.add
        params = {
            'external_unique_id': external_unique_id,
            'join_url': join_url
        }
        
        # Add optional parameters if provided
        if created_by:
            params['created_by'] = created_by
        if date_start:
            params['date_start'] = date_start
        if desktop_app_join_url:
            params['desktop_app_join_url'] = desktop_app_join_url
        if external_display_id:
            params['external_display_id'] = external_display_id
        if title:
            params['title'] = title
        if users:
            # Parse users parameter
            user_list = [user.strip() for user in users.split(',') if user.strip()]
            params['users'] = user_list
        
        # Use the calls.add method
        response = client.calls_add(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to create calls. The bot needs calls:write scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs calls:write scope to create calls.",
                    "successful": False
                }
            elif error == 'invalid_external_unique_id':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid external unique ID provided.",
                    "successful": False
                }
            elif error == 'external_unique_id_already_exists':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nA call with this external unique ID already exists.",
                    "successful": False
                }
            elif error == 'invalid_join_url':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid join URL provided.",
                    "successful": False
                }
            elif error == 'invalid_desktop_app_join_url':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid desktop app join URL provided.",
                    "successful": False
                }
            elif error == 'invalid_date_start':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid date start timestamp provided.",
                    "successful": False
                }
            elif error == 'user_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nOne or more specified users were not found.",
                    "successful": False
                }
            elif error == 'invalid_users':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid user IDs provided.",
                    "successful": False
                }
            elif error == 'too_many_users':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nToo many users specified for the call.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to create call: {error}",
                    "successful": False
                }
        
        # Get the call information
        call_info = response.data.get("call", {})
        
        # Format the call information
        call_data = {
            "id": call_info.get("id", ""),
            "date_start": call_info.get("date_start", 0),
            "external_unique_id": call_info.get("external_unique_id", ""),
            "join_url": call_info.get("join_url", ""),
            "desktop_app_join_url": call_info.get("desktop_app_join_url", ""),
            "external_display_id": call_info.get("external_display_id", ""),
            "title": call_info.get("title", ""),
            "created_by": call_info.get("created_by", ""),
            "date_end": call_info.get("date_end", 0),
            "channels": call_info.get("channels", []),
            "was_desktop_app_switching_enabled": call_info.get("was_desktop_app_switching_enabled", False),
            "was_join_url_shared": call_info.get("was_join_url_shared", False),
            "was_created_by_meeting_plugin": call_info.get("was_created_by_meeting_plugin", False),
            "was_ended": call_info.get("was_ended", False),
            "participants": call_info.get("participants", []),
            "participants_count": call_info.get("participants_count", 0),
            "call_status": "active" if not call_info.get("was_ended", False) else "ended",
            "call_type": "third_party_call"
        }
        
        # Format participants information
        participants_data = []
        for participant in call_info.get("participants", []):
            participant_info = {
                "external_id": participant.get("external_id", ""),
                "avatar_url": participant.get("avatar_url", ""),
                "display_name": participant.get("display_name", ""),
                "slack_id": participant.get("slack_id", ""),
                "is_removed": participant.get("is_removed", False),
                "was_removed": participant.get("was_removed", False)
            }
            participants_data.append(participant_info)
        
        return {
            "data": {
                "call": call_data,
                "participants": participants_data,
                "call_id": call_info.get("id", ""),
                "external_unique_id": external_unique_id,
                "join_url": join_url,
                "status": "call_created",
                "message": "Call created successfully",
                "deprecation_notice": {
                    "deprecated": True,
                    "status": "not_recommended",
                    "warning": "This tool is deprecated. Use 'start call' instead.",
                    "recommended_tool": "slack_start_call",
                    "alternative": "Use the newer 'start call' tool for better functionality"
                },
                "call_info": {
                    "call_id": call_info.get("id", ""),
                    "external_unique_id": external_unique_id,
                    "join_url": join_url,
                    "title": call_info.get("title", ""),
                    "created_by": call_info.get("created_by", ""),
                    "date_start": call_info.get("date_start", 0),
                    "participants_count": call_info.get("participants_count", 0),
                    "call_status": "active" if not call_info.get("was_ended", False) else "ended"
                },
                "creation_details": {
                    "external_unique_id": external_unique_id,
                    "join_url": join_url,
                    "created_by": created_by,
                    "date_start": date_start,
                    "desktop_app_join_url": desktop_app_join_url,
                    "external_display_id": external_display_id,
                    "title": title,
                    "users": users,
                    "creation_successful": True
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to create calls. The bot needs calls:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs calls:write scope to create calls.",
                "successful": False
            }
        elif error_code == 'invalid_external_unique_id':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid external unique ID provided.",
                "successful": False
            }
        elif error_code == 'external_unique_id_already_exists':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nA call with this external unique ID already exists.",
                "successful": False
            }
        elif error_code == 'invalid_join_url':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid join URL provided.",
                "successful": False
            }
        elif error_code == 'invalid_desktop_app_join_url':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid desktop app join URL provided.",
                "successful": False
            }
        elif error_code == 'invalid_date_start':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid date start timestamp provided.",
                "successful": False
            }
        elif error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more specified users were not found.",
                "successful": False
            }
        elif error_code == 'invalid_users':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid user IDs provided.",
                "successful": False
            }
        elif error_code == 'too_many_users':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nToo many users specified for the call.",
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

@mcp.tool()
async def slack_registers_new_call_participants(
    id: str,
    users: str
) -> dict:
    """
    Deprecated: registers new participants added to a slack call. 
    use `add call participants` instead.
    
    Args:
        id (str): Call ID to add participants to
        users (str): Comma-separated list of user IDs to add to the call
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Parse users parameter
        user_list = [user.strip() for user in users.split(',') if user.strip()]
        
        # Use the calls.participants.add method
        response = client.calls_participants_add(id=id, users=user_list)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to add call participants. The bot needs calls:write scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs calls:write scope to add call participants.",
                    "successful": False
                }
            elif error == 'call_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified call was not found.",
                    "successful": False
                }
            elif error == 'invalid_call_id':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid call ID provided.",
                    "successful": False
                }
            elif error == 'user_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nOne or more specified users were not found.",
                    "successful": False
                }
            elif error == 'invalid_users':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid user IDs provided.",
                    "successful": False
                }
            elif error == 'already_in_call':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nOne or more users are already participants in the call.",
                    "successful": False
                }
            elif error == 'call_ended':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe call has already ended.",
                    "successful": False
                }
            elif error == 'too_many_participants':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nToo many participants in the call. Cannot add more users.",
                    "successful": False
                }
            elif error == 'insufficient_permissions':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to add participants to this call.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to add call participants: {error}",
                    "successful": False
                }
        
        # Get the call information
        call_info = response.data.get("call", {})
        
        # Format the call information
        call_data = {
            "id": call_info.get("id", ""),
            "date_start": call_info.get("date_start", 0),
            "external_unique_id": call_info.get("external_unique_id", ""),
            "join_url": call_info.get("join_url", ""),
            "desktop_app_join_url": call_info.get("desktop_app_join_url", ""),
            "external_display_id": call_info.get("external_display_id", ""),
            "title": call_info.get("title", ""),
            "created_by": call_info.get("created_by", ""),
            "date_end": call_info.get("date_end", 0),
            "channels": call_info.get("channels", []),
            "was_desktop_app_switching_enabled": call_info.get("was_desktop_app_switching_enabled", False),
            "was_join_url_shared": call_info.get("was_join_url_shared", False),
            "was_created_by_meeting_plugin": call_info.get("was_created_by_meeting_plugin", False),
            "was_ended": call_info.get("was_ended", False),
            "participants": call_info.get("participants", []),
            "participants_count": call_info.get("participants_count", 0),
            "participants_added": user_list,
            "participants_added_count": len(user_list),
            "call_status": "active" if not call_info.get("was_ended", False) else "ended",
            "call_type": "slack_call"
        }
        
        # Format participants information
        participants_data = []
        for participant in call_info.get("participants", []):
            participant_info = {
                "external_id": participant.get("external_id", ""),
                "avatar_url": participant.get("avatar_url", ""),
                "display_name": participant.get("display_name", ""),
                "slack_id": participant.get("slack_id", ""),
                "is_removed": participant.get("is_removed", False),
                "was_removed": participant.get("was_removed", False)
            }
            participants_data.append(participant_info)
        
        return {
            "data": {
                "call": call_data,
                "participants": participants_data,
                "call_id": id,
                "users_added": user_list,
                "users_added_count": len(user_list),
                "status": "participants_added",
                "message": "Call participants added successfully",
                "deprecation_notice": {
                    "deprecated": True,
                    "status": "not_recommended",
                    "warning": "This tool is deprecated. Use 'add call participants' instead.",
                    "recommended_tool": "slack_add_call_participants",
                    "alternative": "Use the newer 'add call participants' tool for better functionality"
                },
                "call_info": {
                    "call_id": id,
                    "title": call_info.get("title", ""),
                    "created_by": call_info.get("created_by", ""),
                    "date_start": call_info.get("date_start", 0),
                    "date_end": call_info.get("date_end", 0),
                    "was_ended": call_info.get("was_ended", False),
                    "participants_count": call_info.get("participants_count", 0),
                    "participants_added": user_list,
                    "participants_added_count": len(user_list)
                },
                "addition_details": {
                    "call_id": id,
                    "users_added": user_list,
                    "users_added_count": len(user_list),
                    "addition_successful": True,
                    "total_participants": call_info.get("participants_count", 0)
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to add call participants. The bot needs calls:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs calls:write scope to add call participants.",
                "successful": False
            }
        elif error_code == 'call_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified call was not found.",
                "successful": False
            }
        elif error_code == 'invalid_call_id':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid call ID provided.",
                "successful": False
            }
        elif error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more specified users were not found.",
                "successful": False
            }
        elif error_code == 'invalid_users':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid user IDs provided.",
                "successful": False
            }
        elif error_code == 'already_in_call':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more users are already participants in the call.",
                "successful": False
            }
        elif error_code == 'call_ended':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe call has already ended.",
                "successful": False
            }
        elif error_code == 'too_many_participants':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nToo many participants in the call. Cannot add more users.",
                "successful": False
            }
        elif error_code == 'insufficient_permissions':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to add participants to this call.",
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

@mcp.tool()
async def slack_remove_a_star_from_an_item(
    channel: str = "",
    file: str = "",
    file_comment: str = "",
    timestamp: str = ""
) -> dict:
    """
    Removes a star from a previously starred slack item (message, file, file comment, channel, group, or dm), 
    requiring identification via `file`, `file comment`, `channel` (for channel/group/dm), or both `channel` and `timestamp` (for a message).
    
    Args:
        channel (str): Channel ID for channel/group/dm or message identification (optional)
        file (str): File ID to remove star from (optional)
        file_comment (str): File comment ID to remove star from (optional)
        timestamp (str): Message timestamp to remove star from (optional)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_user_client()
        
        # Prepare parameters for stars.remove
        params = {}
        
        # Add parameters based on what's provided
        if channel:
            params['channel'] = channel
        if file:
            params['file'] = file
        if file_comment:
            params['file_comment'] = file_comment
        if timestamp:
            params['timestamp'] = timestamp
        
        # Validate that at least one identifier is provided
        if not any([channel, file, file_comment]):
            return {
                "data": {},
                "error": "At least one identifier must be provided: channel, file, or file_comment",
                "successful": False
            }
        
        # Use the stars.remove method
        response = client.stars_remove(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_USER_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_USER_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to remove stars. The user needs stars:write scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The user needs stars:write scope to remove stars.",
                    "successful": False
                }
            elif error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified channel was not found.",
                    "successful": False
                }
            elif error == 'file_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified file was not found.",
                    "successful": False
                }
            elif error == 'file_comment_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified file comment was not found.",
                    "successful": False
                }
            elif error == 'message_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified message was not found.",
                    "successful": False
                }
            elif error == 'not_starred':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified item is not starred.",
                    "successful": False
                }
            elif error == 'invalid_timestamp':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid timestamp format. Please provide a valid timestamp.",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe user is not a member of the specified channel.",
                    "successful": False
                }
            elif error == 'cant_remove_star':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nCannot remove star from this item. The item may not be starred or may not be accessible.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to remove star: {error}",
                    "successful": False
                }
        
        # Get the item information from the response
        item_info = response.data.get("item", {})
        
        # Format the item information
        item_data = {
            "type": item_info.get("type", ""),
            "channel": item_info.get("channel", ""),
            "message": item_info.get("message", {}),
            "file": item_info.get("file", {}),
            "comment": item_info.get("comment", {}),
            "is_starred": item_info.get("is_starred", False),
            "item_type": item_info.get("type", "unknown"),
            "star_removed": True
        }
        
        # Add message details if available
        if item_info.get("message"):
            message = item_info.get("message", {})
            item_data["message_details"] = {
                "text": message.get("text", ""),
                "user": message.get("user", ""),
                "ts": message.get("ts", ""),
                "type": message.get("type", ""),
                "subtype": message.get("subtype", ""),
                "attachments": message.get("attachments", []),
                "blocks": message.get("blocks", []),
                "reactions": message.get("reactions", []),
                "thread_ts": message.get("thread_ts", ""),
                "reply_count": message.get("reply_count", 0),
                "reply_users_count": message.get("reply_users_count", 0),
                "latest_reply": message.get("latest_reply", ""),
                "is_starred": message.get("is_starred", False),
                "pinned_to": message.get("pinned_to", []),
                "permalink": message.get("permalink", "")
            }
        
        # Add file details if available
        if item_info.get("file"):
            file_info = item_info.get("file", {})
            item_data["file_details"] = {
                "id": file_info.get("id", ""),
                "name": file_info.get("name", ""),
                "title": file_info.get("title", ""),
                "mimetype": file_info.get("mimetype", ""),
                "filetype": file_info.get("filetype", ""),
                "pretty_type": file_info.get("pretty_type", ""),
                "size": file_info.get("size", 0),
                "url_private": file_info.get("url_private", ""),
                "url_private_download": file_info.get("url_private_download", ""),
                "thumb_360": file_info.get("thumb_360", ""),
                "thumb_360_w": file_info.get("thumb_360_w", 0),
                "thumb_360_h": file_info.get("thumb_360_h", 0),
                "permalink": file_info.get("permalink", ""),
                "permalink_public": file_info.get("permalink_public", ""),
                "is_external": file_info.get("is_external", False),
                "is_public": file_info.get("is_public", False),
                "is_starred": file_info.get("is_starred", False),
                "is_tombstoned": file_info.get("is_tombstoned", False),
                "created": file_info.get("created", 0),
                "timestamp": file_info.get("timestamp", 0),
                "user": file_info.get("user", ""),
                "username": file_info.get("username", ""),
                "mode": file_info.get("mode", ""),
                "editable": file_info.get("editable", False),
                "external_type": file_info.get("external_type", ""),
                "external_id": file_info.get("external_id", ""),
                "external_url": file_info.get("external_url", ""),
                "has_rich_preview": file_info.get("has_rich_preview", False)
            }
        
        # Add comment details if available
        if item_info.get("comment"):
            comment = item_info.get("comment", {})
            item_data["comment_details"] = {
                "id": comment.get("id", ""),
                "created": comment.get("created", 0),
                "timestamp": comment.get("timestamp", 0),
                "user": comment.get("user", ""),
                "is_intro": comment.get("is_intro", False),
                "comment": comment.get("comment", ""),
                "replies": comment.get("replies", []),
                "reply_count": comment.get("reply_count", 0),
                "reply_users": comment.get("reply_users", []),
                "reply_users_count": comment.get("reply_users_count", 0),
                "latest_reply": comment.get("latest_reply", ""),
                "is_starred": comment.get("is_starred", False)
            }
        
        return {
            "data": {
                "item": item_data,
                "channel": channel,
                "file": file,
                "file_comment": file_comment,
                "timestamp": timestamp,
                "star_removed": True,
                "status": "star_removed",
                "message": "Star removed successfully",
                "removal_details": {
                    "channel": channel,
                    "file": file,
                    "file_comment": file_comment,
                    "timestamp": timestamp,
                    "item_type": item_info.get("type", "unknown"),
                    "star_removed": True,
                    "removal_successful": True
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_USER_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to remove stars. The user needs stars:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The user needs stars:write scope to remove stars.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified channel was not found.",
                "successful": False
            }
        elif error_code == 'file_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified file was not found.",
                "successful": False
            }
        elif error_code == 'file_comment_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified file comment was not found.",
                "successful": False
            }
        elif error_code == 'message_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified message was not found.",
                "successful": False
            }
        elif error_code == 'not_starred':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified item is not starred.",
                "successful": False
            }
        elif error_code == 'invalid_timestamp':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid timestamp format. Please provide a valid timestamp.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe user is not a member of the specified channel.",
                "successful": False
            }
        elif error_code == 'cant_remove_star':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nCannot remove star from this item. The item may not be starred or may not be accessible.",
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

@mcp.tool()
async def slack_remove_a_user_from_a_conversation(
    channel: str,
    user: str
) -> dict:
    """
    Removes a specified user from a slack conversation (channel); the caller must have permissions 
    to remove users and cannot remove themselves using this action.
    
    Args:
        channel (str): Channel ID to remove user from
        user (str): User ID to remove from the channel
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the conversations.kick method to remove user from channel
        response = client.conversations_kick(channel=channel, user=user)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to remove users from channels. The bot needs channels:manage scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs channels:manage scope to remove users from channels.",
                    "successful": False
                }
            elif error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified channel was not found.",
                    "successful": False
                }
            elif error == 'user_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified user was not found.",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe user is not a member of the specified channel.",
                    "successful": False
                }
            elif error == 'cant_kick_self':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nCannot remove yourself from the channel using this action.",
                    "successful": False
                }
            elif error == 'cant_kick_owner':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nCannot remove the channel owner from the channel.",
                    "successful": False
                }
            elif error == 'cant_kick_admin':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nCannot remove an admin from the channel.",
                    "successful": False
                }
            elif error == 'cant_kick_primary_owner':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nCannot remove the primary owner from the channel.",
                    "successful": False
                }
            elif error == 'restricted_action':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis action is restricted. The channel may have restrictions on removing users.",
                    "successful": False
                }
            elif error == 'method_not_supported_for_channel_type':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis method is not supported for the specified channel type.",
                    "successful": False
                }
            elif error == 'is_archived':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe channel is archived and cannot be modified.",
                    "successful": False
                }
            elif error == 'invalid_user':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid user ID provided.",
                    "successful": False
                }
            elif error == 'invalid_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid channel ID provided.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to remove user from channel: {error}",
                    "successful": False
                }
        
        # Get the channel information from the response
        channel_info = response.data.get("channel", {})
        
        # Format the channel information
        channel_data = {
            "id": channel_info.get("id", ""),
            "name": channel_info.get("name", ""),
            "is_channel": channel_info.get("is_channel", False),
            "is_group": channel_info.get("is_group", False),
            "is_im": channel_info.get("is_im", False),
            "is_mpim": channel_info.get("is_mpim", False),
            "is_private": channel_info.get("is_private", False),
            "is_archived": channel_info.get("is_archived", False),
            "is_general": channel_info.get("is_general", False),
            "is_member": channel_info.get("is_member", False),
            "is_muted": channel_info.get("is_muted", False),
            "is_open": channel_info.get("is_open", False),
            "created": channel_info.get("created", 0),
            "creator": channel_info.get("creator", ""),
            "num_members": channel_info.get("num_members", 0),
            "topic": channel_info.get("topic", {}),
            "purpose": channel_info.get("purpose", {}),
            "previous_names": channel_info.get("previous_names", []),
            "priority": channel_info.get("priority", 0),
            "channel_type": "channel" if channel_info.get("is_channel") else "group" if channel_info.get("is_group") else "im" if channel_info.get("is_im") else "mpim" if channel_info.get("is_mpim") else "unknown",
            "conversation_type": {
                "is_dm": channel_info.get("is_im", False),
                "is_group_dm": channel_info.get("is_mpim", False),
                "is_public_channel": channel_info.get("is_channel", False) and not channel_info.get("is_private", False),
                "is_private_channel": channel_info.get("is_group", False) or (channel_info.get("is_channel", False) and channel_info.get("is_private", False))
            },
            "membership_info": {
                "is_member": channel_info.get("is_member", False),
                "is_muted": channel_info.get("is_muted", False),
                "is_open": channel_info.get("is_open", False),
                "num_members": channel_info.get("num_members", 0)
            },
            "metadata": {
                "created": channel_info.get("created", 0),
                "creator": channel_info.get("creator", ""),
                "is_archived": channel_info.get("is_archived", False),
                "is_general": channel_info.get("is_general", False),
                "previous_names": channel_info.get("previous_names", [])
            }
        }
        
        # Add topic and purpose information
        if channel_info.get("topic"):
            topic = channel_info.get("topic", {})
            channel_data["topic_info"] = {
                "value": topic.get("value", ""),
                "creator": topic.get("creator", ""),
                "last_set": topic.get("last_set", 0)
            }
        
        if channel_info.get("purpose"):
            purpose = channel_info.get("purpose", {})
            channel_data["purpose_info"] = {
                "value": purpose.get("value", ""),
                "creator": purpose.get("creator", ""),
                "last_set": purpose.get("last_set", 0)
            }
        
        return {
            "data": {
                "channel": channel_data,
                "user_removed": user,
                "channel_id": channel,
                "removal_successful": True,
                "status": "user_removed",
                "message": "User removed from channel successfully",
                "removal_details": {
                    "channel_id": channel,
                    "user_id": user,
                    "channel_name": channel_info.get("name", ""),
                    "channel_type": channel_data["channel_type"],
                    "is_public_channel": channel_info.get("is_channel", False) and not channel_info.get("is_private", False),
                    "is_private_channel": channel_info.get("is_group", False) or (channel_info.get("is_channel", False) and channel_info.get("is_private", False)),
                    "num_members": channel_info.get("num_members", 0),
                    "removal_successful": True
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to remove users from channels. The bot needs channels:manage scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:manage scope to remove users from channels.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified channel was not found.",
                "successful": False
            }
        elif error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified user was not found.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe user is not a member of the specified channel.",
                "successful": False
            }
        elif error_code == 'cant_kick_self':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nCannot remove yourself from the channel using this action.",
                "successful": False
            }
        elif error_code == 'cant_kick_owner':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nCannot remove the channel owner from the channel.",
                "successful": False
            }
        elif error_code == 'cant_kick_admin':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nCannot remove an admin from the channel.",
                "successful": False
            }
        elif error_code == 'cant_kick_primary_owner':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nCannot remove the primary owner from the channel.",
                "successful": False
            }
        elif error_code == 'restricted_action':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis action is restricted. The channel may have restrictions on removing users.",
                "successful": False
            }
        elif error_code == 'method_not_supported_for_channel_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis method is not supported for the specified channel type.",
                "successful": False
            }
        elif error_code == 'is_archived':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel is archived and cannot be modified.",
                "successful": False
            }
        elif error_code == 'invalid_user':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid user ID provided.",
                "successful": False
            }
        elif error_code == 'invalid_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid channel ID provided.",
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

@mcp.tool()
async def slack_remove_call_participants(
    id: str,
    users: str
) -> dict:
    """
    Registers participants removed from a slack call.
    
    Args:
        id (str): Call ID to remove participants from
        users (str): Comma-separated list of user IDs to remove from the call
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Parse users parameter
        user_list = [user.strip() for user in users.split(',') if user.strip()]
        
        # Use the calls.participants.remove method
        response = client.calls_participants_remove(id=id, users=user_list)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to remove call participants. The bot needs calls:write scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs calls:write scope to remove call participants.",
                    "successful": False
                }
            elif error == 'call_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified call was not found.",
                    "successful": False
                }
            elif error == 'invalid_call_id':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid call ID provided.",
                    "successful": False
                }
            elif error == 'user_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nOne or more specified users were not found.",
                    "successful": False
                }
            elif error == 'invalid_users':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid user IDs provided.",
                    "successful": False
                }
            elif error == 'not_in_call':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nOne or more users are not participants in the call.",
                    "successful": False
                }
            elif error == 'call_ended':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe call has already ended.",
                    "successful": False
                }
            elif error == 'insufficient_permissions':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to remove participants from this call.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to remove call participants: {error}",
                    "successful": False
                }
        
        # Get the call information
        call_info = response.data.get("call", {})
        
        # Format the call information
        call_data = {
            "id": call_info.get("id", ""),
            "date_start": call_info.get("date_start", 0),
            "external_unique_id": call_info.get("external_unique_id", ""),
            "join_url": call_info.get("join_url", ""),
            "desktop_app_join_url": call_info.get("desktop_app_join_url", ""),
            "external_display_id": call_info.get("external_display_id", ""),
            "title": call_info.get("title", ""),
            "created_by": call_info.get("created_by", ""),
            "date_end": call_info.get("date_end", 0),
            "channels": call_info.get("channels", []),
            "was_desktop_app_switching_enabled": call_info.get("was_desktop_app_switching_enabled", False),
            "was_join_url_shared": call_info.get("was_join_url_shared", False),
            "was_created_by_meeting_plugin": call_info.get("was_created_by_meeting_plugin", False),
            "was_ended": call_info.get("was_ended", False),
            "participants": call_info.get("participants", []),
            "participants_count": call_info.get("participants_count", 0),
            "participants_removed": user_list,
            "participants_removed_count": len(user_list),
            "call_status": "active" if not call_info.get("was_ended", False) else "ended",
            "call_type": "slack_call"
        }
        
        # Format participants information
        participants_data = []
        for participant in call_info.get("participants", []):
            participant_info = {
                "external_id": participant.get("external_id", ""),
                "avatar_url": participant.get("avatar_url", ""),
                "display_name": participant.get("display_name", ""),
                "slack_id": participant.get("slack_id", ""),
                "is_removed": participant.get("is_removed", False),
                "was_removed": participant.get("was_removed", False)
            }
            participants_data.append(participant_info)
        
        return {
            "data": {
                "call": call_data,
                "participants": participants_data,
                "call_id": id,
                "users_removed": user_list,
                "users_removed_count": len(user_list),
                "status": "participants_removed",
                "message": "Call participants removed successfully",
                "call_info": {
                    "call_id": id,
                    "title": call_info.get("title", ""),
                    "created_by": call_info.get("created_by", ""),
                    "date_start": call_info.get("date_start", 0),
                    "date_end": call_info.get("date_end", 0),
                    "was_ended": call_info.get("was_ended", False),
                    "participants_count": call_info.get("participants_count", 0),
                    "participants_removed": user_list,
                    "participants_removed_count": len(user_list)
                },
                "removal_details": {
                    "call_id": id,
                    "users_removed": user_list,
                    "users_removed_count": len(user_list),
                    "removal_successful": True,
                    "remaining_participants": call_info.get("participants_count", 0) - len(user_list)
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to remove call participants. The bot needs calls:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs calls:write scope to remove call participants.",
                "successful": False
            }
        elif error_code == 'call_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified call was not found.",
                "successful": False
            }
        elif error_code == 'invalid_call_id':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid call ID provided.",
                "successful": False
            }
        elif error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more specified users were not found.",
                "successful": False
            }
        elif error_code == 'invalid_users':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid user IDs provided.",
                "successful": False
            }
        elif error_code == 'not_in_call':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOne or more users are not participants in the call.",
                "successful": False
            }
        elif error_code == 'call_ended':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe call has already ended.",
                "successful": False
            }
        elif error_code == 'insufficient_permissions':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to remove participants from this call.",
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

@mcp.tool()
async def slack_remove_reaction_from_item(
    name: str,
    channel: str = "",
    file: str = "",
    file_comment: str = "",
    timestamp: str = ""
) -> dict:
    """
    Removes an emoji reaction from a message, file, or file comment in slack.
    
    Args:
        name (str): Emoji reaction name to remove (required)
        channel (str): Channel ID for message reactions (optional)
        file (str): File ID for file reactions (optional)
        file_comment (str): File comment ID for file comment reactions (optional)
        timestamp (str): Message timestamp for message reactions (optional)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Prepare parameters for reactions.remove
        params = {
            'name': name
        }
        
        # Add parameters based on what's provided
        if channel:
            params['channel'] = channel
        if file:
            params['file'] = file
        if file_comment:
            params['file_comment'] = file_comment
        if timestamp:
            params['timestamp'] = timestamp
        
        # Validate that at least one identifier is provided
        if not any([channel, file, file_comment]):
            return {
                "data": {},
                "error": "At least one identifier must be provided: channel, file, or file_comment",
                "successful": False
            }
        
        # Use the reactions.remove method
        response = client.reactions_remove(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to remove reactions. The bot needs reactions:write scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs reactions:write scope to remove reactions.",
                    "successful": False
                }
            elif error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified channel was not found.",
                    "successful": False
                }
            elif error == 'file_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified file was not found.",
                    "successful": False
                }
            elif error == 'file_comment_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified file comment was not found.",
                    "successful": False
                }
            elif error == 'message_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified message was not found.",
                    "successful": False
                }
            elif error == 'no_reaction':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified reaction does not exist on this item.",
                    "successful": False
                }
            elif error == 'invalid_name':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid reaction name provided.",
                    "successful": False
                }
            elif error == 'invalid_timestamp':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid timestamp format. Please provide a valid timestamp.",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe bot is not a member of the specified channel.",
                    "successful": False
                }
            elif error == 'cant_remove_reaction':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nCannot remove this reaction. The reaction may not exist or may not be accessible.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to remove reaction: {error}",
                    "successful": False
                }
        
        # Get the item information from the response
        item_info = response.data.get("item", {})
        
        # Format the item information
        item_data = {
            "type": item_info.get("type", ""),
            "channel": item_info.get("channel", ""),
            "message": item_info.get("message", {}),
            "file": item_info.get("file", {}),
            "comment": item_info.get("comment", {}),
            "reactions": item_info.get("reactions", []),
            "item_type": item_info.get("type", "unknown"),
            "reaction_removed": True
        }
        
        # Add message details if available
        if item_info.get("message"):
            message = item_info.get("message", {})
            item_data["message_details"] = {
                "text": message.get("text", ""),
                "user": message.get("user", ""),
                "ts": message.get("ts", ""),
                "type": message.get("type", ""),
                "subtype": message.get("subtype", ""),
                "attachments": message.get("attachments", []),
                "blocks": message.get("blocks", []),
                "reactions": message.get("reactions", []),
                "thread_ts": message.get("thread_ts", ""),
                "reply_count": message.get("reply_count", 0),
                "reply_users_count": message.get("reply_users_count", 0),
                "latest_reply": message.get("latest_reply", ""),
                "is_starred": message.get("is_starred", False),
                "pinned_to": message.get("pinned_to", []),
                "permalink": message.get("permalink", "")
            }
        
        # Add file details if available
        if item_info.get("file"):
            file_info = item_info.get("file", {})
            item_data["file_details"] = {
                "id": file_info.get("id", ""),
                "name": file_info.get("name", ""),
                "title": file_info.get("title", ""),
                "mimetype": file_info.get("mimetype", ""),
                "filetype": file_info.get("filetype", ""),
                "pretty_type": file_info.get("pretty_type", ""),
                "size": file_info.get("size", 0),
                "url_private": file_info.get("url_private", ""),
                "url_private_download": file_info.get("url_private_download", ""),
                "thumb_360": file_info.get("thumb_360", ""),
                "thumb_360_w": file_info.get("thumb_360_w", 0),
                "thumb_360_h": file_info.get("thumb_360_h", 0),
                "permalink": file_info.get("permalink", ""),
                "permalink_public": file_info.get("permalink_public", ""),
                "is_external": file_info.get("is_external", False),
                "is_public": file_info.get("is_public", False),
                "is_starred": file_info.get("is_starred", False),
                "is_tombstoned": file_info.get("is_tombstoned", False),
                "created": file_info.get("created", 0),
                "timestamp": file_info.get("timestamp", 0),
                "user": file_info.get("user", ""),
                "username": file_info.get("username", ""),
                "mode": file_info.get("mode", ""),
                "editable": file_info.get("editable", False),
                "external_type": file_info.get("external_type", ""),
                "external_id": file_info.get("external_id", ""),
                "external_url": file_info.get("external_url", ""),
                "has_rich_preview": file_info.get("has_rich_preview", False)
            }
        
        # Add comment details if available
        if item_info.get("comment"):
            comment = item_info.get("comment", {})
            item_data["comment_details"] = {
                "id": comment.get("id", ""),
                "created": comment.get("created", 0),
                "timestamp": comment.get("timestamp", 0),
                "user": comment.get("user", ""),
                "is_intro": comment.get("is_intro", False),
                "comment": comment.get("comment", ""),
                "replies": comment.get("replies", []),
                "reply_count": comment.get("reply_count", 0),
                "reply_users": comment.get("reply_users", []),
                "reply_users_count": comment.get("reply_users_count", 0),
                "latest_reply": comment.get("latest_reply", ""),
                "is_starred": comment.get("is_starred", False)
            }
        
        # Format remaining reactions
        remaining_reactions = []
        for reaction in item_info.get("reactions", []):
            reaction_info = {
                "name": reaction.get("name", ""),
                "count": reaction.get("count", 0),
                "users": reaction.get("users", []),
                "is_removed": reaction.get("name", "") == name
            }
            remaining_reactions.append(reaction_info)
        
        return {
            "data": {
                "item": item_data,
                "reaction_name": name,
                "channel": channel,
                "file": file,
                "file_comment": file_comment,
                "timestamp": timestamp,
                "reaction_removed": True,
                "status": "reaction_removed",
                "message": "Reaction removed successfully",
                "remaining_reactions": remaining_reactions,
                "removal_details": {
                    "reaction_name": name,
                    "channel": channel,
                    "file": file,
                    "file_comment": file_comment,
                    "timestamp": timestamp,
                    "item_type": item_info.get("type", "unknown"),
                    "reaction_removed": True,
                    "removal_successful": True
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to remove reactions. The bot needs reactions:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs reactions:write scope to remove reactions.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified channel was not found.",
                "successful": False
            }
        elif error_code == 'file_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified file was not found.",
                "successful": False
            }
        elif error_code == 'file_comment_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified file comment was not found.",
                "successful": False
            }
        elif error_code == 'message_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified message was not found.",
                "successful": False
            }
        elif error_code == 'no_reaction':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified reaction does not exist on this item.",
                "successful": False
            }
        elif error_code == 'invalid_name':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid reaction name provided.",
                "successful": False
            }
        elif error_code == 'invalid_timestamp':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid timestamp format. Please provide a valid timestamp.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of the specified channel.",
                "successful": False
            }
        elif error_code == 'cant_remove_reaction':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nCannot remove this reaction. The reaction may not exist or may not be accessible.",
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

@mcp.tool()
async def slack_rename_a_conversation(
    channel: str,
    name: str
) -> dict:
    """
    Renames a slack channel, automatically adjusting the new name to meet naming conventions 
    (e.g., converting to lowercase), which may affect integrations using the old name.
    
    Args:
        channel (str): Channel ID to rename
        name (str): New name for the channel
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the conversations.rename method
        response = client.conversations_rename(channel=channel, name=name)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to rename channels. The bot needs channels:manage scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs channels:manage scope to rename channels.",
                    "successful": False
                }
            elif error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified channel was not found.",
                    "successful": False
                }
            elif error == 'invalid_name':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid channel name provided. Channel names must be 21 characters or less and contain only lowercase letters, numbers, hyphens, and underscores.",
                    "successful": False
                }
            elif error == 'name_taken':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nChannel name is already taken. Please choose a different name.",
                    "successful": False
                }
            elif error == 'restricted_action':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis action is restricted. The channel may have restrictions on renaming.",
                    "successful": False
                }
            elif error == 'method_not_supported_for_channel_type':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis method is not supported for the specified channel type.",
                    "successful": False
                }
            elif error == 'is_archived':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe channel is archived and cannot be renamed.",
                    "successful": False
                }
            elif error == 'cant_rename_general':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nCannot rename the #general channel.",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe bot is not a member of the specified channel.",
                    "successful": False
                }
            elif error == 'invalid_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid channel ID provided.",
                    "successful": False
                }
            elif error == 'too_long':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nChannel name is too long. Maximum length is 21 characters.",
                    "successful": False
                }
            elif error == 'too_short':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nChannel name is too short. Minimum length is 1 character.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to rename channel: {error}",
                    "successful": False
                }
        
        # Get the channel information from the response
        channel_info = response.data.get("channel", {})
        
        # Format the channel information
        channel_data = {
            "id": channel_info.get("id", ""),
            "name": channel_info.get("name", ""),
            "is_channel": channel_info.get("is_channel", False),
            "is_group": channel_info.get("is_group", False),
            "is_im": channel_info.get("is_im", False),
            "is_mpim": channel_info.get("is_mpim", False),
            "is_private": channel_info.get("is_private", False),
            "is_archived": channel_info.get("is_archived", False),
            "is_general": channel_info.get("is_general", False),
            "is_member": channel_info.get("is_member", False),
            "is_muted": channel_info.get("is_muted", False),
            "is_open": channel_info.get("is_open", False),
            "created": channel_info.get("created", 0),
            "creator": channel_info.get("creator", ""),
            "num_members": channel_info.get("num_members", 0),
            "topic": channel_info.get("topic", {}),
            "purpose": channel_info.get("purpose", {}),
            "previous_names": channel_info.get("previous_names", []),
            "priority": channel_info.get("priority", 0),
            "channel_type": "channel" if channel_info.get("is_channel") else "group" if channel_info.get("is_group") else "im" if channel_info.get("is_im") else "mpim" if channel_info.get("is_mpim") else "unknown",
            "conversation_type": {
                "is_dm": channel_info.get("is_im", False),
                "is_group_dm": channel_info.get("is_mpim", False),
                "is_public_channel": channel_info.get("is_channel", False) and not channel_info.get("is_private", False),
                "is_private_channel": channel_info.get("is_group", False) or (channel_info.get("is_channel", False) and channel_info.get("is_private", False))
            },
            "membership_info": {
                "is_member": channel_info.get("is_member", False),
                "is_muted": channel_info.get("is_muted", False),
                "is_open": channel_info.get("is_open", False),
                "num_members": channel_info.get("num_members", 0)
            },
            "metadata": {
                "created": channel_info.get("created", 0),
                "creator": channel_info.get("creator", ""),
                "is_archived": channel_info.get("is_archived", False),
                "is_general": channel_info.get("is_general", False),
                "previous_names": channel_info.get("previous_names", [])
            }
        }
        
        # Add topic and purpose information
        if channel_info.get("topic"):
            topic = channel_info.get("topic", {})
            channel_data["topic_info"] = {
                "value": topic.get("value", ""),
                "creator": topic.get("creator", ""),
                "last_set": topic.get("last_set", 0)
            }
        
        if channel_info.get("purpose"):
            purpose = channel_info.get("purpose", {})
            channel_data["purpose_info"] = {
                "value": purpose.get("value", ""),
                "creator": purpose.get("creator", ""),
                "last_set": purpose.get("last_set", 0)
            }
        
        return {
            "data": {
                "channel": channel_data,
                "old_name": name,
                "new_name": channel_info.get("name", ""),
                "channel_id": channel,
                "rename_successful": True,
                "status": "channel_renamed",
                "message": "Channel renamed successfully",
                "rename_details": {
                    "channel_id": channel,
                    "old_name": name,
                    "new_name": channel_info.get("name", ""),
                    "name_changed": name != channel_info.get("name", ""),
                    "channel_type": channel_data["channel_type"],
                    "is_public_channel": channel_info.get("is_channel", False) and not channel_info.get("is_private", False),
                    "is_private_channel": channel_info.get("is_group", False) or (channel_info.get("is_channel", False) and channel_info.get("is_private", False)),
                    "rename_successful": True
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to rename channels. The bot needs channels:manage scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:manage scope to rename channels.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified channel was not found.",
                "successful": False
            }
        elif error_code == 'invalid_name':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid channel name provided. Channel names must be 21 characters or less and contain only lowercase letters, numbers, hyphens, and underscores.",
                "successful": False
            }
        elif error_code == 'name_taken':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nChannel name is already taken. Please choose a different name.",
                "successful": False
            }
        elif error_code == 'restricted_action':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis action is restricted. The channel may have restrictions on renaming.",
                "successful": False
            }
        elif error_code == 'method_not_supported_for_channel_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis method is not supported for the specified channel type.",
                "successful": False
            }
        elif error_code == 'is_archived':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel is archived and cannot be renamed.",
                "successful": False
            }
        elif error_code == 'cant_rename_general':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nCannot rename the #general channel.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of the specified channel.",
                "successful": False
            }
        elif error_code == 'invalid_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid channel ID provided.",
                "successful": False
            }
        elif error_code == 'too_long':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nChannel name is too long. Maximum length is 21 characters.",
                "successful": False
            }
        elif error_code == 'too_short':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nChannel name is too short. Minimum length is 1 character.",
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

@mcp.tool()
async def slack_rename_an_emoji(
    name: str,
    new_name: str,
    token: str
) -> dict:
    """
    Renames an existing custom emoji in a slack workspace, updating all its instances.
    
    Args:
        name (str): Current name of the emoji to rename
        new_name (str): New name for the emoji
        token (str): Authentication token (can be bot token or user token)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        # Use the provided token to create a client
        client = WebClient(token=token)
        
        # Use the admin.emoji.rename method
        response = client.admin_emoji_rename(name=name, new_name=new_name)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your token.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your token.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to rename emojis. This requires Enterprise Grid admin permissions.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required permissions. Emoji renaming requires Enterprise Grid admin access.",
                    "successful": False
                }
            elif error == 'emoji_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified emoji '{name}' was not found.",
                    "successful": False
                }
            elif error == 'invalid_name':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid emoji name provided. Emoji names must be 2-21 characters and contain only lowercase letters, numbers, hyphens, and underscores.",
                    "successful": False
                }
            elif error == 'name_taken':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nEmoji name '{new_name}' is already taken. Please choose a different name.",
                    "successful": False
                }
            elif error == 'restricted_action':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis action is restricted. You may not have permission to rename emojis.",
                    "successful": False
                }
            elif error == 'not_admin':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nOnly workspace admins can rename emojis.",
                    "successful": False
                }
            elif error == 'feature_disabled':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nCustom emojis are disabled for this workspace.",
                    "successful": False
                }
            elif error == 'too_long':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nEmoji name is too long. Maximum length is 21 characters.",
                    "successful": False
                }
            elif error == 'too_short':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nEmoji name is too short. Minimum length is 2 characters.",
                    "successful": False
                }
            elif error == 'invalid_characters':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nEmoji name contains invalid characters. Only lowercase letters, numbers, hyphens, and underscores are allowed.",
                    "successful": False
                }
            elif error == 'emoji_already_exists':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAn emoji with the name '{new_name}' already exists.",
                    "successful": False
                }
            elif error == 'emoji_rename_failed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nFailed to rename the emoji. This may be due to the emoji being in use or other restrictions.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to rename emoji: {error}",
                    "successful": False
                }
        
        # Get the emoji information from the response
        emoji_info = response.data.get("emoji", {})
        
        # Format the emoji information
        emoji_data = {
            "name": emoji_info.get("name", ""),
            "url": emoji_info.get("url", ""),
            "alias": emoji_info.get("alias", ""),
            "created": emoji_info.get("created", 0),
            "created_by": emoji_info.get("created_by", ""),
            "is_alias": emoji_info.get("is_alias", False),
            "is_bad": emoji_info.get("is_bad", False),
            "is_public": emoji_info.get("is_public", False),
            "is_restricted": emoji_info.get("is_restricted", False),
            "is_team_custom": emoji_info.get("is_team_custom", False),
            "is_workflow_step": emoji_info.get("is_workflow_step", False),
            "original_name": emoji_info.get("original_name", ""),
            "previous_names": emoji_info.get("previous_names", []),
            "renamed_from": name,
            "renamed_to": new_name,
            "rename_successful": True,
            "emoji_type": "custom" if emoji_info.get("is_team_custom") else "alias" if emoji_info.get("is_alias") else "unknown",
            "access_info": {
                "is_public": emoji_info.get("is_public", False),
                "is_restricted": emoji_info.get("is_restricted", False),
                "is_team_custom": emoji_info.get("is_team_custom", False)
            },
            "creation_info": {
                "created": emoji_info.get("created", 0),
                "created_by": emoji_info.get("created_by", ""),
                "original_name": emoji_info.get("original_name", "")
            },
            "status_info": {
                "is_bad": emoji_info.get("is_bad", False),
                "is_workflow_step": emoji_info.get("is_workflow_step", False),
                "is_alias": emoji_info.get("is_alias", False)
            }
        }
        
        return {
            "data": {
                "emoji": emoji_data,
                "old_name": name,
                "new_name": new_name,
                "rename_successful": True,
                "status": "emoji_renamed",
                "message": "Emoji renamed successfully",
                "rename_details": {
                    "old_name": name,
                    "new_name": new_name,
                    "emoji_name": emoji_info.get("name", ""),
                    "name_changed": name != emoji_info.get("name", ""),
                    "emoji_type": emoji_data["emoji_type"],
                    "is_custom_emoji": emoji_info.get("is_team_custom", False),
                    "is_alias": emoji_info.get("is_alias", False),
                    "is_public": emoji_info.get("is_public", False),
                    "is_restricted": emoji_info.get("is_restricted", False),
                    "rename_successful": True
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your token.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your token.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to rename emojis. This requires Enterprise Grid admin permissions.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required permissions. Emoji renaming requires Enterprise Grid admin access.",
                "successful": False
            }
        elif error_code == 'emoji_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified emoji '{name}' was not found.",
                "successful": False
            }
        elif error_code == 'invalid_name':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid emoji name provided. Emoji names must be 2-21 characters and contain only lowercase letters, numbers, hyphens, and underscores.",
                "successful": False
            }
        elif error_code == 'name_taken':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nEmoji name '{new_name}' is already taken. Please choose a different name.",
                "successful": False
            }
        elif error_code == 'restricted_action':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis action is restricted. You may not have permission to rename emojis.",
                "successful": False
            }
        elif error_code == 'not_admin':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOnly workspace admins can rename emojis.",
                "successful": False
            }
        elif error_code == 'feature_disabled':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nCustom emojis are disabled for this workspace.",
                "successful": False
            }
        elif error_code == 'too_long':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nEmoji name is too long. Maximum length is 21 characters.",
                "successful": False
            }
        elif error_code == 'too_short':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nEmoji name is too short. Minimum length is 2 characters.",
                "successful": False
            }
        elif error_code == 'invalid_characters':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nEmoji name contains invalid characters. Only lowercase letters, numbers, hyphens, and underscores are allowed.",
                "successful": False
            }
        elif error_code == 'emoji_already_exists':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAn emoji with the name '{new_name}' already exists.",
                "successful": False
            }
        elif error_code == 'emoji_rename_failed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nFailed to rename the emoji. This may be due to the emoji being in use or other restrictions.",
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

@mcp.tool()
async def slack_rename_a_slack_channel(
    channel_id: str,
    name: str
) -> dict:
    """
    Renames a public or private slack channel; for enterprise grid workspaces, 
    the user must be a workspace admin or channel manager.
    
    Args:
        channel_id (str): Channel ID to rename
        name (str): New name for the channel
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the conversations.rename method
        response = client.conversations_rename(channel=channel_id, name=name)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to rename channels. The bot needs channels:manage scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs channels:manage scope to rename channels.",
                    "successful": False
                }
            elif error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified channel was not found.",
                    "successful": False
                }
            elif error == 'invalid_name':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid channel name provided. Channel names must be 21 characters or less and contain only lowercase letters, numbers, hyphens, and underscores.",
                    "successful": False
                }
            elif error == 'name_taken':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nChannel name is already taken. Please choose a different name.",
                    "successful": False
                }
            elif error == 'restricted_action':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis action is restricted. The channel may have restrictions on renaming.",
                    "successful": False
                }
            elif error == 'method_not_supported_for_channel_type':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis method is not supported for the specified channel type.",
                    "successful": False
                }
            elif error == 'is_archived':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe channel is archived and cannot be renamed.",
                    "successful": False
                }
            elif error == 'cant_rename_general':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nCannot rename the #general channel.",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe bot is not a member of the specified channel.",
                    "successful": False
                }
            elif error == 'invalid_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid channel ID provided.",
                    "successful": False
                }
            elif error == 'too_long':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nChannel name is too long. Maximum length is 21 characters.",
                    "successful": False
                }
            elif error == 'too_short':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nChannel name is too short. Minimum length is 1 character.",
                    "successful": False
                }
            elif error == 'enterprise_grid_required':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis action requires Enterprise Grid workspace with admin or channel manager permissions.",
                    "successful": False
                }
            elif error == 'not_admin':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nOnly workspace admins or channel managers can rename channels in Enterprise Grid workspaces.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to rename channel: {error}",
                    "successful": False
                }
        
        # Get the channel information from the response
        channel_info = response.data.get("channel", {})
        
        # Format the channel information
        channel_data = {
            "id": channel_info.get("id", ""),
            "name": channel_info.get("name", ""),
            "is_channel": channel_info.get("is_channel", False),
            "is_group": channel_info.get("is_group", False),
            "is_im": channel_info.get("is_im", False),
            "is_mpim": channel_info.get("is_mpim", False),
            "is_private": channel_info.get("is_private", False),
            "is_archived": channel_info.get("is_archived", False),
            "is_general": channel_info.get("is_general", False),
            "is_member": channel_info.get("is_member", False),
            "is_muted": channel_info.get("is_muted", False),
            "is_open": channel_info.get("is_open", False),
            "created": channel_info.get("created", 0),
            "creator": channel_info.get("creator", ""),
            "num_members": channel_info.get("num_members", 0),
            "topic": channel_info.get("topic", {}),
            "purpose": channel_info.get("purpose", {}),
            "previous_names": channel_info.get("previous_names", []),
            "priority": channel_info.get("priority", 0),
            "channel_type": "channel" if channel_info.get("is_channel") else "group" if channel_info.get("is_group") else "im" if channel_info.get("is_im") else "mpim" if channel_info.get("is_mpim") else "unknown",
            "conversation_type": {
                "is_dm": channel_info.get("is_im", False),
                "is_group_dm": channel_info.get("is_mpim", False),
                "is_public_channel": channel_info.get("is_channel", False) and not channel_info.get("is_private", False),
                "is_private_channel": channel_info.get("is_group", False) or (channel_info.get("is_channel", False) and channel_info.get("is_private", False))
            },
            "membership_info": {
                "is_member": channel_info.get("is_member", False),
                "is_muted": channel_info.get("is_muted", False),
                "is_open": channel_info.get("is_open", False),
                "num_members": channel_info.get("num_members", 0)
            },
            "metadata": {
                "created": channel_info.get("created", 0),
                "creator": channel_info.get("creator", ""),
                "is_archived": channel_info.get("is_archived", False),
                "is_general": channel_info.get("is_general", False),
                "previous_names": channel_info.get("previous_names", [])
            }
        }
        
        # Add topic and purpose information
        if channel_info.get("topic"):
            topic = channel_info.get("topic", {})
            channel_data["topic_info"] = {
                "value": topic.get("value", ""),
                "creator": topic.get("creator", ""),
                "last_set": topic.get("last_set", 0)
            }
        
        if channel_info.get("purpose"):
            purpose = channel_info.get("purpose", {})
            channel_data["purpose_info"] = {
                "value": purpose.get("value", ""),
                "creator": purpose.get("creator", ""),
                "last_set": purpose.get("last_set", 0)
            }
        
        return {
            "data": {
                "channel": channel_data,
                "old_name": name,
                "new_name": channel_info.get("name", ""),
                "channel_id": channel_id,
                "rename_successful": True,
                "status": "channel_renamed",
                "message": "Channel renamed successfully",
                "rename_details": {
                    "channel_id": channel_id,
                    "old_name": name,
                    "new_name": channel_info.get("name", ""),
                    "name_changed": name != channel_info.get("name", ""),
                    "channel_type": channel_data["channel_type"],
                    "is_public_channel": channel_info.get("is_channel", False) and not channel_info.get("is_private", False),
                    "is_private_channel": channel_info.get("is_group", False) or (channel_info.get("is_channel", False) and channel_info.get("is_private", False)),
                    "rename_successful": True
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to rename channels. The bot needs channels:manage scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:manage scope to rename channels.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified channel was not found.",
                "successful": False
            }
        elif error_code == 'invalid_name':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid channel name provided. Channel names must be 21 characters or less and contain only lowercase letters, numbers, hyphens, and underscores.",
                "successful": False
            }
        elif error_code == 'name_taken':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nChannel name is already taken. Please choose a different name.",
                "successful": False
            }
        elif error_code == 'restricted_action':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis action is restricted. The channel may have restrictions on renaming.",
                "successful": False
            }
        elif error_code == 'method_not_supported_for_channel_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis method is not supported for the specified channel type.",
                "successful": False
            }
        elif error_code == 'is_archived':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe channel is archived and cannot be renamed.",
                "successful": False
            }
        elif error_code == 'cant_rename_general':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nCannot rename the #general channel.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of the specified channel.",
                "successful": False
            }
        elif error_code == 'invalid_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid channel ID provided.",
                "successful": False
            }
        elif error_code == 'too_long':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nChannel name is too long. Maximum length is 21 characters.",
                "successful": False
            }
        elif error_code == 'too_short':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nChannel name is too short. Minimum length is 1 character.",
                "successful": False
            }
        elif error_code == 'enterprise_grid_required':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis action requires Enterprise Grid workspace with admin or channel manager permissions.",
                "successful": False
            }
        elif error_code == 'not_admin':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nOnly workspace admins or channel managers can rename channels in Enterprise Grid workspaces.",
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

@mcp.tool()
async def slack_retrieve_a_user_s_identity_details() -> dict:
    """
    Retrieves the authenticated user's and their team's identity, with details varying 
    based on oauth scopes (e.g., identity.basic, identity.email, identity.avatar).
    
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the auth.test method to get identity information
        response = client.auth_test()
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to retrieve identity details: {error}",
                    "successful": False
                }
        
        # Get the identity information from the response
        identity_data = response.data
        
        # Format the identity information
        identity_details = {
            "user_id": identity_data.get("user_id", ""),
            "user": identity_data.get("user", ""),
            "team_id": identity_data.get("team_id", ""),
            "team": identity_data.get("team", ""),
            "url": identity_data.get("url", ""),
            "bot_id": identity_data.get("bot_id", ""),
            "is_enterprise_install": identity_data.get("is_enterprise_install", False),
            "enterprise_id": identity_data.get("enterprise_id", ""),
            "app_id": identity_data.get("app_id", ""),
            "authentication_type": "bot" if identity_data.get("bot_id") else "user",
            "workspace_info": {
                "team_id": identity_data.get("team_id", ""),
                "team": identity_data.get("team", ""),
                "url": identity_data.get("url", ""),
                "is_enterprise_install": identity_data.get("is_enterprise_install", False),
                "enterprise_id": identity_data.get("enterprise_id", "")
            },
            "user_info": {
                "user_id": identity_data.get("user_id", ""),
                "user": identity_data.get("user", ""),
                "bot_id": identity_data.get("bot_id", "")
            },
            "app_info": {
                "app_id": identity_data.get("app_id", ""),
                "bot_id": identity_data.get("bot_id", "")
            }
        }
        
        # Add enterprise information if available
        if identity_data.get("enterprise_id"):
            identity_details["enterprise_info"] = {
                "enterprise_id": identity_data.get("enterprise_id", ""),
                "is_enterprise_install": identity_data.get("is_enterprise_install", False)
            }
        
        # Add additional details based on available scopes
        if identity_data.get("user"):
            identity_details["user_details"] = {
                "user_id": identity_data.get("user_id", ""),
                "username": identity_data.get("user", ""),
                "bot_id": identity_data.get("bot_id", ""),
                "is_bot": bool(identity_data.get("bot_id"))
            }
        
        if identity_data.get("team"):
            identity_details["team_details"] = {
                "team_id": identity_data.get("team_id", ""),
                "team_name": identity_data.get("team", ""),
                "workspace_url": identity_data.get("url", ""),
                "is_enterprise": identity_data.get("is_enterprise_install", False)
            }
        
        return {
            "data": {
                "identity": identity_details,
                "authentication_status": "authenticated",
                "token_type": "bot" if identity_data.get("bot_id") else "user",
                "workspace_type": "enterprise" if identity_data.get("is_enterprise_install") else "standard",
                "status": "identity_retrieved",
                "message": "User identity details retrieved successfully",
                "identity_summary": {
                    "user_id": identity_data.get("user_id", ""),
                    "team_id": identity_data.get("team_id", ""),
                    "bot_id": identity_data.get("bot_id", ""),
                    "is_enterprise": identity_data.get("is_enterprise_install", False),
                    "workspace_url": identity_data.get("url", ""),
                    "authentication_type": "bot" if identity_data.get("bot_id") else "user"
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
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

@mcp.tool()
async def slack_retrieve_call_information(
    id: str
) -> dict:
    """
    Retrieves a point-in-time snapshot of a specific slack call's information.
    
    Args:
        id (str): Call ID to retrieve information for
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the calls.info method
        response = client.calls_info(id=id)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'call_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified call was not found.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to retrieve call information. The bot needs calls:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs calls:read scope to retrieve call information.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to retrieve call information: {error}",
                    "successful": False
                }
        
        # Get the call information from the response
        call_info = response.data.get("call", {})
        
        # Format the call information
        call_data = {
            "id": call_info.get("id", ""),
            "date_start": call_info.get("date_start", 0),
            "external_unique_id": call_info.get("external_unique_id", ""),
            "join_url": call_info.get("join_url", ""),
            "desktop_app_join_url": call_info.get("desktop_app_join_url", ""),
            "external_display_id": call_info.get("external_display_id", ""),
            "title": call_info.get("title", ""),
            "created_by": call_info.get("created_by", ""),
            "date_end": call_info.get("date_end", 0),
            "channels": call_info.get("channels", []),
            "was_rejected": call_info.get("was_rejected", False),
            "was_missed": call_info.get("was_missed", False),
            "was_accepted": call_info.get("was_accepted", False),
            "call_type": call_info.get("call_type", ""),
            "status": call_info.get("status", ""),
            "participants": call_info.get("participants", []),
            "call_duration": call_info.get("date_end", 0) - call_info.get("date_start", 0) if call_info.get("date_end") and call_info.get("date_start") else 0,
            "is_active": call_info.get("status") == "active",
            "is_ended": call_info.get("status") == "ended",
            "call_info": {
                "id": call_info.get("id", ""),
                "title": call_info.get("title", ""),
                "status": call_info.get("status", ""),
                "call_type": call_info.get("call_type", ""),
                "created_by": call_info.get("created_by", ""),
                "date_start": call_info.get("date_start", 0),
                "date_end": call_info.get("date_end", 0),
                "duration": call_info.get("date_end", 0) - call_info.get("date_start", 0) if call_info.get("date_end") and call_info.get("date_start") else 0
            },
            "participation_info": {
                "participants": call_info.get("participants", []),
                "channels": call_info.get("channels", []),
                "was_accepted": call_info.get("was_accepted", False),
                "was_rejected": call_info.get("was_rejected", False),
                "was_missed": call_info.get("was_missed", False)
            },
            "external_info": {
                "external_unique_id": call_info.get("external_unique_id", ""),
                "external_display_id": call_info.get("external_display_id", ""),
                "join_url": call_info.get("join_url", ""),
                "desktop_app_join_url": call_info.get("desktop_app_join_url", "")
            }
        }
        
        return {
            "data": {
                "call": call_data,
                "call_id": id,
                "retrieval_successful": True,
                "status": "call_info_retrieved",
                "message": "Call information retrieved successfully",
                "call_summary": {
                    "id": call_info.get("id", ""),
                    "title": call_info.get("title", ""),
                    "status": call_info.get("status", ""),
                    "call_type": call_info.get("call_type", ""),
                    "is_active": call_info.get("status") == "active",
                    "participants_count": len(call_info.get("participants", [])),
                    "channels_count": len(call_info.get("channels", [])),
                    "duration": call_data["call_duration"]
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'call_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified call was not found.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to retrieve call information. The bot needs calls:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs calls:read scope to retrieve call information.",
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

@mcp.tool()
async def slack_retrieve_conversation_information(
    channel: str,
    include_locale: bool = False,
    include_num_members: bool = False
) -> dict:
    """
    Retrieves metadata for a slack conversation by id (e.g., name, purpose, creation date, 
    with options for member count/locale), excluding message content; requires a valid channel id.
    
    Args:
        channel (str): Channel ID to retrieve information for
        include_locale (bool): Whether to include locale information
        include_num_members (bool): Whether to include member count
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the conversations.info method
        response = client.conversations_info(
            channel=channel,
            include_locale=include_locale,
            include_num_members=include_num_members
        )
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to retrieve conversation information. The bot needs channels:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs channels:read scope to retrieve conversation information.",
                    "successful": False
                }
            elif error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified channel was not found.",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe bot is not a member of the specified channel.",
                    "successful": False
                }
            elif error == 'invalid_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid channel ID provided.",
                    "successful": False
                }
            elif error == 'method_not_supported_for_channel_type':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis method is not supported for the specified channel type.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to retrieve conversation information: {error}",
                    "successful": False
                }
        
        # Get the conversation information from the response
        conversation_info = response.data.get("channel", {})
        
        # Format the conversation information
        conversation_data = {
            "id": conversation_info.get("id", ""),
            "name": conversation_info.get("name", ""),
            "is_channel": conversation_info.get("is_channel", False),
            "is_group": conversation_info.get("is_group", False),
            "is_im": conversation_info.get("is_im", False),
            "is_mpim": conversation_info.get("is_mpim", False),
            "is_private": conversation_info.get("is_private", False),
            "is_archived": conversation_info.get("is_archived", False),
            "is_general": conversation_info.get("is_general", False),
            "is_member": conversation_info.get("is_member", False),
            "is_muted": conversation_info.get("is_muted", False),
            "is_open": conversation_info.get("is_open", False),
            "created": conversation_info.get("created", 0),
            "creator": conversation_info.get("creator", ""),
            "num_members": conversation_info.get("num_members", 0),
            "topic": conversation_info.get("topic", {}),
            "purpose": conversation_info.get("purpose", {}),
            "previous_names": conversation_info.get("previous_names", []),
            "priority": conversation_info.get("priority", 0),
            "locale": conversation_info.get("locale", "") if include_locale else "",
            "channel_type": "channel" if conversation_info.get("is_channel") else "group" if conversation_info.get("is_group") else "im" if conversation_info.get("is_im") else "mpim" if conversation_info.get("is_mpim") else "unknown",
            "conversation_type": {
                "is_dm": conversation_info.get("is_im", False),
                "is_group_dm": conversation_info.get("is_mpim", False),
                "is_public_channel": conversation_info.get("is_channel", False) and not conversation_info.get("is_private", False),
                "is_private_channel": conversation_info.get("is_group", False) or (conversation_info.get("is_channel", False) and conversation_info.get("is_private", False))
            },
            "membership_info": {
                "is_member": conversation_info.get("is_member", False),
                "is_muted": conversation_info.get("is_muted", False),
                "is_open": conversation_info.get("is_open", False),
                "num_members": conversation_info.get("num_members", 0)
            },
            "metadata": {
                "created": conversation_info.get("created", 0),
                "creator": conversation_info.get("creator", ""),
                "is_archived": conversation_info.get("is_archived", False),
                "is_general": conversation_info.get("is_general", False),
                "previous_names": conversation_info.get("previous_names", []),
                "priority": conversation_info.get("priority", 0)
            }
        }
        
        # Add topic and purpose information
        if conversation_info.get("topic"):
            topic = conversation_info.get("topic", {})
            conversation_data["topic_info"] = {
                "value": topic.get("value", ""),
                "creator": topic.get("creator", ""),
                "last_set": topic.get("last_set", 0)
            }
        
        if conversation_info.get("purpose"):
            purpose = conversation_info.get("purpose", {})
            conversation_data["purpose_info"] = {
                "value": purpose.get("value", ""),
                "creator": purpose.get("creator", ""),
                "last_set": purpose.get("last_set", 0)
            }
        
        # Add locale information if requested
        if include_locale and conversation_info.get("locale"):
            conversation_data["locale_info"] = {
                "locale": conversation_info.get("locale", ""),
                "language": conversation_info.get("locale", "").split("_")[0] if conversation_info.get("locale") else "",
                "country": conversation_info.get("locale", "").split("_")[1] if conversation_info.get("locale") and "_" in conversation_info.get("locale", "") else ""
            }
        
        return {
            "data": {
                "conversation": conversation_data,
                "channel_id": channel,
                "retrieval_successful": True,
                "status": "conversation_info_retrieved",
                "message": "Conversation information retrieved successfully",
                "conversation_summary": {
                    "id": conversation_info.get("id", ""),
                    "name": conversation_info.get("name", ""),
                    "channel_type": conversation_data["channel_type"],
                    "is_private": conversation_info.get("is_private", False),
                    "is_archived": conversation_info.get("is_archived", False),
                    "is_member": conversation_info.get("is_member", False),
                    "num_members": conversation_info.get("num_members", 0),
                    "created": conversation_info.get("created", 0),
                    "creator": conversation_info.get("creator", "")
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to retrieve conversation information. The bot needs channels:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:read scope to retrieve conversation information.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified channel was not found.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of the specified channel.",
                "successful": False
            }
        elif error_code == 'invalid_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid channel ID provided.",
                "successful": False
            }
        elif error_code == 'method_not_supported_for_channel_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis method is not supported for the specified channel type.",
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

@mcp.tool()
async def slack_retrieve_conversation_members_list(
    channel: str,
    cursor: str = "",
    limit: int = 100
) -> dict:
    """
    Retrieves a paginated list of active member ids for a specified slack public channel, 
    private channel, direct message (dm), or multi-person direct message (mpim).
    
    Args:
        channel (str): Channel ID to retrieve members for
        cursor (str): Pagination cursor for next page
        limit (int): Maximum number of members to retrieve (default: 100)
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the conversations.members method
        params = {'channel': channel, 'limit': min(limit, 1000)}
        if cursor:
            params['cursor'] = cursor
        
        response = client.conversations_members(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to retrieve conversation members. The bot needs channels:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs channels:read scope to retrieve conversation members.",
                    "successful": False
                }
            elif error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified channel was not found.",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe bot is not a member of the specified channel.",
                    "successful": False
                }
            elif error == 'invalid_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid channel ID provided.",
                    "successful": False
                }
            elif error == 'method_not_supported_for_channel_type':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis method is not supported for the specified channel type.",
                    "successful": False
                }
            elif error == 'restricted_action':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis action is restricted. The channel may have restrictions on member access.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to retrieve conversation members: {error}",
                    "successful": False
                }
        
        # Get the members and pagination info from the response
        members = response.data.get("members", [])
        response_metadata = response.data.get("response_metadata", {})
        next_cursor = response_metadata.get("next_cursor", "")
        
        # Format the members information
        members_data = {
            "members": members,
            "member_count": len(members),
            "channel_id": channel,
            "pagination": {
                "cursor": cursor,
                "next_cursor": next_cursor,
                "has_more": bool(next_cursor),
                "limit": min(limit, 1000)
            },
            "retrieval_info": {
                "total_members_returned": len(members),
                "requested_limit": min(limit, 1000),
                "has_more_members": bool(next_cursor),
                "next_page_available": bool(next_cursor)
            }
        }
        
        return {
            "data": {
                "conversation_members": members_data,
                "channel_id": channel,
                "retrieval_successful": True,
                "status": "members_retrieved",
                "message": "Conversation members retrieved successfully",
                "members_summary": {
                    "channel_id": channel,
                    "member_count": len(members),
                    "has_more": bool(next_cursor),
                    "next_cursor": next_cursor,
                    "members": members[:10] if len(members) > 10 else members  # Show first 10 members
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to retrieve conversation members. The bot needs channels:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:read scope to retrieve conversation members.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified channel was not found.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of the specified channel.",
                "successful": False
            }
        elif error_code == 'invalid_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid channel ID provided.",
                "successful": False
            }
        elif error_code == 'method_not_supported_for_channel_type':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis method is not supported for the specified channel type.",
                "successful": False
            }
        elif error_code == 'restricted_action':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis action is restricted. The channel may have restrictions on member access.",
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

@mcp.tool()
async def slack_retrieve_current_user_dnd_status(
    user: str
) -> dict:
    """
    Retrieves a slack user's current do not disturb (dnd) status to determine their availability 
    before interaction; any specified user id must be a valid slack user id.
    
    Args:
        user (str): User ID to retrieve DND status for
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the dnd.info method
        response = client.dnd_info(user=user)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to retrieve DND status. The bot needs dnd:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs dnd:read scope to retrieve DND status.",
                    "successful": False
                }
            elif error == 'user_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified user was not found.",
                    "successful": False
                }
            elif error == 'invalid_user':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid user ID provided.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to retrieve DND status: {error}",
                    "successful": False
                }
        
        # Get the DND information from the response
        dnd_info = response.data.get("dnd_status", {})
        
        # Calculate time remaining if DND is active
        current_time = int(time.time())
        dnd_end_time = dnd_info.get("dnd_end_time", 0)
        time_remaining = max(0, dnd_end_time - current_time) if dnd_end_time > current_time else 0
        
        # Format the DND information
        dnd_data = {
            "user_id": user,
            "dnd_enabled": dnd_info.get("dnd_enabled", False),
            "next_dnd_start_ts": dnd_info.get("next_dnd_start_ts", 0),
            "next_dnd_end_ts": dnd_info.get("next_dnd_end_ts", 0),
            "snooze_enabled": dnd_info.get("snooze_enabled", False),
            "snooze_endtime": dnd_info.get("snooze_endtime", 0),
            "snooze_remaining": dnd_info.get("snooze_remaining", 0),
            "dnd_end_time": dnd_end_time,
            "time_remaining": time_remaining,
            "is_currently_dnd": dnd_info.get("dnd_enabled", False) and dnd_end_time > current_time,
            "dnd_status": {
                "enabled": dnd_info.get("dnd_enabled", False),
                "end_time": dnd_end_time,
                "time_remaining": time_remaining,
                "is_active": dnd_info.get("dnd_enabled", False) and dnd_end_time > current_time
            },
            "snooze_status": {
                "enabled": dnd_info.get("snooze_enabled", False),
                "end_time": dnd_info.get("snooze_endtime", 0),
                "remaining": dnd_info.get("snooze_remaining", 0),
                "is_active": dnd_info.get("snooze_enabled", False) and dnd_info.get("snooze_endtime", 0) > current_time
            },
            "scheduled_dnd": {
                "next_start": dnd_info.get("next_dnd_start_ts", 0),
                "next_end": dnd_info.get("next_dnd_end_ts", 0),
                "has_scheduled": dnd_info.get("next_dnd_start_ts", 0) > 0
            },
            "availability": {
                "is_available": not (dnd_info.get("dnd_enabled", False) and dnd_end_time > current_time),
                "is_dnd_active": dnd_info.get("dnd_enabled", False) and dnd_end_time > current_time,
                "is_snoozed": dnd_info.get("snooze_enabled", False) and dnd_info.get("snooze_endtime", 0) > current_time,
                "can_be_contacted": not (dnd_info.get("dnd_enabled", False) and dnd_end_time > current_time) and not (dnd_info.get("snooze_enabled", False) and dnd_info.get("snooze_endtime", 0) > current_time)
            }
        }
        
        return {
            "data": {
                "dnd_status": dnd_data,
                "user_id": user,
                "retrieval_successful": True,
                "status": "dnd_status_retrieved",
                "message": "DND status retrieved successfully",
                "dnd_summary": {
                    "user_id": user,
                    "is_dnd_active": dnd_data["is_currently_dnd"],
                    "is_available": dnd_data["availability"]["is_available"],
                    "can_be_contacted": dnd_data["availability"]["can_be_contacted"],
                    "time_remaining": time_remaining,
                    "dnd_end_time": dnd_end_time,
                    "is_snoozed": dnd_data["availability"]["is_snoozed"]
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to retrieve DND status. The bot needs dnd:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs dnd:read scope to retrieve DND status.",
                "successful": False
            }
        elif error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified user was not found.",
                "successful": False
            }
        elif error_code == 'invalid_user':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid user ID provided.",
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

@mcp.tool()
async def slack_retrieve_detailed_user_information(
    user: str,
    include_locale: bool = False
) -> dict:
    """
    Retrieves comprehensive information for a valid slack user id, excluding message history 
    and channel memberships.
    
    Args:
        user (str): User ID to retrieve information for
        include_locale (bool): Whether to include locale information
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the users.info method
        response = client.users_info(user=user, include_locale=include_locale)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to retrieve user information. The bot needs users:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs users:read scope to retrieve user information.",
                    "successful": False
                }
            elif error == 'user_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified user was not found.",
                    "successful": False
                }
            elif error == 'invalid_user':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid user ID provided.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to retrieve user information: {error}",
                    "successful": False
                }
        
        # Get the user information from the response
        user_info = response.data.get("user", {})
        
        # Format the user information
        user_data = {
            "id": user_info.get("id", ""),
            "name": user_info.get("name", ""),
            "real_name": user_info.get("real_name", ""),
            "display_name": user_info.get("display_name", ""),
            "profile": user_info.get("profile", {}),
            "is_admin": user_info.get("is_admin", False),
            "is_owner": user_info.get("is_owner", False),
            "is_primary_owner": user_info.get("is_primary_owner", False),
            "is_restricted": user_info.get("is_restricted", False),
            "is_ultra_restricted": user_info.get("is_ultra_restricted", False),
            "is_bot": user_info.get("is_bot", False),
            "is_app_user": user_info.get("is_app_user", False),
            "is_invited_user": user_info.get("is_invited_user", False),
            "is_stranger": user_info.get("is_stranger", False),
            "is_workflow_bot": user_info.get("is_workflow_bot", False),
            "deleted": user_info.get("deleted", False),
            "has_2fa": user_info.get("has_2fa", False),
            "two_factor_type": user_info.get("two_factor_type", ""),
            "tz": user_info.get("tz", ""),
            "tz_label": user_info.get("tz_label", ""),
            "tz_offset": user_info.get("tz_offset", 0),
            "locale": user_info.get("locale", "") if include_locale else "",
            "updated": user_info.get("updated", 0),
            "enterprise_user": user_info.get("enterprise_user", {}),
            "user_type": "bot" if user_info.get("is_bot") else "app" if user_info.get("is_app_user") else "workflow" if user_info.get("is_workflow_bot") else "user",
            "status": {
                "status_text": user_info.get("profile", {}).get("status_text", ""),
                "status_emoji": user_info.get("profile", {}).get("status_emoji", ""),
                "status_expiration": user_info.get("profile", {}).get("status_expiration", 0)
            },
            "presence": user_info.get("presence", ""),
            "profile_info": {
                "first_name": user_info.get("profile", {}).get("first_name", ""),
                "last_name": user_info.get("profile", {}).get("last_name", ""),
                "real_name": user_info.get("profile", {}).get("real_name", ""),
                "display_name": user_info.get("profile", {}).get("display_name", ""),
                "email": user_info.get("profile", {}).get("email", ""),
                "phone": user_info.get("profile", {}).get("phone", ""),
                "title": user_info.get("profile", {}).get("title", ""),
                "skype": user_info.get("profile", {}).get("skype", ""),
                "status_text": user_info.get("profile", {}).get("status_text", ""),
                "status_emoji": user_info.get("profile", {}).get("status_emoji", ""),
                "status_expiration": user_info.get("profile", {}).get("status_expiration", 0),
                "avatar_hash": user_info.get("profile", {}).get("avatar_hash", ""),
                "image_24": user_info.get("profile", {}).get("image_24", ""),
                "image_32": user_info.get("profile", {}).get("image_32", ""),
                "image_48": user_info.get("profile", {}).get("image_48", ""),
                "image_72": user_info.get("profile", {}).get("image_72", ""),
                "image_192": user_info.get("profile", {}).get("image_192", ""),
                "image_512": user_info.get("profile", {}).get("image_512", ""),
                "image_1024": user_info.get("profile", {}).get("image_1024", ""),
                "is_custom_image": user_info.get("profile", {}).get("is_custom_image", False)
            },
            "team_info": {
                "team_id": user_info.get("team_id", ""),
                "enterprise_user": user_info.get("enterprise_user", {}),
                "is_admin": user_info.get("is_admin", False),
                "is_owner": user_info.get("is_owner", False),
                "is_primary_owner": user_info.get("is_primary_owner", False)
            },
            "security_info": {
                "has_2fa": user_info.get("has_2fa", False),
                "two_factor_type": user_info.get("two_factor_type", ""),
                "is_restricted": user_info.get("is_restricted", False),
                "is_ultra_restricted": user_info.get("is_ultra_restricted", False)
            },
            "timezone_info": {
                "tz": user_info.get("tz", ""),
                "tz_label": user_info.get("tz_label", ""),
                "tz_offset": user_info.get("tz_offset", 0)
            }
        }
        
        # Add locale information if requested
        if include_locale and user_info.get("locale"):
            user_data["locale_info"] = {
                "locale": user_info.get("locale", ""),
                "language": user_info.get("locale", "").split("_")[0] if user_info.get("locale") else "",
                "country": user_info.get("locale", "").split("_")[1] if user_info.get("locale") and "_" in user_info.get("locale", "") else ""
            }
        
        return {
            "data": {
                "user": user_data,
                "user_id": user,
                "retrieval_successful": True,
                "status": "user_info_retrieved",
                "message": "User information retrieved successfully",
                "user_summary": {
                    "id": user_info.get("id", ""),
                    "name": user_info.get("name", ""),
                    "real_name": user_info.get("real_name", ""),
                    "display_name": user_info.get("display_name", ""),
                    "is_bot": user_info.get("is_bot", False),
                    "is_admin": user_info.get("is_admin", False),
                    "is_owner": user_info.get("is_owner", False),
                    "deleted": user_info.get("deleted", False),
                    "has_2fa": user_info.get("has_2fa", False),
                    "presence": user_info.get("presence", ""),
                    "user_type": user_data["user_type"]
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to retrieve user information. The bot needs users:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs users:read scope to retrieve user information.",
                "successful": False
            }
        elif error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified user was not found.",
                "successful": False
            }
        elif error_code == 'invalid_user':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid user ID provided.",
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

@mcp.tool()
async def slack_retrieve_message_permalink_url(
    channel: str,
    message_ts: str
) -> dict:
    """
    Retrieves a permalink url for a specific message in a slack channel or conversation; 
    the permalink respects slack's privacy settings.
    
    Args:
        channel (str): Channel ID where the message is located
        message_ts (str): Message timestamp to get permalink for
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the chat.getPermalink method
        response = client.chat_getPermalink(channel=channel, message_ts=message_ts)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to retrieve message permalink. The bot needs channels:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs channels:read scope to retrieve message permalink.",
                    "successful": False
                }
            elif error == 'channel_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified channel was not found.",
                    "successful": False
                }
            elif error == 'message_not_found':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe specified message was not found.",
                    "successful": False
                }
            elif error == 'not_in_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe bot is not a member of the specified channel.",
                    "successful": False
                }
            elif error == 'invalid_channel':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid channel ID provided.",
                    "successful": False
                }
            elif error == 'invalid_timestamp':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid message timestamp provided.",
                    "successful": False
                }
            elif error == 'message_too_old':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe message is too old to create a permalink.",
                    "successful": False
                }
            elif error == 'restricted_action':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThis action is restricted. The channel may have restrictions on permalink access.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to retrieve message permalink: {error}",
                    "successful": False
                }
        
        # Get the permalink information from the response
        permalink = response.data.get("permalink", "")
        
        # Format the permalink information
        permalink_data = {
            "permalink": permalink,
            "channel_id": channel,
            "message_ts": message_ts,
            "url": permalink,
            "permalink_info": {
                "permalink": permalink,
                "channel_id": channel,
                "message_ts": message_ts,
                "is_valid": bool(permalink),
                "url_components": {
                    "workspace": permalink.split("//")[1].split(".")[0] if "//" in permalink and "." in permalink else "",
                    "channel": channel,
                    "timestamp": message_ts
                }
            },
            "access_info": {
                "requires_channel_access": True,
                "respects_privacy_settings": True,
                "workspace_restricted": True
            }
        }
        
        return {
            "data": {
                "message_permalink": permalink_data,
                "channel_id": channel,
                "message_ts": message_ts,
                "retrieval_successful": True,
                "status": "permalink_retrieved",
                "message": "Message permalink retrieved successfully",
                "permalink_summary": {
                    "permalink": permalink,
                    "channel_id": channel,
                    "message_ts": message_ts,
                    "is_valid": bool(permalink),
                    "url": permalink
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to retrieve message permalink. The bot needs channels:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:read scope to retrieve message permalink.",
                "successful": False
            }
        elif error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified channel was not found.",
                "successful": False
            }
        elif error_code == 'message_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified message was not found.",
                "successful": False
            }
        elif error_code == 'not_in_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe bot is not a member of the specified channel.",
                "successful": False
            }
        elif error_code == 'invalid_channel':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid channel ID provided.",
                "successful": False
            }
        elif error_code == 'invalid_timestamp':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid message timestamp provided.",
                "successful": False
            }
        elif error_code == 'message_too_old':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe message is too old to create a permalink.",
                "successful": False
            }
        elif error_code == 'restricted_action':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis action is restricted. The channel may have restrictions on permalink access.",
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

@mcp.tool()
async def slack_retrieve_team_profile_details(
    visibility: str = ""
) -> dict:
    """
    Retrieves all profile field definitions for a slack team, optionally filtered by visibility, 
    to understand the team's profile structure.
    
    Args:
        visibility (str): Filter by visibility (e.g., "all", "visible", "hidden")
        
    Returns:
        dict: Response with data, error, and successful fields
    """
    try:
        client = get_slack_client()
        
        # Use the team.profile.get method
        params = {}
        if visibility:
            params['visibility'] = visibility
        
        response = client.team_profile_get(**params)
        
        if not response.data.get("ok", False):
            error = response.data.get('error', 'Unknown error')
            if error == 'not_authed':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'invalid_auth':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                    "successful": False
                }
            elif error == 'account_inactive':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token belongs to a deactivated user.",
                    "successful": False
                }
            elif error == 'token_revoked':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nThe authentication token has been revoked.",
                    "successful": False
                }
            elif error == 'no_permission':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInsufficient permissions to retrieve team profile details. The bot needs team.profile:read scope.",
                    "successful": False
                }
            elif error == 'missing_scope':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nMissing required OAuth scope. The bot needs team.profile:read scope to retrieve team profile details.",
                    "successful": False
                }
            elif error == 'invalid_visibility':
                return {
                    "data": {},
                    "error": f"Slack API Error: {error}\n\nInvalid visibility filter provided. Use 'all', 'visible', or 'hidden'.",
                    "successful": False
                }
            else:
                return {
                    "data": {},
                    "error": f"Failed to retrieve team profile details: {error}",
                    "successful": False
                }
        
        # Get the profile fields from the response
        profile_fields = response.data.get("profile", {}).get("fields", [])
        
        # Format the profile fields information
        profile_data = {
            "fields": profile_fields,
            "field_count": len(profile_fields),
            "visibility_filter": visibility if visibility else "all",
            "profile_structure": {
                "total_fields": len(profile_fields),
                "visible_fields": len([f for f in profile_fields if f.get("is_hidden", False) == False]),
                "hidden_fields": len([f for f in profile_fields if f.get("is_hidden", False) == True]),
                "required_fields": len([f for f in profile_fields if f.get("is_required", False) == True]),
                "optional_fields": len([f for f in profile_fields if f.get("is_required", False) == False])
            },
            "field_categories": {
                "text_fields": [f for f in profile_fields if f.get("type") == "text"],
                "email_fields": [f for f in profile_fields if f.get("type") == "email"],
                "phone_fields": [f for f in profile_fields if f.get("type") == "phone"],
                "date_fields": [f for f in profile_fields if f.get("type") == "date"],
                "link_fields": [f for f in profile_fields if f.get("type") == "link"],
                "options_fields": [f for f in profile_fields if f.get("type") == "options"]
            },
            "field_details": []
        }
        
        # Process each field for detailed information
        for field in profile_fields:
            field_info = {
                "id": field.get("id", ""),
                "ordering": field.get("ordering", 0),
                "label": field.get("label", ""),
                "hint": field.get("hint", ""),
                "type": field.get("type", ""),
                "possible_values": field.get("possible_values", []),
                "options": field.get("options", []),
                "is_hidden": field.get("is_hidden", False),
                "is_required": field.get("is_required", False),
                "is_read_only": field.get("is_read_only", False),
                "field_metadata": {
                    "id": field.get("id", ""),
                    "label": field.get("label", ""),
                    "hint": field.get("hint", ""),
                    "type": field.get("type", ""),
                    "ordering": field.get("ordering", 0)
                },
                "field_settings": {
                    "is_hidden": field.get("is_hidden", False),
                    "is_required": field.get("is_required", False),
                    "is_read_only": field.get("is_read_only", False)
                },
                "field_options": {
                    "possible_values": field.get("possible_values", []),
                    "options": field.get("options", []),
                    "has_options": bool(field.get("options", [])),
                    "has_possible_values": bool(field.get("possible_values", []))
                }
            }
            profile_data["field_details"].append(field_info)
        
        return {
            "data": {
                "team_profile": profile_data,
                "visibility_filter": visibility if visibility else "all",
                "retrieval_successful": True,
                "status": "profile_details_retrieved",
                "message": "Team profile details retrieved successfully",
                "profile_summary": {
                    "total_fields": len(profile_fields),
                    "visible_fields": len([f for f in profile_fields if f.get("is_hidden", False) == False]),
                    "hidden_fields": len([f for f in profile_fields if f.get("is_hidden", False) == True]),
                    "required_fields": len([f for f in profile_fields if f.get("is_required", False) == True]),
                    "field_types": list(set([f.get("type", "") for f in profile_fields])),
                    "visibility_filter": visibility if visibility else "all"
                }
            },
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        error_code = e.response.get('error', 'unknown_error')
        if error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAuthentication failed. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid authentication token. Please check your SLACK_BOT_TOKEN.",
                "successful": False
            }
        elif error_code == 'account_inactive':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token belongs to a deactivated user.",
                "successful": False
            }
        elif error_code == 'token_revoked':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to retrieve team profile details. The bot needs team.profile:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs team.profile:read scope to retrieve team profile details.",
                "successful": False
            }
        elif error_code == 'invalid_visibility':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInvalid visibility filter provided. Use 'all', 'visible', or 'hidden'.",
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

@mcp.tool()
def slack_retrieve_user_profile_information(include_labels: bool = False, user: str = None) -> dict:
    """
    Retrieves profile information for a specified slack user (defaults to the authenticated user if `user` id is omitted); a provided `user` id must be valid.
    """
    try:
        # Get Slack client
        client = get_slack_client()
        
        # Prepare parameters
        params = {
            "include_labels": include_labels
        }
        
        # Add user parameter if provided
        if user:
            params["user"] = user
        
        # Call Slack API
        response = client.users_profile_get(**params)
        
        # Check if the API call was successful
        if response["ok"]:
            return {
                "data": {
                    "user": response["profile"]
                },
                "error": None,
                "successful": True
            }
        else:
            error = response.get("error", "unknown_error")
            return {
                "data": {},
                "error": f"Slack API Error: {error}",
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response["error"]
        
        if error_code == 'user_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified user ID does not exist or is not accessible.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token is missing or invalid.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to retrieve user profile information. The bot needs users:read scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs users:read scope to retrieve user profile information.",
                "successful": False
            }
        elif error_code == 'invalid_user':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe provided user ID is invalid or malformed.",
                "successful": False
            }
        elif error_code == 'user_not_visible':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified user is not visible to the bot or the user has restricted their profile visibility.",
                "successful": False
            }
        else:
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAn unexpected error occurred while retrieving user profile information.",
                "successful": False
            }
            
    except Exception as e:
        return {
            "data": {},
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }

@mcp.tool()
def slack_reverse_a_conversation_s_archival_status(channel: str) -> dict:
    """
    Deprecated: reverses conversation archival. use `unarchive channel` instead.
    """
    try:
        # Get Slack client
        client = get_slack_client()
        
        # Call Slack API
        response = client.conversations_unarchive(channel=channel)
        
        # Check if the API call was successful
        if response["ok"]:
            return {
                "data": {
                    "channel": channel,
                    "message": "Conversation has been unarchived successfully"
                },
                "error": None,
                "successful": True
            }
        else:
            error = response.get("error", "unknown_error")
            return {
                "data": {},
                "error": f"Slack API Error: {error}",
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response["error"]
        
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified channel does not exist or is not accessible.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token is missing or invalid.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to unarchive the conversation. The bot needs channels:manage scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs channels:manage scope to unarchive conversations.",
                "successful": False
            }
        elif error_code == 'not_archived':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified conversation is not archived.",
                "successful": False
            }
        elif error_code == 'cant_unarchive_general':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe #general channel cannot be unarchived.",
                "successful": False
            }
        elif error_code == 'restricted_action':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis action is restricted and cannot be performed on this conversation.",
                "successful": False
            }
        else:
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAn unexpected error occurred while unarchiving the conversation.",
                "successful": False
            }
            
    except Exception as e:
        return {
            "data": {},
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }

@mcp.tool()
def slack_schedule_message(
    channel: str,
    post_at: str,
    text: Optional[str] = None,
    blocks: Optional[str] = None,
    attachments: Optional[str] = None,
    as_user: bool = False,
    link_names: bool = False,
    markdown_text: Optional[str] = None,
    parse: Optional[str] = None,
    reply_broadcast: bool = False,
    thread_ts: Optional[str] = None,
    unfurl_links: bool = True,
    unfurl_media: bool = True
) -> dict:
    """
    Schedules a message to a slack channel, dm, or private group for a future time (`post at`), requiring `text`, `blocks`, or `attachments` for content; scheduling is limited to 120 days in advance.
    """
    try:
        # Get Slack client
        client = get_slack_client()
        
        # Prepare parameters
        params = {
            "channel": channel,
            "post_at": post_at
        }
        
        # Add content parameters (at least one is required)
        if text:
            params["text"] = text
        if blocks:
            params["blocks"] = blocks
        if attachments:
            params["attachments"] = attachments
        
        # Add optional parameters
        if as_user is not None:
            params["as_user"] = as_user
        if link_names is not None:
            params["link_names"] = link_names
        if markdown_text:
            params["markdown_text"] = markdown_text
        if parse:
            params["parse"] = parse
        if reply_broadcast is not None:
            params["reply_broadcast"] = reply_broadcast
        if thread_ts:
            params["thread_ts"] = thread_ts
        if unfurl_links is not None:
            params["unfurl_links"] = unfurl_links
        if unfurl_media is not None:
            params["unfurl_media"] = unfurl_media
        
        # Call Slack API
        response = client.chat_scheduleMessage(**params)
        
        # Check if the API call was successful
        if response["ok"]:
            return {
                "data": {
                    "channel": response.get("channel"),
                    "scheduled_message_id": response.get("scheduled_message_id"),
                    "post_at": response.get("post_at"),
                    "message": response.get("message")
                },
                "error": None,
                "successful": True
            }
        else:
            error = response.get("error", "unknown_error")
            return {
                "data": {},
                "error": f"Slack API Error: {error}",
                "successful": False
            }
            
    except SlackApiError as e:
        error_code = e.response["error"]
        
        if error_code == 'channel_not_found':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe specified channel does not exist or is not accessible.",
                "successful": False
            }
        elif error_code == 'not_authed':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token is missing or invalid.",
                "successful": False
            }
        elif error_code == 'invalid_auth':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe authentication token has been revoked.",
                "successful": False
            }
        elif error_code == 'no_permission':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nInsufficient permissions to schedule messages. The bot needs chat:write scope.",
                "successful": False
            }
        elif error_code == 'missing_scope':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMissing required OAuth scope. The bot needs chat:write scope to schedule messages.",
                "successful": False
            }
        elif error_code == 'invalid_time':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe scheduled time is invalid. Ensure the time is in the future and within 120 days.",
                "successful": False
            }
        elif error_code == 'time_in_past':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe scheduled time is in the past. Please schedule for a future time.",
                "successful": False
            }
        elif error_code == 'time_too_far':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThe scheduled time is too far in the future. Maximum scheduling is 120 days in advance.",
                "successful": False
            }
        elif error_code == 'no_text':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nMessage content is required. Provide text, blocks, or attachments.",
                "successful": False
            }
        elif error_code == 'restricted_action':
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nThis action is restricted and cannot be performed on this channel.",
                "successful": False
            }
        else:
            return {
                "data": {},
                "error": f"Slack API Error: {error_code}\n\nAn unexpected error occurred while scheduling the message.",
                "successful": False
            }
            
    except Exception as e:
        return {
            "data": {},
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }

@mcp.tool()
def slack_schedules_a_message_to_a_channel_at_a_specified_time(
    channel: str,
    post_at: str,
    text: Optional[str] = None,
    blocks: Optional[str] = None,
    attachments: Optional[str] = None,
    as_user: bool = False,
    link_names: bool = False,
    markdown_text: Optional[str] = None,
    parse: Optional[str] = None,
    reply_broadcast: bool = False,
    thread_ts: Optional[str] = None,
    unfurl_links: bool = True,
    unfurl_media: bool = True
) -> dict:
    """
    Deprecated: schedules a message to a slack channel, dm, or private group for a future time. use `schedule message` instead.
    """
    try:
        # Get Slack client
        client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        
        # Prepare parameters
        params = {
            "channel": channel,
            "post_at": post_at,
            "as_user": as_user,
            "link_names": link_names,
            "reply_broadcast": reply_broadcast,
            "unfurl_links": unfurl_links,
            "unfurl_media": unfurl_media
        }
        
        # Add optional parameters if provided
        if text is not None:
            params["text"] = text
        if blocks is not None:
            params["blocks"] = blocks
        if attachments is not None:
            params["attachments"] = attachments
        if markdown_text is not None:
            params["markdown_text"] = markdown_text
        if parse is not None:
            params["parse"] = parse
        if thread_ts is not None:
            params["thread_ts"] = thread_ts
        
        # Schedule the message
        response = client.chat_scheduleMessage(**params)
        
        return {
            "data": response.data,
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        return {
            "data": {},
            "error": f"Slack API Error: {e.response['error']}",
            "successful": False
        }
    except Exception as e:
        return {
            "data": {},
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }

@mcp.tool()
def slack_search_for_messages_with_query(
    query: str,
    auto_paginate: bool = False,
    count: int = 1,
    highlight: bool = False,
    page: int = 1,
    sort: str = "score",
    sort_dir: str = "desc"
) -> dict:
    """
    Deprecated: searches messages in a slack workspace using a query with optional modifiers. use `search messages` instead.
    """
    try:
        # Get Slack client - search requires user token, not bot token
        client = WebClient(token=os.getenv("SLACK_USER_TOKEN"))
        
        # Prepare parameters
        params = {
            "query": query,
            "count": count,
            "highlight": highlight,
            "page": page,
            "sort": sort,
            "sort_dir": sort_dir
        }
        
        # Search messages
        response = client.search_messages(**params)
        
        return {
            "data": response.data,
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        return {
            "data": {},
            "error": f"Slack API Error: {e.response['error']}",
            "successful": False
        }
    except Exception as e:
        return {
            "data": {},
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }

@mcp.tool()
def slack_search_messages(
    query: str,
    auto_paginate: bool = False,
    count: int = 1,
    highlight: bool = False,
    page: int = 1,
    sort: str = "score",
    sort_dir: str = "desc"
) -> dict:
    """
    Workspace‑wide slack message search with date ranges and filters. use `query` modifiers (e.g., in:#channel, from:@user, before/after:yyyy-mm-dd), sorting (score/timestamp), and pagination.
    """
    try:
        # Get Slack client - search requires user token, not bot token
        client = WebClient(token=os.getenv("SLACK_USER_TOKEN"))
        
        # Prepare parameters
        params = {
            "query": query,
            "count": count,
            "highlight": highlight,
            "page": page,
            "sort": sort,
            "sort_dir": sort_dir
        }
        
        # Search messages
        response = client.search_messages(**params)
        
        return {
            "data": response.data,
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        return {
            "data": {},
            "error": f"Slack API Error: {e.response['error']}",
            "successful": False
        }
    except Exception as e:
        return {
            "data": {},
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }

@mcp.tool()
def slack_send_ephemeral_message(
    channel: str,
    user: str,
    text: Optional[str] = None,
    attachments: Optional[str] = None,
    blocks: Optional[str] = None,
    as_user: bool = False,
    icon_emoji: Optional[str] = None,
    icon_url: Optional[str] = None,
    link_names: bool = False,
    parse: Optional[str] = None,
    thread_ts: Optional[str] = None,
    username: Optional[str] = None
) -> dict:
    """
    Sends an ephemeral message to a user in a channel.
    """
    try:
        # Get Slack client
        client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        
        # Prepare parameters
        params = {
            "channel": channel,
            "user": user,
            "as_user": as_user,
            "link_names": link_names
        }
        
        # Add optional parameters if provided
        if text is not None:
            params["text"] = text
        if attachments is not None:
            params["attachments"] = attachments
        if blocks is not None:
            params["blocks"] = blocks
        if icon_emoji is not None:
            params["icon_emoji"] = icon_emoji
        if icon_url is not None:
            params["icon_url"] = icon_url
        if parse is not None:
            params["parse"] = parse
        if thread_ts is not None:
            params["thread_ts"] = thread_ts
        if username is not None:
            params["username"] = username
        
        # Send ephemeral message
        response = client.chat_postEphemeral(**params)
        
        return {
            "data": response.data,
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        return {
            "data": {},
            "error": f"Slack API Error: {e.response['error']}",
            "successful": False
        }
    except Exception as e:
        return {
            "data": {},
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }

@mcp.tool()
def slack_sends_a_message_to_a_slack_channel(
    channel: str,
    text: Optional[str] = None,
    blocks: Optional[str] = None,
    attachments: Optional[str] = None,
    as_user: bool = False,
    icon_emoji: Optional[str] = None,
    icon_url: Optional[str] = None,
    link_names: bool = False,
    markdown_text: Optional[str] = None,
    mrkdwn: bool = True,
    parse: Optional[str] = None,
    reply_broadcast: bool = False,
    thread_ts: Optional[str] = None,
    unfurl_links: bool = True,
    unfurl_media: bool = True,
    username: Optional[str] = None
) -> dict:
    """
    Deprecated: posts a message to a slack channel, direct message, or private group. use `send message` instead.
    """
    try:
        # Get Slack client
        client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        
        # Prepare parameters
        params = {
            "channel": channel,
            "as_user": as_user,
            "link_names": link_names,
            "mrkdwn": mrkdwn,
            "reply_broadcast": reply_broadcast,
            "unfurl_links": unfurl_links,
            "unfurl_media": unfurl_media
        }
        
        # Add optional parameters if provided
        if text is not None:
            params["text"] = text
        if blocks is not None:
            params["blocks"] = blocks
        if attachments is not None:
            params["attachments"] = attachments
        if icon_emoji is not None:
            params["icon_emoji"] = icon_emoji
        if icon_url is not None:
            params["icon_url"] = icon_url
        if markdown_text is not None:
            params["markdown_text"] = markdown_text
        if parse is not None:
            params["parse"] = parse
        if thread_ts is not None:
            params["thread_ts"] = thread_ts
        if username is not None:
            params["username"] = username
        
        # Post message
        response = client.chat_postMessage(**params)
        
        return {
            "data": response.data,
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        return {
            "data": {},
            "error": f"Slack API Error: {e.response['error']}",
            "successful": False
        }
    except Exception as e:
        return {
            "data": {},
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }

@mcp.tool()
def slack_sends_ephemeral_messages_to_channel_users(
    channel: str,
    user: str,
    text: Optional[str] = None,
    attachments: Optional[str] = None,
    blocks: Optional[str] = None,
    as_user: bool = False,
    icon_emoji: Optional[str] = None,
    icon_url: Optional[str] = None,
    link_names: bool = False,
    parse: Optional[str] = None,
    thread_ts: Optional[str] = None,
    username: Optional[str] = None
) -> dict:
    """
    Deprecated: sends an ephemeral message to a user in a channel. use `send ephemeral message` instead.
    """
    try:
        # Get Slack client
        client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        
        # Prepare parameters
        params = {
            "channel": channel,
            "user": user,
            "as_user": as_user,
            "link_names": link_names
        }
        
        # Add optional parameters if provided
        if text is not None:
            params["text"] = text
        if attachments is not None:
            params["attachments"] = attachments
        if blocks is not None:
            params["blocks"] = blocks
        if icon_emoji is not None:
            params["icon_emoji"] = icon_emoji
        if icon_url is not None:
            params["icon_url"] = icon_url
        if parse is not None:
            params["parse"] = parse
        if thread_ts is not None:
            params["thread_ts"] = thread_ts
        if username is not None:
            params["username"] = username
        
        # Send ephemeral message
        response = client.chat_postEphemeral(**params)
        
        return {
            "data": response.data,
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        return {
            "data": {},
            "error": f"Slack API Error: {e.response['error']}",
            "successful": False
        }
    except Exception as e:
        return {
            "data": {},
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }

@mcp.tool()
def slack_set_a_conversation_s_purpose(
    channel: str,
    purpose: str
) -> dict:
    """
    Sets the purpose (a short description of its topic/goal, displayed in the header) for a slack conversation; the calling user must be a member.
    """
    try:
        # Get Slack client
        client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        
        # Set conversation purpose
        response = client.conversations_setPurpose(
            channel=channel,
            purpose=purpose
        )
        
        return {
            "data": response.data,
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        return {
            "data": {},
            "error": f"Slack API Error: {e.response['error']}",
            "successful": False
        }
    except Exception as e:
        return {
            "data": {},
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }

@mcp.tool()
def slack_set_dnd_duration(
    num_minutes: str
) -> dict:
    """
    Turns on do not disturb mode for the current user, or changes its duration.
    """
    try:
        # Get Slack client - DND requires user token, not bot token
        client = WebClient(token=os.getenv("SLACK_USER_TOKEN"))
        
        # Set DND duration
        response = client.dnd_setSnooze(
            num_minutes=int(num_minutes)
        )
        
        return {
            "data": response.data,
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        return {
            "data": {},
            "error": f"Slack API Error: {e.response['error']}",
            "successful": False
        }
    except Exception as e:
        return {
            "data": {},
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }

@mcp.tool()
def slack_set_profile_photo(
    image: str,
    crop_w: Optional[int] = None,
    crop_x: Optional[int] = None,
    crop_y: Optional[int] = None
) -> dict:
    """
    This method allows the user to set their profile image.
    """
    try:
        # Get Slack client - profile photo requires user token, not bot token
        client = WebClient(token=os.getenv("SLACK_USER_TOKEN"))
        
        # Clean the image path - remove quotes and normalize path
        clean_image_path = image.strip().strip('"').strip("'")
        
        # Prepare parameters
        params = {
            "image": clean_image_path
        }
        
        # Add optional crop parameters if provided
        if crop_w is not None:
            params["crop_w"] = crop_w
        if crop_x is not None:
            params["crop_x"] = crop_x
        if crop_y is not None:
            params["crop_y"] = crop_y
        
        # Set profile photo
        response = client.users_setPhoto(**params)
        
        return {
            "data": response.data,
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        return {
            "data": {},
            "error": f"Slack API Error: {e.response['error']}",
            "successful": False
        }
    except Exception as e:
        return {
            "data": {},
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }

@mcp.tool()
def slack_set_read_cursor_in_a_conversation(
    channel: str,
    ts: int
) -> dict:
    """
    Marks a message, specified by its timestamp (`ts`), as the most recently read for the authenticated user in the given `channel`, provided the user is a member of the channel and the message exists within it.
    """
    try:
        # Get Slack client
        client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        
        # Set read cursor - convert timestamp to proper format
        # Slack expects timestamps as strings in format "1234567890.123456"
        if isinstance(ts, int):
            # Convert integer timestamp to string format with decimal places
            ts_str = f"{ts}.000000"
        else:
            # Already a string, use as is
            ts_str = str(ts)
        
        response = client.conversations_mark(
            channel=channel,
            ts=ts_str
        )
        
        return {
            "data": response.data,
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        return {
            "data": {},
            "error": f"Slack API Error: {e.response['error']}",
            "successful": False
        }
    except Exception as e:
        return {
            "data": {},
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }

@mcp.tool()
def slack_set_slack_user_profile_information(
    user: str,
    name: Optional[str] = None,
    profile: Optional[str] = None,
    value: Optional[str] = None
) -> dict:
    """
    Updates a slack user's profile, setting either individual fields or multiple fields via a json object.
    """
    try:
        # Get Slack client - profile updates require user token, not bot token
        client = WebClient(token=os.getenv("SLACK_USER_TOKEN"))
        
        # Prepare parameters
        params = {
            "user": user
        }
        
        # Add optional parameters if provided
        if name is not None:
            params["name"] = name
        if profile is not None:
            # Parse profile JSON if provided
            try:
                import json
                params["profile"] = json.loads(profile)
            except json.JSONDecodeError:
                return {
                    "data": {},
                    "error": "Invalid JSON format for profile parameter",
                    "successful": False
                }
        if value is not None:
            params["value"] = value
        
        # Update user profile
        response = client.users_profile_set(**params)
        
        return {
            "data": response.data,
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        return {
            "data": {},
            "error": f"Slack API Error: {e.response['error']}",
            "successful": False
        }
    except Exception as e:
        return {
            "data": {},
            "error": f"Unexpected error: {str(e)}",
            "successful": False
        }

@mcp.tool()
def slack_set_the_topic_of_a_conversation(
    channel: str,
    topic: str
) -> dict:
    """
    Sets or updates the topic for a specified slack conversation.
    """
    try:
        # Get Slack client
        client = WebClient(token=os.getenv("SLACK_BOT_TOKEN"))
        
        # Set conversation topic
        response = client.conversations_setTopic(
            channel=channel,
            topic=topic
        )
        
        return {
            "data": response.data,
            "error": "",
            "successful": True
        }
        
    except SlackApiError as e:
        return {
            "data": {},
            "error": f"Slack API Error: {e.response['error']}",
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
