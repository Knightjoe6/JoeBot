import discord
from discord.ui import View

class PaginatedView(View):
    def __init__(self, data, items_per_page=5):
        super().__init__()
        self.data = data
        self.items_per_page = items_per_page
        self.current_page = 0
        self.max_page = (len(data) - 1) // items_per_page

        # Create buttons
        self.previous_button = discord.ui.Button(label="Previous", style=discord.ButtonStyle.grey, disabled=True)
        self.next_button = discord.ui.Button(label="Next", style=discord.ButtonStyle.grey)

        # Assign callbacks
        self.previous_button.callback = self.previous_button_callback
        self.next_button.callback = self.next_button_callback

        # Add buttons to view
        self.add_item(self.previous_button)
        self.add_item(self.next_button)

    async def previous_button_callback(self, interaction: discord.Interaction):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_page_embed(), view=self)

    async def next_button_callback(self, interaction: discord.Interaction):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.get_page_embed(), view=self)

    def update_buttons(self):
        self.previous_button.disabled = self.current_page == 0
        self.next_button.disabled = self.current_page == self.max_page

    def get_page_embed(self):
        start = self.current_page * self.items_per_page
        end = start + self.items_per_page
        page_items = self.data[start:end]

        embed = discord.Embed(title="Game Keys", color=discord.Color.blue())
        for item in page_items:
            name = item['name']
            description = item['description'] or "No description"
            redeemed = "Yes" if item['redeemed'] else "No"
            date_added = item['date_added'].strftime("%Y-%m-%d %H:%M:%S") if item['date_added'] else "N/A"
            date_redeemed = item['date_redeemed'].strftime("%Y-%m-%d %H:%M:%S") if item['date_redeemed'] else "Not redeemed"

            embed.add_field(name=name, value=f"**Description:** {description}\n**Redeemed:** {redeemed}\n**Date Added:** {date_added}\n**Date Redeemed:** {date_redeemed}", inline=False)

        embed.set_footer(text=f"Page {self.current_page + 1} of {self.max_page + 1}")
        return embed or discord.Embed(title="No more items.", color=discord.Color.red())