# Docker for Surya

## easy_inference

As a heads up all changes to easy_inference/run_easy_inference.py were vibe coded and the entire easy_inference/visualize_prediction.py was vibe coded.
I have lightly tested these scripts, but haven't properly read through the code. Beware. 

### Performance

The first build will take up to an hour the first time you build it as there are quite a few dependencies that result in lots
of file operations that docker has to unpack. Subsequent builds, even of other images or with code changes just to easy_inference/, should build in under a minute.

Running the container using colima on the Mac showed memory usage above 12 GiB which I set as the VM memory. 

Running on m6a.2xlarge amazon ec2 instance takes 15-20 minutes. The instance has 8 CPUs running at 3.6 Ghz with 32GB of RAM.

### Local Container

#### Build the Local/Non-AWS Version of the Image

Note that this can take up to an hour the first time you build it as there are quite a few dependencies that result in lots
of file operations that docker has to unpack. Subsequent runs with code changes just to easy_inference/ should build in under a minute.

```bash
docker build -t easy_inference_local --target easy_inference .
```

#### Run the Local/Non-AWS Version of the Image

The results will be stored in your local ./container_output directory. 

Note that subsequent runs are likely to overwrite data in this directory.

```bash
docker run -d -v ./container_output:/Surya/easy_inference/outputs_24h easy_inference_local:latest
```

### AWS Container

#### Build the AWS Version of the Image

```bash
docker build -t surya/easy_inference . --target easy_inference_realtime
```

#### Run the AWS Version of the Image

It is recommended you run it on an ec2 that has an IAM role with the necessary permissions. 
The easiest way to do this is to deploy the [surya-cdk](https://github.com/BryanTurns/surya-cdk)

Note that this version of the image does not persist it's data as it expects it all to end up in S3. 

```bash
inference_alerts_topic_arn=...
region=...
surya_status_table_name=...
output_bucket_name=...
surya_easy_inference_image=...
docker run --rm ${surya_easy_inference_image} ${output_bucket_name} ${surya_status_table_name} ${region} ${inference_alerts_topic_arn}
```

### Potential optimizations

- Move the copy of surya/ outside of the dependency image that way the dependency image doesn't need to be re-exported on surya/ code changes
