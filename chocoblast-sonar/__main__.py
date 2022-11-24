import os

from discord import Client, Embed, Message, AllowedMentions, Streaming
import discord
from discord.raw_models import RawReactionActionEvent
from dotenv import load_dotenv
import sqlite3

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN", "")
ADMINS = os.getenv("DISCORD_ADMINS", "").split(",")

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
        "rules": "Afficher les règles",
        "vote": "Voter pour décompter un chocoblast",
        "help": "Aide des commandes",
        "validate_chocoblast": "Valider le chocoblast d'une personne (Admin uniquement)"
    }

    async def on_ready(self):
        print(f"{self.user} has connected to Discord!")
        
        await self.change_presence(activity=Streaming(name="Mange des chocos", url="https://www.youtube.com/watch?v=yw35BYhKVoo"))

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
        elif message_content == "!vote":
            await self.on_vote_chocoblast(message)
        elif message_content == "!help":
            await message.reply("\n".join((f"`!{k}`: {v}") for k, v in ChocoblastClient.COMMANDS.items()))
        elif message_content.startswith("!validate_chocoblast"):
            await self.on_validate_chocoblast(message)

    def get_vote(self, guild_id, message_id):
        cursor = con.cursor()

        cursor.execute("SELECT guild_id, message_id, user_id FROM votes WHERE guild_id = :guild_id AND message_id = :message_id LIMIT 1;", {
            "guild_id": guild_id,
            "message_id": message_id
        })

        record = cursor.fetchone()

        cursor.close()

        return record

    async def on_raw_reaction_add(self, payload: RawReactionActionEvent):
        vote = self.get_vote(payload.guild_id, payload.message_id)
        if not vote:
            return

        await self.on_vote_reaction_chocoblast(payload, vote)

    async def on_raw_reaction_remove(self, payload: RawReactionActionEvent):
        vote = self.get_vote(payload.guild_id, payload.message_id)
        if not vote:
            return

        await self.on_vote_reaction_chocoblast(payload, vote)

    async def on_vote_reaction_chocoblast(self, payload: RawReactionActionEvent, vote):
        guild_id = vote[0]
        user_id = vote[2]

        channel = self.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)

        guild = self.get_guild(guild_id)

        num_members = round(guild.member_count / 2)
        if num_members <= 0:
            num_members = 1

        vote_up = 0
        vote_down = 0
        for reaction in message.reactions:
            if reaction.emoji == "👍":
                vote_up = reaction.count
            elif reaction.emoji == "👎":
                vote_down = reaction.count

        total_votes = vote_up + vote_down

        if total_votes < num_members:
            return

        cursor = con.cursor()

        if vote_up == vote_down:
            await message.reply("Résultat : Egalité (null)")
        elif vote_up > vote_down:
            cursor.execute("UPDATE statistics SET chocoblasted = chocoblasted - 1 WHERE guild_id = :guild_id AND user_id = :user_id AND chocoblasted > 0;", {
                "guild_id": guild_id,
                "user_id": user_id
            })

            con.commit()

            await message.reply("Résultat : Accepté")
        else:
            await message.reply("Résultat : Refusé")

        cursor.execute("DELETE FROM votes WHERE guild_id = :guild_id AND user_id = :user_id;", {
            "guild_id": guild.id,
            "user_id": user_id
        })

        con.commit()
        cursor.close()

    async def on_chocoblast(self, message: Message):
        embed = Embed()
        embed.set_image(url = "https://media.giphy.com/media/3o7TKD4yHgfzuvGWcg/giphy.gif")

        sended_message = await message.reply(f"<@{message.author.id}> Nous offre les chocos !!!",
                                                embed = embed,
                                                allowed_mentions = AllowedMentions.none(),
                                                tts = True)

        philhead = discord.utils.get(message.guild.emojis, name="philhead")
        if philhead:
            await message.add_reaction(philhead)
            await sended_message.add_reaction(philhead)
        else:
            print("Warning: No philhead found !")

        statistics_chocoblasted_user(message.guild.id, message.author.id)

    async def on_top_chocoblast(self, message: Message):
        cursor = con.cursor()
        cursor.execute("SELECT user_id, chocoblasted FROM statistics WHERE guild_id = :guild_id AND chocoblasted > 0 ORDER BY chocoblasted;", {
            "guild_id": message.guild.id
        })

        content_message = "Top:\n"
        for statistic in cursor.fetchall():
            user_id = statistic[0]
            chocoblasted = statistic[1]

            content_message += f"- <@{user_id}> : {chocoblasted}\n"

        cursor.close()

        await message.reply(content=content_message)

    async def on_vote_chocoblast(self, message: Message):
        guild_id = message.guild.id
        channel_id = message.channel.id
        user_id = message.author.id

        cursor = con.cursor()

        cursor.execute("SELECT message_id FROM votes WHERE guild_id = :guild_id AND user_id = :user_id LIMIT 1;", {
            "guild_id": guild_id,
            "user_id": user_id
        })
        vote = cursor.fetchone()

        if vote:
            await message.reply(content=f"Une demande de vote existe déjà\n\nhttps://discord.com/channels/{guild_id}/{channel_id}/{vote[0]}")

            cursor.close()

            return

        content_message = f"<@{message.author.id}> demande un vote pour décompter son dernier chocoblast\n\n:thumbsup: Oui - :thumbdown: Non"

        reply = await message.reply(content=content_message)

        cursor.execute("INSERT OR IGNORE INTO votes (guild_id, message_id, user_id) VALUES (:guild_id, :message_id, :user_id);", {
            "guild_id": guild_id,
            "message_id": reply.id,
            "user_id": user_id
        })
        con.commit()

        cursor.close()

    async def on_validate_chocoblast(self, message: Message):
        guild_id = message.guild.id
        channel_id = message.channel.id
        user_id = message.author.id

        if str(user_id) not in ADMINS:
            await message.reply(content=f"Tu n'es pas administrateur")

            return

        selected_user = next(iter(message.mentions), None)
        if not selected_user:
            await message.reply(content=f"Aucun utilisateur mentionné")

            return

        cursor = con.cursor()
        cursor.execute("UPDATE statistics SET chocoblasted = chocoblasted - 1 WHERE guild_id = :guild_id AND user_id = :user_id AND chocoblasted > 0;", {
            "guild_id": guild_id,
            "user_id": selected_user.id
        })
        con.commit()
        cursor.close()

        await message.reply(content=f"La réception des chocos de <@{selected_user.id}> a bien été effectué")

apply_migrations()

intents = discord.Intents.default()
intents.message_content = True

client = ChocoblastClient(intents=intents)
client.run(TOKEN)