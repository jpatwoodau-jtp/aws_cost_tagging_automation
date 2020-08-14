# %%
import boto3
import jmespath
import botocore
import libs.notag_modules as ntm
# %%


def tag_ebs_volume(ec2_client, volume, environment_tag, system_code):
    ec2_client.create_tags(
        Resources=[volume['VolumeId']],
        Tags=[{'Key': 'Environment', 'Value': environment_tag},
              {'Key': 'SystemCode', 'Value': system_code.upper()}]
    )


def tag_ebs_volumes(region, session, environment_tag, system_codes, **kwargs):
    print(f"Checking region {region}")
    my_config = botocore.config.Config(
        region_name=region
    )
    ec2_client = session.client('ec2', config=my_config)

    volumes = ec2_client.describe_volumes(
        MaxResults=500)["Volumes"]

    encrypted_volumes = {"Volumes": [
        volume for volume in volumes if volume["Encrypted"]]}

    already_tagged_encrypted_volumes = jmespath.search(
        "Volumes[?Tags[?Key==`SystemCode`]]", encrypted_volumes)

    notag_encrypted_volumes = [
        volume for volume in encrypted_volumes["Volumes"] if volume not in already_tagged_encrypted_volumes]

    print(
        f"Found {len(notag_encrypted_volumes)} untagged, encrypted volume{'s' if len(notag_encrypted_volumes) != 1 else ''}.")

    if notag_encrypted_volumes:
        tag_counter = 0

        notag_ids = [{"KmsKeyId": volume["KmsKeyId"],
                      "VolumeId": volume["VolumeId"]} for volume in notag_encrypted_volumes]

        aliases_dict = ntm.get_kms_aliases_dict(
            region, session, system_codes)

        for volume in notag_ids:
            try:
                system_code = aliases_dict[volume['KmsKeyId'][-36:]]
                tag_ebs_volume(ec2_client, volume,
                               environment_tag, system_code)
                tag_counter += 1
            except KeyError:
                tag_ebs_volume(ec2_client, volume,
                               environment_tag, "JGAM")
                tag_counter += 1

        print(
            f"Tagged {tag_counter} encrypted volume{'s' if tag_counter != 1 else ''}.")

    unencrypted_volumes = {"Volumes": [
        volume for volume in volumes if not volume["Encrypted"]
    ]}

    attached_unencrypted_volumes = {"Volumes": [
        volume for volume in unencrypted_volumes["Volumes"] if volume["Attachments"]]}

    already_tagged_attached_unencrypted_volumes = jmespath.search(
        "Volumes[?Tags[?Key==`SystemCode`]]", attached_unencrypted_volumes)

    notag_attached_unencrypted_volumes = [
        volume for volume in attached_unencrypted_volumes["Volumes"] if volume not in already_tagged_attached_unencrypted_volumes]

    print(f"Found {len(notag_attached_unencrypted_volumes)} untagged, unencrypted, in-use volume{'s' if len(notag_attached_unencrypted_volumes) != 1 else ''}.")

    if notag_attached_unencrypted_volumes:
        tag_counter = 0
        notag_ids = [{"InstanceId": volume["Attachments"][0]["InstanceId"],
                      "VolumeId": volume["VolumeId"]} for volume in notag_attached_unencrypted_volumes]
        reservations = ec2_client.describe_instances(
            InstanceIds=[volume["InstanceId"] for volume in notag_ids])
        tagged_instance_tags = jmespath.search(
            "Reservations[*].Instances[?Tags[?Key==`SystemCode`]].{InstanceId:InstanceId,SystemCode:Tags[?Key==`SystemCode`].Value}", reservations)

        tagged_instance_tags = [tagged_instance_tag[0]
                                for tagged_instance_tag in tagged_instance_tags]

        instance_id_code_dict = {}

        for tagged_instance_tag in tagged_instance_tags:
            instance_id_code_dict[tagged_instance_tag["InstanceId"]
                                  ] = tagged_instance_tag["SystemCode"][0]

        for volume in notag_ids:
            tag_ebs_volume(ec2_client, volume, environment_tag,
                           instance_id_code_dict[volume["InstanceId"]])
            tag_counter += 1
        print(
            f"Tagged {tag_counter} unencrypted, in-use volume{'s' if tag_counter != 1 else ''}.")


if __name__ == "__main__":
    available_regions, initial_parameters = ntm.initial_setup()
    for region in available_regions:
        tag_ebs_volumes(region, **initial_parameters)
