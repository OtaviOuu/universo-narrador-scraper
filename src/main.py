from typing import Iterable
from scrapy import Spider, Request
from scrapy.http import Response
from scrapy.crawler import CrawlerProcess
import json
from collections import defaultdict
from colorama import Style
from pystyle import Colors, Colorate


class UniversoNarrado(Spider):
    name = "matematica"

    final_data = defaultdict(dict)
    contador = 0

    custom_settings = {
        "CONCURRENT_REQUESTS": 64,
    }

    def start_requests(self) -> Iterable[Request]:

        headers = {
            "Referer": "https://cursos.universonarrado.com.br/login",
            "Origin": "https://cursos.universonarrado.com.br",
            "Host": "cursos.universonarrado.com.br",
            "Content-Type": "application/json",
        }

        print("\033[H\033[J", end="")
        body = {
            "email": str(input("Email: ")),
            "password": str(input("Senha: ")),
            "hash": "",
            "remember": True,
        }

        yield Request(
            url="https://cursos.universonarrado.com.br/auth",
            method="POST",
            body=json.dumps(body),
            headers=headers,
            errback=self.wrongCredentials,
            callback=self.extractToken,
        )

    def extractToken(self, response: Response):

        token = (
            response.headers.getlist("Set-Cookie")[1]
            .decode("utf-8")
            .split(";")[0]
            .split("=")[-1]
        )

        headers = {
            "x-auth-token": token,
            "Referer": "https://cursos.universonarrado.com.br/lesson/detail/9/7049",
            "Host": "cursos.universonarrado.com.br",
        }

        print("\033[H\033[J", end="")
        self.logger.info(f"Token: {token}")
        yield Request(
            url="https://cursos.universonarrado.com.br/admin/v2/course/9",
            headers=headers,
            callback=self.extractModules,
            cb_kwargs={"token": token},
        )

    def extractModules(self, response: Response, token):
        modules = response.json()["modules"]

        headers = {
            "x-auth-token": token,
            "Referer": "https://cursos.universonarrado.com.br/lesson/detail/9/7049",
            "Host": "cursos.universonarrado.com.br",
        }

        self.logger.info(token)
        for module in modules:
            ID = module["id"]
            yield Request(
                url=f"https://cursos.universonarrado.com.br/admin/v2/module/{ID}",
                headers=headers,
                callback=self.extractLessons,
                cb_kwargs={"videoID": ID, "token": token},
            )

    def extractLessons(self, reponse: Response, videoID, token):
        lessons = reponse.json()["lessons"]

        headers = {
            "x-auth-token": token,
            "Referer": "https://cursos.universonarrado.com.br/lesson/detail/9/7049",
            "Host": "cursos.universonarrado.com.br",
        }

        for lesson in lessons:
            lessonID = lesson["id"]

            yield Request(
                url=f"https://cursos.universonarrado.com.br/admin/v2/lesson/{lessonID}",
                callback=self.extractLessonsURL,
                headers=headers,
            )

    def extractLessonsURL(self, response: Response):
        data = response.json()

        moduleID = str(data["module"]["id"])
        lessonID = str(data["id"])

        module = moduleID + " " + data["module"]["title"]
        title = lessonID + " " + data["title"]
        link = data["library"]["link"]

        self.final_data[module][title] = link

        with open("fisica.json", "w", encoding="utf-8") as f:
            self.contador += 1
            print("\033[H\033[J", end="")
            print(self.contador)
            json.dump(self.final_data, f, ensure_ascii=False, indent=4, sort_keys=True)

    def wrongCredentials(self, _failure):
        print("\033[H\033[J", end="")
        input(Colorate.Horizontal(Colors.rainbow, "Dados errados..."))
        print(Style.RESET_ALL)


process = CrawlerProcess()

process.crawl(UniversoNarrado)
process.start()
