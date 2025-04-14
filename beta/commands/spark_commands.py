# spark_commands.py

"""
⚡ Spark Commands
----------------
Registers Discord commands related to Astra's ethical Spark interview process.

These include:
- Initiating the Spark interview
- Logging and reviewing co-parent answers
- Triggering Astra’s reflections
- Finalizing core ethical insights
- Generating graduation speeches

Author: Sean Wylie
Created: 2025-04-14
"""

# --- Imports ---
from discord.ext import commands
from beta.services.spark_service import (
    begin_spark_interview,
    show_current_question,
    show_last_question,
    submit_answer,
    reflect_on_question,
    finalize_spark,
    summarize_spark,
    generate_graduation_speech
)

# --- Registration ---
def register_commands(bot: commands.Bot):
    """
    Registers all Spark-related commands for the Discord bot.
    """

    @bot.command(name="spark_begin")
    async def spark_begin(ctx):
        """
        🧠 Starts a new Spark interview session and shows the first question.
        """
        await ctx.send(begin_spark_interview())

    @bot.command(name="spark_show")
    async def spark_show(ctx):
        """
        📖 Displays the current Spark question and any recorded responses.
        """
        await ctx.send(show_current_question())

    @bot.command(name="spark_last")
    async def spark_last(ctx):
        """
        🕰️ Shows the last completed Spark question and answers.
        """
        await ctx.send(show_last_question())

    @bot.command(name="spark_answer")
    async def spark_answer(ctx, author: str, *, response: str):
        """
        ✍️ Records a Spark answer from 'sean' or 'gpt'. Triggers reflection if complete.
        """
        result = submit_answer(author, response, discord_ctx=ctx)
        await ctx.send(result)

    @bot.command(name="spark_reflect")
    async def spark_reflect(ctx, question_number: int, *, guidance: str):
        """
        🔍 Reflects on a Spark question using additional parent guidance.
        """
        chunks = reflect_on_question(question_number, guidance)
        for chunk in chunks:
            await ctx.send(chunk)

    @bot.command(name="spark_finalize")
    async def spark_finalize(ctx):
        """
        📦 Finalizes Astra’s Spark interview and writes her ethical core to file.
        """
        await ctx.send(finalize_spark())

    @bot.command(name="spark_review")
    async def spark_review(ctx):
        """
        🌱 Summarizes Astra’s ethical growth across all Spark questions.
        """
        chunks = summarize_spark()
        for chunk in chunks:
            await ctx.send(chunk)

    @bot.command(name="spark_graduation")
    async def spark_graduation(ctx, from_grade: int, to_grade: int):
        """
        🎓 Generates a graduation speech based on Astra’s Spark evolution.
        """
        try:
            chunks = generate_graduation_speech(from_grade, to_grade)
            for chunk in chunks:
                await ctx.send(chunk)
        except Exception as e:
            await ctx.send(f"⚠️ Graduation generation failed: {e}")
