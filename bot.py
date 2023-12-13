#!/usr/bin/env python3

import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from logs import loggers

logger = loggers.createLogger("main")


def loadEnvironmentVars() -> None:
    """Loads environment variables from the directory's env file"""
    load_dotenv(".env")


def getIntents() -> discord.Intents:
    """Returns customized intents for the discord bot."""
    customIntents = discord.Intents.all()

    return customIntents


def getToken() -> str:
    """Returns the bot token from the environment variables."""
    tokenName = "BOT-TOKEN"

    return os.environ[tokenName]


def createBot() -> commands.Bot:
    """Creates and returns the discord bot."""
    prefix = "!"
    logger.debug(f"Prefix set to {prefix}")
    customIntents = getIntents()

    return commands.Bot(command_prefix=prefix, intents=customIntents, help_command=None, case_insensitive=True,
                        application_id=1078497026041467051)


async def loadCogs(discordBot: commands.Bot) -> None:
    """Loads all the cogs in the directory onto the bot."""
    cogFiles = os.listdir("cogs")

    for filename in cogFiles:
        if filename.endswith(".py") and filename != "__init__.py" and filename != "sample.py":
            cogName = filename[:-3]

            logger.debug(f"Loading the {cogName} cog...")
            try:
                await discordBot.load_extension(f"cogs.{cogName}")
                logger.debug(f"Loaded the {cogName} cog!")
            except Exception:
                logger.error(f"Failed to load the {cogName} cog!", exc_info=True)


if __name__ == "__main__":
    logger.info("Initializing bot...")

    loadEnvironmentVars()

    bot = createBot()
    asyncio.run(loadCogs(bot))
    token = getToken()


    @bot.command(name='sync')
    async def _sync(ctx):
        await ctx.bot.tree.sync()
        logger.info('Application commands have been synced.')


    bot.run(token)
