import sys
from unittest import TestCase
from mock import patch

sys.path.append('../src/')
import uploader


class TestUploaderCheck(TestCase):
    def test_ascii_check(self):
        item = "1"
        test_result = True
        uploader_instance = uploader.Uploader(uploader.log)
        try:
            uploader_instance.ascii_check(item)
        except Exception as e:
            print(e)
            test_result = False

        self.assertTrue(test_result)

    def test_failed_ascii_check(self):
        item = "あ"
        test_result = True
        uploader_instance = uploader.Uploader(uploader.log)
        try:
            uploader_instance.ascii_check(item)
        except Exception:
            test_result = False

        self.assertFalse(test_result)

    def test_number_check(self):
        item = "1"
        uploader_instance = uploader.Uploader(uploader.log)

        self.assertTrue(uploader_instance.number_check(item))

    def test_failed_number_check(self):
        item = "a"
        uploader_instance = uploader.Uploader(uploader.log)

        self.assertFalse(uploader_instance.number_check(item))

    def test_csv_null_check(self):
        csv_path = "index.csv"
        test_result = True
        uploader_instance = uploader.Uploader(uploader.log)
        try:
            uploader_instance.csv_null_check(csv_path)
        except Exception:
            test_result = False

        self.assertTrue(test_result)

    def test_failed_csv_null_check(self):
        csv_path = "index_null.csv"
        test_result = True
        uploader_instance = uploader.Uploader(uploader.log)
        try:
            uploader_instance.csv_null_check(csv_path)
        except Exception:
            test_result = False

        self.assertFalse(test_result)

    def test_column_null_check(self):
        item = "1"
        test_result = True
        uploader_instance = uploader.Uploader(uploader.log)
        try:
            uploader_instance.column_null_check(item)
        except Exception:
            test_result = False

        self.assertTrue(test_result)

    def test_failed_column_null_check(self):
        item=""
        test_result = True
        uploader_instance = uploader.Uploader(uploader.log)
        try:
            uploader_instance.column_null_check(item)
        except Exception:
            test_result = False

        self.assertFalse(test_result)

    @patch('uploader.Uploader.csv_null_check')
    @patch('uploader.Uploader.ascii_check')
    @patch('uploader.Uploader.number_check')
    def test_check_plot_csv_data(self, csv_null_check_mock, ascii_check_mock, number_check_mock):
        csv_path = "data/test.csv"

        # csv_null_check_mock.return_value =""
        number_check_mock.return_value = True
        test_result = True
        uploader_instance = uploader.Uploader(uploader.log)
        try:
            uploader_instance.check_plot_csv_data(csv_path)
        except Exception as e:
            print(e)
            test_result = False

        self.assertTrue(test_result)

    @patch('uploader.Uploader.csv_null_check')
    @patch('uploader.Uploader.ascii_check')
    @patch('uploader.Uploader.number_check')
    def test_failed_check_plot_csv_data(self, csv_null_check_mock, ascii_check_mock, number_check_mock):
        csv_path = "data/error_test.csv"

        # csv_null_check_mock.return_value =""
        number_check_mock.return_value = True
        test_result = True
        uploader_instance = uploader.Uploader(uploader.log)
        try:
            uploader_instance.check_plot_csv_data(csv_path)
        except Exception:
            test_result = False

        self.assertFalse(test_result)

    @patch('uploader.Uploader.csv_null_check')
    @patch('uploader.Uploader.ascii_check')
    @patch('uploader.Uploader.number_check')
    @patch('uploader.Uploader.column_null_check')
    @patch('uploader.Uploader.check_plot_csv_data')
    def test_check_csv_data(self, csv_null_check_mock, ascii_check_mock,
                            number_check_mock, column_null_check_mock, check_plot_csv_data_mock):
        csv_path = "index.csv"

        # csv_null_check_mock.return_value =""
        number_check_mock.return_value = True
        test_result = True
        uploader_instance = uploader.Uploader(uploader.log)

        try:
            uploader_instance.check_csv_data(csv_path)
        except Exception as e:
            print(e)
            test_result = False

        self.assertTrue(test_result)

    @patch('uploader.Uploader.csv_null_check')
    @patch('uploader.Uploader.ascii_check')
    @patch('uploader.Uploader.number_check')
    @patch('uploader.Uploader.column_null_check')
    @patch('uploader.Uploader.check_plot_csv_data')
    def test_failed_check_csv_data(self, csv_null_check_mock, ascii_check_mock,
                                   number_check_mock, column_null_check_mock, check_plot_csv_data_mock):
        csv_path = "index_header_only.csv"

        # csv_null_check_mock.return_value =""
        number_check_mock.return_value = True
        test_result = True
        uploader_instance = uploader.Uploader(uploader.log)

        try:
            uploader_instance.check_csv_data(csv_path)
        except Exception:
            test_result = False

        self.assertFalse(test_result)
