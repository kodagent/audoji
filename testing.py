import boto3


def start_transcription_task(audio_file_url, callback_url, group_name):
    ecs = boto3.client("ecs")
    response = ecs.run_task(
        cluster="your-cluster-name",
        launchType="FARGATE",
        taskDefinition="your-task-definition",
        count=1,
        overrides={
            "containerOverrides": [
                {
                    "name": "audoji-container",
                    "environment": [
                        {"name": "CALLBACK_URL", "value": callback_url},
                        {"name": "GROUP_NAME", "value": group_name},
                        {"name": "TEST_AUDIO_FILE_URL", "value": audio_file_url},
                    ],
                }
            ],
        },
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": ["subnet-id"],
                "assignPublicIp": "ENABLED",
            }
        },
    )
    return response
