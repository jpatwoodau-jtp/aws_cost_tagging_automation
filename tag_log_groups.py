# %%
import boto3
import botocore
import jmespath
import time
import libs.notag_modules as ntm


def tag_log_group(logs_client, log_group, environment_tag, system_code):
    logs_client.tag_log_group(
        logGroupName=log_group,
        tags={
            "Environment": environment_tag,
            "SystemCode": system_code.upper()
        }
    )


def tag_log_groups(region, session, environment_tag, system_codes, **kwargs):
    print(f"Checking region {region}")
    my_config = botocore.config.Config(
        region_name=region
    )

    logs_client = session.client('logs', config=my_config)

    paginator = logs_client.get_paginator('describe_log_groups')

    response_iterator = paginator.paginate()

    log_groups = []

    for page in response_iterator:
        log_groups = log_groups + page['logGroups']

    log_groups = [log_group['logGroupName'] for log_group in log_groups]

    print(f"Total log groups: {len(log_groups)}")

    tag_counter = 0

    if log_groups:
        for idx, log_group in enumerate(log_groups):
            time.sleep(0.25)
            if not idx % 10:
                print(f"Checking tags on log group #{idx + 1}...")
            tags = logs_client.list_tags_log_group(
                logGroupName=log_group
            )['tags']
            try:
                tagged = tags["SystemCode"]
            except KeyError:
                tagged = False
                for system_code in system_codes:
                    if system_code in log_group.lower():
                        tag_log_group(logs_client, log_group,
                                      environment_tag, system_code)
                        tag_counter += 1
                        tagged = True
                        break
                if not tagged:
                    system_code = ntm.manual_system_code_input(
                        log_group, system_codes)
                    if system_code:
                        tag_log_group(logs_client, log_group,
                                      environment_tag, system_code)
                        tag_counter += 1
        print(
            f"Tagged {tag_counter} log group{'s' if tag_counter != 1 else ''}.")


if __name__ == "__main__":
    available_regions, initial_parameters = ntm.initial_setup()
    for region in available_regions:
        tag_log_groups(region, **initial_parameters)
