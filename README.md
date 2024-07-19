<h1>TwichGram: Twitch to Telegram Clips Tool 🎥➡️📲</h1>

TwichGram is a Python tool that automates downloading Twitch clips and sending them to a Telegram channel. It also offers an optional server for displaying random clips, perfect for OBS integration during offline moments.

<h2>Features ✨</h2>

    Automatic Clip Download 🎥: Downloads clips from a specified Twitch streamer.
    Telegram Integration 📲: Sends downloaded clips to a Telegram channel.
    Clip Viewing Server 🌐: Optionally create a server to display random clips.

<h2>Getting Started 🚀</h2>
<h3>Prerequisites 📋</h3>

    Python 3.12

<h3>Installation 💻</h3>

    git clone https://github.com/spectreDeveloper/TwichGram---Twitch-To-Telegram-Clips-Tool.git

    cd TwichGram---Twitch-To-Telegram-Clips-Tool

<h3>Install the dependencies:</h3>

    pip install -r requirements.txt
    pip install https://github.com/KurimuzonAkuma/pyrogram/archive/v2.1.22.zip --force-reinstall (check the latest version from here: https://github.com/KurimuzonAkuma/pyrogram/tags)


<h2>Usage 📖</h2>
<h3>Configuration</h3>

Set up your configuration in data/config.json following this legend:

    {
        'broadcaster_id': 12345678, # Broadcaster ID is the numeric ID of a Twitch channel (can be retrieved via API)
        'broadcaster_name': "twitchstreamername", # Broadcaster name is the username of the Twitch channel
        'twitch_client_id': "", # Twitch client ID for API requests
        'twitch_client_secret': "", # Twitch client secret for API requests
        'clip_fetch_interval': 120, # Interval in seconds to wait before fetching new clips
        
        'app_id': 0, # Telegram app ID (retrieve from my.telegram.org)
        'app_hash': "", # Telegram app hash (retrieve from my.telegram.org)
        'session_name': "clips", # Session name, used to store session Telegram data (advised not to change it)
        
        'telegram_channel_name': "theclips", # Telegram channel name to share clips (needs to be public)
        'telegram_bot_token': "", # Telegram bot token (retrieve from BotFather)
        'target_chat_ids': [ 
            -123456789 # Telegram chat IDs where to send clips (can be multiple)
        ],
        'enable_clip_server': True, # Enable or disable the clip server (allows the server to be up or not)
        'clip_server_host': '0.0.0.0', # Clip server host (use 0.0.0.0 to listen on all interfaces, or set a specific IP like "127.0.0.1")
        'clip_server_port': 5000, # Clip server port (set a port to listen for HTTP requests)
        'loading_video_picture': 'https://static-cdn.jtvnw.net/jtv_user_pictures/12345678/picture.jpeg' # Picture to show while loading the video on the server page
    }

Downloading Clips and Sending to Telegram
Ensure your configuration is set up with the necessary Twitch and Telegram credentials.

    python main.py

<h2>Setting Up the Clip Viewing Server 🌐</h2>

  If enable_clip_server is set to True, the clip server will be automatically started (no https, just http)

    Use the server URL in OBS to display random clips.

<h2>📝 Customize</h2>
    <h3>You can customize two part of codes:<br></h3>
    The HTML Inside handle_index_request function (here can customize the template of the clip web-server page)<br>
    Telegram message from send_clip_to_telegram function<br>

<h2>Contributing 🤝</h2>

Contributions are welcome! Fork the repository and submit a pull request.

<h2>ℹ️ Support</h2>
Feel free to open an issue here on github to keep in touch.
