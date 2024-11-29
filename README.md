<h1>TwichGram: Twitch to Telegram Clips Tool 🎥➡️📲</h1>

TwichGram is a Python tool that automates downloading Twitch clips and sending them to a Telegram channel. It also offers an optional server for displaying random clips, perfect for OBS integration during offline moments.

<h2>Features ✨</h2>

    Automatic Clip Download 🎥: Downloads clips from a specified Twitch streamer.
    Telegram Integration 📲: Sends downloaded clips to a Telegram channel.
    Clip Viewing Server 🌐: Optionally create a server to display random clips.
    API Support ⚡️: to handle a Blacklist to prevent show clips with inside bannable words.
<h2>Getting Started 🚀</h2>
<h3>Prerequisites 📋</h3>

    Python 3.12

<h3>Installation 💻</h3>
    You can use: docker-compose build && docker-compose up to install easy otherwise follow the next steps.

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
        'loading_video_pictures':[
            'https://static-cdn.jtvnw.net/jtv_user_pictures/12345678/picture.jpeg' # Pictures to show while loading the video on the server page. Separe it using json syntax.
        ],
        "webserver_secret_token": "ADDSECRETHERE" # Secret token for WEBSERVER API, Make it complex.
    }

Downloading Clips and Sending to Telegram
Ensure your configuration is set up with the necessary Twitch and Telegram credentials.

    python main.py

<h2>Setting Up the Clip Viewing Server 🌐</h2>

  If enable_clip_server is set to True, the clip server will be automatically started (no https, just http)

    Use the server URL in OBS to display random clips.

<h2>📝 Customize</h2>
    <h3>You can customize two part of codes:<br></h3>
    The HTML Inside the file index.html located in static/index.html<br>
    Telegram message from send_clip_to_telegram function<br>

<h2>⚡️API Integration and Blacklist</h2>
    <h3>You can now use three new endpoints to handle the clips blacklist</h3>
    - /get_blacklisted_clips | GET | Require webserver_secret_token | Show all clips blacklisted.<br>
    - /add_to_blacklist | POST | Require webserver_secret_token | Add a slug as json body to add a clip in blacklist.<br>
    - /remove_from_blacklist | POST | Require webserver_secret_token | Add a slug as json body to remove a clip in blacklist.<br>

<h2>API Screenshots</h2>
    <img src="https://telegra.ph/file/d64a5b709eff5f5f04040.jpg"></img><br>
    <img src="https://telegra.ph/file/1b40c9745cbd1c184fed9.jpg"></img><br>
    <img src="https://telegra.ph/file/4f615e297d68104db14af.jpg"></img><br>
    
<h2>Contributing 🤝</h2>

Contributions are welcome! Fork the repository and submit a pull request.

<h2>ℹ️ Support</h2>
Feel free to open an issue here on github to keep in touch.
