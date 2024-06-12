from pyspark.sql import SparkSession
from sparknlp.pretrained import PretrainedPipeline
from pyspark.conf import SparkConf
import pyspark.sql.types as tp
from pyspark.sql.functions import from_json
from pyspark.sql.functions import col, explode, map_values

kafkaServer = "kafka:9092"
topic = "sentiment"
elastic_index = "am_sentiment"

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
                        .set("spark.jars.packages", "com.johnsnowlabs.nlp:spark-nlp_2.12:5.3.3")              

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

# Parse and simplify dataframe structure
df = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json("value", kafka_schema).alias("data")) \
    .select(
        col("data.@timestamp").alias("timestamp"),
        col("data.message").alias("text")
    )

# Set up one Pretrained Pipeline for Sentiment Analysis
sentiment_pipeline = PretrainedPipeline.from_disk('/code/models/analyze_sentiment_en_4.4.2_3.2_1685186425752')

# Process each batch of data into sentiment analysis pipeline 
df_sentiment_exploded = sentiment_pipeline.transform(df) \
                                            .select(
                                                    col("timestamp"),
                                                    col("text"),
                                                    explode(col("sentiment"))
                                                )

# Select relevant data
df_sentiment = df_sentiment_exploded.select(
                                        col("timestamp"),
                                        col("text"),
                                        col("col.result").alias("sentiment"),
                                        map_values(col("col.metadata"))[0].alias("confidence")
                                    )

# Send data to ElasticSearch
df_sentiment.writeStream \
            .format("es") \
            .option("checkpointLocation", "/tmp/") \
            .option("failOnDataLoss", "false") \
            .start(elastic_index) \
            .awaitTermination()                           


