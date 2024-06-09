from pyspark.sql import SparkSession
from sparknlp.pretrained import PretrainedPipeline
from pyspark.conf import SparkConf
import pyspark.sql.types as tp
from pyspark.sql.functions import from_json
from pyspark.sql.functions import col, explode

kafkaServer="kafka:9092"
topic = "main"
elastic_index="audiomood_log"

# Define Spark connection to ElasticSearch
print("Defining SparkConf")
sparkConf = SparkConf().set("es.nodes", "elasticsearch") \
                        .set("es.port", "9200") \
                        .set("spark.driver.memory","64G") \
                        .set("spark.driver.maxResultSize", "0") \
                        .set("spark.kryoserializer.buffer.max", "2000M") \
                        .set("spark.jars.packages", "com.johnsnowlabs.nlp:spark-nlp_2.12:5.3.3")

# Define kafka messages structure
kafka_schema = tp.StructType([
    tp.StructField('@timestamp', tp.StringType(), True),
    tp.StructField('message', tp.StringType(), True)
])

# Build Spark Session in SparkNLP mode
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

# Select relevant data from dataframe
df = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json("value", kafka_schema).alias("data")) \
    .select("data.@timestamp",col("data.message").alias("text"))

# Set up Pretrained Pipeline
pipeline = PretrainedPipeline('analyze_sentiment', lang='en')

# Function to process each batch of data
df1 = pipeline.transform(df)


df1 = df1.select(
        col("@timestamp"),
        col("text"),
        explode(col("sentiment")).alias("sentiment_exploded")
    ).select(
        col("@timestamp"),
        col("text"),
        col("sentiment_exploded.result").alias("sentiment"),
        col("sentiment_exploded.metadata")["confidence"].alias("confidence")
    )

df1.writeStream \
   .option("checkpointLocation", "/tmp/") \
   .option("failOnDataLoss", "false") \
   .format("es") \
   .start(elastic_index) \
   .awaitTermination()
