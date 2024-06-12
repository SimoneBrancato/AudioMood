from pyspark.sql import SparkSession
from sparknlp.pretrained import PretrainedPipeline
from pyspark.conf import SparkConf
import pyspark.sql.types as tp
from pyspark.sql.functions import from_json, expr, current_timestamp, lit
from pyspark.sql.functions import col, explode, map_values

kafkaServer = "kafka:9092"
topic = "main"
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
                        .set("spark.jars.packages", "com.johnsnowlabs.nlp:spark-nlp_2.12:5.3.3") \
                        .set("spark.sql.streaming.statefulOperator.checkCorrectness.enabled", "false")               

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
    .select(col("data.message").alias("text")) \
    

# Set up one Pretrained Pipeline for Sentiment Analysis and another one for Entities Recognition
sentiment_pipeline = PretrainedPipeline.from_disk('/code/models/analyze_sentiment_en_4.4.2_3.2_1685186425752')
entities_pipeline = PretrainedPipeline.from_disk('/code/models/onto_recognize_entities_bert_small_en_4.4.2_3.2_1685202632553')

# Process each batch of data into sentiment pipeline 
df_sentiment = sentiment_pipeline.transform(df) \
                                 .select(col('text'), explode(col('sentiment')))

# Process each bach of data into entities pipeline and select relevant data
df_entities = entities_pipeline.transform(df) \
                                .select(col('text'), explode(col('entities')))


# Add timestamp and watermark to make possible joining dataframes
df_sentiment_with_watermark = df_sentiment.withColumn(
                                                    "timestamp", 
                                                    lit(current_timestamp()).cast(tp.TimestampType())
                                                ).withWatermark("timestamp", "10 minutes")
df_entities_with_watermark = df_entities.withColumn(
                                                "timestamp",
                                                lit(current_timestamp()).cast(tp.TimestampType())
                                                ).withWatermark("timestamp", "10 minutes")


# Perform the outer join
joined_df = df_sentiment_with_watermark.alias("sentiment").join(
    df_entities_with_watermark.alias("entities"),
    expr('''
        sentiment.text = entities.text
        sentiment.timestamp >= entities.timestamp AND
        sentiment.timestamp <= entities.timestamp + interval 5 minutes
    '''),
    'outer'
)


# Select relevant values
selected_df = joined_df.select(
    #col("sentiment.timestamp").alias("timestamp"),
    col("sentiment.text").alias("text"),
    col("sentiment.col.result").alias("sentiment"),
    map_values(col("sentiment.col.metadata"))[0].alias("confidence"),
    col("entities.col.result").alias("entities")
).distinct()

selected_df.printSchema()


# Send data to ElasticSearch
selected_df.writeStream \
            .format("org.elasticsearch.spark.sql") \
            .option("checkpointLocation", "/tmp/") \
            .option("failOnDataLoss", "false") \
            .start(elastic_index) \
            .awaitTermination()                           


