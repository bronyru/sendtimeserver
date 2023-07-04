from asyncio import run
from datetime import datetime
from functools import partial
from hashlib import sha256
from json import loads, dump, dumps
from os import makedirs, execl
from os.path import exists
from sys import executable
from threading import Timer
from traceback import format_exc

from discord_webhook import AsyncDiscordWebhook, DiscordEmbed
from flask import Flask, request, render_template_string, send_file, abort, make_response
from natsort import natsorted, ns
from pytz import timezone
from waitress import serve
from werkzeug.exceptions import HTTPException
from werkzeug.middleware.proxy_fix import ProxyFix

APP, LEVELS = Flask(import_name=__name__), {"DEBUG": 0x0000FF,
                                            "INFO": 0x008000,
                                            "WARNING": 0xFFFF00,
                                            "ERROR": 0xFFA500,
                                            "CRITICAL": 0xFF0000}
APP.wsgi_app = ProxyFix(app=APP.wsgi_app)
TIME = str(datetime.now(tz=timezone(zone="Europe/Moscow")))[:-13].replace(" ", "_").replace("-", "_").replace(":", "_")
ADMINS = {}
TOKENS = [sha256((x + ADMINS[x]).encode(encoding="UTF-8",
                                        errors="ignore")).hexdigest() for x in ADMINS]


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
        execl(executable, "python", "sendtimeserver.py")
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


async def db_sort(db, item, trigger):
    try:
        temp = []

        for item_2 in db[item]["temp"]:
            users = db[item]["temp"][item_2]["users"]

            if len(users) >= 5 or "84.39.241.206" in users:
                trigger = True
                db[item]["confirmed"].update({item_2: db[item]["temp"][item_2]})
                temp.append(item_2)

        for item_3 in temp:
            db[item]["temp"].pop(item_3)

        return db, trigger
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())


@APP.route(rule="/")
async def url_home():
    try:
        if request.method == "GET":
            with open(file="www/html/services/index.html",
                      mode="r",
                      encoding="UTF-8") as index_html:
                return render_template_string(source=index_html.read())
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=404)


@APP.route(rule="/css/<path:file>")
async def url_css(file):
    try:
        if request.method == "GET":
            return send_file(path_or_file=f"www/css/{file}")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=404)


@APP.route(rule="/fonts/<path:file>")
async def url_fonts(file):
    try:
        if request.method == "GET":
            return send_file(path_or_file=f"www/fonts/{file}")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=404)


@APP.route(rule="/images/<path:file>")
async def url_images(file):
    try:
        if request.method == "GET":
            return send_file(path_or_file=f"www/images/{file}")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=404)


@APP.route(rule="/js/<path:file>")
async def url_js(file):
    try:
        if request.method == "GET":
            return send_file(path_or_file=f"www/js/{file}")
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=404)


@APP.route(rule="/admin")
async def url_admin():
    try:
        if request.method == "GET":
            if "token" in request.args:
                token = request.args["token"]
            else:
                token = request.cookies.get("sts_token")

            if token in TOKENS:
                with open(file=f"www/html/admins/admin.html",
                          mode="r",
                          encoding="UTF-8") as admin_html:
                    return render_template_string(source=admin_html.read())
            else:
                with open(file=f"www/html/admins/login.html",
                          mode="r",
                          encoding="UTF-8") as login_html:
                    return render_template_string(source=login_html.read())
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=500)


@APP.route(rule="/api/add")
async def url_api_add():
    try:
        if request.method == "GET":
            url, start, end = request.args["id"], request.args["start"], request.args["end"]

            with open(file="db/db.json",
                      mode="r",
                      encoding="UTF-8") as db_json:
                db = loads(s=db_json.read())

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
                                          encoding="UTF-8") as db_json_2:
                                    dump(obj=db,
                                         fp=db_json_2,
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
                                          encoding="UTF-8") as db_json_3:
                                    dump(obj=db,
                                         fp=db_json_3,
                                         indent=4,
                                         ensure_ascii=False)
                            return "1125"

                db[url]["temp"].update({start: {"end": end,
                                                "users": [request.remote_addr]}})
                with open(file="db/db.json",
                          mode="w",
                          encoding="UTF-8") as db_json_4:
                    dump(obj=db,
                         fp=db_json_4,
                         indent=4,
                         ensure_ascii=False)
                return "1125"
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=400)


@APP.route(rule="/api/time")
async def url_api_time():
    try:
        if request.method == "GET":
            return str(datetime.now(tz=timezone(zone="Europe/Moscow")))[:-13]
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=500)


@APP.route(rule="/api/confirmed")
async def url_api_confirmed():
    try:
        if request.method == "GET":
            trigger = False

            with open(file="db/db.json",
                      mode="r",
                      encoding="UTF-8") as db_json:
                db, output = loads(s=db_json.read()), {}

                for item in db:
                    db, trigger = await db_sort(db=db, item=item, trigger=trigger)

                    if len(db[item]["confirmed"]) > 0:
                        temp = []

                        for item_2 in db[item]["confirmed"]:
                            temp.append([int(item_2), int(db[item]["confirmed"][item_2]["end"])])

                        output.update({item: temp})

                if trigger:
                    with open(file="db/db.json",
                              mode="w",
                              encoding="UTF-8") as db_json_2:
                        dump(obj=db,
                             fp=db_json_2,
                             indent=4,
                             ensure_ascii=False)

                return dumps(obj=dict(natsorted(output.items(),
                                                alg=ns.IGNORECASE)),
                             ensure_ascii=False)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=500)


