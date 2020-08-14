# %%
import boto3
import jmespath
import botocore
import libs.notag_modules as ntm


def tag_vpces(region, session, environment_tag, **kwargs):
    my_config = botocore.config.Config(region_name=region)
    ec2_client = session.client('ec2', config=my_config)
    endpoints = ec2_client.describe_vpc_endpoints()
    endpoints = [endpoint["VpcEndpointId"]
                 for endpoint in endpoints["VpcEndpoints"]]
    try:
        ec2_client.create_tags(
            Resources=endpoints,
            Tags=[{'Key':        'Environment', 'Value': environment_tag},
                  {'Key': 'SystemCode', 'Value': "JGAM"}]
        )
        print(f"Tagged {len(endpoints)} VPC endpoints in {region}.")
    except:
        print(f"No VPC endpoints in {region}.")


if __name__ == "__main__":
    available_regions, initial_parameters = ntm.initial_setup()
    for region in available_regions:
        tag_vpces(region, **initial_parameters)
