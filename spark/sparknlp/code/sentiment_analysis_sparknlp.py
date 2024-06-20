

from sparknlp.base import DocumentAssembler, Pipeline
from sparknlp.annotator import BertForSequenceClassification, Tokenizer
from pyspark.sql import SparkSession
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
    tp.StructField('id', tp.IntegerType(), True),
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
        col("data.id").alias("id"),
        col("data.message").alias("text")
    )

# Set up Bert Pipeline for Sentiment Analysis
document_assembler = DocumentAssembler()\
    .setInputCol("text")\
    .setOutputCol("document")

tokenizer = Tokenizer()\
    .setInputCols("document")\
    .setOutputCol("token")  
    
sequenceClassifier = BertForSequenceClassification.load("/code/models/bert_base_multilingual_uncased_sentiment_3labels_xx_5.1.4_3.4_1698813884609")\
            .setInputCols(["document","token"])\
            .setOutputCol("class")

pipeline = Pipeline().setStages([document_assembler, tokenizer, sequenceClassifier])

# Process each batch of data into sentiment analysis pipeline
result = pipeline.fit(df).transform(df)

# Select relevant data
result = result.select("timestamp", "id", "text", "class.result")

# Send data to ElasticSearch
result.writeStream \
            .format("es") \
            .option("checkpointLocation", "/tmp/") \
            .option("failOnDataLoss", "false") \
            .start(elastic_index) \
            .awaitTermination()                        


