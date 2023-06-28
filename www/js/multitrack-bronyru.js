class MultitrackJSLoader {
    constructor(data) {
        let xhr = new XMLHttpRequest();
        
        xhr.open("GET", "https://bronyru.info/api/v1/episodes/name/" + encodeURIComponent(data.data.episode_name), true);

        xhr.addEventListener("load", () => {
            if (xhr.status === 200) {
                let episodeData = JSON.parse(xhr.responseText);

                let videos = episodeData.videos.sort(function (a, b) {
                    a = parseInt(a, 10);
                    b = parseInt(b, 10);
                    if (a > b) return -1;
                    if (a < b) return 1;
                    return 0;
                }).map(function (video) {
                    if (parseInt(video, 10) > 1080) {
                        return {
                            name: video + "p",
                            path: episodeData.path + video + ".webm"
                        };
                    } else {
                        return {
                            name: video + "p",
                            path: episodeData.path + video + ".mp4"
                        };
                    }
                });

                let audios = episodeData.dubs.map(function (dub) {
                    return {
                        name: "[" + dub.lang.toUpperCase() + "] " + dub.name,
                        code: dub.code,
                        path: episodeData.path + dub.code + ".mp4"
                    };
                });

                let subtitles = episodeData["subs"].map(function (sub) {
                    return {
                        name: "[" + sub.lang.toUpperCase() + "] " + sub.name,
                        code: sub.code,
                        path: episodeData.path + sub.code + ".ass"
                    };
                });

                const preferredQuality = episodeData.videos.find((video) => parseInt(video, 10) <= 1080);
                const preferredVideoName = preferredQuality ? preferredQuality + "p" : null;

                return new MultitrackJS(data.el, {
                    videos: videos,
                    audios: audios,
                    subtitles: subtitles,
                    placeholder: episodeData.path + "index.jpg",
                    preview: episodeData.path + "preview.webp",
                    preferredVideoName: preferredVideoName,
                    title: episodeData.title,
                    start: data.start,
                    end: data.end
                });
            } else {
                alert("При загрузке базы данных произошла ошибка:\n\n" + xhr.status + ": " + xhr.statusText);
            }
        });

        xhr.addEventListener("error", () => {
            alert("При загрузке базы данных произошла ошибка:\n\n" + xhr.status + ": " + xhr.statusText);
        });

        xhr.send();
    }
}
