import libs.notag_modules as ntm
import tag_buckets
import tag_asgs
import tag_elbs
import tag_ebs_snapshots
import tag_ebs_volumes
import tag_vpces
import tag_log_groups

available_regions, initial_parameters = ntm.initial_setup()

ntm.announce("S3 Buckets")
tag_buckets.tag_buckets(**initial_parameters)

ntm.announce("AutoScaling Groups")
for region in available_regions:
    tag_asgs.tag_asgs(region, **initial_parameters)

ntm.announce("Elastic Load Balancers")
for region in available_regions:
    tag_elbs.tag_elbs(region, **initial_parameters)

ntm.announce("EBS Snapshots")
for region in available_regions:
    tag_ebs_snapshots.tag_ebs_snapshots(region, **initial_parameters)

ntm.announce("EBS Volumes")
for region in available_regions:
    tag_ebs_volumes.tag_ebs_volumes(region, **initial_parameters)

ntm.announce("VPC Endpoints")
for region in available_regions:
    tag_vpces.tag_vpces(region, **initial_parameters)

ntm.announce("Log Groups")
for region in available_regions:
    tag_log_groups.tag_log_groups(region, **initial_parameters)
