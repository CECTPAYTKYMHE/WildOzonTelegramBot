FROM python:latest

WORKDIR /app
RUN mkdir /app/db
RUN chmod 777 /app/db
RUN mkdir /app/logs
RUN chmod 777 /app/logs

RUN pip install bs4 aiogram requests asyncio aiohttp[speedups]

COPY . .

CMD [ "python", "telegrambot.py" ]

