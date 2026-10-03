import os
import json
import re
import traceback
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
DATA_FILE = "data/roles.json"


def load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    for users in data.values():
        for user_id, val in list(users.items()):
            if isinstance(val, int):
                users[user_id] = {"role": val, "emoji": None}
    return data


def save_data(data: dict) -> None:
    os.makedirs("data", exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_user_role_id(guild_id: int, user_id: int):
    return load_data().get(str(guild_id), {}).get(str(user_id), {}).get("role")


def get_user_emoji_id(guild_id: int, user_id: int):
    return load_data().get(str(guild_id), {}).get(str(user_id), {}).get("emoji")


def set_user_role_id(guild_id: int, user_id: int, role_id: int) -> None:
    data = load_data()
    user = data.setdefault(str(guild_id), {}).setdefault(str(user_id), {})
    user["role"] = role_id
    save_data(data)


def set_user_emoji_id(guild_id: int, user_id: int, emoji_id) -> None:
    data = load_data()
    user = data.setdefault(str(guild_id), {}).setdefault(str(user_id), {})
    user["emoji"] = emoji_id
    save_data(data)


def remove_user(guild_id: int, user_id: int) -> None:
    data = load_data()
    if str(guild_id) in data and str(user_id) in data[str(guild_id)]:
        del data[str(guild_id)][str(user_id)]
        save_data(data)


class RoleModal(discord.ui.Modal):
    name = discord.ui.TextInput(
        label="Nom du rôle",
        placeholder="Mon rôle",
        min_length=1,
        max_length=100,
    )
    color = discord.ui.TextInput(
        label="Couleur (hex sans #)",
        placeholder="FF0000",
        min_length=6,
        max_length=7,
        required=False,
    )

    def __init__(self, bot: commands.Bot, interaction: discord.Interaction):
        super().__init__(title="Mon rôle", timeout=300)
        self.bot = bot
        self.guild = interaction.guild
        self.user = interaction.user

        existing_id = get_user_role_id(self.guild.id, self.user.id)
        if existing_id:
            role = self.guild.get_role(existing_id)
            if role:
                self.name.default = role.name
                if role.color.value:
                    self.color.default = f"{role.color.value:06X}"

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        name = self.name.value.strip()
        color_hex = (self.color.value or "").strip().lstrip("#")

        color = discord.Color.default()
        if color_hex:
            if not re.fullmatch(r"[0-9A-Fa-f]{6}", color_hex):
                return await interaction.followup.send(
                    "Couleur invalide. Format : `FF0000`.", ephemeral=True
                )
            color = discord.Color(int(color_hex, 16))

        await interaction.followup.send(
            "Choisis une icône (ou **Aucune**) :",
            view=IconView(self.bot, self.guild, name, color),
            ephemeral=True,
        )


class IconView(discord.ui.View):
    def __init__(self, bot: commands.Bot, guild: discord.Guild, name: str, color: discord.Color):
        super().__init__(timeout=300)
        self.bot = bot
        self.guild = guild
        self.name = name
        self.color = color

        emojis = sorted(
            (e for e in guild.emojis if e.available),
            key=lambda e: e.name.lower(),
        )[:24]
        options = [discord.SelectOption(label="Aucune", value="none")]
        for e in emojis:
            options.append(discord.SelectOption(
                label=e.name[:100],
                value=str(e.id),
                description="animé" if e.animated else "statique",
            ))
        self.select = discord.ui.Select(
            placeholder="Icône du serveur (boost 2+)",
            options=options,
        )
        self.select.callback = self.on_select
        self.add_item(self.select)

    async def on_select(self, interaction: discord.Interaction):
        try:
            await interaction.response.defer(ephemeral=True)

            val = self.select.values[0]
            icon_bytes = None
            new_emoji_id = None

            if val != "none":
                if self.guild.premium_tier < 2:
                    return await interaction.followup.send(
                        "Les icônes nécessitent le serveur niveau 2 de boost.",
                        ephemeral=True,
                    )
                emoji = self.guild.get_emoji(int(val))
                if not emoji:
                    return await interaction.followup.send(
                        "Emoji introuvable sur ce serveur.", ephemeral=True
                    )
                icon_bytes = await emoji.read()
                new_emoji_id = emoji.id

            existing_id = get_user_role_id(self.guild.id, interaction.user.id)

            if existing_id:
                role = self.guild.get_role(existing_id)
                if role:
                    try:
                        await role.edit(
                            name=self.name, color=self.color, display_icon=icon_bytes,
                            reason=f"Modif par {interaction.user}",
                        )
                    except discord.Forbidden:
                        return await interaction.followup.send(
                            "Permission refusée. Le rôle du bot doit être au-dessus du tien.",
                            ephemeral=True,
                        )
                    except discord.HTTPException as e:
                        return await interaction.followup.send(
                            f"Erreur Discord : `{e}`", ephemeral=True
                        )
                    set_user_emoji_id(self.guild.id, interaction.user.id, new_emoji_id)
                    self.stop()
                    return await interaction.followup.send(
                        f"Rôle **{role.name}** mis à jour.", ephemeral=True
                    )

            try:
                role = await self.guild.create_role(
                    name=self.name, color=self.color,
                    reason=f"Créé par {interaction.user}",
                )
                print(f"[OK] Rôle créé: {role.name} (id={role.id}, pos={role.position})")
            except discord.Forbidden:
                return await interaction.followup.send(
                    "Impossible de créer le rôle (permission Gérer les rôles manquante).",
                    ephemeral=True,
                )
            except discord.HTTPException as e:
                return await interaction.followup.send(
                    f"Erreur création rôle : `{e}`", ephemeral=True
                )

            # L'icône doit être ajoutée via edit(), create_role() ne l'accepte pas
            if icon_bytes:
                try:
                    await role.edit(display_icon=icon_bytes)
                    print(f"[OK] Icône ajoutée")
                except discord.Forbidden:
                    print(f"[SKIP] Icône refusée (Forbidden)")
                except discord.HTTPException as e:
                    print(f"[SKIP] Icône échouée: {e}")

            # Placer le rôle juste EN DESSOUS du rôle du bot dans la hiérarchie
            bot_member = self.guild.get_member(self.bot.user.id)
            if bot_member:
                target_pos = bot_member.top_role.position + 1
                try:
                    await role.edit(position=target_pos)
                    print(f"[OK] Position changée à {target_pos}")
                except Exception as e:
                    # Pas critique : on garde la position par défaut
                    print(f"[SKIP] Position non modifiée: {type(e).__name__}: {e}")

            try:
                await interaction.user.add_roles(role, reason="Auto-attribué")
            except discord.Forbidden:
                try:
                    await role.delete()
                except discord.Forbidden:
                    pass
                return await interaction.followup.send(
                    "Rôle créé mais impossible de te l'attribuer. "
                    "Vérifie que le rôle du bot est en haut de la hiérarchie.",
                    ephemeral=True,
                )
            except discord.HTTPException as e:
                try:
                    await role.delete()
                except discord.Forbidden:
                    pass
                return await interaction.followup.send(
                    f"Erreur attribution : `{e}`", ephemeral=True
                )

            set_user_role_id(self.guild.id, interaction.user.id, role.id)
            set_user_emoji_id(self.guild.id, interaction.user.id, new_emoji_id)
            self.stop()
            await interaction.followup.send(
                f"Rôle **{role.name}** créé et attribué.", ephemeral=True
            )
        except Exception as e:
            print(f"[ERREUR IconView] {type(e).__name__}: {e}")
            traceback.print_exc()
            try:
                await interaction.followup.send(
                    f"Erreur inattendue : `{e}`", ephemeral=True
                )
            except Exception:
                pass


class RoleView(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    def _can_manage(self, interaction: discord.Interaction) -> bool:
        if get_user_role_id(interaction.guild.id, interaction.user.id):
            return True
        if interaction.user.id == interaction.guild.owner_id:
            return True
        return interaction.user.premium_since is not None

    @discord.ui.button(
        label="Gérer mon rôle",
        style=discord.ButtonStyle.primary,
        custom_id="btn_personal_role_create",
    )
    async def create_modify(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self._can_manage(interaction):
            return await interaction.response.send_message(
                "Tu dois booster le serveur. L'owner peut l'utiliser sans booster.",
                ephemeral=True,
            )
        await interaction.response.send_modal(RoleModal(self.bot, interaction))

    @discord.ui.button(
        label="Supprimer",
        style=discord.ButtonStyle.danger,
        custom_id="btn_personal_role_delete",
    )
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        existing_id = get_user_role_id(interaction.guild.id, interaction.user.id)
        if not existing_id:
            return await interaction.followup.send(
                "Tu n'as pas de rôle perso.", ephemeral=True
            )
        role = interaction.guild.get_role(existing_id)
        if role:
            try:
                await role.delete(reason=f"Suppression par {interaction.user}")
            except discord.Forbidden:
                return await interaction.followup.send(
                    "Permission refusée.", ephemeral=True
                )
        remove_user(interaction.guild.id, interaction.user.id)
        await interaction.followup.send("Rôle supprimé.", ephemeral=True)


class Bot(commands.Bot):
    async def setup_hook(self):
        self.add_view(RoleView(self))


intents = discord.Intents.default()
intents.members = True
intents.guilds = True

bot = Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="/éphémère",
        )
    )
    try:
        synced = await bot.tree.sync()
        print("=" * 50)
        print(f"  Connecte : {bot.user}")
        print(f"  {len(synced)} commande(s)")
        print(f"  {len(bot.guilds)} serveur(s)")
        print("=" * 50)
    except Exception as e:
        print(f"Erreur sync : {e}")


@bot.tree.command(name="panneau", description="Poste le panneau des roles persos (owner only)")
async def panneau(interaction: discord.Interaction):
    if interaction.user.id != interaction.guild.owner_id:
        return await interaction.response.send_message(
            "Seul l'owner du serveur peut utiliser cette commande.",
            ephemeral=True,
        )

    embed = discord.Embed(
        title="Rôles personnalisés",
        description=(
            "**Boosters**, créez votre propre rôle : nom, couleur, icône.\n"
            "Modifiable et supprimable à tout moment.\n\n"
            "Cliquez ci-dessous pour gérer votre rôle.\n\n"
            "*Confidentialité : chacun ne voit et modifie que son propre rôle.*"
        ),
        color=discord.Color.blurple(),
    )
    await interaction.response.send_message(embed=embed, view=RoleView(bot))


@bot.event
async def on_member_update(before: discord.Member, after: discord.Member):
    if before.premium_since is None and after.premium_since is not None:
        embed = discord.Embed(
            title="Merci pour le boost !",
            description=(
                "Tu peux maintenant créer ton propre rôle personnalisé.\n"
                "Clique sur le bouton ci-dessous."
            ),
            color=discord.Color.pink(),
        )
        try:
            await after.send(embed=embed, view=RoleView(bot))
        except discord.Forbidden:
            pass


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Token manquant. Mets DISCORD_TOKEN dans .env")
    bot.run(TOKEN)