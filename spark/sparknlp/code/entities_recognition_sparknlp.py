from pyspark.sql import SparkSession
from sparknlp.pretrained import PretrainedPipeline
from pyspark.conf import SparkConf
import pyspark.sql.types as tp
from pyspark.sql.functions import from_json
from pyspark.sql.functions import col, explode

kafkaServer = "kafka:9092"
topic = "entities"
elastic_index = "am_entities"

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

# Set up one Pretrained Pipeline for Entities Recognition
entities_pipeline = PretrainedPipeline.from_disk('/code/models/onto_recognize_entities_bert_small_en_4.4.2_3.2_1685202632553')

# Process each batch of data into entities recognition pipeline 
df_entities = entities_pipeline.transform(df) \
                        .select("timestamp",
                                "text",
                                "id",
                                explode(col("entities"))
                            )

# Select relevant data
df_entities = df_entities.select(
    "timestamp",
    "text",
    "id",
    col("col.result").alias("entities")
)

# Send data to ElasticSearch
df_entities.writeStream \
            .format("es") \
            .option("checkpointLocation", "/tmp/") \
            .option("failOnDataLoss", "false") \
            .start(elastic_index) \
            .awaitTermination()                         


