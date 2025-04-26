# beta/utils/send_chunked_message.py

# beta/utils/send_chunked_message.py

import re

async def send_chunked_message(channel, content, prefix=""):
    """
    Sends a long message to a Discord channel in chunks that fit within Discord's 2000 character limit.
    Tries to avoid breaking mid-sentence by splitting at sentence boundaries.

    Args:
        channel: The Discord channel to send the message to.
        content (str): The message content.
        prefix (str, optional): A prefix added to the first chunk.
    """
    limit = 2000
    if prefix:
        content = prefix + content

    # Split content into sentences (naive version)
    sentences = re.split(r'(?<=[.!?]) +', content)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        # If adding the next sentence exceeds the limit, push the current chunk
        if len(current_chunk) + len(sentence) + 1 > limit:
            chunks.append(current_chunk)
            current_chunk = sentence
        else:
            current_chunk += (" " if current_chunk else "") + sentence

    if current_chunk:
        chunks.append(current_chunk)

    for chunk in chunks:
        await channel.send(chunk)

