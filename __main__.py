#!/usr/bin/env python
import time
import logging
import os

from io import BytesIO
from datetime import datetime, timedelta
from dataclasses import dataclass

import asyncio
import aiohttp
import aiosqlite

from pyrogram import Client
from pyrogram.errors import FloodWait

from aiohttp import web

import orjson
import argparse

import random

@dataclass
class TwitchClip:
    slug: str
    title: str
    url: str
    created_at: str
    durationSeconds: int
    curator_name: str | None
    curator_url:  str | None
    thumbnail_url: str
    mp4_url:  str | None

class TimestampFilter(logging.Filter):
    def filter(self, record):
        record.timestamp = int(time.time())
        return True

logging.getLogger('pyrogram').setLevel(logging.CRITICAL)
  
log_format = "[%(asctime)s] [%(levelname)s] [%(timestamp)s] %(message)s"
date_format = "%d/%m/%Y %H:%M:%S"
formatter = logging.Formatter(log_format, datefmt=date_format)

handler = logging.StreamHandler()
handler.setFormatter(formatter)

handler.addFilter(TimestampFilter())

logger = logging.getLogger()
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def load_configs():
    parse_json = lambda p: orjson.loads(open(p, "rb").read())
    argparser: argparse.ArgumentParser = argparse.ArgumentParser()
    try:
        argparser.add_argument("-config", type=parse_json, required=False, default="./data/configs.json", help="Path to the config file")
        arguments = argparser.parse_args()
        return arguments.config
    except Exception as e:
        logging.error(f"Error during loading config file: {e}")
        exit(1)

# load configs as CONFIGS
CONFIGS: dict = load_configs()

# db parts
async def init_clips_database():
    async with aiosqlite.connect('clips.db') as db:
        await db.execute('CREATE TABLE IF NOT EXISTS clips (slug TEXT PRIMARY KEY, title TEXT, url TEXT, created_at TEXT, durationSeconds INTEGER, curator_name TEXT, curator_url TEXT, thumbnail_url TEXT, mp4_url TEXT)')
        await db.execute('CREATE TABLE IF NOT EXISTS blacklist_clips (slug TEXT PRIMARY KEY)')
        
        await db.execute('CREATE INDEX IF NOT EXISTS idx_clips_slug ON clips (slug)')
        await db.execute('CREATE INDEX IF NOT EXISTS idx_blacklist_clips_slug ON blacklist_clips (slug)')
        
        await db.commit()

async def add_clip_to_db(clip: TwitchClip, db: aiosqlite.Connection):
    async with db.execute('INSERT OR IGNORE INTO clips VALUES (?,?,?,?,?,?,?,?,?)', (clip.slug, clip.title, clip.url, clip.created_at, clip.durationSeconds, clip.curator_name, clip.curator_url, clip.thumbnail_url, clip.mp4_url)) as cursor:
        await db.commit()

async def check_if_clip_exists(slug: str, db: aiosqlite.Connection) -> bool:
    async with db.execute('SELECT slug FROM clips WHERE slug = ?', (slug,)) as cursor:
        if await cursor.fetchone():
            return True
        return False

async def check_if_clip_is_blacklisted(slug: str, db: aiosqlite.Connection) -> bool:
    async with db.execute('SELECT slug FROM blacklist_clips WHERE slug = ?', (slug,)) as cursor:
        if await cursor.fetchone():
            return True
        return False
    
async def add_clip_to_blacklist(slug: str, db: aiosqlite.Connection):
    if await check_if_clip_exists(slug, db) and not await check_if_clip_is_blacklisted(slug, db):
        async with db.execute('INSERT INTO blacklist_clips VALUES (?)', (slug,)) as cursor:
            await db.commit()
        
async def remove_clip_from_blacklist(slug: str, db: aiosqlite.Connection):
    if await check_if_clip_exists(slug, db) and await check_if_clip_is_blacklisted(slug, db):
        async with db.execute('DELETE FROM blacklist_clips WHERE slug = ?', (slug,)) as cursor:
            await db.commit()
        
async def get_blacklisted_clips(db: aiosqlite.Connection) -> list:
    async with db.execute('SELECT title, url FROM clips WHERE slug IN (SELECT slug FROM blacklist_clips)') as cursor:
        return await cursor.fetchall()
    

# oauth2/token params
def get_oauth_headers(auth_token: str, client_id: str) -> dict:
    return {
        'Authorization': f'Bearer {auth_token}',
        'Client-Id': client_id,
    }

async def get_twitch_bearer() -> tuple:
    async with aiohttp.ClientSession() as session:
        async with session.post("https://id.twitch.tv/oauth2/token", data={
            "client_id": CONFIGS['twitch_client_id'],
            "client_secret": CONFIGS['twitch_client_secret'],
            "grant_type": "client_credentials"
        }) as response:
            if response.status == 200:
                try:
                    response_json = await response.json()
                    return (response_json["access_token"], response_json["expires_in"])
                except Exception as e:
                    logging.error(f"Error: {e}")
                    return (None, None)
            else:
                return (None, None)
           
