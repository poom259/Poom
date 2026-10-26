
import os
import discord
from discord import app_commands
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)


@bot.event
async def on_ready():
    try:
        await bot.tree.sync()
        print(f"Nanami is online: {bot.user}")
    except Exception as e:
        print(f"Command sync error: {e}")


@bot.tree.command(
    name="announce",
    description="Create a server announcement"
)
@app_commands.guild_only()
@app_commands.default_permissions(manage_messages=True)
@app_commands.describe(
    channel="Channel to post in",
    title="Announcement title",
    message="Announcement details"
)
async def announce(
    interaction: discord.Interaction,
    channel: discord.TextChannel,
    title: str,
    message: str
):
    if not isinstance(interaction.user, discord.Member):
        return

    if not (
        interaction.user.guild_permissions.manage_messages
        or interaction.user.guild_permissions.administrator
    ):
        await interaction.response.send_message(
            "ขออภัยค่ะ คำสั่งนี้สงวนไว้สำหรับทีมงานนะคะ",
            ephemeral=True
        )
        return

    if len(title) > 256 or len(message) > 4000:
        await interaction.response.send_message(
            "หัวข้อหรือรายละเอียดประกาศยาวเกินไปค่ะ",
            ephemeral=True
        )
        return

    permissions = channel.permissions_for(interaction.guild.me)
    if not permissions.view_channel or not permissions.send_messages:
        await interaction.response.send_message(
            "Nanami ไม่มีสิทธิ์ดูห้องหรือส่งข้อความในห้องนี้ค่ะ",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=f"📢 {title}",
        description=message,
        color=discord.Color.from_rgb(232, 160, 194),
        timestamp=discord.utils.utcnow()
    )
    embed.set_footer(text="Nanami • Announcement Assistant")

    view = ConfirmView(channel, embed, interaction.user.id)

    await interaction.response.send_message(
        f"ตรวจสอบประกาศก่อนส่งนะคะ 🌸\nห้องปลายทาง: {channel.mention}",
        embed=embed,
        view=view,
        ephemeral=True
    )


class ConfirmView(discord.ui.View):
    def __init__(self, channel, embed, author_id):
        super().__init__(timeout=180)
        self.channel = channel
        self.embed = embed
        self.author_id = author_id

    async def interaction_check(self, interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                "ปุ่มนี้เป็นของผู้สร้างประกาศเท่านั้นค่ะ",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="ยืนยันส่งประกาศ",
        style=discord.ButtonStyle.success,
        emoji="📢"
    )
    async def confirm(self, interaction, button):
        if not isinstance(interaction.user, discord.Member):
            return

        if not (
            interaction.user.guild_permissions.manage_messages
            or interaction.user.guild_permissions.administrator
        ):
            await interaction.response.send_message(
                "คุณไม่มีสิทธิ์ส่งประกาศค่ะ",
                ephemeral=True
            )
            return

        permissions = self.channel.permissions_for(
            interaction.guild.me
        )
        if not permissions.view_channel or not permissions.send_messages:
            await interaction.response.send_message(
                "Nanami ไม่มีสิทธิ์ส่งข้อความในห้องนี้ค่ะ",
                ephemeral=True
            )
            return

        if not permissions.embed_links:
            await interaction.response.send_message(
                "กรุณาเปิดสิทธิ์ Embed Links ให้ Nanami ค่ะ",
                ephemeral=True
            )
            return

        try:
            await self.channel.send(embed=self.embed)
        except discord.HTTPException:
            await interaction.response.send_message(
                "ส่งประกาศไม่สำเร็จค่ะ กรุณาตรวจสอบสิทธิ์",
                ephemeral=True
            )
            return

        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            content=f"ส่งประกาศเรียบร้อยแล้วค่ะ 🌸 {self.channel.mention}",
            view=self
        )

    @discord.ui.button(
        label="ยกเลิก",
        style=discord.ButtonStyle.secondary
    )
    async def cancel(self, interaction, button):
        for item in self.children:
            item.disabled = True

        await interaction.response.edit_message(
            content="ยกเลิกประกาศแล้วค่ะ ไม่มีข้อความถูกส่ง",
            view=self
        )


if not TOKEN:
    raise RuntimeError("Please set DISCORD_TOKEN in hosting variables")

bot.run(TOKEN)
  
