FROM python:3.8

RUN apt-get update && apt-get install -y ffmpeg && pip install --upgrade pip setuptools

ENV PATH /usr/src/app/bin:$PATH
WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./ ./
CMD [ "python3","-u", "producer.py" ]