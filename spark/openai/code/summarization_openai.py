from pyspark.sql import SparkSession
from pyspark.conf import SparkConf
import pyspark.sql.types as tp
from pyspark.sql.functions import from_json, col, udf
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

load_dotenv('.env')
OPENAI_API_KEY: str = os.getenv('OPENAI_API_KEY')

kafkaServer = "kafka:9092"
topic = "summary"
elastic_index = "am_summary"

# Define kafka messages structure
kafka_schema = tp.StructType([
    tp.StructField('@timestamp', tp.StringType(), True),
    tp.StructField('message', tp.StringType(), True)
])

# Define Spark connection to ElasticSearch
print("Defining SparkConf")
sparkConf = SparkConf().set("es.nodes", "elasticsearch") \
                        .set("es.port", "9200") \
                        .set("spark.driver.memory","64G") \
                        .set("spark.driver.maxResultSize", "0") \
                        .set("spark.kryoserializer.buffer.max", "2000M") \
                        .set("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
                        
# Build Spark Session
print("Starting Spark Session")
spark = SparkSession.builder \
    .appName("Spark NLP") \
    .master("local[16]") \
    .config(conf=sparkConf) \
    .getOrCreate()

# To reduce verbose output
spark.sparkContext.setLogLevel("ERROR") 

# Read the stream from Kafka
print("Reading stream from kafka...")
df = spark \
    .readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", kafkaServer) \
    .option("subscribe", topic) \
    .load()

# Parse and simplify dataframe structure
df = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json("value", kafka_schema).alias("data")) \
    .select(
        col("data.@timestamp").alias("timestamp"),
        col("data.message").alias("text")
    )  

# Define function to get summary from OpenAI GPT-3.5-Turbo
def get_summary(text):

    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY environment variable not found.")
    else:
        print(f"API_KEY loaded successfully: {OPENAI_API_KEY[:4]}...") 

    # Get connection to OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Send request to GPT-3.5-Turbo for text summarization
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You must summarize the following text, your response must be long between 1500 and 1700 characters. You are obliged to answer only with the summary, without any additional text. You are obliged to talk about it as a video, given that the following text is an transcription of an audio of a video."},
                {"role": "user", "content": text}
            ]
        )
    
    # Select message content
    response_dict = json.loads(response.model_dump_json())
    summary = response_dict["choices"][0]["message"]["content"]

    return summary

# Transform Dataframe adding Summary Column
get_summary_udf = udf(get_summary, tp.StringType())
df = df.withColumn("summary", get_summary_udf(col("text"))).select("timestamp", "summary")

# Send data to ElasticSearch
df.writeStream \
        .format("es") \
        .option("checkpointLocation", "/tmp/") \
        .option("failOnDataLoss", "false") \
        .start(elastic_index) \
        .awaitTermination()                


