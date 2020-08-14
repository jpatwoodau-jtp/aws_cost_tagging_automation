# %%
import boto3
import jmespath
import botocore
import libs.notag_modules as ntm
# %%


def tag_ebs_snapshot(ec2_client, snapshot, environment_tag, system_code):
    ec2_client.create_tags(
        Resources=[snapshot['SnapshotId']],
        Tags=[{'Key': 'Environment', 'Value': environment_tag},
              {'Key': 'SystemCode', 'Value': system_code.upper()}]
    )


def tag_ebs_snapshots(region, session, environment_tag, system_codes, **kwargs):
    print(f"Checking region {region}")
    my_config = botocore.config.Config(
        region_name=region
    )
    ec2_client = session.client('ec2', config=my_config)
    snapshots = ec2_client.describe_snapshots(
        MaxResults=1000, OwnerIds=["self"])["Snapshots"]

    encrypted_snapshots = [
        snapshot for snapshot in snapshots if snapshot["Encrypted"]]

    snapshots = {"Snapshots": encrypted_snapshots}

    already_tagged = jmespath.search(
        "Snapshots[?Tags[?Key==`SystemCode`]]", snapshots)

    notag_snapshots = [
        snapshot for snapshot in snapshots["Snapshots"] if snapshot not in already_tagged]

    print(f"Found {len(notag_snapshots)} untagged, encrypted snapshots.")

    if notag_snapshots:
        tag_counter = 0
        notag_ids = [{"KmsKeyId": snapshot["KmsKeyId"],
                      "SnapshotId": snapshot["SnapshotId"]} for snapshot in notag_snapshots]

        aliases_dict = ntm.get_kms_aliases_dict(
            region, session, system_codes)

        for snapshot in notag_ids:
            try:
                system_code = aliases_dict[snapshot['KmsKeyId'][-36:]]
                tag_ebs_snapshot(ec2_client, snapshot,
                                 environment_tag, system_code)
                tag_counter += 1
            except KeyError:
                tag_ebs_snapshot(ec2_client, snapshot, environment_tag, "JGAM")
                tag_counter += 1

        print(f"Tagged {tag_counter} snapshots.")


if __name__ == "__main__":
    available_regions, initial_parameters = ntm.initial_setup()
    for region in available_regions:
        tag_ebs_snapshots(region, **initial_parameters)
