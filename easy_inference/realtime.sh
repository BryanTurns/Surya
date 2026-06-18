#!/bin/bash
usage="./realtime.sh [ s3 bucket ] [ dynamo db table ] [ aws region ] [ sns_topic_arn ]"

if [ $# -ne 4 ]; then
    echo "$usage"
    echo "Invalid number of arguments. Exiting..."
    exit 1
fi

end_date=$(date -u -d "+30 minutes -4 years" '+%Y-%m-%d %H:00:00')

# This is +8 hours because the script looks back 2 hours so it needs +2 hours for the input data and +6 hours for the output
# Another way to think about this is there are 8 ground truth images 6 of which we compare against our output
start_date=$(date -d "$end_date +8 hours" '+%Y-%m-%d %H:00:00')

start_date_for_s3_uri=$(date -d "$start_date" '+%Y-%m-%dT%H:00:00Z')
s3_bucket=$1
s3_uri="s3://$s3_bucket/results/$start_date_for_s3_uri/"
dynamodb_table=$2
aws_region=$3
sns_topic_arn=$4

source .venv/bin/activate
if [ -z "$*" ]; then
    uv run python /Surya/easy_inference/run_easy_inference.py --output-s3-uri "$s3_uri" --start-date "$start_date" --end-date "$end_date" --config-path "/config/easy_inference_docker_config.yaml" --no-prompt
else
    uv run python /Surya/easy_inference/run_easy_inference.py --start-date "$start_date" --end-date "$end_date" --no-prompt --output-s3-uri "$s3_uri" --dynamodb-table "$dynamodb_table" --aws-region "$aws_region" --sns-topic-arn  "$sns_topic_arn"
fi