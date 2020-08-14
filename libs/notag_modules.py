import sys
import json
import subprocess
import botocore
from datetime import datetime, timedelta
import boto3
import jmespath


def get_profile():
    session = boto3.session.Session()
    available_profiles = session.available_profiles
    profile = ""
    while profile not in available_profiles:
        profile = input("Input profile: ")
        if profile not in available_profiles:
            print("Profile not found in ~/.aws/config")
    return profile


def get_environment_tag():
    environment_tag = ""
    while environment_tag not in ["dev", "prd"]:
        environment_tag = input("Input Environment tag value (dev or prd): ")
    return environment_tag


def get_available_regions():
    region_checker = boto3.client("ec2", region_name="ap-northeast-1")
    available_regions = [region["RegionName"]
                         for region in region_checker.describe_regions()["Regions"]]
    return available_regions


def get_system_codes(session):
    ce_client = session.client('ce')
    system_codes = ce_client.get_tags(
        TimePeriod={
            "Start": (datetime.today() - timedelta(days=30)).strftime('%Y-%m-%d'),
            "End": datetime.today().strftime('%Y-%m-%d')
        },
        TagKey="SystemCode"
    )["Tags"]
    system_codes = list(set([system_code.lower()
                             for system_code in system_codes if system_code.lower() not in ["", "test"]]))
    return system_codes


def get_kms_aliases_dict(region, session, system_codes):
    my_config = botocore.config.Config(region_name=region)
    kms_client = session.client('kms', config=my_config)

    aliases = [
        alias for alias in jmespath.search(
            "Aliases[?TargetKeyId]", kms_client.list_aliases(Limit=100)) if "alias/aws/" not in alias["AliasName"]]
    aliases_dict = {}
    for idx, alias in enumerate(aliases):
        for system_code in system_codes:
            if system_code in alias["AliasName"]:
                aliases_dict[alias["TargetKeyId"]] = system_code
                break
        if len(aliases_dict) != idx + 1:
            system_code = manual_system_code_input(
                alias["AliasName"], system_codes)
            if system_code:
                aliases_dict[alias["TargetKeyId"]] = system_code
    return aliases_dict


def manual_system_code_input(no_tag, system_codes):
    system_code = input(
        f"No system code found:\n{no_tag}\nManually enter a system code, or press enter to skip: ")
    if system_code:
        while system_code and system_code.lower() not in system_codes:
            system_code = input(
                f"No such system code is currently in use.\nTry again or press enter to skip: ")
    return system_code


def print_no_tags(no_tags, resources="resources"):
    print(f"No tags on the following {resources}: {no_tags}")


def initial_setup():
    profile = get_profile()

    session = boto3.session.Session(profile_name=profile)

    environment_tag = get_environment_tag()

    system_codes = get_system_codes(session)

    available_regions = get_available_regions()

    return available_regions, {"profile": profile, "session": session, "environment_tag": environment_tag, "system_codes": system_codes}


def announce(resources):
    print(f"\n-- Checking {resources} --")
