import aws_cdk as core
import aws_cdk.assertions as assertions

from timestream_cdk.timestream_cdk_stack import TimestreamCdkStack


def test_timestream_database_and_table_created():
    app = core.App()
    stack = TimestreamCdkStack(app, "timestream-cdk")
    template = assertions.Template.from_stack(stack)

    template.has_resource(
        "AWS::Timestream::Database", 
        {
            "Properties": {
                "DatabaseName": "AirQualityDuplicate",
            }
        }
    )

    template.has_resource(
        "AWS::Timestream::Table",
        {
            "Properties": {
                "DatabaseName": "AirQualityDuplicate",
                "TableName": "airQualityDuplicate"
            },
            "DependsOn": ["AirQualityDuplicate"]
        }
    )


def test_iam_role_and_policy_created():
    app = core.App()
    stack = TimestreamCdkStack(app, "timestream-cdk")
    template = assertions.Template.from_stack(stack)
    template.has_resource(
        "AWS::IAM::Role",
        {
            "Properties": {
                "AssumeRolePolicyDocument": {
                    "Statement": [
                        {
                            "Action": "sts:AssumeRole",
                            "Effect": "Allow",
                            "Principal": {
                                "Service": "iot.amazonaws.com", 
                            }
                        },
                    ]
                },
            }
        }
    )


def test_iot_rule_created():
    app = core.App()
    stack = TimestreamCdkStack(app, "timestream-cdk")
    template = assertions.Template.from_stack(stack)
    template.has_resource(
        "AWS::IoT::TopicRule",
        {
            "Properties": {
                "RuleName": "IoT2TimestreamReplicate",
                "TopicRulePayload": {
                    "Actions": [
                        {
                            "Timestream": {
                                "DatabaseName": "AirQualityDuplicate",
                                "Dimensions": [
                                    {
                                        "Name": "DeviceEUI",
                                        "Value": "${dev_eui}",
                                        }
                                ],
                                "RoleArn": {
                                    "Fn::GetAtt": ["IoTTimestreamRole6C3940E8", "Arn"]
                                },
                                "TableName": "airQualityDuplicate",
                                "Timestamp": {
                                    "Unit": "MILLISECONDS",
                                    "Value": "${reported_at}",
                                }
                            }
                        },
                    ],
                    "Sql": "SELECT decoded.payload.data.* FROM 'air_quality'",
                }
            }
        }
    )


def test_logs_group_created():
    app = core.App()
    stack = TimestreamCdkStack(app, "timestream-cdk")
    template = assertions.Template.from_stack(stack)

    template.has_resource(
        "AWS::Logs::LogGroup",
        {
            "Properties": {
                "RetentionInDays": 7, 
            },
            "UpdateReplacePolicy": "Retain",
            "DeletionPolicy": "Retain",
        }
    )

