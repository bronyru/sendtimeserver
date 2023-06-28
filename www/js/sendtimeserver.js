function update_time() {
    let time = document.getElementById("time");
    let xhr = new XMLHttpRequest();

    xhr.open("GET", "/api/time", true);

    xhr.addEventListener("load", () => {
        if (xhr.status === 200) {
            time.innerText = xhr.responseText;
        } else {
            time.innerText = "Во время обработки запроса возникла ошибка!";
        }
    });

    xhr.addEventListener("error", () => {
        time.innerText = "Во время обработки запроса возникла ошибка!";
    });

    xhr.send();

    setTimeout(() => {
        update_time();
    }, 1000);
}

function admin_login() {
    let alert = document.getElementById("alert");
    let xhr = new XMLHttpRequest();

    xhr.open("GET", ("/api/admin/auth?login=" + encodeURIComponent(document.getElementById("login").value) + "&password=" + encodeURIComponent(document.getElementById("password").value)), true);

    xhr.addEventListener("load", () => {
        if (xhr.status === 200) {
            location.href = "/admin";
        } else if (xhr.status === 401) {
            alert.innerText = "Значение \"Логин\" или \"Пароль\" неверные!";
        } else {
            alert.innerText = "Во время обработки запроса возникла ошибка!";
        }
    });

    xhr.addEventListener("error", () => {
        alert.innerText = "Во время обработки запроса возникла ошибка!";
    });

    xhr.send();
}

function admin_load() {
    let xhr = new XMLHttpRequest();

    xhr.open("GET", ("/api/admin/user"), true);

    xhr.addEventListener("load", () => {
        if (xhr.status === 200) {
            let data = JSON.parse(xhr.responseText);

            document.getElementById("user").innerText += (" " + data["user"]);

            document.getElementById("token").addEventListener("click", () => {
                if (isSecureContext && navigator.clipboard) {
                    navigator.clipboard.writeText(data["token"]).then(r => r);
                } else {
                    let input = document.createElement("input");
                    document.getElementById("token").appendChild(input);
                    input.value = data["token"];
                    input.select();
                    document.execCommand("copy");
                    input.remove();
                }
            });

            document.getElementById("restart").addEventListener("click", () => {
                if (confirm("Вы действительно хотите перезагрузить сервер?\n\nСервер перезагрузится без какого либо ответа.\n\nПосле подтверждения вам нужно будет вручную перезагрузить страницу через несколько секунд.\n\nВнимание: Если в коде сервера имеются ошибки, сервер может не запустится после перезагрузки!")) {
                    let xhr = new XMLHttpRequest();

                    xhr.open("GET", ("/api/admin/restart"), true);
                    xhr.send();

                    location.reload();
                }
            });
        }
    });

    xhr.send();

    document.getElementById("logout").addEventListener("click", () => {
        document.cookie = "sts_token=null; max-age=0";
        location.reload();
    });

    admin_generate("confirmed");
    admin_generate("temp");
}

