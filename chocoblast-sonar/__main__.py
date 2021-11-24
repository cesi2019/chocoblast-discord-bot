import os

from discord import Client, Embed, Message, user
import discord
from dotenv import load_dotenv
import sqlite3

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

con = sqlite3.connect("chocoblast.db")
cursor = con.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS statistics (
    user_id INTEGER NOT NULL,
    chocoblasted INTEGER NOT NULL DEFAULT 0
);""")
con.commit()
cursor.close()

def statistics_chocoblasted_user(user_id: int):
    cursor = con.cursor()
    cursor.execute("INSERT OR IGNORE INTO statistics (user_id) VALUES (:user_id);", { "user_id": user_id })
    cursor.execute("UPDATE statistics SET chocoblasted = chocoblasted + 1 WHERE user_id = :user_id;", { "user_id": user_id })
    con.commit()
    cursor.close()

class ChocoblastClient(Client):
    COMMANDS = {
        "chocoblast" : "Chocoblaster quelqu'un",
        "top_chocoblast": "Top du nombre de chocoblast par personne"
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

        statistics_chocoblasted_user(message.author.id)

    async def on_top_chocoblast(self, message: Message):
        cursor = con.cursor()
        cursor.execute("SELECT user_id, chocoblasted FROM statistics ORDER BY chocoblasted")

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


client = ChocoblastClient()
client.run(TOKEN)