@APP.route(rule="/api/temp")
async def url_api_temp():
    try:
        if request.method == "GET":
            trigger = False

            with open(file="db/db.json",
                      mode="r",
                      encoding="UTF-8") as db_json:
                db, output = loads(s=db_json.read()), {}

                for item in db:
                    db, trigger = await db_sort(db=db, item=item, trigger=trigger)

                    if len(db[item]["temp"]) > 0:
                        temp = []

                        for item_2 in db[item]["temp"]:
                            temp.append([int(item_2), int(db[item]["temp"][item_2]["end"])])

                        output.update({item: temp})

                if trigger:
                    with open(file="db/db.json",
                              mode="w",
                              encoding="UTF-8") as db_json_2:
                        dump(obj=db,
                             fp=db_json_2,
                             indent=4,
                             ensure_ascii=False)

                return dumps(obj=dict(natsorted(output.items(),
                                                alg=ns.IGNORECASE)),
                             ensure_ascii=False)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=500)


@APP.route(rule="/api/admin/auth")
async def url_api_admin_auth():
    try:
        if request.method == "GET":
            try:
                password = sha256(request.args["password"].encode(encoding="UTF-8",
                                                                  errors="ignore")).hexdigest()
                token = sha256((request.args["login"] + password).encode(encoding="UTF-8",
                                                                         errors="ignore")).hexdigest()
            except Exception:
                raise Exception

            if token in TOKENS:
                response = make_response({"user": request.args["login"],
                                          "token": token})
                response.set_cookie("sts_token", token)

                return response
            else:
                raise HTTPException
    except HTTPException:
        return abort(code=401)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=400)


@APP.route(rule="/api/admin/user")
async def url_api_admin_user():
    try:
        if request.method == "GET":
            if "token" in request.args:
                token = request.args["token"]
            else:
                token = request.cookies.get("sts_token")

            if token is None:
                raise HTTPException

            try:
                for admin in ADMINS:
                    if token == sha256((admin + ADMINS[admin]).encode(encoding="UTF-8",
                                                                      errors="ignore")).hexdigest():
                        return {"user": admin,
                                "token": token}
                raise Exception
            except Exception:
                raise Exception
    except HTTPException:
        return abort(code=401)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=404)


@APP.route(rule="/api/admin/move")
async def url_api_admin_move():
    try:
        if request.method == "GET":
            cats = {"confirmed": "temp",
                    "temp": "confirmed"}

            if "token" in request.args:
                token = request.args["token"]
            else:
                token = request.cookies.get("sts_token")

            if token is None or token not in TOKENS:
                raise HTTPException

            try:
                url, cat, start = request.args["id"], request.args["cat"], request.args["start"]

                print(url, cat, start)

                with open(file="db/db.json",
                          mode="r",
                          encoding="UTF-8") as db_json:
                    db = loads(s=db_json.read())

                    db[url][cats[cat]].update({start: db[url][cat][start]})
                    db[url][cats[cat]][start]["users"] = []
                    db[url][cat].pop(start)

                    with open(file="db/db.json",
                              mode="w",
                              encoding="UTF-8") as db_json_2:
                        dump(obj=db,
                             fp=db_json_2,
                             indent=4,
                             ensure_ascii=False)

                    return "1125"
            except Exception:
                raise Exception
    except HTTPException:
        return abort(code=401)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=400)


@APP.route(rule="/api/admin/del")
async def url_api_admin_del():
    try:
        if request.method == "GET":
            if "token" in request.args:
                token = request.args["token"]
            else:
                token = request.cookies.get("sts_token")

            if token is None or token not in TOKENS:
                raise HTTPException

            try:
                url, cat, start = request.args["id"], request.args["cat"], request.args["start"]

                with open(file="db/db.json",
                          mode="r",
                          encoding="UTF-8") as db_json:
                    db = loads(s=db_json.read())

                    db[url][cat].pop(start)

                    with open(file="db/db.json",
                              mode="w",
                              encoding="UTF-8") as db_json_2:
                        dump(obj=db,
                             fp=db_json_2,
                             indent=4,
                             ensure_ascii=False)

                    return "1125"
            except Exception:
                raise Exception
    except HTTPException:
        return abort(code=401)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=400)


@APP.route(rule="/api/admin/restart")
async def url_api_admin_restart():
    try:
        if request.method == "GET":
            if "token" in request.args:
                token = request.args["token"]
            else:
                token = request.cookies.get("sts_token")

            if token is None or token not in TOKENS:
                raise HTTPException

            try:
                await restart()
            except Exception:
                raise Exception
    except HTTPException:
        return abort(code=401)
    except Exception:
        await logs(level="ERROR",
                   message=format_exc())
        return abort(code=500)


@APP.errorhandler(code_or_exception=HTTPException)
async def error_handler(error):
    try:
        print(error)

        with open(file=f"www/html/services/error.html",
                  mode="r",
                  encoding="UTF-8") as error_html:
            return render_template_string(source=error_html.read(),
                                          name=error.name,
                                          code=error.code), error.code
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