# clips part
async def fetch_clips(clips_queue: asyncio.Queue, aiohttp_session: aiohttp.ClientSession):
    oauth_token: str = await get_twitch_bearer()
    oauth_headers: dict = get_oauth_headers(oauth_token[0], CONFIGS['twitch_client_id'])
    expiring_date: datetime = datetime.now() + timedelta(seconds=oauth_token[1])
    logging.info(f"Bearer token: {oauth_token[0]} - Expires at: {expiring_date} - Expires in: {oauth_token[1]} seconds")
    
    while True:
        if expiring_date < datetime.now():
            oauth_token = await get_twitch_bearer()
            logging.info(f"Renewing bearer token! New token: {oauth_token[0]}")
            expiring_date = datetime.now() + timedelta(seconds=oauth_token[1])
            
        cursor: str = ""
        start_date: str = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        try:
            while True:
                params = {
                    'broadcaster_id': CONFIGS['broadcaster_id'],
                    'after': cursor,
                    'started_at': start_date,
                    'ended_at': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'first': 100,
                    'is_featured': 'false',
                }

                async with aiohttp_session.get('https://api.twitch.tv/helix/clips', params=params, headers=oauth_headers) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        clips = data['data']

                        if not clips:
                            logging.info("No clips found for this cycle")
                            break

                        for clip in clips:
                            await clips_queue.put(TwitchClip(
                                clip['id'],
                                clip['title'],
                                clip['url'],
                                clip['created_at'],
                                clip['duration'],
                                clip['creator_name'],
                                f"https://www.twitch.tv/{clip['creator_name']}",
                                clip['thumbnail_url'],
                                clip['thumbnail_url'].replace('-preview-480x272.jpg', '.mp4')
                            ))
                            
                        cursor = data.get('pagination', {}).get('cursor', "")
                        
                        if not cursor:
                            break
                    else:
                        logging.info(f"Error: {response.status}")
                        return None
        finally:
            logging.info(f"Cycle ended! Sleeping for {CONFIGS['clip_fetch_interval']} seconds")
            await asyncio.sleep(CONFIGS['clip_fetch_interval'])
                
async def process_clips_queue(clips_queue: asyncio.Queue, telegram_queue: asyncio.Queue, database_instance: aiosqlite.Connection):
    while True:
        clip = await clips_queue.get()
        if isinstance(clip, TwitchClip):
            if not await check_if_clip_exists(clip.slug, database_instance):
                await add_clip_to_db(clip, database_instance)
                await telegram_queue.put(clip)

async def send_clip_to_telegram(clip: TwitchClip, aiohttp_session: aiohttp.ClientSession, pyro_instance: Client, target_chat_id: int):
    share_clip_url = f"https://t.me/share/url?url={clip.url}"
    share_channel_url = f"https://t.me/share/url?url=t.me/{CONFIGS['telegram_channel_name']}&text=Scopri altre fantastiche clip su @{CONFIGS['telegram_channel_name']}!"
    share_channel_url = share_channel_url.replace(' ', '%20')
    caption = f"⚡️ <b>{clip.title}</b>\n\nGrazie a <a href='{clip.curator_url}'>{clip.curator_name}</a> per aver condiviso questa <b>clip!</b> 🔗\n\n<a href='{clip.url}'>📺 Guarda la clip su <b>Twitch</b></a>\n👉 <b>Iscriviti</b> al canale <b><a href='https://twitch.tv/{CONFIGS['broadcaster_name']}'>Twitch</a></b> per vedere le clip in <b>diretta</b>!\n\n🔗 <b><a href='{share_clip_url}'>Condividi la clip su Telegram</a></b>\n<b>⏩ <a href='{share_channel_url}'>Condividi il canale su Telegram</a></b>\n"
        
    async with aiohttp_session.get(clip.mp4_url) as response:
        if response.status == 200:
            video = BytesIO(await response.read())
            video.name = f"{clip.slug}.mp4"
            video.seek(0)
            try:
                await pyro_instance.send_video(
                    chat_id=target_chat_id,
                    caption=caption,
                    video=video,
                )
                logging.info(f"Clip {clip.slug} was sent to telegram successfully!")
                
            except FloodWait as e:
                logging.error(f"Error during sending clip to telegram due to floodwait! waiting for {e.value} seconds before retrying")
                await asyncio.sleep(e.value)
                await pyro_instance.send_video(
                    chat_id=target_chat_id,
                    caption=caption,
                    video=video,
                    thumb=clip.thumbnail_url,
                    disable_notification=True,
                    supports_streaming=True,
                )
                
            except Exception as e:
                logging.error(f"Error during sending clip to telegram: {e}")
        else:
            logging.error(f"Error downloading clip: {response.status} - {clip.mp4_url} - {clip.slug}")
            
