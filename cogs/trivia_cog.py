import asyncio
import html
from discord.ext import commands
from discord import app_commands, Interaction, Guild, Forbidden, ui, ButtonStyle, SelectOption
from discord.ext.commands import Bot
from random import shuffle
from requests import get
from datetime import datetime, timedelta

# TODO make it send out a message with a countdown to when the quiz starts to allow people to prepare

QUESTION_DURATION = 30  # Time to wait for each question, in seconds
ANSWER_DURATION = 5  # Time to wait after showing the answer and scores, in seconds

class QuestionSetupView(ui.View):
    def __init__(self, bot: Bot, trivia_cog, interaction: Interaction):
        super().__init__(timeout=None)
        self.bot = bot
        self.trivia_cog = trivia_cog
        self.num_questions = 5  # Default value
        self.interaction = interaction

    @ui.select(placeholder='Select number of questions', min_values=1, max_values=1, options=[
        SelectOption(label=str(i), value=str(i)) for i in range(1, 11)
    ])
    async def select_callback(self, interaction: Interaction, select: ui.Select):
        self.num_questions = int(select.values[0])
        await interaction.response.send_message(f"Number of questions set to {self.num_questions}.", ephemeral=True, delete_after=5)

    @ui.button(label='Start', style=ButtonStyle.green)
    async def start_button(self, interaction: Interaction, button: ui.Button):
        await self.trivia_cog.start_game(interaction, self.num_questions)
        await self.interaction.delete_original_response()

    @ui.button(label='Cancel', style=ButtonStyle.red)
    async def cancel_button(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message("Trivia game setup canceled.", ephemeral=True, delete_after=5)
        await self.interaction.delete_original_response()


class TriviaCog(commands.GroupCog, group_name="trivia"):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.is_started = False
        self.current_question = 0
        self.scores = {}
        self.responses = {}
        self.game_interaction = None
        self.questions = []
        self.message = None
        self.original_question_text = ""

    @app_commands.command()
    async def start(self, interaction: Interaction):
        if self.is_started:
            await interaction.response.send_message("A game of Trivia is already running", ephemeral=True)
            return

        view = QuestionSetupView(self.bot, self, interaction)
        await interaction.response.send_message("Set up your Trivia game:", view=view, ephemeral=True)

    async def start_game(self, interaction: Interaction, num_questions: int):
        guild: Guild = interaction.guild
        if guild is None:
            await interaction.response.send_message('This command can only be used in a server.', ephemeral=True)
            return

        try:    
            self.game_interaction = interaction
            self.is_started = True
            self.scores = {}
            self.responses = {}

            self.get_questions(num_questions)
            
            await interaction.response.send_message("Trivia game is starting!", ephemeral=True)
            await self.send_question()
            
        except Forbidden as e:
            await interaction.response.send_message(f"Forbidden: {e}", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}", ephemeral=True)
    
    def get_questions(self, num_questions):
        resp = get(f"https://opentdb.com/api.php?amount={num_questions}&type=multiple")
        questions = resp.json()['results']

        valid_questions = []
        for question in questions:
            if question['category'] != 'Politics' or 'Hitler' in question['question'] or 'Nazi' in question['question']:
                valid_questions.append(question)

        num_to_replace = num_questions - len(valid_questions)
        if num_to_replace:
            resp = get(f"https://opentdb.com/api.php?amount={num_to_replace}&category=17&type=multiple")
            questions = resp.json()['results']
            valid_questions += questions

        difficulty_order = {"easy": 0, "medium": 1, "hard": 2}
        self.questions = sorted(valid_questions, key=lambda x: difficulty_order[x["difficulty"]])

        self.current_question = 0

    async def send_question(self):
        question = self.questions[self.current_question]
        difficulty_order = {"easy": 0, "medium": 1, "hard": 2}
        self.original_question_text = html.unescape(f"{self.current_question+1}/{len(self.questions)} - {question['question']} - ({question['difficulty']} - {(difficulty_order[question['difficulty']] + 1)}pts)")

        def create_button_callback(answer):
            async def button_click(btn_interaction: Interaction):
                self.responses[btn_interaction.user.id] = answer
                # Add user to the scoreboard if not already present
                if btn_interaction.user.id not in self.scores:
                    self.scores[btn_interaction.user.id] = 0
                await btn_interaction.response.send_message(f"{answer} selected", ephemeral=True, delete_after=5)
            return button_click

        view = ui.View(timeout=None)

        answers = [html.unescape(ans) for ans in [question['correct_answer'], *question['incorrect_answers']]]
        shuffle(answers)

        for i, answer in enumerate(answers):
            btn: ui.Button = ui.Button(custom_id=f"key{i}", label=answer, style=ButtonStyle.primary, row=1)
            view.add_item(btn)
            btn.callback = create_button_callback(answer)

        end_time = datetime.now() + timedelta(seconds=QUESTION_DURATION)
        end_timestamp = int(end_time.timestamp())
        question_text_with_timer = f"{self.original_question_text}\n\nRound will end <t:{end_timestamp}:R>."

        self.message = await self.game_interaction.channel.send(question_text_with_timer, view=view)
        self.current_view = view

        # Wait for QUESTION_DURATION before tallying the scores and moving to the next question
        await asyncio.sleep(QUESTION_DURATION)  # Adjust the duration as needed
        await self.remove_timestamp()
        await self.tally_scores_and_next()

    async def remove_timestamp(self):
        await self.message.edit(content=self.original_question_text, view=self.current_view)

    async def disable_buttons(self):
        for item in self.current_view.children:
            item.disabled = True
        await self.message.edit(view=self.current_view)

    async def tally_scores_and_next(self):
        question = self.questions[self.current_question]
        correct_answer = html.unescape(question['correct_answer'])

        correct_users = []
        difficulty_order = {"easy": 0, "medium": 1, "hard": 2}

        for user_id, answer in self.responses.items():
            if answer == correct_answer:
                self.scores[user_id] += (difficulty_order[question['difficulty']] + 1)
                correct_users.append(user_id)
            else:
                self.scores[user_id] -= (difficulty_order[question['difficulty']] + 1)

        # Clear responses for the next question
        self.responses.clear()

        # Disable the buttons of the current view
        await self.disable_buttons()

        if self.current_question < len(self.questions) - 1:
            # Show the correct answer and current scores
            score_text = "\n".join(
                [f"<@{user_id}>: {score}" for user_id, score in sorted(self.scores.items(), key=lambda item: item[1], reverse=True)]
            )
            correct_users_text = ", ".join([f"<@{user_id}>" for user_id in correct_users]) if correct_users else "No one"
            await self.game_interaction.channel.send(f"The correct answer was: **{correct_answer}**\n\n{correct_users_text} answered correctly.\n\nCurrent scores:\n{score_text}")

            # Wait for ANSWER_DURATION seconds before moving to the next question
            await asyncio.sleep(ANSWER_DURATION)
            
            # Move to the next question
            self.current_question += 1
            await self.send_question()
        else:
            # End the game if it was the last question
            self.is_started = False
            # Display final scores or any other end game logic
            final_scores = "\n".join(
                [f"<@{user_id}>: {score}" for user_id, score in sorted(self.scores.items(), key=lambda item: item[1], reverse=True)]
            )
            correct_users_text = ", ".join([f"<@{user_id}>" for user_id in correct_users]) if correct_users else "No one"
            await self.game_interaction.channel.send(f"The correct answer was: **{html.unescape(self.questions[-1]['correct_answer'])}**\n\n{correct_users_text} answered correctly.\n\nGame over! Final scores:\n{final_scores}")

async def setup(bot):
    await bot.add_cog(TriviaCog(bot))
