"""
Cortana Discord Bot - Main Entry Point
=======================================

Handles Discord client initialization, message processing,
and slash command registration.
"""

import discord
from discord import app_commands
import asyncio
import logging

from .config import config
from . import agent
from .memory import memory_client
from .scheduler import ReminderScheduler
from .rotator_client import (
    get_rotating_client,
    close_rotating_client,
    get_key_pool_status,
    get_available_models,
    get_usage_summary,
    get_detailed_usage,
    normalize_model_name
)

logger = logging.getLogger(__name__)


class SettingsGroup(app_commands.Group):
    """Slash command group for Cortana settings."""
    
    def __init__(self):
        super().__init__(name="settings", description="Cortana settings")

    @app_commands.command(name="model", description="Change the LLM model (e.g. gpt-4o, openai/gpt-4o, gemini/gemini-2.5-flash)")
    @app_commands.describe(model_name="The name of the model to use (format: provider/model or just model)")
    async def model(self, interaction: discord.Interaction, model_name: str):
        """Change the active LLM model."""
        try:
            # Normalize the model name
            normalized = normalize_model_name(model_name)
            
            agent.update_agent_model(model_name)
            await interaction.response.send_message(
                f"✅ Model updated to **{normalized}** for this session.\n"
                f"*Original input: `{model_name}`*"
            )
            logger.info(f"Model updated to {normalized} by {interaction.user}")
        except Exception as e:
            logger.error(f"Failed to update model: {e}")
            await interaction.response.send_message(f"❌ Failed to update model: {e}", ephemeral=True)

    @app_commands.command(name="status", description="Show current model and API key pool status")
    async def status(self, interaction: discord.Interaction):
        """Display current agent and rotator status."""
        try:
            status = await agent.get_agent_status()
            
            # Format provider info
            providers_info = []
            for provider in status.get("providers", []):
                key_count = status.get("key_counts", {}).get(provider, 0)
                providers_info.append(f"  • **{provider}**: {key_count} key(s)")
            
            providers_str = "\n".join(providers_info) if providers_info else "  • *No providers configured*"
            
            rotator_status = "✅ Enabled" if status.get("rotator_enabled") else "❌ Disabled"
            
            embed = discord.Embed(
                title="🤖 Cortana Status",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Current Model",
                value=f"`{status.get('current_model', 'unknown')}`",
                inline=True
            )
            embed.add_field(
                name="Rotator",
                value=rotator_status,
                inline=True
            )
            embed.add_field(
                name="Available Providers",
                value=providers_str,
                inline=False
            )
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to get status: {e}")
            await interaction.response.send_message(f"❌ Failed to get status: {e}", ephemeral=True)

    @app_commands.command(name="models", description="List available models for a provider")
    @app_commands.describe(provider="Provider name (e.g. openai, gemini, anthropic)")
    async def models(self, interaction: discord.Interaction, provider: str = None):
        """List available models from the rotator."""
        await interaction.response.defer()  # May take a moment to fetch
        
        try:
            models = await get_available_models(provider)
            
            if provider:
                # Single provider list
                if isinstance(models, list) and models:
                    model_list = "\n".join([f"• `{m}`" for m in models[:20]])
                    if len(models) > 20:
                        model_list += f"\n*...and {len(models) - 20} more*"
                    
                    embed = discord.Embed(
                        title=f"📋 Models for {provider}",
                        description=model_list,
                        color=discord.Color.green()
                    )
                else:
                    embed = discord.Embed(
                        title=f"📋 Models for {provider}",
                        description="*No models available or provider not configured*",
                        color=discord.Color.orange()
                    )
            else:
                # All providers
                embed = discord.Embed(
                    title="📋 Available Models",
                    color=discord.Color.green()
                )
                
                if isinstance(models, dict):
                    for prov, model_list in models.items():
                        if model_list:
                            display = ", ".join([f"`{m}`" for m in model_list[:5]])
                            if len(model_list) > 5:
                                display += f" *+{len(model_list) - 5} more*"
                            embed.add_field(name=prov.upper(), value=display, inline=False)
                else:
                    embed.description = "*No models available*"
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            await interaction.followup.send(f"❌ Failed to list models: {e}")

    @app_commands.command(name="usage", description="Show API key usage statistics")
    async def usage(self, interaction: discord.Interaction):
        """Display API key usage statistics."""
        try:
            usage = get_usage_summary()
            
            embed = discord.Embed(
                title="📊 API Key Usage Statistics",
                color=discord.Color.purple()
            )
            
            # Overview
            embed.add_field(
                name="Total Requests",
                value=f"`{usage.get('total_requests', 0):,}`",
                inline=True
            )
            embed.add_field(
                name="Total Tokens",
                value=f"`{usage.get('total_tokens', 0):,}`",
                inline=True
            )
            embed.add_field(
                name="Est. Cost",
                value=f"`${usage.get('total_cost', 0):.4f}`",
                inline=True
            )
            
            # Provider breakdown
            by_provider = usage.get("by_provider", {})
            if by_provider:
                provider_lines = []
                for provider, stats in by_provider.items():
                    keys = stats.get("keys", 0)
                    requests = stats.get("requests", 0)
                    tokens = stats.get("tokens", 0)
                    provider_lines.append(
                        f"**{provider}**: {keys} key(s), {requests:,} req, {tokens:,} tok"
                    )
                embed.add_field(
                    name="By Provider",
                    value="\n".join(provider_lines) if provider_lines else "*No data*",
                    inline=False
                )
            
            # Top models
            by_model = usage.get("by_model", {})
            if by_model:
                # Sort by requests descending
                sorted_models = sorted(by_model.items(), key=lambda x: x[1], reverse=True)[:5]
                model_lines = [f"`{model}`: {count:,} requests" for model, count in sorted_models]
                embed.add_field(
                    name="Top Models",
                    value="\n".join(model_lines) if model_lines else "*No data*",
                    inline=False
                )
            
            # Last updated
            last_updated = usage.get("last_updated")
            if last_updated:
                embed.set_footer(text=f"Last updated: {last_updated}")
            else:
                embed.set_footer(text="No usage data available yet")
            
            await interaction.response.send_message(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to get usage: {e}")
            await interaction.response.send_message(f"❌ Failed to get usage: {e}", ephemeral=True)

    @app_commands.command(name="oauth-status")
    async def oauth_status(self, interaction: discord.Interaction):
        """Show OAuth credentials status and token expiry times."""
        try:
            from .rotator_client import get_oauth_status
            
            await interaction.response.defer()
            
            oauth_status = await get_oauth_status()
            
            if not oauth_status:
                await interaction.followup.send("❌ No OAuth credentials configured")
                return
            
            # Create embed
            embed = discord.Embed(
                title="🔐 OAuth Credentials Status",
                color=discord.Color.blue(),
                timestamp=datetime.now()
            )
            
            # Show status for each provider
            for provider, creds in oauth_status.items():
                if not creds:
                    continue
                
                status_lines = []
                for i, cred in enumerate(creds):
                    expired = "❌ EXPIRED" if cred["is_expired"] else "✅ Valid"
                    time_left = cred.get("time_to_expiry")
                    
                    if time_left is not None:
                        hours = time_left // 3600
                        mins = (time_left % 3600) // 60
                        time_str = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
                        status_lines.append(f"Credential {i}: {expired} ({time_str})")
                    else:
                        status_lines.append(f"Credential {i}: {expired}")
                    
                    if cred.get("last_refreshed"):
                        status_lines.append(f"  Last refreshed: {cred['last_refreshed']}")
                
                if status_lines:
                    embed.add_field(
                        name=f"{provider.upper()}",
                        value="\n".join(status_lines),
                        inline=False
                    )
            
            embed.set_footer(text="Use /settings oauth-refresh to manually refresh tokens")
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to get OAuth status: {e}")
            await interaction.followup.send(f"❌ Failed to get OAuth status: {e}", ephemeral=True)

    @app_commands.command(name="oauth-refresh")
    async def oauth_refresh(self, interaction: discord.Interaction, provider: str):
        """Manually refresh an OAuth token for a specific provider."""
        try:
            from .rotator_client import refresh_oauth_token
            
            await interaction.response.defer()
            
            # Attempt refresh
            success = await refresh_oauth_token(provider.lower())
            
            if success:
                embed = discord.Embed(
                    title="✅ OAuth Token Refreshed",
                    description=f"Successfully refreshed token for **{provider}**",
                    color=discord.Color.green()
                )
            else:
                embed = discord.Embed(
                    title="❌ OAuth Refresh Failed",
                    description=f"Failed to refresh token for **{provider}**\n\nMake sure:\n• Credential file is writable\n• Refresh token is not revoked\n• Provider endpoint is accessible",
                    color=discord.Color.red()
                )
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            logger.error(f"OAuth refresh error: {e}")
            await interaction.followup.send(f"❌ OAuth refresh error: {e}", ephemeral=True)


class CortanaClient(discord.Client):
    """Main Discord client for Cortana."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scheduler = None
        self.tree = app_commands.CommandTree(self)
    
    async def setup_hook(self):
        """Called when the client is setting up."""
        self.tree.add_command(SettingsGroup())
        await self.tree.sync()
        logger.info("Slash commands synced")
        
        # Pre-initialize the rotating client
        try:
            client = await get_rotating_client()
            if client:
                logger.info("RotatingClient pre-initialized successfully")
            else:
                logger.info("Running in legacy single-key mode")
        except Exception as e:
            logger.warning(f"RotatingClient initialization skipped: {e}")

    async def on_ready(self):
        """Called when the bot is ready."""
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        logger.info('Cortana is online and ready to serve.')
        
        # Log rotator status
        status = await get_key_pool_status()
        if status.get("providers"):
            logger.info(f"API Key Pool: {status['providers']} with {status['key_counts']}")
        
        # Start the reminder scheduler
        if self.scheduler is None:
            self.scheduler = ReminderScheduler(self)
            self.scheduler.start()
            logger.info('Reminder scheduler initialized')

    async def close(self):
        """Clean up resources on shutdown."""
        logger.info("Shutting down Cortana...")
        
        # Close the rotating client
        await close_rotating_client()
        
        # Call parent close
        await super().close()

    async def on_message(self, message):
        """Handle incoming messages."""
        # Don't reply to self
        if message.author.id == self.user.id:
            return

        # Optional: Only respond to mentions or specific channels
        # if not self.user.mentioned_in(message):
        #     return

        logger.debug(f"Message from {message.author}: {message.content[:100]}...")

        # 1. Retrieve Context from Zep
        user_id = str(message.author.id)
        thread_id = f"discord_{user_id}"
        
        # Ensure user exists in Zep
        try:
            await memory_client.user.get(user_id=user_id)
        except Exception:
            # User doesn't exist, create it
            try:
                await memory_client.user.add(
                    user_id=user_id,
                    first_name=message.author.display_name,
                    metadata={"discord_id": str(message.author.id)}
                )
            except Exception as user_err:
                logger.warning(f"User creation error: {user_err}")
        
        # Ensure thread exists
        try:
            await memory_client.thread.get(thread_id=thread_id)
        except Exception:
            # Thread doesn't exist, create it
            try:
                await memory_client.thread.create(thread_id=thread_id, user_id=user_id)
            except Exception as create_err:
                logger.warning(f"Thread creation error: {create_err}")
        
        zep_context = "No previous context."
        try:
            # Get user context (memory)
            memory = await memory_client.thread.get_user_context(thread_id=thread_id)
            zep_context = memory.context if memory and memory.context else "No previous context."
        except Exception as e:
            logger.warning(f"Zep memory retrieval error: {e}")

        # 2. Run Agent
        user_info = {
            "id": message.author.id,
            "name": message.author.name,
            "display_name": message.author.display_name
        }
        
        deps = {
            "user_info": user_info,
            "zep_memory_context": zep_context
        }

        try:
            async with message.channel.typing():
                result = await agent.cortana_agent.run(message.content, deps=deps)
                response_text = result.output if hasattr(result, 'output') else str(result)
                
                # 3. Send Response (handle long messages)
                if len(response_text) > 2000:
                    # Split into chunks
                    chunks = [response_text[i:i+1990] for i in range(0, len(response_text), 1990)]
                    for chunk in chunks:
                        await message.channel.send(chunk)
                else:
                    await message.channel.send(response_text)
                
                # 4. Save Both Messages to Zep
                from zep_cloud.types import Message
                
                try:
                    await memory_client.thread.add_messages(
                        thread_id=thread_id,
                        messages=[
                            Message(role_type="user", role="user", content=message.content, name=message.author.display_name),
                            Message(role_type="assistant", role="assistant", content=response_text, name="Cortana")
                        ]
                    )
                except Exception as mem_err:
                    logger.warning(f"Memory save error: {mem_err}")

        except Exception as e:
            logger.error(f"Agent Error: {e}", exc_info=True)
            await message.channel.send("I encountered a critical error processing your request. Please check the logs.")


def main():
    """Main entry point for the Cortana bot."""
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration Error: {e}")
        return

    # Log startup info
    logger.info(f"Starting Cortana with model: {config.LLM_MODEL_NAME}")
    logger.info(f"Rotator enabled: {config.ENABLE_ROTATOR}")
    
    intents = discord.Intents.default()
    intents.message_content = True
    
    client = CortanaClient(intents=intents)
    client.run(config.DISCORD_TOKEN)


if __name__ == "__main__":
    main()
