FROM python:3.10.11-alpine3.16

WORKDIR /code

COPY ./req.txt /code/req.txt

RUN pip install --no-cache-dir --upgrade -r /code/req.txt

COPY . /code

CMD [ "python", "src/main.py"]
