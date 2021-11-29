# pyamicreator

CLI for ami creation

## Run in docker

```bash
# create ami
docker run \
	-v ~/.aws/app/aws \
	-v ami_config:/app/config \
    -e AWS_SHARED_CREDENTIALS_FILE=/app/aws/credentials  \
    -e AWS_PROFILE=smarties-pipeline  \
    -e AWS_DEFAULT_REGION=eu-west-1  \
    -t emetriq/ami-creator:latest \
    --use_graylog true create_image /app/config/config.json ami_ec2_name "crtt-batch v1.1.1" "This is a test image"
# get latest image id
docker run \
	-v ~/.aws/app/aws \
	-v ami_config:/app/config \
	-e AWS_SHARED_CREDENTIALS_FILE=/app/aws/credentials \
	-e AWS_PROFILE=smarties-pipeline \
	-e AWS_DEFAULT_REGION=eu-west-1 \
	-t emetriq/ami-creator:latest \
	--use_graylog true get_latest_image
```
## config example

```json
{
    "ImageId": "ami-05080fcbe553dc533",
    "MinCount": 1,
    "MaxCount": 1,
    "InstanceType": "c5.large",
    "KeyName": "aws-smarties-emetriq-developer",
    "SubnetId": "subnet-3cb48958",
    "IamInstanceProfile": {
        "Name": "aws-crtt-batch-ec2"
    },
    "SecurityGroupIds": [
        "sg-f682da90"
    ],
    "InstanceInitiatedShutdownBehavior": "terminate",
    "UserData": "#!/bin/bash\naws s3 cp s3://mybucket/libs /home/ec2-user/ --recursive\npip3 install /home/ec2-user/pywaitforit/*any.whl\npip3 install /home/ec2-user/pycrttbatch/*any.whl"
}
```

