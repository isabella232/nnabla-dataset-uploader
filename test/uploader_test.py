import json
import shutil
import sys
from unittest import TestCase

import boto3
import requests
from parameterized import parameterized

sys.path.append('../src/')
import uploader
import os
import random


class TestUploader(TestCase):
    @parameterized.expand([
        ("https://dev-api.cdd-sdeep.com", "", "index.csv", "175460142186987520", "71437614-7d0c-45e2-91d5-f8875f476ca9",
         "de9c6080-6e79-4b40-bfe3-3eed052b2c9a")
    ])
    def test_success(self, endpoint, token, filename, user_id, tenant_id, cookie):
        # コマンドライン引数の初期化と設定
        del sys.argv[1:]

        # ランダムの数値を取得
        random_name = random.randint(10000, 99999)
        random_name_csv = str(random_name) + ".csv"
        random_name_tar = str(random_name) + ".tar"

        # headersとcookiesの設定
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        cookies = dict(s=cookie)
        # tarがアップロードされるディレクトリ名前を設定
        bucket_name = 'sdeep-upload-dev'

        # csvファイルをランダムの名前を付けてコピー
        shutil.copy(filename, random_name_csv)

        # tokenを取得　エラーの場合のみ値を渡す
        if token == "":
            token_request = requests.get('{}/v1/users/{}/datasets/create'.format(endpoint, user_id, tenant_id),
                                         headers=headers, cookies=cookies)
            token = json.loads(token_request.text)['encrypted_text']

        # 環境変数を設定
        sys.argv.append('-e' + endpoint)
        sys.argv.append(token)
        sys.argv.append(random_name_csv)

        # uploaderを実行
        uploader.main()

        # tarがアップロードされているか確認
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        uploader_tar_folder_list = bucket.meta.client.list_objects(Bucket=bucket.name, Delimiter='/')
        tar_check = False

        # tarがある階層を再帰的に取得して比較
        for uploader_tar_folder in uploader_tar_folder_list.get('CommonPrefixes'):
            uploader_tar = bucket.meta.client.list_objects(Bucket=bucket.name, Prefix=uploader_tar_folder.get('Prefix'),
                                                           Delimiter='/')
            uploader_tar_name = uploader_tar['Contents']
            if random_name_tar in uploader_tar_name[0]['Key']:
                tar_check = True

        # コピーしたcsvを削除
        os.remove(random_name_csv)
        self.assertTrue(tar_check)

    @parameterized.expand([
        ("https://dev-api.cdd-sdeep.com", "error", "index.csv", "175460142186987520",
         "71437614-7d0c-45e2-91d5-f8875f476ca9", "de9c6080-6e79-4b40-bfe3-3eed052b2c9a"),
        # ("https://dev-api.cdd-sdeep.com", "", "/test/index.csv", "175460142186987520",
        #  "71437614-7d0c-45e2-91d5-f8875f476ca9", "de9c6080-6e79-4b40-bfe3-3eed052b2c9a"),
        ("https://dev-api.cdd-sdeep.com", "", "", "175460142186987520",
         "71437614-7d0c-45e2-91d5-f8875f476ca9", "de9c6080-6e79-4b40-bfe3-3eed052b2c9a"),
        ("https://dev-api.cdd-sdeep.com", "", "index", "175460142186987520",
         "71437614-7d0c-45e2-91d5-f8875f476ca9", "de9c6080-6e79-4b40-bfe3-3eed052b2c9a")
        # ("https://dev-api.cdd-sdeep.com", "", "index_not_ascii.csv", "175460142186987520",
        #  "71437614-7d0c-45e2-91d5-f8875f476ca9", "de9c6080-6e79-4b40-bfe3-3eed052b2c9a"),
        # ("https://dev-api.cdd-sdeep.com", "", "index_space.csv", "175460142186987520",
        #  "71437614-7d0c-45e2-91d5-f8875f476ca9", "de9c6080-6e79-4b40-bfe3-3eed052b2c9a"),
        # ("https://dev-api.cdd-sdeep.com", "", "index_null.csv", "175460142186987520",
        #  "71437614-7d0c-45e2-91d5-f8875f476ca9", "de9c6080-6e79-4b40-bfe3-3eed052b2c9a")
    ])
    def test_failed(self, endpoint, token, filename, user_id, tenant_id, cookie):
        # コマンドライン引数の初期化と設定
        del sys.argv[1:]

        # ランダムの数値を取得
        random_name = random.randint(10000, 99999)
        random_name_csv = str(random_name) + ".csv"
        random_name_tar = str(random_name) + ".tar"

        # headersとcookiesの設定
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        cookies = dict(s=cookie)

        # tarがアップロードされるディレクトリ名前を設定
        bucket_name = 'sdeep-upload-dev'

        # csvファイルをランダムの名前を付けてコピー
        if os.path.isfile(filename):
            shutil.copy(filename, random_name_csv)

        # tokenを取得　エラーの場合のみ値を渡す
        if token == "":
            token_request = requests.get('{}/v1/users/{}/datasets/create'.format(endpoint, user_id, tenant_id), headers=headers, cookies=cookies)
            token = json.loads(token_request.text)['encrypted_text']

        # 環境変数を設定
        sys.argv.append('-e' + endpoint)
        sys.argv.append(token)
        if os.path.isfile(filename):
            sys.argv.append(random_name_csv)
        else:
            sys.argv.append(filename)

        # uploaderを実行
        uploader.main()

        # tarがアップロードされているか確認
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        uploader_tar_folder_list = bucket.meta.client.list_objects(Bucket=bucket.name, Delimiter='/')
        tar_check = False

        # tarがある階層を再帰的に取得して比較
        for uploader_tar_folder in uploader_tar_folder_list.get('CommonPrefixes'):
            uploader_tar = bucket.meta.client.list_objects(Bucket=bucket.name,
                                                           Prefix=uploader_tar_folder.get('Prefix'), Delimiter='/')
            uploader_tar_name = uploader_tar['Contents']
            if random_name_tar in uploader_tar_name[0]['Key']:
                tar_check = True

        # コピーしたcsvを削除
        if os.path.isfile(filename):
            os.remove(random_name_csv)
        self.assertFalse(tar_check)

    @parameterized.expand([
        ("https://error-api.cdd-sdeep.com", "", "index.csv", "175460142186987520",
         "71437614-7d0c-45e2-91d5-f8875f476ca9", "de9c6080-6e79-4b40-bfe3-3eed052b2c9a")
    ])
    def test_except(self, endpoint, token, filename, user_id, tenant_id, cookie):
        # コマンドライン引数の初期化と設定
        del sys.argv[1:]

        # ランダムの数値を取得
        random_name = random.randint(10000, 99999)
        random_name_csv = str(random_name) + ".csv"
        random_name_tar = str(random_name) + ".tar"

        # headersとcookiesの設定
        headers = {'X-Requested-With': 'XMLHttpRequest'}
        cookies = dict(s=cookie)

        # tarがアップロードされるディレクトリ名前を設定
        bucket_name = 'sdeep-upload-dev'

        # csvファイルをランダムの名前を付けてコピー
        shutil.copy(filename, random_name_csv)

        # error確認変数定義
        error_check = False

        # tokenを取得　エラーの場合のみ値を渡す
        if token == "":
            token_request = requests.get('{}/v1/users/{}/datasets/create'.format("https://dev-api.cdd-sdeep.com", user_id, tenant_id), headers=headers, cookies=cookies)
            token = json.loads(token_request.text)['encrypted_text']

        # 環境変数を設定
        sys.argv.append('-e' + endpoint)
        sys.argv.append(token)
        sys.argv.append(random_name_csv)

        # 期待したerrorが起きるか確認
        try:
            uploader.main()
        except OSError:
            error_check = True

        # tarがアップロードされているか確認
        s3 = boto3.resource('s3')
        bucket = s3.Bucket(bucket_name)
        uploader_tar_folder_list = bucket.meta.client.list_objects(Bucket=bucket.name, Delimiter='/')
        tar_check = False

        # tarがある階層を再帰的に取得して比較
        for uploader_tar_folder in uploader_tar_folder_list.get('CommonPrefixes'):
            uploader_tar = bucket.meta.client.list_objects(Bucket=bucket.name, Prefix=uploader_tar_folder.get('Prefix'),
                                                           Delimiter='/')
            uploader_tar_name = uploader_tar['Contents']
            if random_name_tar in uploader_tar_name[0]['Key']:
                tar_check = True

        # コピーしたcsvを削除
        os.remove(random_name_csv)
        self.assertFalse(tar_check)
        self.assertTrue(error_check)
