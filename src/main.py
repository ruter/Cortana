import discord
import asyncio
from .config import config
from .agent import cortana_agent
from .memory import memory_client

class CortanaClient(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('Cortana is online and ready to serve.')

    async def on_message(self, message):
        # Don't reply to self
        if message.author.id == self.user.id:
            return

        # Optional: Only respond to mentions or specific channels
        # if not self.user.mentioned_in(message):
        #     return

        print(f"Message from {message.author}: {message.content}")

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
            
        except Exception as e:
            print(f"Zep Error: {e}")
            zep_context = "Memory system unavailable."

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
                result = await cortana_agent.run(message.content, deps=deps)
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
