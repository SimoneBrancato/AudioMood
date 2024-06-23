<img src="images\AudioMoodLogo.jpg" width="400" height="140"/>

## What is AudioMood
AudioMood offers advanced analysis features for YouTube videos, including sentiment analysis (positive, neutral, negative), keyword/tag recognition, and text summarization.
Here’s what AudioMood can provide:
- **Sentiment Distribution:** A graph with the sentiment distribution percentage.
- **Sentiment Timeline:** Sentiment analysis for each phrase (approximately every 15 words) throughout the video.
- **Top 10 Tags:** a list of the top 10 tags identified in the video, classified by count.
- **Top 5 Tags Introduction Timing:** The first appearance of the top 5 tags, showing when each theme is introduced in the video.
- **Top 5 Tags Median Position:** The median position of the top 5 tags, helping to estimate how long each topic is discussed in the video.
- **Extract:** A little summarization of the main topics discussed in the video.

## Prerequisites
- **Docker/Docker Compose:** Ensure you have a fully functional [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installation on your local computer.
- **OpenAI API Key:** To leverage the power of GPT-3.5-Turbo, [obtain an API key from OpenAI](https://platform.openai.com/api-keys).
- **Environment Variable:** Create a ".env" file in the main directory and add the line `OPENAI_API_KEY=your-api-key`.

## Let's get started!
You first need to clone the repository on your local computer. Then, navigate to the application's main directory and execute the following command:
```bash
docker-compose -f docker-compose.yml up --build
```
Then go to [localhost:5000]()

## Useful links
- **User Interface:** [localhost:5000]()
- **KafkaUI:** [localhost:8080]()
- **Kibana:** [localhost:5601]()

## Project Architecture
The user needs to input a YouTube URL of the video they want to analyze and select the OpenAI Whisper model size for audio-to-text transcription. A **producer** service in Python will download the video's audio in mp3 format, send it to **OpenAI Whisper** for full transcription, and forward the entire text to **Logstash**, which provides data ingestion. The producer will split the text into chunks (about 15 words each) and send each chunk to Logstash for sentiment analysis and keyword recognition. Logstash will distribute each message to a **Kafka** broker across three different topics: summary, entities, and sentiment. Kafka provides data streaming in **KRaft** mode.

Three different services in **Spark** will read data from Kafka topics:
- **Spark-Sentiment** will read from the Sentiment Topic to perform sentiment analysis on each text chunk using **SparkNLP**, evaluating it as Positive, Neutral or Negative.
- **Spark-Entities** will read from the Entities Topic to perform entity recognition on each text chunk using **SparkNLP**, extracting the main keywords.
- **Spark-Summary** will read from the Summary Topic to retrieve the full text and send a query to **GPT-3.5-Turbo** for text summarization.

Each Spark service will send data to a different **Elasticsearch** index for data indexing. In the end, **Kibana** will then provide data visualization for each feature, and the user will be able to see the embedded Kibana dashboard on their User Interface.

<img src="images\project-architecture.jpg" width="900" height="550" />

## Contacts
- **E-Mail:** simonebrancato18@gmail.com | simonealfio.brancato@gmail.com
- **LinkedIn:** [Simone Brancato](https://www.linkedin.com/in/simonebrancato18/)
- **GitHub:** [Simone Brancato](https://github.com/SimoneBrancato)

## Final remarks
This data engineering project is the final exam for the Technologies for Advanced Programming course, taught by Professor Salvatore Nicotra at the University of Catania, academic year 2023/24.

