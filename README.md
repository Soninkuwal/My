# Telegram Bot Project

## Description

This bot manages Telegram channels, groups, and users with features such as:

•   **User Authentication:** Login with a phone number and logout.
•   **Link Management:** Joining multiple links in batches.
•   **Settings:** Custom thumbnail, word replacement, word deletion.
•   **Broadcasts:** Message broadcasts to all users.
•   **User Tracking:** Logging new users and profile details.
•   **Command Handling:** Automatic reaction emojis.
•   **High-Speed:** Using `asyncio` for improved performance.
•   **Docker Deployment:** Containerized deployment for Koyeb and Render.

## Usage

### Commands

•   `/start`: Start the bot and display the welcome message.
•   `/login`: Login with your phone number and country code.
•   `/logout`: Log out of the current bot session.
•   `/join`: Join the pre-configured Telegram groups.
•   `/batch`: Join multiple links provided in a single command.
•   `/settings`: Access the settings menu.
•   `/broadcast`: Broadcast a message to all users.
•   `/test`: A test command that responds with a thumbs-up emoji.
•   `/cancelbatch`: Cancel the ongoing batch link join process.

### Settings Menu

•   `change_thumb`: Update the bot's start message thumbnail.
•   `replace_word`: Replace specific words in messages.
•   `delete_word`: Remove specific words from messages.

### Environment Variables

Configuration is done via a `.env` file:

•   `API_ID`: Your Telegram API ID.
•   `API_HASH`: Your Telegram API hash.
•   `BOT_TOKEN`: Your bot token.
•   `MONGODB_URL`: Your MongoDB connection URL.
•   `LOG_CHANNEL_ID`: Your logging channel ID.

### Deployment

1.  Build the Docker image: `docker build -t your-bot-image .`
2.  Push the Docker image to your container registry.
3.  Deploy to Koyeb or Render using the Docker image. Make sure environment variables are configured correctly in the hosting environment.

## Note

•   The bot uses Pyrogram and MongoDB.
•   Ensure you have created your bot on Telegram and have the `bot_token`.
•   Be sure to update the placeholder links and details in `config.py` with your actual data.
