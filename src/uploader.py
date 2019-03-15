import argparse
import boto3
import csv
import os
import requests
import shutil
import tarfile
import tempfile
import threading
import tqdm

from version import versionString


class Uploader:
    # plotで使用するグラフ用のCSVの中身の確認
    def check_plot_csv_data(self, filename):
        csv_list = []

        # sizeが0ではないか確認
        self.csv_null_check(filename)

        # csvファイルを開く
        with open(filename, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                csv_list.append(row)
        for row in csv_list:

            # 2列であるか確認
            if not len(row) == 2:
                self._log("plot_csv_data is not 2 row")
                raise Exception

            for item in row:
                # 対応している文字コードか確認を行う
                self.ascii_check(item)
                # 数値のみであるか確認
                if not self.number_check(item):
                    self._log("plot_csv_data is not number")
                    raise Exception

    def ascii_check(self, item):
        try:
            item.encode('ascii')
        except UnicodeEncodeError:
            self._log("ascii_check error")
            raise UnicodeEncodeError

    def number_check(self, item):
        # floatに変換できるか確認
        try:
            float(item)
            return True
        except ValueError:
            return False

    def csv_null_check(self, filename):
        # sizeが0ではないか確認
        size = os.path.getsize(filename)
        if size == 0:
            self._log("csv file is null")
            raise Exception

    def column_null_check(self, item):
        # null チェック
        if item.strip() == '':
            self._log('Null data found')
            raise Exception

    def check_csv_data(self, filename):
        Extention = []
        csv_list = []

        try:
            # sizeが0ではないか確認
            self.csv_null_check(filename)

            # csvファイルを開く
            with open(filename, 'r') as f:
                reader = csv.reader(f)
                for row in reader:
                    csv_list.append(row)

                # 1行のみの場合はヘッダーのみとみなしエラー
                if 1 == len(csv_list):
                    self._log("header only")
                    raise Exception

                # 2行目のデータ形式を配列にいれる
                for item in csv_list[1]:

                    # 対応している文字コードか確認を行う
                    self.ascii_check(item)

                    # null チェック
                    self.column_null_check(item)

                    # 数値である場合は拡張子チェックに数字であることを追加
                    if self.number_check(item):
                        Extention.append('number')
                    # 数値でない場合は、対応している拡張子がついているか確認
                    elif os.path.splitext(item)[1] in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', 'tiff']:
                        Extention.append(os.path.splitext(item)[1])
                    elif os.path.splitext(item)[1] in ['.csv']:
                        Extention.append(os.path.splitext(item)[1])
                        self.check_plot_csv_data(item)

                # 3行目以降のデータが2行目のデータ形式と同じか確認
                csv_list_comparison = csv_list[2:len(csv_list)]
                record_count = 3
                for row in csv_list_comparison:
                    Extention_count = 0
                    for item in row:

                        # 対応している文字コードか確認を行う
                        self.ascii_check(item)

                        # null チェック
                        self.column_null_check(item)

                        # 拡張子が2行目と同じか確認
                        if self.number_check(item):
                            if not Extention[Extention_count] is 'number':
                                self._log('data_extention is Disagreement {} line {} number is not {}'
                                          .format(record_count, (Extention_count + 1), Extention[Extention_count]))
                                raise Exception
                        elif os.path.splitext(item)[1] in ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tif', 'tiff']:
                            if not os.path.splitext(item)[1] == Extention[Extention_count]:
                                self._log('data_extention is Disagreement {} line {} {} is not {} '
                                          .format(record_count, (Extention_count + 1), os.path.splitext(item)[1],
                                                  Extention[Extention_count]))
                                raise Exception
                        elif os.path.splitext(item)[1] in ['.csv']:
                            if not os.path.splitext(item)[1] == Extention[Extention_count]:
                                self._log('data_extention is Disagreement {} line {} {} is not {} '
                                          .format(record_count, (Extention_count + 1), os.path.splitext(item)[1],
                                                  Extention[Extention_count]))
                                raise Exception
                            self.check_plot_csv_data(item)

                        else:
                            self._log('data_extention is Disagreement {} line {} {} is not {} '
                                      .format(record_count, (Extention_count + 1), os.path.splitext(item)[1],
                                              Extention[Extention_count]))
                            raise Exception
                        Extention_count = Extention_count + 1
                        # 1行処理毎にカウントをあげる
                    record_count = record_count + 1
        except Exception:
            raise Exception

    def createCsvData(self, csvfilename):
        data_files = {}
        csv_data = []
        num_of_data_files = 0

        try:
            if os.path.exists(csvfilename):
                with open(csvfilename, 'r') as f:
                    csv_lines = f.readlines()
                    self.check_csv_data(csvfilename)
                    linecount = 0

                    num_of_items = -1
                    csvreader = csv.reader(csv_lines)

                    self._progress.init(len(csv_lines), 'Create CSV')

                    for row in csvreader:

                        self._progress(1.0)

                        # Validate
                        if linecount == 0:  # Header
                            num_of_items = len(row)
                            for item in row:
                                self.ascii_check(item)

                        else:  # Data
                            if num_of_items != len(row):
                                self._log(
                                    'invalid line {} in csv file.'.format(linecount))
                                return None, None

                        new_row = []
                        for item in row:
                            data_file = None
                            if os.path.isfile(item):
                                data_file = item
                            else:
                                fn = '/'.join([os.path.dirname(
                                    csvfilename), '/'.join(item.split('\\'))])
                                if os.path.isfile(fn):
                                    data_file = fn

                            if data_file is not None:
                                name = '/'.join(['data', '{:012d}_{}'.format(
                                    num_of_data_files, os.path.splitext(data_file)[1])])
                                data_files[name] = os.path.abspath(data_file)
                                new_row.append(name)
                                num_of_data_files += 1
                            else:
                                new_row.append(item)
                        csv_data.append(new_row)
                        linecount += 1
                    self._progress.finish()
            else:
                self._log("upload file not found")
                raise Exception
            return csv_data, data_files
        except Exception:
            raise Exception

    def createTemporaryTar(self, name, csv_data, data_files, tmpdir):
        indexcsvfilename = os.path.join(tmpdir, 'index.csv')

        self._log('Create index.csv')
        self._progress.init(len(csv_data), 'Create index.csv')
        with open(indexcsvfilename, 'w') as f:
            for row in csv_data:
                self._progress(1.0)
                f.write(','.join(row) + '\n')
        self._progress.finish()

        tarfilename = os.path.join(tmpdir, '{}.tar'.format(name))

        self._log('Add file to tar archive.')
        self._progress.init(len(data_files), 'Create TAR')
        with tarfile.open(tarfilename, 'w') as tar:
            tar.add(indexcsvfilename, 'index.csv')
            for datafile in sorted(data_files.keys()):
                self._progress(1.0)
                tar.add(data_files[datafile], datafile)
        self._progress.finish()

        return tarfilename

    def uploadFile(self, endpoint, token, filename, name):
        size = os.path.getsize(filename)
        if endpoint == 'https://console-api.dl.sony.com':
            self._log('Getting Upload path')
        else:
            self._log('Getting Upload path from [{}]'.format(endpoint))
        try:
            r = requests.get('{}/v1/misc/credential'.format(endpoint),
                             params={
                                 'encrypted_text': token,
                                 'dataset_name': name,
                                 'dataset_size': size})
        except OSError:
            self._log("get credential error")
            raise Exception

        info = r.json()

        if 'upload_path' not in info:
            if endpoint == 'https://console-api.dl.sony.com':
                self._log('ERROR! Upload_path could not be retrieved from the server.')
            else:
                self._log('ERROR! Server returns [{}]'.format(info['message']))
            raise Exception

        upload_url = info['upload_path']
        if endpoint == 'https://console-api.dl.sony.com':
            self._log('Got upload_url')
        else:
            pass

        bucketname, key = upload_url.split('://', 1)[1].split('/', 1)
        upload_key = '{}/{}.tar'.format(key, name)

        s3 = boto3.session.Session(aws_access_key_id=info['access_key_id'],
                                   aws_secret_access_key=info['secret_access_key'],
                                   aws_session_token=info['session_token']).client('s3')
        tc = boto3.s3.transfer.TransferConfig(
            multipart_threshold=10 * 1024 * 1024,
            max_concurrency=10)
        t = boto3.s3.transfer.S3Transfer(client=s3, config=tc)

        self._progress.init(os.path.getsize(filename), 'Upload')
        t.upload_file(filename, bucketname, upload_key,
                      callback=self._progress)
        self._progress.finish()

        return True

    def __init__(self,
                 log,
                 token=None,
                 progress=None):
        self._log = log
        self._progress = progress

    def convert(self, source, destination):
        tmpdir = tempfile.mkdtemp()
        self._log('Temprary dir {} created'.format(tmpdir))

        try:
            self._log('Prepare csv data')
            csv_data, data_files = self.createCsvData(source)
            if csv_data is not None:
                self._log('Prepare tar file')
                name = os.path.splitext(os.path.basename(source))[0]
                tarfile = self.createTemporaryTar(name,
                                                  csv_data,
                                                  data_files,
                                                  tmpdir)
                shutil.copyfile(tarfile, destination)
        except Exception:
            raise Exception
        finally:
            shutil.rmtree(tmpdir, ignore_errors=True)
            self._log('Temprary dir removed')

    def upload(self, token, filename, name, finishCallback=None, endpoint=None):
        _, ext = os.path.splitext(filename)
        if ext == '.csv':
            tmpdir = tempfile.mkdtemp()
            self._log('Temprary dir {} created'.format(tmpdir))

            try:
                self._log('Prepare csv data')
                csv_data, data_files = self.createCsvData(filename)
                if csv_data is not None:
                    self._log('Prepare tar file')
                    tarfile = self.createTemporaryTar(name,
                                                      csv_data,
                                                      data_files,
                                                      tmpdir)
                    self._log('Upload')
                    self.uploadFile(endpoint, token, tarfile, name)
            except Exception:
                raise Exception

            finally:
                shutil.rmtree(tmpdir, ignore_errors=True)
                self._log('Temprary dir removed')

        else:
            self._log('filename with extension {} is not supported.'.format(ext))
            if finishCallback is not None:
                finishCallback(False)
            raise Exception

        if finishCallback is not None:
            finishCallback(True)


class Progress:
    def __init__(self):
        self._lock = threading.Lock()
        self._pbar = None

    def __call__(self, amount):
        with self._lock:
            if self._pbar is not None:
                self._pbar.update(amount)

    def init(self, maximum, label):
        if self._pbar is not None:
            self._pbar.close()
        self._pbar = tqdm.tqdm(total=maximum, desc=label)

    def finish(self):
        self._pbar.close()


def log(string):
    print(string)


def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument('-e', '--endpoint',
                            help='set specific endpoint', type=str)
        parser.add_argument('token', help='token for upload')
        parser.add_argument('filename', help='filename to upload')

        args = parser.parse_args()
        if not args.endpoint:
            args.endpoint = os.getenv(
                "NNC_ENDPOINT", 'https://console-api.dl.sony.com')

        uploader = Uploader(log=log, progress=Progress())
        name = os.path.splitext(os.path.basename(args.filename))[0]
        uploader.upload(args.token, args.filename, name,
                        endpoint=args.endpoint)
        log("upload Finished")
    except Exception:
        log("upload Failed")


if __name__ == '__main__':
    print('Uploader Script ({})'.format(versionString))
    main()
