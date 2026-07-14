import re

# define functions
def list_user_folders(client):
    """All userNN folders directly under SANDBOX, sorted by name."""
    sandbox = client.get_project_folder('SANDBOX')
    USER_FOLDER_PATTERN = re.compile(r'^user\d{2}$')
    
    folders = [
        f for f in sandbox.list_child_folders()
        if USER_FOLDER_PATTERN.match(f.get_name())
    ]
    return sorted(folders, key=lambda f: f.get_name())

def walk_folder_tree(folder, depth=0):
    """
    Depth-first, deepest first. Yields (folder, depth, project_keys, child_folders).

    child_folders is this folder's direct children, fetched once up front
    (before any of them can be deleted by the caller). Callers must use this
    list instead of calling folder.list_child_folders() again later in the
    walk: by that point some of those children may already have been deleted,
    and re-listing would try to re-fetch a folder id that no longer exists
    on the server (raising UnauthorizedException/NotFoundException).

    Ordering guarantees children are yielded before their parent,
    so deleting in iteration order is always safe.
    """
    child_folders = folder.list_child_folders()
    for child in child_folders:
        for item in walk_folder_tree(child, depth + 1):
            yield item
    yield folder, depth, folder.list_project_keys(), child_folders

def get_user_folder_by_id(client, user_id, create_if_not_exist_TF):
    """Return the user's project folder under SANDBOX, or None."""
    sandbox = client.get_project_folder('SANDBOX')
    child_folders = sandbox.list_child_folders()

    user_folder = next(
        (f for f in child_folders if f.get_name() == user_id), None
    )

    if user_folder is not None:
        print(f"{user_id}'s folder already exists")
        return user_folder

    print(f"{user_id}'s folder doesn't exist")
    if not create_if_not_exist_TF:
        return None

    user_folder = sandbox.create_sub_folder(user_id)
    print(f"{user_id} folder created")

    folder_settings = user_folder.get_settings()
    folder_settings.set_owner(user_id)
    folder_settings.save()

    return user_folder

def get_project_folder_by_num(client, project_id_prefix, user_num):
    project_id = project_id_prefix + '_' + user_num
    project = client.get_project(project_id)

    project_folder = project.get_project_folder()
    
    return project_folder

def duplicate_project_by_id(client, project_id, user_id, dest_folder):
    # get original project
    project = client.get_project(project_id)
    project_meta = project.get_metadata()
    project_name = project_meta['label']

    # duplicate project
    new_project_id = project_id + '_' + user_id
    print('Duplicating ' + new_project_id)

    try:
        project.duplicate(new_project_id, project_name, target_project_folder=dest_folder, duplication_mode='FULL', export_saved_models=True)
        new_project = client.get_project(new_project_id)
#        new_project.move_to_folder(dest_folder)

        # set tag
        project_metadata = new_project.get_metadata()
        project_metadata['tags'] = ['duplicated', project_name]
        new_project.set_metadata(project_metadata)

    except Exception as err:
        print('duplicate failed')
        print("Error = ", str(err))
        return None
    
    return new_project_id

def duplicate_project_by_num(client, project_id, user_num, dest_folder):
    project = client.get_project(project_id)
    project_name = project.get_metadata()['label']

    new_project_id = f"{project_id}_{user_num}"
    print(f"Start duplicating {new_project_id}")

    project.duplicate(
        new_project_id,
        project_name,
        duplication_mode='FULL',
        target_project_folder=dest_folder,
        export_saved_models=True,
    )

    new_project = client.get_project(new_project_id)

    metadata = new_project.get_metadata()
    metadata['tags'] = ['duplicated', project_name]
    new_project.set_metadata(metadata)

    return new_project_id

def set_project_owner_by_id(client, project_id, user_id):
    new_project_id = project_id + '_' + user_id
    print("Set owner of " + new_project_id)

    # set owner
    new_project = client.get_project(new_project_id)
    project_permissions = new_project.get_permissions()
    project_permissions['owner'] = user_id
    print('Owner = ' + user_id )
    new_project.set_permissions(project_permissions)
    
    return 1

def set_project_owner(client, project_id, user_id):
    print("Set owner of " + project_id)

    # set owner
    try:
        update_project = client.get_project(project_id)
        project_permissions = update_project.get_permissions()
        project_permissions['owner'] = user_id
        update_project.set_permissions(project_permissions)
    except:
        return 0
    
    return 1


def set_project_owner_by_num(client, project_id, user_num, set_owner_to_admin_TF=False):
    new_project_id = project_id + '_' + user_num
    #print("Set owner of " + new_project_id)

    # set owner
    try:
        new_project = client.get_project(new_project_id)
        project_permissions = new_project.get_permissions()

        if set_owner_to_admin_TF == True:
            project_permissions['owner'] = 'admin'
        else:
            project_permissions['owner'] = 'user' + user_num
            #print('Owner = ' + 'user' + user_num )

        new_project.set_permissions(project_permissions)
    except:
        return 0
    
    return 1

def delete_project_by_id(client, project_id, user_id):
    del_project_id = project_id + '_' + user_id
    print("Delete " + del_project_id)
    del_project = client.get_project(del_project_id)

    try:
        del_project.delete(clear_managed_datasets=True, clear_job_and_scenario_logs=True)
    except Exception as err:
        print('delete failed')
        print("Error = ", str(err))
        return 0
    
    return 1

def delete_project_by_num(client, project_id, user_num):
    del_project_id = project_id + '_' + user_num
    print("Delete " + del_project_id)
    del_project = client.get_project(del_project_id)

    try:
        del_project.delete(clear_managed_datasets=True, clear_job_and_scenario_logs=True)
    except Exception as err:
        print('delete failed')
        print("Error = ", str(err))
        return 0
    
    return 1

def get_aws_ec2_instance_details(ec2_client, instance_id):
    try:
        response = ec2_client.describe_instances(InstanceIds=[instance_id])
        
        # Check if we have any reservations
        if not response.get('Reservations'):
            return None, None
            
        instance = response['Reservations'][0]['Instances'][0]
        tags = instance.get('Tags', [])
        
        # Get instance name from tags
        name = next((tag['Value'] for tag in tags if tag['Key'] == 'Name'), None)
        # Get instance state
        instance_state = instance['State']['Name']

        return name, instance_state
        
    except Exception as e:
        print(f"Error getting instance details: {str(e)}")
        return None, None
    
def project_exists(client, project_id):
    """True if project_id exists. Single listing call, no permission probing."""
    return project_id in set(client.list_project_keys())
        