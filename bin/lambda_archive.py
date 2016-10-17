import conf
import zipfile
import os
import datetime

ARCHIVE_DIR = '/chatbot/'
DESTINATION_DIR = '/archive_file/'


def parent_file_dir_iter(n, path):
    n = int(n)
    if n <= 1:
        print path
        return path
    return parent_file_dir_iter(n - 1, os.path.dirname(path))


def zip_dir(path, zip_file):
    # Iterate all the directories and files
    for root, dirs, files in os.walk(path):
        # Create a prefix variable with the folder structure inside the path folder.
        # So if a file is at the path directory will be at the root directory of the zip file
        # so the prefix will be empty. If the file belongs to a containing folder of path folder
        # then the prefix will be that folder.
        if root.replace(path,'') == '':
                prefix = ''
        else:
                # Keep the folder structure after the path folder, append a '/' at the end
                # and remome the first character, if it is a '/' in order to have a path like
                # folder1/folder2/file.txt
                prefix = root.replace(path, '') + '/'
                if (prefix[0] == '/'):
                        prefix = prefix[1:]
        for filename in files:
                actual_file_path = root + '/' + filename
                zipped_file_path = prefix + filename
                zip_file.write(actual_file_path, zipped_file_path)


def create_zip(archive_dir, zip_name):
    """
    Create zip file
    :param archive_dir: directory path that will be archived.
    :param zip_name: zip file path.
    :return:
    """

    try:
        zip_file = zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED)
        zip_dir(archive_dir, zip_file)
        zip_file.close()
        return True
    except Exception, e:
        print e
        return False


def send_lambda_update_request(zip_path, lambda_name):
    """
    Upload zip file to lambda function
    :param zip_path: zip file path
    :param lambda_name: lambda function name that will be updated.
    :return:
    """

    try:
        # opening for [r]eading as [b]inary
        in_file = open(zip_path, "rb")
        # if you only wanted to read 512 bytes, do .read(512)
        data = in_file.read()
        in_file.close()

        lambda_client = conf.session.client('lambda')
        response = lambda_client.update_function_code(
            FunctionName=lambda_name,
            ZipFile=data,
            Publish=True
        )
        return response
    except Exception, e:
        print e
        return


def deploy_update_code_to_lambda(lambda_functions):
    """
    Create zip file with updated code and upload to each lambda functions
    :param lambda_functions: list of lambda functions name that will be updated.
    :return:
    """
    parent_dir = os.path.abspath(parent_file_dir_iter(2, os.path.dirname(__file__)))
    archive_dir = parent_dir + ARCHIVE_DIR

    zip_name = 'bopbot_%s.zip' % datetime.datetime.now()
    zip_name = zip_name.replace(' ', '')
    zip_name = parent_dir + DESTINATION_DIR + zip_name

    if create_zip(archive_dir, zip_name):
        zip_path = zip_name
        for function in lambda_functions:
            print function
            send_lambda_update_request(zip_path, function)


deploy_update_code_to_lambda(conf.lambda_functions)
