from constructs import Construct
from aws_cdk import (
    Stack,
    aws_timestream as timestream,
    aws_iot as iot,
)

class TimestreamCdkStack(Stack):
    
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        timestream_database = timestream.CfnDatabase(
            self, "AirQualityReplicate",
            database_name="AirQualityReplicate",
        )

        timestream_table = timestream.CfnTable(
            self, "airQuality",
            table_name="airQualityReplicate",
            database_name=timestream_database.database_name,
        )
        timestream_table.add_dependency(timestream_database)

        timestream_action = iot.CfnTopicRule.TimestreamActionProperty(
            database_name=timestream_database.database_name,
            table_name=timestream_table.table_name,
            dimensions=[
                iot.CfnTopicRule.TimestreamDimensionProperty(
                    name="DeviceEUI",
                    value="${dev_eui}",
                )
            ],
            role_arn="arn:aws:iam::691324371036:role/service-role/IoT2Timestream",
            timestamp=iot.CfnTopicRule.TimestreamTimestampProperty(
                unit="MILLISECONDS",
                value="${reported_at}",
            )
        )

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