function admin_generate(value, trigger = true) {
    let title = {
        "confirmed": "Подтвержденные",
        "temp": "Временные"
    }

    let block = document.getElementById(value);
    block.innerHTML = "";

    let h3 = document.createElement("h3");
    h3.innerText = title[value] + ":";
    h3.addEventListener("click", () => {
        admin_generate(value, !trigger);
    });
    block.appendChild(h3);

    if (trigger) {
        let xhr = new XMLHttpRequest();

        xhr.open("GET", ("/api/" + value), true);

        xhr.addEventListener("load", () => {
            if (xhr.status === 200) {
                let data = JSON.parse(xhr.responseText);

                for (let item in data) {
                    block.appendChild(document.createElement("hr"));

                    let p = document.createElement("p");
                    p.classList.add("names");
                    p.innerText = item.replace("/стафф/видео/", "").replace(new RegExp("/$"), "").replace(new RegExp("^/"), "");
                    block.appendChild(p);

                    let root = document.createElement("div");
                    root.classList.add("times");
                    block.appendChild(root);

                    for (let time in data[item]) {
                        let div = document.createElement("div");
                        div.classList.add("times_item");
                        root.appendChild(div);

                        let start = document.createElement("div");
                        start.innerText = "Начало: " + secondsToTime(data[item][time][0]);
                        div.appendChild(start);

                        let end = document.createElement("div");
                        end.innerText = "Конец: " + secondsToTime(data[item][time][1]);
                        div.appendChild(end);

                        let buttons_green = document.createElement("input");
                        buttons_green.type = "button";
                        buttons_green.value = "Посмотреть";
                        buttons_green.classList.add("buttons", "buttons_green");
                        buttons_green.addEventListener("click", () => {
                            let player = document.createElement("div");
                            player.id = "player";

                            let load = document.createElement("h1");
                            load.innerText = "Загрузка...";
                            load.style.textAlign = "center";
                            player.appendChild(load);

                            let body = document.getElementsByTagName("body")[0];
                            body.appendChild(player);
                            setTimeout(() => {
                                body.addEventListener("click", (event) => {
                                    show_player(event, player, body);
                                });
                            }, 100);

                            let xhr = new XMLHttpRequest();

                            xhr.open("GET", ("https://bronyru.info" + item), true);

                            xhr.addEventListener("load", () => {
                                if (xhr.status === 200) {
                                    load.remove();

                                    let vm = new MultitrackJSLoader({
                                        el: "#player",
                                        start: data[item][time][0],
                                        end: data[item][time][1],
                                        data: {
                                            episode_name: xhr.responseText.match(new RegExp("episode_name: \"(.*)\"$", "m"))[1]
                                        }
                                    });
                                } else {
                                    player.remove();
                                }
                            });

                            xhr.addEventListener("error", () => {
                                player.remove();
                            });

                            xhr.send();
                        });
                        div.appendChild(buttons_green);

                        let buttons_orange = document.createElement("input");
                        buttons_orange.type = "button";
                        buttons_orange.value = "Переместить";
                        buttons_orange.classList.add("buttons", "buttons_orange");
                        buttons_orange.addEventListener("click", () => {
                            let xhr = new XMLHttpRequest();

                            xhr.open("GET", ("/api/admin/move?id=" + item + "&cat=" + value + "&start=" + data[item][time][0]), true);

                            xhr.addEventListener("load", () => {
                                if (xhr.status === 200) {
                                    admin_generate("confirmed");
                                    admin_generate("temp");
                                } else {
                                    alert("Во время обработки запроса возникла ошибка!");
                                }
                            });

                            xhr.addEventListener("error", () => {
                                alert("Во время обработки запроса возникла ошибка!");
                            });

                            xhr.send();
                        });
                        div.appendChild(buttons_orange);

                        let buttons_red = document.createElement("input");
                        buttons_red.type = "button";
                        buttons_red.value = "Удалить";
                        buttons_red.classList.add("buttons", "buttons_red");
                        buttons_red.addEventListener("click", () => {
                            if (confirm("Вы действительно хотите удалить этот сегмент?\n\nКатегория: " + title[value] + "\nID: " + item + "\nНачало: " + secondsToTime(data[item][time][0]) + "\nКонец: " + secondsToTime(data[item][time][1]))) {
                                let xhr = new XMLHttpRequest();

                                xhr.open("GET", ("/api/admin/del?id=" + item + "&cat=" + value + "&start=" + data[item][time][0]), true);

                                xhr.addEventListener("load", () => {
                                    if (xhr.status === 200) {
                                        admin_generate(value);
                                    } else {
                                        alert("Во время обработки запроса возникла ошибка!");
                                    }
                                });

                                xhr.addEventListener("error", () => {
                                    alert("Во время обработки запроса возникла ошибка!");
                                });

                                xhr.send();
                            }
                        });
                        div.appendChild(buttons_red);
                    }
                }
            } else {
                block.innerText = "Во время обработки запроса возникла ошибка!";
            }
        });

        xhr.addEventListener("error", () => {
            block.innerText = "Во время обработки запроса возникла ошибка!";
        });

        xhr.send();
    }
}

function secondsToTime(sec) {
    sec = Math.floor(sec);
    let seconds = sec % 60;
    let minutes = Math.floor(sec / 60) % 60;
    let hours = Math.floor(sec / 3600);

    let Sminutes = minutes.toString().padStart(2, "0");
    let Sseconds = seconds.toString().padStart(2, "0");

    return (hours > 0) ? (hours + ":" + Sminutes + ":" + Sseconds) : (Sminutes + ":" + Sseconds);
}

function show_player(event, player, body) {
    if (!event.path.includes(player)) {
        player.remove();
        body.removeEventListener("click", (event) => {
            show_player(event, player, body);
        });
    }
}
