from bot.core.session_creator import SessionCreator, SessionExistsError
from bot.utils.logger import logger
from bot.core.main import Bot

async def main_process(settings) -> None:
    logger.info("Start prepareting sessions")
    print()
    while True:
        # Select an option
        try:
            print("┌───────────────────────────────────┐")
            print("│          Select an Option         │")
            print("├───────────────────────────────────┤")
            print("│  1 - Register sessions            │")
            print("│  2 - Start bot                    │")
            print("└───────────────────────────────────┘")
            command = int(input("➤ "))
            print(command)
            if command not in [1, 2]:
                logger.warning("Command must be 1 or 2")
                continue
            break
        except ValueError:
            logger.warning("Command must be number")
    

    # Register sessions command
    if command == 1:
        logger.info("Register sessions")
        while True:
            try:
                res = SessionCreator(settings)
                await res.create_session()
                if res:
                    logger.info("Session created successfully")
                else:
                    logger.error("Failed to create session")
                while True:
                    print("Do you want to register another session? (y/n)")
                    ans = input("➤ ")
                    if ans not in ["y", "n"]:
                        logger.warning("Answer must be y or n") 
                        continue
                    break
                if ans == "n":
                    logger.info("Stop creating sessions")
                    break
                logger.info("Register another session")
            except SessionExistsError:
                logger.error("Session already exists")

    # Start bot command
    if command == 2:
        logger.info("Start bot")
        bot = Bot(settings)
        await bot.start()