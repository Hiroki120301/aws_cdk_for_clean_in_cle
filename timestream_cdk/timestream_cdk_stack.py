from constructs import Construct
from aws_cdk import (
    Stack,
    aws_timestream as timestream,
    aws_iot as iot,
    aws_iam as iam,
    aws_logs as logs,
)

class TimestreamCdkStack(Stack):
    
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # create timestream database
        timestream_database = timestream.CfnDatabase(
            self, "AirQualityDuplicate",
            database_name="AirQualityDuplicate",
        )

        # create timesream table with previously created timestream database
        timestream_table = timestream.CfnTable(
            self, "airQualityDuplicate",
            table_name="airQualityDuplicate",
            database_name=timestream_database.database_name,
        )

        # add dependency between timestream table and db
        timestream_table.add_dependency(timestream_database)

        # create iam role for the new timestream database
        iot_timestream_role = iam.Role(
            self, "IoTTimestreamRole",
            assumed_by=iam.ServicePrincipal('iot.amazonaws.com'),
        )

        timestream_policy = iam.PolicyStatement(
            actions=[
                "timestream:WriteRecords",
                "timestream:ListMeasures",
            ],
            resources=[f"arn:aws:timestream:{self.region}:{self.account}:database/{timestream_database.database_name}/table/{timestream_table.table_name}"]
        )

        iot_timestream_role.add_to_policy(timestream_policy)

        # create cloud watch log for the new timestream 
        log_group = logs.LogGroup(
            self, "AirQualityLogGroup",
            retention=logs.RetentionDays.ONE_WEEK,
        )
        cloud_watch_log_policy = iam.PolicyStatement(
            actions=[
                "logs:CreateLogStream", 
                "logs:CreateLogGroup",
                "logs:PutLogEvents",
                "logs:PutMetricFilter",
                "logs:PutRetentionPolicy"
            ],
            resources=[
                log_group.log_group_arn,
            ]
        )
        iot_timestream_role.add_to_policy(cloud_watch_log_policy)

        timestream_action = iot.CfnTopicRule.TimestreamActionProperty(
            database_name=timestream_database.database_name,
            table_name=timestream_table.table_name,
            dimensions=[
                iot.CfnTopicRule.TimestreamDimensionProperty(
                    name="DeviceEUI",
                    value="${dev_eui}",
                )
            ],
            role_arn=iot_timestream_role.role_arn,
            timestamp=iot.CfnTopicRule.TimestreamTimestampProperty(
                unit="MILLISECONDS",
                value="${reported_at}",
            )
        )

        # create IoT core topic rule for the new timestream db
        iot.CfnTopicRule(
            self, 
            "IoT2TimestreamReplicate",
            rule_name="IoT2TimestreamReplicate",
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                actions=[
                    iot.CfnTopicRule.ActionProperty(
                        timestream=timestream_action,
                    )],
                sql="SELECT decoded.payload.data.* FROM 'air_quality'",
            )
        )