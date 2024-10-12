import asyncio
from datetime import datetime
from PIL import Image
import io
from random import choice, randint, uniform
from time import time
from urllib.parse import unquote
from pyrogram import Client
from bot.utils.proxy import Proxy
from bot.utils.headers import headers_example
from pydantic_settings import BaseSettings
from bot.utils.logger import logger
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.functions.messages import RequestWebView, StartBot
from aiocfscrape import CloudflareScraper

available_colors = [
    "#E46E6E", "#FFD635", "#7EED56", "#00CCC0", "#51E9F4", "#94B3FF", "#E4ABFF", "#6A5CFF",
    "#FF99AA", "#FFB470", "#FFFFFF", "#BE0039", "#FF9600", "#00CC78", "#009EAA", "#3690EA",
    "#B44AC0", "#FF3881", "#9C6926", "#898D90", "#6D001A", "#BF4300", "#00A368", "#00756F",
    "#2450A4", "#493AC1", "#811E9F", "#A00357", "#6D482F", "#000000"
]

#https://notpx.app/api/v1/mining/boost/check/paintReward
prices = {
    2: 5,
    3: 100,
    4: 200,
    5: 300,
    6: None,
    7: None,
    8: None,
}





class InvalidStartTgApp(BaseException):
    ...

class GetPixelTemplateError(BaseException):
    ...




