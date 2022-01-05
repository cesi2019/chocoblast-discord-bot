import os

from discord import Client, Embed, Message, guild, user
import discord
from dotenv import load_dotenv
import sqlite3

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN", "")

con = sqlite3.connect("chocoblast.db")

def get_migration_version(path):
    return int(path.split('_')[0].split("/")[::-1][0])

def apply_migrations():
    cursor = con.cursor()

    current_version = cursor.execute("pragma user_version").fetchone()[0]

    print(f"Current migration version: {current_version}")

    migrations_path = os.path.join(os.path.dirname(__file__), "migrations/")
    migration_files = list(os.listdir(migrations_path))
    for migration in sorted(migration_files):
        path = f"{migrations_path}/{migration}"
        migration_version = get_migration_version(path)

        if migration_version <= current_version:
            continue

        print(f"Apply migration {migration}")

        with open(path, "r") as f:
            cursor.executescript(f.read())

    con.commit()
    cursor.close()

def statistics_chocoblasted_user(guild_id: int, user_id: int):
    cursor = con.cursor()
    cursor.execute("INSERT OR IGNORE INTO statistics (guild_id, user_id) VALUES (:guild_id, :user_id);", {
        "guild_id": guild_id,
        "user_id": user_id
    })
    cursor.execute("UPDATE statistics SET chocoblasted = chocoblasted + 1 WHERE guild_id = :guild_id AND user_id = :user_id;", {
        "guild_id": guild_id,
        "user_id": user_id
    })
    con.commit()
    cursor.close()

class ChocoblastClient(Client):
    COMMANDS = {
        "chocoblast" : "Chocoblaster quelqu'un",
        "top_chocoblast": "Top du nombre de chocoblast par personne",
        "rules": "Afficher les règles"
    }

    async def on_ready(self):
        print(f"{self.user} has connected to Discord!")

        for guild in self.guilds:
            print(f"{guild.name}")

    async def on_message(self, message: Message):
        if message.author == self.user:
            return

        message_content = message.content.lower()

        if message_content == "!chocoblast":
            await self.on_chocoblast(message)
        elif message_content == "!top_chocoblast":
            await self.on_top_chocoblast(message)
        elif message_content == "!rules":
            await message.reply("https://www.chocoblast.fr/reglement/")
        elif message_content == "!help":
            await message.reply("\n".join((f"!{k}: {v}") for k, v in ChocoblastClient.COMMANDS.items()))

    async def on_chocoblast(self, message: Message):
        embed = Embed()
        embed.set_image(url = "https://media.giphy.com/media/3o7TKD4yHgfzuvGWcg/giphy.gif")

        sended_message = await message.reply(f"<@{message.author.id}> Nous offre les chocos !!!", embed = embed)

        philhead = discord.utils.get(message.guild.emojis, name="philhead")
        if philhead:
            await message.add_reaction(philhead)
            await sended_message.add_reaction(philhead)
        else:
            print("Warning: No philhead found !")

        statistics_chocoblasted_user(message.guild.id, message.author.id)

    async def on_top_chocoblast(self, message: Message):
        cursor = con.cursor()
        cursor.execute("SELECT user_id, chocoblasted FROM statistics WHERE guild_id = :guild_id ORDER BY chocoblasted", {
            "guild_id": message.guild.id
        })

        content_message = "Top:\n"
        for statistic in cursor.fetchall():
            user_id = statistic[0]
            chocoblasted = statistic[1]

            user = self.get_user(user_id)
            if not user:
                user = await self.fetch_user(user_id)

            content_message += f"- {user.display_name} : {chocoblasted}\n"

        cursor.close()

        await message.reply(content=content_message)

apply_migrations()

client = ChocoblastClient()
client.run(TOKEN)