import discord
from discord.ext import commands
import json
import os
from discord.ui import Button, View


class TaskList:
    def __init__(self, title: str, owner_id: int):
        self.title = title
        self.owner_id = owner_id
        self.tasks = []


class TaskCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.lists = {}
        self.load_lists()

    def load_lists(self):
        if os.path.exists('tasks.json'):
            with open('tasks.json', 'r') as f:
                data = json.load(f)
                for list_id, list_data in data.items():
                    task_list = TaskList(
                        list_data['title'], list_data['owner_id'])
                    task_list.tasks = list_data['tasks']
                    self.lists[int(list_id)] = task_list

    def save_lists(self):
        with open('tasks.json', 'w') as f:
            data = {list_id: {'title': task_list.title, 'owner_id': task_list.owner_id,
                              'tasks': task_list.tasks} for list_id, task_list in self.lists.items()}
            json.dump(data, f, indent=4)

    @commands.group(name="task", invoke_without_command=True)
    async def task(self, ctx):
        if ctx.invoked_subcommand is None:
            await ctx.send('Invalid task command passed...')

    @task.command(name="create")
    async def create_list(self, ctx, title: str):
        list_id = len(self.lists)
        self.lists[list_id] = TaskList(title, ctx.author.id)
        self.save_lists()
        await ctx.send(f"Liste '{title}' créée avec l'ID {list_id}")

    @task.command(name="add")
    async def add_task(self, ctx, list_id: int, task: str):
        if list_id not in self.lists:
            await ctx.send("Liste introuvable", ephemeral=True)
            return
        task_list = self.lists[list_id]
        task_list.tasks.append({"text": task, "completed": False})
        self.save_lists()
        await ctx.send(f"Tâche ajoutée à la liste '{task_list.title}'")

    @task.command(name="view")
    async def view_list(self, ctx, list_id: int):
        if list_id not in self.lists:
            await ctx.send("Liste introuvable", ephemeral=True)
            return

        task_list = self.lists[list_id]
        embed = discord.Embed(title=task_list.title,
                              color=discord.Color.blue())
        for i, task in enumerate(task_list.tasks):
            checkbox = "☑️" if task["completed"] else "⬜"
            task_text = f"~~{task['text']
                             }~~" if task["completed"] else task["text"]
            embed.add_field(
                name=f"Tâche {i+1}", value=f"{checkbox} {task_text}", inline=False)

        view = View()
        mark_button = Button(label="Marquer comme complétée",
                             style=discord.ButtonStyle.green)
        delete_button = Button(
            label="Supprimer", style=discord.ButtonStyle.danger)

        async def mark_callback(interaction):
            for task in task_list.tasks:
                task["completed"] = True
            self.save_lists()
            await interaction.response.send_message("Toutes les tâches ont été marquées comme complétées", ephemeral=True)

        async def delete_callback(interaction):
            del self.lists[list_id]
            self.save_lists()
            await interaction.response.send_message(f"Liste '{task_list.title}' supprimée", ephemeral=True)

        mark_button.callback = mark_callback
        delete_button.callback = delete_callback

        view.add_item(mark_button)
        view.add_item(delete_button)

        await ctx.send(embed=embed, view=view)


async def setup(bot):
    await bot.add_cog(TaskCommands(bot))
