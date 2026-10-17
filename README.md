# Movie Hub Telegram Posting Bot

This bot posts a configurable image + caption + inline buttons to your Telegram channel.

## Render environment variables
- `BOT_TOKEN`: token from BotFather
- `ADMIN_IDS`: numeric Telegram user ID(s), comma-separated
- `CHANNEL_ID`: channel username such as `@yourchannel` or numeric ID
- `POSTER_URL`: public direct JPG/PNG image URL
- `CHANNEL_TITLE`: default brand heading, e.g. `MOVIE HUB`
- `POST_TITLE`: default main title
- `MOVIE_URL`: Browse Movies button URL
- `QUALITY_URL`: Video Quality button URL
- `PREMIUM_URL`: Premium Membership button URL
- `START_BOT_URL`: Get Started button URL
- `POST_CAPTION`: optional caption; supports `{channel_title}` and `{post_title}` placeholders

Only set button URLs you want displayed. The button layout is one button per row, with Get Started last, matching the supplied reference structure.

## Admin commands in Telegram
- `/start` — command help
- `/settings` — show current settings
- `/setposter https://example.com/poster.jpg` — change poster
- `/setchanneltitle MOVIE HUB` — change brand heading
- `/settitle ALL YOUR ENTERTAINMENT IN ONE PLACE` — change main title
- `/setcaption Your custom caption` — change caption
- `/setbutton movies | 🎬 Browse Movies | https://t.me/YourBot`
- `/setbutton quality | 📺 Video Quality | https://example.com/quality`
- `/setbutton premium | 👑 Premium Membership | https://t.me/YourBot`
- `/setbutton start | 🚀 Get Started → | https://t.me/YourBot`
- `/preview` — send a preview to your private chat
- `/post` — publish to the channel
- `/id` — show your numeric Telegram ID

For hiding a button, set its URL empty, e.g. `/setbutton quality | 📺 Video Quality |`

## Important
- Make the bot an administrator of your Telegram channel with permission to post.
- `POSTER_URL` must be a direct, publicly accessible image URL, not a webpage link.
- The in-chat customizations are saved to `post_config.json`. On Render, the ordinary worker filesystem may reset on redeploy/restart. For durable customization, configure a Render persistent disk or later add a database.
- This bot does not automatically search movie databases or fetch movie details; it provides editable posting layout and buttons.
