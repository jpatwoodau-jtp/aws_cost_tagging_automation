# %%
import boto3
import jmespath
import botocore
import libs.notag_modules as ntm

# %%


def tag_bucket(s3_client, bucket, environment_tag, system_code):
    try:
        s3_client.put_bucket_tagging(
            Bucket=bucket,
            Tagging={
                "TagSet": [
                    {
                        "Key": "Environment",
                        "Value": environment_tag
                    },
                    {
                        "Key": "SystemCode",
                        "Value": system_code
                    }
                ]
            }
        )
        print(
            f"Tagged bucket {bucket} with SystemCode {system_code.upper()}.")
    except botocore.exceptions.ClientError as err:
        print(
            f"Unable to tag bucket {bucket}. Error message: {err}.")


def tag_buckets(profile, session, environment_tag, system_codes, **kwargs):
    s3_client = session.client("s3")
    buckets = s3_client.list_buckets()["Buckets"]
    print(f"Total buckets: {len(buckets)}")

    no_tags = []
    for idx, bucket in enumerate(buckets):
        try:
            if not idx % 10:
                print(f"Checking tags on bucket #{idx + 1}...")
            tag_set = s3_client.get_bucket_tagging(
                Bucket=bucket["Name"])["TagSet"]
            already_tagged = False
            for tag in tag_set:
                if tag["Key"] == "SystemCode":
                    already_tagged = True
            if not already_tagged:
                no_tags.append(bucket["Name"])
        except botocore.exceptions.ClientError:
            no_tags.append(bucket["Name"])
    print(
        f"Found {len(no_tags)} untagged bucket{'s' if len(no_tags) != 1 else ''}")

    for bucket in no_tags:
        tagged = False
        for system_code in system_codes:
            if system_code in bucket:
                tag_bucket(s3_client, bucket, environment_tag, system_code)
                tagged = True
                break
        if not tagged:
            system_code = ntm.manual_system_code_input(bucket, system_codes)
            if system_code:
                tag_bucket(s3_client, bucket, environment_tag, system_code)


# %%
if __name__ == "__main__":
    available_regions, initial_parameters = ntm.initial_setup()
    tag_buckets(**initial_parameters)
