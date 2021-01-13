import discord
from discord.ext import commands
import asyncio
import datetime
import numpy
import json
import traceback
import dotenv
import os

dotenv.load_dotenv()

INITIAL_EXTENSIONS = [

]


class TypingBot(commands.Bot):
    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)
        for ext in INITIAL_EXTENSIONS:
            try:
                self.load_extension(ext)
            except Exception:
                traceback.print_exc()

    async def on_ready(self):
        await self.change_presence(
            activity=discord.Game("「!ヘルプ」でヘルプ"), type=1
        )
        print("ready")

    async def on_command_error(self, ctx, err):
        if isinstance(err, commands.CommandNotFound):
            return
        else:
            traceback_str = "".join(traceback.TracebackException.from_exception(err).format())
            return await ctx.send(f"```py\n{traceback_str}\n```")


if __name__ == "__main__":
    intents = discord.Intents.all()
    intents.typing = False
    bot = TypingBot(command_prefix=("！", "!"), intents=intents, help_command=None)
    bot.run(os.environ["TOKEN"])
