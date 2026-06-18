# Easy Inference

Use this folder for the simplest Surya flow:
1. choose date window,
2. download only required hourly files,
3. run rollout inference,
4. save one `prediction.nc`,
5. save one default visualization PNG in the output directory.

## Quick start

```bash
source .venv/bin/activate
bash easy_inference/run_easy_inference.sh
```

Non-interactive defaults:

```bash
bash easy_inference/run_easy_inference.sh --no-prompt
```

Skip the visualization PNG:

```bash
bash easy_inference/run_easy_inference.sh --skip-visualization
```

Sync outputs to S3 after inference:

```bash
OUTPUT_S3_URI=s3://my-bucket/prefix bash easy_inference/run_easy_inference.sh
```

Or pass the URI explicitly:

```bash
bash easy_inference/run_easy_inference.sh --output-s3-uri s3://my-bucket/prefix
```

Track run completion in DynamoDB:

```bash
DYNAMODB_TABLE=surya-runs bash easy_inference/run_easy_inference.sh
```

Or pass the table explicitly:

```bash
bash easy_inference/run_easy_inference.sh --dynamodb-table surya-runs
```

The table must already exist with `start_datetime` as its partition key. The
script writes `completed` as `no`, then `yes` or `error`.

If AWS region is not already configured in the environment, pass it explicitly:

```bash
bash easy_inference/run_easy_inference.sh --dynamodb-table surya-runs --aws-region us-east-1
```

Send SNS email alerts for handled errors:

```bash
SNS_TOPIC_ARN=arn:aws:sns:us-east-1:123456789012:surya-errors bash easy_inference/run_easy_inference.sh
```

Or pass the topic explicitly:

```bash
bash easy_inference/run_easy_inference.sh --sns-topic-arn arn:aws:sns:us-east-1:123456789012:surya-errors
```

SNS alerts use the same `--aws-region` setting as DynamoDB and S3.

Stop the current EC2 instance after a successful run:

```bash
bash easy_inference/run_easy_inference.sh --stop-instance-on-complete
```

This requires the instance profile to allow `ec2:StopInstances`. When running inside
Docker on EC2, the instance metadata hop limit must allow container access to IMDS.

## Config

Edit `easy_inference/config_easy.yaml`.

- Normal users: edit only the top `user:` section.
- Advanced users: optional changes in `advanced:`.

Default and override behavior:

```bash
# Uses easy_inference/config_easy.yaml by default.
python easy_inference/run_easy_inference.py

# Optional: use a different YAML file.
python easy_inference/run_easy_inference.py --config-path /path/to/custom_easy.yaml
```

### Debug mode

Set in `advanced:`:
- `debug_mode: true`
- optional `debug_log_path: "path/to/inference_debug.txt"` (default is `<user.output_dir>/inference_debug.txt`)

When enabled, the text log contains stage timings and per-step diagnostics with line number + UTC timestamp:
- input file read / transform timing
- GT file read timing
- per-step forward / CPU-copy / inverse-transform / write timing
- per-step memory stats (`CUDA` peak/allocated/reserved when available)

## Metrics Notebook

Use `easy_inference/compare_prediction_groundtruth.ipynb` to compare `prediction.nc` vs GT and compute:
- overall metrics (`MSE`, `RMSE`, `MAE`, `bias`, `max_abs_error`)
- per-channel metrics
- per-step metrics
- visual prediction vs ground-truth plots
