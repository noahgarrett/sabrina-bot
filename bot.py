import discord
import os, io
from dotenv import load_dotenv
from make_meme import make_meme

load_dotenv()
bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"{bot.user} is ready and online!")

@bot.slash_command(
    name="process_file",
    description="Upload a file and provide a prompt",
    guild_ids=[int(os.getenv("GUILD_ID"))] if os.getenv("GUILD_ID") else [],
)
async def process_file(
    ctx: discord.ApplicationContext,
    prompt: discord.Option(str, description="Enter your prompt"),
    file: discord.Option(discord.Attachment, description="Upload a file"),
    font_size: discord.Option(int, description="Font size", default=36),
):
    await ctx.defer()  # optional, if processing takes time

    # Download the file bytes
    file_bytes = await file.read()

    prompt_template = f"""
    SABRINA CARPENTER DOES NOT KNOW HOW TO {prompt.upper()}
    """

    try:
        generated_img = make_meme(io.BytesIO(file_bytes), prompt_template, "output_meme.png", font_size=font_size)
    except Exception as e:
        await ctx.respond(f"❌ An error occurred: {str(e)}")
        return

    img_buffer = io.BytesIO()
    generated_img.save(img_buffer, format="PNG")
    img_buffer.seek(0)

    # Example: Just send back info for now
    await ctx.respond(content="✅ Meme created!", file=discord.File(img_buffer, filename="meme.png"))

bot.run(os.getenv('DISCORD_TOKEN'))