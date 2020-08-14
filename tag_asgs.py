# %%
import boto3
import jmespath
import botocore
import libs.notag_modules as ntm
# %%


def tag_asg(autoscaling_client, asg, environment_tag, system_code):
    autoscaling_client.create_or_update_tags(Tags=[
        {
            'ResourceId': asg,
            'ResourceType': 'auto-scaling-group',
            'Key': 'Environment',
            'Value': environment_tag,
            'PropagateAtLaunch': True
        },
        {
            'ResourceId': asg,
            'ResourceType': 'auto-scaling-group',
            'Key': 'SystemCode',
            'Value': system_code.upper(),
            'PropagateAtLaunch': True
        }
    ])
    print(
        f"Tagged ASG {asg} with SystemCode {system_code.upper()}.")


def tag_asgs(region, session, environment_tag, system_codes, **kwargs):
    print(f"Checking region {region}")
    my_config = botocore.config.Config(region_name=region)
    autoscaling_client = session.client('autoscaling', config=my_config)
    asgs = autoscaling_client.describe_auto_scaling_groups()
    already_tagged = jmespath.search(
        "AutoScalingGroups[?Tags[?Key==`SystemCode` && PropagateAtLaunch]]", asgs)
    no_tags = []
    for asg in asgs["AutoScalingGroups"]:
        if asg not in already_tagged:
            no_tags.append(asg["AutoScalingGroupName"])

    ntm.print_no_tags(no_tags, "asgs")

    for asg in no_tags:
        tagged = False
        for system_code in system_codes:
            if system_code in asg.lower():
                tag_asg(autoscaling_client, asg, environment_tag, system_code)
                tagged = True
                break
        if not tagged:
            system_code = ntm.manual_system_code_input(asg, system_codes)
            if system_code:
                tag_asg(autoscaling_client, asg, environment_tag, system_code)


if __name__ == "__main__":
    available_regions, initial_parameters = ntm.initial_setup()
    for region in available_regions:
        tag_asgs(region, **initial_parameters)
