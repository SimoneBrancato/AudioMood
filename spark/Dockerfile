FROM apache/spark:3.4.2

#RUN apt-get update
#RUN apt-get install -y oracle-java8-installer 

USER 0

RUN pip install --upgrade pip

RUN pip install tensorflow==2.13.1 torch==2.1.0
RUN pip3 install pyspark spark-nlp==5.3.3 numpy

RUN apt-get update
RUN apt-get install -y openjdk-11-jdk

ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64

USER spark