async def process_telegram_queue(telegram_queue: asyncio.Queue, aiohttp_session: aiohttp.ClientSession, pyro_instance: Client):
    await pyro_instance.start()
    
    while not pyro_instance.is_initialized:
        logging.info("Waiting for pyrogram to initialize")
        await asyncio.sleep(1)
        
    while True:
        clip = await telegram_queue.get()
        if isinstance(clip, TwitchClip):
            for target_chat_id in CONFIGS['target_chat_ids']:
                await send_clip_to_telegram(clip, aiohttp_session, pyro_instance, target_chat_id)

# clip server part
async def run_clip_server(database_instance: aiosqlite.Connection, host: str, port: int):
        
    async def handle_clip_request(request):
        async with database_instance.execute('SELECT slug, mp4_url, title FROM clips WHERE slug NOT IN (SELECT slug FROM blacklist_clips) ORDER BY RANDOM() LIMIT 1') as cursor:
            clip = await cursor.fetchone()
            if clip:
                slug, mp4_url, title = clip
                return web.json_response({'slug': slug, 'mp4_url': mp4_url, 'title': title})
            else:
                return web.json_response({'error': 'No clips found'}, status=404)

    async def handle_index_request(request):
        html_content: str = open('static/index.html', 'r').read().replace('[PICTURE_LOAD_HERE]', random.choice(CONFIGS['loading_video_pictures']))
        return web.Response(text=html_content, content_type='text/html')

    async def get_blacklist_clips(request):
        if request.method == 'GET' and request.query.get('webserver_secret_token') == CONFIGS['webserver_secret_token']:
            blacklisted_clips = await get_blacklisted_clips(database_instance)
            return web.json_response({'blacklisted_clips': blacklisted_clips})
        
    async def add_to_blacklist(request):
        if request.method == 'POST' and request.query.get('webserver_secret_token') == CONFIGS['webserver_secret_token']:
            data: dict = await request.json()
            slug: str = data.get('slug')
            if slug:
                await add_clip_to_blacklist(slug, database_instance)
                return web.json_response({'status': 'success'})
            else:
                return web.json_response({'error': 'No slug provided'}, status=400)
            
    async def remove_from_blacklist(request):
        if request.method == 'POST' and request.query.get('webserver_secret_token') == CONFIGS['webserver_secret_token']:
            data: dict = await request.json()
            slug: str = data.get('slug')
            if slug:
                await remove_clip_from_blacklist(slug, database_instance)
                return web.json_response({'status': 'success'})
            else:
                return web.json_response({'error': 'No slug provided'}, status=400)

    app = web.Application()
    app.add_routes([web.get('/clip', handle_clip_request)])
    app.add_routes([web.get('/', handle_index_request)])

    app.add_routes([web.get('/get_blacklisted_clips', get_blacklist_clips)])
    app.add_routes([web.post('/add_to_blacklist', add_to_blacklist)])
    app.add_routes([web.post('/remove_from_blacklist', remove_from_blacklist)])
    
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host, port)
    await site.start()
    logging.info(f"Clip server started on port {port}")
                
    
async def main():
    await init_clips_database()
    pyro_instance: Client = Client(
        name=CONFIGS['session_name'],
        api_id=CONFIGS['app_id'],
        api_hash=CONFIGS['app_hash'],
        bot_token=CONFIGS['telegram_bot_token']
    )
        
    tasks: asyncio.Task = []
    clips_queue: asyncio.Queue = asyncio.Queue()
    telegram_queue: asyncio.Queue = asyncio.Queue()
    
    aiohttp_session: aiohttp.ClientSession = aiohttp.ClientSession()
    
    database_instance: aiosqlite.Connection = await aiosqlite.connect("clips.db")
    
    tasks.append(asyncio.create_task(fetch_clips(clips_queue, aiohttp_session)))
    tasks.append(asyncio.create_task(process_clips_queue(clips_queue, telegram_queue, database_instance)))
    tasks.append(asyncio.create_task(process_telegram_queue(telegram_queue, aiohttp_session, pyro_instance)))
                 
    if CONFIGS['enable_clip_server'] and os.path.exists('static/index.html'):
        tasks.append(asyncio.create_task(run_clip_server(database_instance, CONFIGS['clip_server_host'], CONFIGS['clip_server_port'])))
    elif not os.path.exists('static/index.html'):
        logging.error("No index.html file found in static/ directory! Server will not start")
        
    await asyncio.gather(*tasks)
    
if __name__ == '__main__':
    asyncio.run(main())
    
    


