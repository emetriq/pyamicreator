import logging
import sys
import pytargetingutilities.tools.log as lg
from pytargetingutilities.aws.e2.helper import EC2Helper as ec2
from pytargetingutilities.aws.e2.run_command import RunCommandEc2 as cmd
from pytargetingutilities.aws.s3.helper import S3Helper
import fire
import json

__author__ = "Slash Gordon"
__copyright__ = "emetriq GmbH"
__license__ = "MIT"

_logger = logging.getLogger('ami_creator')


class Cli:
    def __init__(
        self,
        loglevel=logging.INFO,
        use_graylog=False,
        graylog_host=lg.GRAYLOG_HOST_RZ,
        graylog_port=12201,
    ):
        """Setup basic logging

        Args:
        loglevel (int): minimum loglevel for emitting messages
        use_graylog (bool): set to true if you want to activate graylog
        graylog_host (str): IP or hostname of graylog server
        graylog_port (int): Port of graylog server
        """

        lg.setup_logging_graylog(
            'ami_creator', loglevel, use_graylog, graylog_host, graylog_port
        )
        super().__init__()

    def create_image(
        self,
        config_path,
        instance_name,
        ami_name,
        ami_description,
        bucket=None,
        bucket_prefix=None,
        local_directory=None,
        extension='.whl',
        delete_existing=True,
        keep_alive=False,
    ):
        """AMI image creator

        Args:
            config_path (str): path to config file. The file content
            follows the syntax of
            https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ec2.html#EC2.Client.run_instances
            instance_name (str): name of ec2 instance
            ami_name (str)): name of ami image
            ami_description (str): description of ami image
            bucket (str, optional): bucket for dependency upload. Defaults to None.
            bucket_prefix (str, optional): bucket prefix. Defaults to None.
            local_directory (str, optional): local directory with libs. Defaults to None.
            extension (str, optional): Filters local directory. Defaults to '.whl'.
            delete_existing (bool, optional): Deletes s3 prefix if set to true. Defaults to True.
            keep_alive (bool, optional): Keeps ec2 instance alive if set to True. Defaults to False.
        """
        _logger.info(f'Start create image with config file {config_path}')
        instance_id = None
        with open(config_path) as f:
            cfg = json.load(f)
            _logger.info(f'Config {config_path} loaded successfully')
        try:
            if bucket and bucket_prefix and local_directory:
                _logger.info(
                    f'Upload dependency files from {local_directory} to s3://{bucket}/{bucket_prefix}'
                )
                S3Helper.upload_filtered_directory(
                    bucket,
                    bucket_prefix,
                    local_directory,
                    extension,
                    delete_existing,
                )
            _logger.info('Start ec2 instance')
            instance = ec2.start_instance(cfg, instance_name)
            instance_id = instance['Instances'][0]['InstanceId']
            dns = instance['Instances'][0]['PrivateDnsName']
            ip = instance['Instances'][0]['PrivateIpAddress']
            _logger.info(
                f'Wait until instance {instance_id} - {dns} ({ip}) is reachable'
            )
            ec2.await_startup([instance_id])
            _logger.info('Delete user data script')
            Cli.__evaluate_cloud_init(instance_id)
            _logger.info(f'Create image from instance {instance_id}')
            image_id = ec2.create_image(instance_id, ami_name, ami_description)
            if not ec2.is_image_available(image_id['ImageId']):
                raise RuntimeError('Image creation failed')
        except:
            _logger.exception('Image creation failed')
            return False
        finally:
            if instance_id and not keep_alive:
                _logger.info(f'Terminate instance {instance_id}')
                ec2.terminate_instances([instance_id])
        return True

    @staticmethod
    def __evaluate_cloud_init(instance_id):
        for log_file in [
            'sudo cat /var/log/cloud-init.log',
            'sudo cat /var/log/cloud-init-output.log',
        ]:
            _logger.info(f'Output of {log_file}')
            debug_output = cmd.run_commands_and_wait(
                [log_file],
                [instance_id],
                60,
                60,
                60,
            )
            if (
                len(debug_output) > 0
                and debug_output[0]['Status'] == 'Success'
            ):
                msg = debug_output[0]['StandardOutputContent']
                _logger.info(f'Output of {log_file}: {msg}')
            else:
                _logger.warning("Couldn't evaluate cloud init output")

    @staticmethod
    def clean_ami_group(ami_group, ami_group_sizes):
        """Deletes older images of an ami group

        Args:
            ami_group (str): name of ami group. Actually just the
            prefix of an ami image.
            ami_group_sizes (int): Group size of the ami image.
            If you set to 1, only the most recent ami remains in the group.
        """
        ami_ids = ec2.get_image_ids(ami_group)
        if ami_group_sizes >= len(ami_ids):
            _logger.info(
                f'''Clean not necessary ami size of group is
             {len(ami_ids)} and the max group size is {ami_group_sizes}'''
            )
            return False

        delete_items = len(ami_ids) - ami_group_sizes

        for idx in range(delete_items):
            _logger.info(f'Delete AMI {ami_ids[idx]}')
            ec2.delete_ami(ami_ids[idx])
        return True

    @staticmethod
    def get_latest_image(starts_with=''):
        return ec2.get_latest_image_id(starts_with)


def main(args):
    return fire.Fire(Cli, name="pyamicreator")


def run():
    sys.exit(not main(sys.argv[1:]))


if __name__ == "__main__":
    run()
