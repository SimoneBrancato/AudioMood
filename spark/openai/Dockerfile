FROM apache/spark:3.4.2

USER 0

RUN pip install --upgrade pip

RUN pip3 install spark-nlp==5.3.3 openai python-dotenv

RUN apt-get update
RUN apt-get install -y openjdk-11-jdk

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

USER spark