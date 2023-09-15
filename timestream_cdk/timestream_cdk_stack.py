from constructs import Construct
from aws_cdk import (
    Stack,
    aws_timestream as timestream,
    aws_iot as iot,
    aws_iam as iam,
    aws_logs as logs,
    CfnParameter
)


class TimestreamCdkStack(Stack):
    
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        upload_timstream_database_name = CfnParameter(
            self, "databasename", 
            type="String", description="The name of the Amazon Timestream database where data from sensors will be stored."
        )

        # create timestream database
        timestream_database = timestream.CfnDatabase(
            self, "AirQualityDuplicate",
            database_name=upload_timstream_database_name.value_as_string, 
        )

        upload_timestream_table_name = CfnParameter(
            self, "tablename",
            type="String", description="The name of the Amazon Timestream table"
        )

        upload_timestream_magnetic_store_retention = CfnParameter(
            self, "magneticretention",
            type="String", description="The retention period of magnetic storage in days"
        )

        upload_timestream_memory_store_retention = CfnParameter(
            self, "memoryretention",
            type="String", description="The retention period of memory storage in hours"
        )

        # create timesream table with previously created timestream database
        timestream_table = timestream.CfnTable(
            self, "airQualityDuplicate",
            table_name=upload_timestream_table_name.value_as_string,
            database_name=timestream_database.database_name,
            retention_properties=timestream.CfnTable.RetentionPropertiesProperty(
                magnetic_store_retention_period_in_days=upload_timestream_magnetic_store_retention.value_as_string,
                memory_store_retention_period_in_hours=upload_timestream_memory_store_retention.value_as_string,
            )
        )

        # add dependency between timestream table and db
        timestream_table.add_dependency(timestream_database)

        # create iam role for the new timestream database
        iot_timestream_role = iam.Role(
            self, "IoTTimestreamRole", 
            assumed_by=iam.ServicePrincipal('iot.amazonaws.com'),
        )

        timestream_policy = iam.ManagedPolicy(
            self, 
            "TimestreamPolicy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["timestream:WriteRecords"],
                    resources=[f"arn:aws:timestream:{self.region}:{self.account}:database/{timestream_database.database_name}/table/{timestream_table.table_name}"],
                ),
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["timestream:DescribeEndpoints"],
                    resources=["*"],
                )
            ],
        )

        timestream_policy.attach_to_role(iot_timestream_role)

        cloud_watch_log_policy = iam.ManagedPolicy(
            self,
            "CloudWatchPolicy",
            statements=[
                iam.PolicyStatement(
                    actions=[
                        "logs:CreateLogStream", 
                        "logs:CreateLogGroup",
                        "logs:PutLogEvents",
                        "logs:PutMetricFilter",
                        "logs:PutRetentionPolicy"
                    ],
                    resources=[f"arn:aws:logs:*:{self.account}:log-group:*:log-stream:*"],
                )
            ],
        )
        cloud_watch_log_policy.attach_to_role(iot_timestream_role)

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

        upload_iot_topic_rule_name = CfnParameter(
            self, "topicrule_name",
            type="String", description="The name of the topic rule that sends data to Amazon Timestream database"
        )

        upload_iot_topic_rule_sql_statement = CfnParameter(
            self, "sql",
            type="String", description="The sql statement used for IoT core topic rule."
        )
        # create IoT core topic rule for the new timestream db
        iot.CfnTopicRule(
            self, 
            "IoT2TimestreamReplicate",
            rule_name=upload_iot_topic_rule_name.value_as_string,
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                actions=[
                    iot.CfnTopicRule.ActionProperty(
                        timestream=timestream_action,
                    )],
                # "SELECT decoded.payload.data.* FROM 'air_quality'"
                sql=upload_iot_topic_rule_sql_statement.value_as_string,
            )
        )

