import boto3
from datetime import datetime

# Toggle this to False when you're ready to actually terminate instances
DRY_RUN = True

def lambda_handler(event, context):
    today = datetime.utcnow().strftime("%Y%m%d")
    ec2_client = boto3.client('ec2')
    
    # Get all EC2 regions
    regions = [r['RegionName'] for r in ec2_client.describe_regions()['Regions']]
    
    for region in regions:
        print(f"Checking region: {region}")
        ec2 = boto3.resource('ec2', region_name=region)
        
        instances = ec2.instances.filter(
            Filters=[{'Name': 'instance-state-name', 'Values': ['running', 'pending']}]
        )
        
        for instance in instances:
            killdate = None
            if instance.tags:
                for tag in instance.tags:
                    if tag['Key'].lower() == 'killdate':
                        killdate = tag['Value']
                        break
            
            if killdate and killdate.isdigit() and len(killdate) == 8:
                if killdate < today:
                    if DRY_RUN:
                        print(f"[DRY RUN] Would terminate instance {instance.id} in {region} (killdate: {killdate})")
                    else:
                        print(f"Terminating instance {instance.id} in {region} (killdate: {killdate})")
                        try:
                            instance.terminate()
                        except Exception as e:
                            print(f"Error terminating {instance.id}: {e}")
                else:
                    print(f"Instance {instance.id} in {region} has future killdate {killdate}")
            else:
                print(f"Instance {instance.id} in {region} has no valid killdate, skipping")

