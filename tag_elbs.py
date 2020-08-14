# %%
import boto3
import jmespath
import botocore
import libs.notag_modules as ntm
# %%


def tag_elb(elbv2_client, elb, environment_tag, system_code):
    elbv2_client.add_tags(ResourceArns=[elb], Tags=[{"Key": "Environment", "Value": environment_tag}, {
                          "Key": "SystemCode", "Value": system_code.upper()}])
    print(
        f"Tagged {elb} with system code {system_code.upper()}")


def tag_elbs(region, session, environment_tag, system_codes, **kwargs):
    print(f"Checking region {region}")
    my_config = botocore.config.Config(region_name=region)
    elbv2_client = session.client('elbv2', config=my_config)
    lbs = elbv2_client.describe_load_balancers()
    lb_arns = [lb["LoadBalancerArn"] for lb in lbs["LoadBalancers"]]
    lb_arns_dup = lb_arns

    lb_tags = []

    while len(lb_arns) > 0:
        if len(lb_arns) <= 20:
            lb_tags += elbv2_client.describe_tags(
                ResourceArns=lb_arns)["TagDescriptions"]
            lb_arns = []
        else:
            lb_tags += elbv2_client.describe_tags(
                ResourceArns=lb_arns[:20])["TagDescriptions"]
            lb_arns = lb_arns[20:]

    lb_arns = lb_arns_dup
    lb_tags = {"lbs": lb_tags}

    already_tagged = jmespath.search(
        "lbs[?Tags[?Key==`SystemCode`]]", lb_tags)

    no_tags = [lb["ResourceArn"]
               for lb in lb_tags["lbs"] if lb not in already_tagged]

    ntm.print_no_tags(no_tags, "elbs")

    for elb in no_tags:
        tagged = False
        for system_code in system_codes:
            if system_code in elb:
                tag_elb(elbv2_client, elb, environment_tag, system_code)
                tagged = True
                break
        if not tagged:
            system_code = ntm.manual_system_code_input(elb, system_codes)
            if system_code:
                tag_elb(elbv2_client, elb, environment_tag, system_code)


# %%
if __name__ == "__main__":
    available_regions, initial_parameters = ntm.initial_setup()
    for region in available_regions:
        tag_elbs(region, **initial_parameters)