class Blum:
    def __init__(self, tg_session: Client,
                settings: BaseSettings,
                proxy: Proxy | None = None,
                user_agent: str | None = None):
        
        self.tg_session = tg_session
        self.settings = settings
        self.name = "@" + str(tg_session.workdir).split("/")[-1] if tg_session.workdir else tg_session.name
        self.proxy = proxy

        self.headers = headers_example.copy()
        self.headers["User-Agent"] = user_agent

        self.logged = False
        self.auth_token = None
        self.__name_tg_bot = 'notpixel'
        self.referal_param = settings.REF
        self.user_balance = 0
        self.charges = 0
        self.max_charges = 0
        self.charge_speed = 0
        self.paint_reward_level = 0
        self.energy_limit_level = 0
        self.charge_speed_level = 0

        self.template_id = 0
        self.template_img = ""
        self.template_pixels = []

        self.use_template = True


        


    # async def night_sleep_check(self):
    #     if bool(self.settings.NIGHT_SLEEP):
    #         time_now = datetime.now()

    #         # Start and end of the day
    #         sleep_start = time_now.replace(hour=0, minute=0, second=0, microsecond=0)  # 00:00 ночи
    #         sleep_end = time_now.replace(hour=8, minute=0, second=0, microsecond=0)    # 08:00 утра

    #         if time_now >= sleep_start and time_now <= sleep_end:
    #             time_to_sleep = (sleep_end - time_now).total_seconds()
    #             wake_up_time = time_to_sleep + randint(0, 3600)

    #             logger.info(f"{self.name} | Sleep until {sleep_end.strftime('%H:%M')}")
    #             await asyncio.sleep(wake_up_time)

    #         logger.info(f"{self.name} | Sleep cancelled | Now start the game")


    async def tg_app_start(self):
        try:
            if not self.tg_session.is_connected:
                await self.tg_session.connect()
            async for message in self.tg_session.get_chat_history(self.__name_tg_bot):
                if message.text and message.text.startswith('/start'):
                    logger.info('Command /start found.')
                    bot_peer = await self.tg_session.resolve_peer(self.__name_tg_bot)
                    break 
            else:
                logger.info('Command /start not found. Send new command with referral parameter.')
                bot_peer = await self.tg_session.resolve_peer(self.__name_tg_bot)
                await self.tg_session.invoke(
                    StartBot(
                        bot=bot_peer,
                        peer=bot_peer,
                        start_param=self.referal_param,
                        random_id=randint(1, 9999999),
                    )
                )
                logger.info('Command /start sent successfully.')
        except (Unauthorized, UserDeactivated, AuthKeyUnregistered) as e:
            logger.error(f'Error start tg app: {e}')
            raise InvalidStartTgApp(e)

    async def get_tg_web_data(self):
        peer = await self.tg_session.resolve_peer(self.__name_tg_bot)
        web_view = await self.tg_session.invoke(RequestWebView(
            peer=peer,
            bot=peer,
            platform='android',
            from_bot_menu=False,
            url="https://app.notpx.app",
            start_param=self.referal_param
        ))
        auth_url = web_view.url
        print(auth_url)
        tg_web_data = unquote(
            string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
        )
        if self.tg_session.is_connected:
            await self.tg_session.disconnect()
        self.headers['Authorization'] = f"initData {tg_web_data}"
        self.auth_token = tg_web_data
        return tg_web_data


    async def get_status(self, session: CloudflareScraper) -> bool:
        async with session.get("https://notpx.app/api/v1/mining/status", headers=self.headers) as res:
            if res.status != 200:
                logger.warning(f"{self.name} | <yellow>Get user status failed: {await res.text()})</yellow>")
                return False
            data = await res.json()
            self.user_balance = data.get('userBalance', 0)
            self.charges = data.get('charges', 0)
            self.max_charges  = data.get('maxCharges', 0)
            self.charge_speed = data.get('reChargeSpeed', 0)
            boosts = data.get('boosts', {})
            self.energy_limit_level = boosts.get('energyLimit', 0)
            self.paint_reward_level = boosts.get('paintReward', 0)
            self.charge_speed_level = boosts.get('reChargeSpeed', 0)
            return True


    async def get_template(self, session: CloudflareScraper) -> bool:
        try:
            payload = {
                "limit": 12,
                "offset": 0
            }
            async with session.get("https://notpx.app/api/v1/image/template/list", headers=self.headers, json=payload) as res:
                if res.status != 200:
                    logger.warning(f"{self.name} | <yellow>Get list templates failed: {await res.text()})</yellow>")
                    return False
                data = await res.json()
                template = choice(data)
                self.template_id = template.get('templateId', 0)
                self.template_img = template.get('url', "")
            async with session.get(self.template_img, headers=self.headers) as res:
                if res.status != 200:
                    logger.warning(f"{self.name} | <yellow>Get template image failed: {await res.text()})</yellow>")
                    return False
                img_data = await res.read()
                with open('template.png', 'wb') as f:
                    f.write(img_data)
                img = Image.open(io.BytesIO(img_data))
                img = img.convert('RGB')
                pixels = list(img.getdata())
                self.template_pixels = [[f'#{r:02X}{g:02X}{b:02X}' for r, g, b in pixels[i:i + img.width]] for i in range(0, len(pixels), img.width)]
                return True
        except Exception as e:
            raise GetPixelTemplateError(e)
    

    async def get_template_info(self, session: CloudflareScraper) -> bool:
        try:
            async with session.get(f"https://notpx.app/api/v1/image/template/{self.template_id}", headers=self.headers) as res:
                if res.status != 200:
                    logger.warning(f"{self.name} | <yellow>Get template info failed: {await res.text()})</yellow>")
                    return False
                data = await res.json()
                self.template_size = data.get('imageSize', 0)
                self.template_x = data.get('x', 0)
                self.template_y = data.get('y', 0)
                return True
        except Exception as e:
            return False


    async def get_pixel_on_board(self, session: CloudflareScraper) -> bool | tuple[int, str]:
        attempts = 0
        attempts_retry = 0
        if not self.use_template:
            self.template_x = 0
            self.template_y = 0
            self.template_size = 1000
        while attempts < 3 and attempts_retry < 3:
            logger.info(f"{self.name} | Get pixel attempts: {attempts+1} | Retry: {attempts_retry+1}")
            await asyncio.sleep(uniform(0.5, 3.5))
            random_x = randint(self.template_x, self.template_x + self.template_size - 1)
            random_y = randint(self.template_y, self.template_y + self.template_size - 1)
            id_pixel = random_y * 1000 + random_x + 1
            print(id_pixel, f"x:{random_x} y:{random_y}")
            async with session.get(f"https://notpx.app/api/v1/image/get/{id_pixel}", headers=self.headers) as res:
                if res.status == 504:
                    logger.warning(f"{self.name} | Many requests get this pixel. Try again")
                    attempts_retry += 1
                    asyncio.sleep(1)
                    continue
                if res.status != 200:
                    logger.warning(f"{self.name} | <yellow>Get pixel failed: {await res.text()})</yellow>")
                    return False
                data = await res.json()
                pixel = data.get('pixel', {}).get('color', "")
                if not pixel:
                    attempts += 1
                    continue
                if pixel.upper() not in available_colors:
                    attempts += 1
                    continue
                if not self.use_template:
                    logger.info(f"{self.name} | <light-green>Pixel random: </light-green><cyan>{pixel}</cyan>")
                    return id_pixel, choice(available_colors)
                picture_pixel = self.template_pixels[random_y-self.template_y][random_x-self.template_x]
                if picture_pixel == pixel.upper():
                    logger.info(f"{self.name} | <light-green>Pixel found: </light-green><cyan>{pixel}</cyan> is used")
                    if attempts + 1 >= 3:
                        return id_pixel, choice(available_colors)
                    attempts += 1
                    continue
                logger.info(f"{self.name} | <light-green>Pixel found: </light-green><cyan>{pixel}</cyan>")
                return id_pixel, picture_pixel
        return False


    async def draw_pixel(self, session: CloudflareScraper, id_pixel: int, pixel: str) -> bool:
        payload = {
            "pixelId": id_pixel,
            "newColor": pixel
        }
        async with session.post("https://notpx.app/api/v1/repaint/start", headers=self.headers, json=payload) as res:
            if res.status != 200:
                logger.warning(f"{self.name} | <yellow>Draw pixel failed: {await res.text()})</yellow>")
                return False
            data = await res.json()
            self.user_balance = data.get('balance', 0)
            return True


    async def upgrade_boost(self, session: CloudflareScraper):
        price_next_paint_level = prices.get(self.paint_reward_level + 1, None)
        if not price_next_paint_level:
            logger.warning(f"{self.name} | <yellow>Upgrade boost (paintReward) failed: price not found</yellow>")
        price_next_charge_level = prices.get(self.charge_speed_level  + 1, None)
        if not price_next_charge_level:
            logger.warning(f"{self.name} | <yellow>Upgrade boost (reChargeSpeed) failed: price not found</yellow>")
        price_next_energy_level = prices.get(self.energy_limit_level  + 1, None)
        if not price_next_energy_level:
            logger.warning(f"{self.name} | <yellow>Upgrade boost (energyLimit) failed: price not found</yellow>")
        if not price_next_energy_level or not price_next_charge_level or not price_next_paint_level:
            return False
        if price_next_paint_level and self.user_balance > price_next_paint_level:
            async with session.get("https://notpx.app/api/v1/mining/boost/check/paintReward", headers=self.headers) as res:
                if res.status != 200:
                    logger.warning(f"{self.name} | <yellow>Upgrade boost failed: {await res.text()})</yellow>")
                    return False
                self.user_balance -= price_next_paint_level
                logger.success(f"{self.name} | <light-green>Upgrade boost (paintReward) success: </light-green><cyan>{self.user_balance}</cyan>")
                await asyncio.sleep(2)
        if price_next_charge_level and self.user_balance > price_next_charge_level:
            async with session.get("https://notpx.app/api/v1/mining/boost/check/reChargeSpeed", headers=self.headers) as res:
                if res.status != 200:
                    logger.warning(f"{self.name} | <yellow>Upgrade boost failed: {await res.text()})</yellow>")
                    return False
                self.user_balance -= price_next_charge_level
                logger.success(f"{self.name} | <light-green>Upgrade boost (reChargeSpeed) success: </light-green><cyan>{self.user_balance}</cyan>")
                await asyncio.sleep(2)
        if price_next_energy_level and self.user_balance > price_next_energy_level:
            async with session.get("https://notpx.app/api/v1/mining/boost/check/energyLimit", headers=self.headers) as res:
                if res.status != 200:
                    logger.warning(f"{self.name} | <yellow>Upgrade boost failed: {await res.text()})</yellow>")
                    return False
                self.user_balance -= price_next_energy_level
                logger.success(f"{self.name} | <light-green>Upgrade boost (energyLimit) success: </light-green><cyan>{self.user_balance}</cyan>")
                await asyncio.sleep(2)
        return True

    async def start(self):

        while True:
            logger.info(f"Account {self.name} | started")
            connector = self.proxy.get_connector() if isinstance(self.proxy, Proxy) else None
            client = CloudflareScraper(headers=self.headers, connector=connector)
            self.use_template = True
            try:
                async with client as session:
                    await self.tg_app_start()
                    await self.get_tg_web_data()
                    res = await self.get_status(session)
                    if not res:
                        return
                    logger.success(f"Account {self.name} | connected")
                    logger.info(f"Account {self.name} | Balance: {self.user_balance} | Charges: {self.charges}")
                    logger.info(f"Account {self.name} | Boosts: Energy: {self.energy_limit_level} Paint: {self.paint_reward_level} Charge: {self.charge_speed_level}")

                    # Upgrade boost
                    await self.upgrade_boost(session)
                    

                
                    #Draw pixels
                    if self.charges > 0:
                        # Check template if needed and open
                        try:
                            if self.use_template:
                                logger.info(f"Account {self.name} | atempt using template")
                                res = await self.get_template(session)
                                if res:
                                    logger.info(f"Account {self.name} | template open success")
                                    info = await self.get_template_info(session)
                                    if info:
                                        logger.info(f"Account {self.name} | template ready")
                                        self.use_template = True
                                    else:
                                        self.use_template = False
                                else:
                                    self.use_template = False
                        except Exception:
                            self.use_template = False
                        # Start drawing
                        logger.info(f"Account {self.name} | start draw pixels")
                        while self.charges > 0:
                            await asyncio.sleep(1)
                            self.charges -= 1
                            try:
                                res = await self.get_pixel_on_board(session)
                                if res:
                                    pixel_id, pixel_color = res
                                    logger.info(f"{self.name} | Draw pixel id: {pixel_id} color: {pixel_color}")
                                    res = await self.draw_pixel(session, pixel_id, pixel_color)
                                    if not res:
                                        logger.warning(f"{self.name} | <yellow>Draw pixel failed</yellow>")
                                        continue
                                    logger.info(f"{self.name} | <light-green>Draw pixel success</light-green> Balance: <cyan>{self.user_balance}</cyan>")
                            except Exception as e:
                                print(e)
                    else:
                        logger.info(f"Account {self.name} | no charges")

                    logger.info(f"Account {self.name} | Finished Balance: {self.user_balance} | Charges: {self.charges}")
                seconds = (self.max_charges - self.charges) * self.charge_speed // 1000
                antifrost_time = uniform(600, 3600*2)
                seconds += antifrost_time
                hours = seconds // 3600
                minutes = (seconds % 3600) // 60
                logger.info(f"Account {self.name} | Sleep for get new charge: {hours}h {minutes}m (antifrost {antifrost_time} seconds)")
                await asyncio.sleep(seconds)
            except Exception as e:
                logger.error(f"Account {self.name} | Error: {e}")
                break
            
        logger.info(f"Account {self.name} | finished")


async def run_gamer(tg_session: tuple[Client, Proxy, str], settings) -> None:
    """
    Starts a Gamer instance and waits for a random time between 1-5 seconds before doing so.
    
    Args:
        tg_session (tuple[Client, Proxy, str]): A tuple containing a Client instance, a Proxy instance and a User-Agent string.
        settings (Settings): The settings to use for this Gamer instance.
    """
    tg_session, proxy, user_agent = tg_session
    gamer = Blum(tg_session=tg_session, settings=settings, proxy=proxy, user_agent=user_agent)
    try:
        sleep = randint(1, 5)
        logger.info(f"Account {gamer.name} | ready in {sleep}s")
        await asyncio.sleep(sleep)
        await gamer.start()
    except Exception as e:
        logger.error(f"Account {gamer.name} | Error: {e}")




