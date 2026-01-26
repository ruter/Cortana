import discord
from discord import app_commands
import asyncio
from .config import config
from . import agent
from .memory import memory_client
from .scheduler import ReminderScheduler
from .providers import get_oauth_providers, get_provider
from .providers.base import OAuthProviderInterface
from .models import MODELS, find_model_by_id

class SettingsGroup(app_commands.Group):
    def __init__(self):
        super().__init__(name="settings", description="Cortana settings")

    @app_commands.command(name="model", description="Change the LLM model")
    @app_commands.describe(model_name="The name of the model to use")
    async def model(self, interaction: discord.Interaction, model_name: str):
        model_info = find_model_by_id(model_name)
        if not model_info:
            await interaction.response.send_message(f"❌ Unknown model: **{model_name}**. Use `/models` to see available models.", ephemeral=True)
            return

        try:
            await agent.update_agent_model(model_name)
            await interaction.response.send_message(f"✅ Model updated to **{model_info.name}** ({model_info.provider}) for this session.")
            print(f"Model updated to {model_name} by {interaction.user}")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to update model: {e}", ephemeral=True)

class CortanaClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.scheduler = None
        self.tree = app_commands.CommandTree(self)
        self._pending_logins = {} # user_id -> provider_id
    
    async def setup_hook(self):
        self.tree.add_command(SettingsGroup())
        
        # Add /models command
        @self.tree.command(name="models", description="List all available AI models")
        async def models(interaction: discord.Interaction):
            embed = discord.Embed(title="Available AI Models", color=discord.Color.blue())
            for provider, provider_models in MODELS.items():
                model_list = "\n".join([f"- `{m.id}`: {m.name}" for m in provider_models.values()])
                embed.add_field(name=provider.capitalize(), value=model_list, inline=False)
            await interaction.response.send_message(embed=embed)

        # Add /login command
        @self.tree.command(name="login", description="Login to an AI provider (e.g. anthropic, google-gemini-cli)")
        @app_commands.describe(provider_id="The ID of the provider to login to")
        async def login(interaction: discord.Interaction, provider_id: str):
            prov = get_provider(provider_id)
            if not prov or not isinstance(prov, OAuthProviderInterface):
                await interaction.response.send_message(f"❌ Provider `{provider_id}` does not support OAuth login.", ephemeral=True)
                return

            try:
                auth_info = await prov.login(interaction.user.id)
                instructions = auth_info.instructions or "Please follow the link to authorize."
                
                embed = discord.Embed(title=f"Login to {prov.name}", description=instructions, color=discord.Color.gold())
                embed.add_field(name="Authorization URL", value=f"[Click here to login]({auth_info.url})")
                
                await interaction.user.send(embed=embed)
                await interaction.user.send(f"After you have the authorization code or redirect URL, reply to this message with: `!code {provider_id} <your_code_or_url>`")
                
                self._pending_logins[interaction.user.id] = provider_id
                await interaction.response.send_message("✅ I've sent you a DM with login instructions.", ephemeral=True)
            except Exception as e:
                await interaction.response.send_message(f"❌ Failed to initiate login: {e}", ephemeral=True)

        await self.tree.sync()
        print("Slash commands synced")

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('Cortana is online and ready to serve.')
        
        # Start the reminder scheduler
        if self.scheduler is None:
            self.scheduler = ReminderScheduler(self)
            self.scheduler.start()
            print('Reminder scheduler initialized')

    async def on_message(self, message):
        # Don't reply to self
        if message.author.id == self.user.id:
            return

        # Handle !code for OAuth
        if isinstance(message.channel, discord.DMChannel) and message.content.startswith("!code "):
            parts = message.content[6:].strip().split(" ", 1)
            if len(parts) < 2:
                await message.channel.send("❌ Invalid format. Use: `!code <provider_id> <code_or_url>`")
                return
            
            provider_id = parts[0]
            code = parts[1]
            
            prov = get_provider(provider_id)
            if prov and isinstance(prov, OAuthProviderInterface):
                try:
                    from .providers.oauth import store_credentials
                    creds = await prov.complete_login(message.author.id, code)
                    await store_credentials(message.author.id, prov.id, creds)
                    await message.channel.send(f"✅ Successfully logged in to **{prov.name}**! You can now use its models with your own account.")
                except Exception as e:
                    await message.channel.send(f"❌ Login failed: {e}")
            else:
                await message.channel.send(f"❌ Unknown or non-OAuth provider: `{provider_id}`")
            return

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
                print(f"User creation error: {user_err}")
        
        # Ensure thread exists
        try:
            await memory_client.thread.get(thread_id=thread_id)
        except Exception:
            # Thread doesn't exist, create it
            try:
                await memory_client.thread.create(thread_id=thread_id, user_id=user_id)
            except Exception as create_err:
                print(f"Thread creation error: {create_err}")
        
        try:
            # Get user context (memory)
            memory = await memory_client.thread.get_user_context(thread_id=thread_id)
            zep_context = memory.context if memory and memory.context else "No previous context."
        except Exception as e:
            print(f"Zep memory retrieval error: {e}")
            zep_context = "No previous context."

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
                # Get user-specific agent
                user_agent = await agent.get_agent(message.author.id)
                result = await user_agent.run(message.content, deps=deps)
                response_text = result.output if hasattr(result, 'output') else str(result)
                
                # 3. Send Response
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
                    print(f"Memory save error: {mem_err}")

        except Exception as e:
            print(f"Agent Error: {e}")
            await message.channel.send("I encountered a critical error processing your request. Please check the logs.")

def main():
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return

    intents = discord.Intents.default()
    intents.message_content = True
    
    client = CortanaClient(intents=intents)
    client.run(config.DISCORD_TOKEN)

if __name__ == "__main__":
    main()
