from asyncio import run
from datetime import datetime
from functools import partial
from json import loads, dump, dumps
from os import makedirs, execl
from os.path import exists
from sys import executable
from threading import Timer
from traceback import format_exc

from discord_webhook import AsyncDiscordWebhook, DiscordEmbed
from flask import Flask, request, render_template_string, send_file
from pytz import timezone
from waitress import serve
from werkzeug.middleware.proxy_fix import ProxyFix

APP, LEVELS = Flask(import_name=__name__), {"DEBUG": 0x0000FF,
                                            "INFO": 0x008000,
                                            "WARNING": 0xFFFF00,
                                            "ERROR": 0xFFA500,
                                            "CRITICAL": 0xFF0000}
APP.wsgi_app = ProxyFix(app=APP.wsgi_app)
TIME = str(datetime.now(tz=timezone(zone="Europe/Moscow")))[:-13].replace(" ", "_").replace("-", "_").replace(":", "_")


async def logs(level, message, file=None):
    try:
        print(f"{datetime.now(tz=timezone(zone='Europe/Moscow'))} {level}:\n{message}\n\n")
        if not exists(path="logs"):
            makedirs(name="logs")
        with open(file=f"logs/{TIME}.log",
                  mode="a+",
                  encoding="UTF-8") as log_file:
            log_file.write(f"{datetime.now(tz=timezone(zone='Europe/Moscow'))} {level}:\n{message}\n\n")
        webhook = AsyncDiscordWebhook(username="Send Time Server",
                                      avatar_url="https://cdn.discordapp.com/attachments/1021085537802649661/"
                                                 "1051579517564616815/bronyru.png",
                                      url="")
        if len(message) <= 4096:
            webhook.add_embed(embed=DiscordEmbed(title=level,
                                                 description=message,
                                                 color=LEVELS[level]))
        else:
            webhook.add_file(file=message.encode(encoding="UTF-8",
                                                 errors="ignore"),
                             filename=f"{level}.log")
        if file is not None:
            with open(file=file,
                      mode="rb") as backup_file:
                webhook.add_file(file=backup_file.read(),
                                 filename=file)
        await webhook.execute()
    except Exception:
        await logs(level="CRITICAL",
                   message=format_exc())


async def backup():
    try:
        await logs(level="INFO",
                   message="Бэкап БД создан успешно!",
                   file="db/db.json")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


async def restart():
    try:
        execl(executable, "python", "sts.py")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


async def autores():
    try:
        time = int(datetime.now(tz=timezone(zone="Europe/Moscow")).strftime("%H%M%S"))
        print(f"sendtimeserver: {time}")
        if time == 0 or time == 120000:
            await backup()
        Timer(interval=1,
              function=partial(run, main=autores())).start()
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


@APP.route(rule="/",
           methods=["GET", "POST"])
async def url_home():
    try:
        with open(file="www/html/index.html",
                  mode="r",
                  encoding="UTF-8") as index_html:
            return render_template_string(source=index_html.read())
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


@APP.route(rule="/css/<file>",
           methods=["GET", "POST"])
async def url_css(file):
    try:
        return send_file(path_or_file=f"www/css/{file}")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


@APP.route(rule="/fonts/<file>",
           methods=["GET", "POST"])
async def url_fonts(file):
    try:
        return send_file(path_or_file=f"www/fonts/{file}")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


@APP.route(rule="/images/<path:file>",
           methods=["GET", "POST"])
async def url_images(file):
    try:
        return send_file(path_or_file=f"www/images/{file}")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


@APP.route(rule="/sts",
           methods=["GET", "POST"])
async def url_sts():
    try:
        start = request.args["start"]
        end = request.args["end"]
        url = request.args["id"]

        with open(file="db/db.json",
                  mode="r",
                  encoding="UTF-8") as file_1:
            db = loads(s=file_1.read())

            if url not in db:
                db.update({url: {"confirmed": {},
                                 "temp": {}}})

            for item_1 in db[url]["confirmed"]:
                if item_1 in [start, str(int(start) + 1), str(int(start) - 1)]:
                    if db[url]["confirmed"][item_1]["end"] in [end, str(int(end) + 1), str(int(end) - 1)]:
                        if request.remote_addr not in db[url]["confirmed"][item_1]["users"]:
                            db[url]["confirmed"][item_1]["users"].append(request.remote_addr)
                            with open(file="db/db.json",
                                      mode="w",
                                      encoding="UTF-8") as file_2:
                                dump(obj=db,
                                     fp=file_2,
                                     indent=4,
                                     ensure_ascii=False)
                        return "1125"

            for item_2 in db[url]["temp"]:
                if item_2 in [start, str(int(start) + 1), str(int(start) - 1)]:
                    if db[url]["temp"][item_2]["end"] in [end, str(int(end) + 1), str(int(end) - 1)]:
                        if request.remote_addr not in db[url]["temp"][item_2]["users"]:
                            db[url]["temp"][item_2]["users"].append(request.remote_addr)
                            with open(file="db/db.json",
                                      mode="w",
                                      encoding="UTF-8") as file_3:
                                dump(obj=db,
                                     fp=file_3,
                                     indent=4,
                                     ensure_ascii=False)
                        return "1125"

            db[url]["temp"].update({start: {"end": end,
                                            "users": [request.remote_addr]}})
            with open(file="db/db.json",
                      mode="w",
                      encoding="UTF-8") as file_4:
                dump(obj=db,
                     fp=file_4,
                     indent=4,
                     ensure_ascii=False)
            return "1125"
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return "ERROR"


@APP.route(rule="/confirmed",
           methods=["GET", "POST"])
async def url_confirmed():
    try:
        with open(file="db/db.json",
                  mode="r",
                  encoding="UTF-8") as file_1:
            db, output = loads(s=file_1.read()), {}

            for item in db:
                temp = []
                for item_2 in db[item]["temp"]:
                    users = db[item]["temp"][item_2]["users"]
                    if len(users) >= 5 or "84.39.241.206" in users:
                        db[item]["confirmed"].update({item_2: db[item]["temp"][item_2]})
                        temp.append(item_2)

                for item_3 in temp:
                    db[item]["temp"].pop(item_3)

                if len(db[item]["confirmed"]) > 0:
                    t = []
                    for item_4 in db[item]["confirmed"]:
                        t.append([int(item_4), int(db[item]["confirmed"][item_4]["end"])])
                    output.update({item: t})

            with open(file="db/db.json",
                      mode="w",
                      encoding="UTF-8") as file_2:
                dump(obj=db,
                     fp=file_2,
                     indent=4,
                     ensure_ascii=False)

            return dumps(obj=output,
                         ensure_ascii=False)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return "ERROR"


@APP.route(rule="/api/<path:get>",
           methods=["GET", "POST"])
async def url_api(get):
    try:
        if get == "time":
            return str(datetime.now(tz=timezone(zone="Europe/Moscow")))[:-13]
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return "ERROR"


@APP.errorhandler(code_or_exception=404)
async def error_404(error):
    try:
        print(error)
        with open(file="www/html/error.html",
                  mode="r",
                  encoding="UTF-8") as error_html:
            return error_html.read()
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


@APP.errorhandler(code_or_exception=500)
async def error_500(error):
    try:
        print(error)
        with open(file="www/html/error.html",
                  mode="r",
                  encoding="UTF-8") as error_html:
            return error_html.read()
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


if __name__ == "__main__":
    try:
        run(main=autores())
        serve(app=APP,
              port=1126,
              threads=16)
    except Exception:
        run(main=logs(level="ERROR",
                      message=format_exc()))
