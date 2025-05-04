import os
import discord
from discord import app_commands
from discord.ext import commands
import json
from myserver import server_on

# ตั้งค่า intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

DATA_FILE = "data.json"

# โหลดข้อมูลจากไฟล์
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# เซฟข้อมูลลงไฟล์
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# สร้าง View สำหรับปุ่ม
class ItemView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="เพิ่ม", style=discord.ButtonStyle.green, custom_id="add_item")
    async def add_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = AddItemModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="ลบ", style=discord.ButtonStyle.red, custom_id="delete_item")
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = DeleteItemModal()
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="อัปเดต", style=discord.ButtonStyle.blurple, custom_id="update_item")
    async def update_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = UpdateItemModal()
        await interaction.response.send_modal(modal)

# Modal สำหรับเพิ่มของ
class AddItemModal(discord.ui.Modal, title="เพิ่มของใหม่"):
    item_name = discord.ui.TextInput(label="ชื่อของ", placeholder="เช่น รถของเล่น")
    owner_name = discord.ui.TextInput(label="ชื่อเจ้าของ", placeholder="เช่น นิก")

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        item = self.item_name.value.strip()
        owner = self.owner_name.value.strip()

        if not item or not owner:
            await interaction.response.send_message("❌ กรุณากรอกทั้งชื่อของและชื่อเจ้าของ", ephemeral=True)
            return

        if item in data:
            await interaction.response.send_message(f"❌ ของชื่อ `{item}` มีอยู่ในรายการแล้ว", ephemeral=True)
            return

        data[item] = owner
        save_data(data)
        await interaction.response.send_message(f"✅ เพิ่ม `{item}` → {owner} แล้ว", ephemeral=True)
        await update_list_message(interaction)

# Modal สำหรับลบของ
class DeleteItemModal(discord.ui.Modal, title="ลบของ"):
    item_name = discord.ui.TextInput(label="ชื่อของ", placeholder="เช่น รถของเล่น")

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        item = self.item_name.value.strip()

        if item not in data:
            await interaction.response.send_message(f"❌ ไม่มีของชื่อ `{item}` ในรายการ", ephemeral=True)
            return

        del data[item]
        save_data(data)
        await interaction.response.send_message(f"✅ ลบ `{item}` ออกแล้ว", ephemeral=True)
        await update_list_message(interaction)

# Modal สำหรับอัปเดตของ
class UpdateItemModal(discord.ui.Modal, title="อัปเดตเจ้าของ"):
    item_name = discord.ui.TextInput(label="ชื่อของ", placeholder="เช่น รถของเล่น")
    new_owner = discord.ui.TextInput(label="ชื่อเจ้าของใหม่", placeholder="เช่น ฟิว")

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        item = self.item_name.value.strip()
        owner = self.new_owner.value.strip()

        if item not in data:
            await interaction.response.send_message(f"❌ ไม่มีของชื่อ `{item}` ในรายการ", ephemeral=True)
            return

        if not owner:
            await interaction.response.send_message("❌ กรุณากรอกชื่อเจ้าของใหม่", ephemeral=True)
            return

        data[item] = owner
        save_data(data)
        await interaction.response.send_message(f"✅ อัปเดต `{item}` → {owner} แล้ว", ephemeral=True)
        await update_list_message(interaction)

# ฟังก์ชันสำหรับอัปเดตรายการ
async def update_list_message(interaction: discord.Interaction):
    data = load_data()
    message_content = "**📦 รายการของทั้งหมด:**\n"
    if not data:
        message_content += "ยังไม่มีของในรายการเลยนะ"
    else:
        for item, owner in data.items():
            message_content += f"• `{item}` → {owner}\n"

    view = ItemView()
    # หาข้อความล่าสุดที่มีปุ่มในช่องนี้
    async for msg in interaction.channel.history(limit=100):
        if msg.author == bot.user and msg.components:
            try:
                await msg.edit(content=message_content, view=view)
                return
            except discord.HTTPException:
                break
    # ถ้าไม่เจอข้อความเดิมหรือแก้ไขไม่ได้ ส่งข้อความใหม่
    await interaction.channel.send(content=message_content, view=view)

# อีเวนต์เมื่อบอทออนไลน์
@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ บอทออนไลน์แล้ว: {bot.user}")
    print("📤 Slash commands synced แล้ว!")

# คำสั่ง /list
@bot.tree.command(name="list", description="ดูรายการของทั้งหมด")
async def list_items(interaction: discord.Interaction):
    data = load_data()
    message = "**📦 รายการของทั้งหมด:**\n"
    if not data:
        message += "ยังไม่มีของในรายการเลยนะ"
    else:
        for item, owner in data.items():
            message += f"• `{item}` → {owner}\n"

    view = ItemView()
    await interaction.response.send_message(message, view=view)

server_on()

# เริ่มบอท (ใส่ TOKEN ของคุณเอง)
bot.run(os.getenv['TOKEN'])


