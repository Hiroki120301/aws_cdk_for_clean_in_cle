import aws_cdk as core
import aws_cdk.assertions as assertions

from timestream_cdk.timestream_cdk_stack import TimestreamCdkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in timestream_cdk/timestream_cdk_stack.py
def test_sqs_queue_created():
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

