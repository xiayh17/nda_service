import base64
import configparser
import csv
from pathlib import Path
import os
import requests
import subprocess
import time
from dotenv import load_dotenv

class NDAService:
    def __init__(self, manifest_file, package_id, download_directory, aria2c_options):
        load_dotenv()
        self.username = os.getenv('NDA_USERNAME')
        self.password = os.getenv('NDA_PASSWORD')
        self.credentials = base64.b64encode(f'{self.username}:{self.password}'.encode('utf-8')).decode('utf-8')

        self.headers = {
            'Authorization': 'Basic ' + self.credentials,
            'User-Agent': 'Example Client',
            'Accept': 'application/json'
        }

        self.manifest_file = manifest_file
        self.package_id = package_id
        self.download_directory = download_directory
        self.aria2c_options = aria2c_options.split()
        self.files = {}

    def authenticate(self):
        response = requests.get('https://nda.nih.gov/api/package/auth', headers=self.headers)
        if response.status_code != requests.codes.ok:
            print('Failed to authenticate')
            response.raise_for_status()

    @staticmethod
    def get_s3_files(manifest_file):
        s3_files = []
        with open(manifest_file, 'r') as manifest:
            for rows in csv.reader(manifest, dialect='excel-tab'):
                for row in rows:
                    if row.startswith('s3://'):
                        s3_files.append(row)
        return s3_files[2:]

    def get_files(self, s3_files):
        response = requests.post(f'https://nda.nih.gov/api/package/{self.package_id}/files', json=s3_files, headers=self.headers)
        for f in response.json():
            self.files[f['package_file_id']] = {'name': f['download_alias']}

    def get_presigned_urls(self):
        response = requests.post(f'https://nda.nih.gov/api/package/{self.package_id}/files/batchGeneratePresignedUrls', json=list(self.files.keys()), headers=self.headers)
        results = response.json()['presignedUrls']
        for url in results:
            self.files[url['package_file_id']]['download'] = url['downloadURL']

    def download_files(self):
        all_files_downloaded = True
        with open('download.log', 'a') as log_file:
            for id, data in self.files.items():
                name = data['name']
                download_url = data['download']
                file_path = Path(self.download_directory) / name
                file_path.parent.mkdir(parents=True, exist_ok=True)
                command = ['aria2c', '--file-allocation=none', download_url, '-d', str(file_path.parent), '-l', 'aria2c.log', '-j', '1'] + self.aria2c_options
                result = subprocess.run(command, capture_output=True, text=True)
                if result.returncode != 0:
                    log_file.write(f'Failed to download file {name} from URL {download_url}\n')
                    all_files_downloaded = False
                else:
                    with open('aria2c.log', 'r') as aria2c_log:
                        download_speed = 'Unknown'
                        for line in aria2c_log:
                            if 'Download Results:' in line:
                                break
                            if 'Download Speed:' in line:
                                download_speed = line.split(':')[-1].strip()
                        log_file.write(f'Successfully downloaded file {name} from URL {download_url} with speed {download_speed}\n')
                os.remove('aria2c.log')
        return all_files_downloaded

    def refresh_and_download(self):
        while True:
            self.authenticate()
            s3_files = self.get_s3_files(self.manifest_file)
            self.get_files(s3_files)
            self.get_presigned_urls()
            all_files_downloaded = self.download_files()
            if all_files_downloaded:
                break
            time.sleep(7200)  # wait for 2 hours


if __name__ == "__main__":
    config = configparser.ConfigParser()
    config.read('config.ini')
    manifest_file = config.get('DEFAULT', 'ManifestFile')
    package_id = config.getint('DEFAULT', 'PackageId')
    download_directory = config.get('DEFAULT', 'DownloadDirectory')
    aria2c_options = config.get('DEFAULT', 'Aria2cOptions')

    service = NDAService(manifest_file, package_id, download_directory, aria2c_options)
    service.refresh_and_download()
