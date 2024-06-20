echo "Waiting for Kibana to be ready..."

until $(curl --output /dev/null --silent --head --fail http://kibana:5601); do
  sleep 5
done

sleep 20 

echo "Importing dashboard in Kibana..."

# Import the dashboard
curl -X POST "http://kibana:5601/api/saved_objects/_import?overwrite=true" -H "kbn-xsrf: true" --form file=@/export.ndjson

sleep 20

echo "Setting up summary index..."

curl -X PUT "elasticsearch:9200/am_summary" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "properties": {
      "timestamp": {
        "type": "date"
      },
      "summary": {
        "type": "text",
        "fields": {
          "keyword": {
            "type": "keyword",
            "ignore_above": 5000
          }
        }
      }
    }
  }
}'

