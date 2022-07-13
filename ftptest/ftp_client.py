import io
from ftplib import FTP, error_perm
from pathlib import Path
import os
import traceback


class FtpInfo:
    def __init__(self, host, port, user, passwd, timeout=30, encoding='utf-8'):
        self.host = host
        self.port = port
        self.user = user
        self.passwd = passwd
        self.timeout = timeout
        self.encoding = encoding

    def __setattr__(self, name, value):
        if name in self.__dict__:
            raise Exception('immutable')
        self.__dict__[name] = value

    def __delattr__(self, name):
        if name in self.__dict__:
            raise Exception('immutable')

    def __str__(self):
        return str(self.__dict__)


class FtpClient:
    def __init__(self, ftp_info, debuglevel=0):
        self._ftp_info = ftp_info
        self._debuglevel = debuglevel
        self._ftp = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def connect(self):
        if self._ftp:
            raise Exception()

        try:
            self.check_ftp_info()
            self._ftp = FTP()
            self._ftp.encoding = self._ftp_info.encoding
            self._ftp.debugging = self._debuglevel
            self._ftp.connect(self._ftp_info.host, self._ftp_info.port, self._ftp_info.timeout)
            self._ftp.login(self._ftp_info.user, self._ftp_info.passwd)
            return self._ftp
        except Exception as e:
            raise e

    def get_connection(self):
        if self._ftp:
            return self._ftp
        return self.connect()

    def close(self):
        if not self._ftp:
            return

        try:
            self._ftp.quit()
        except Exception:
            pass
        finally:
            self._ftp.close()
            self._ftp = None

    def check_ftp_info(self):
        pass

    def _mkdir_recur(self, arg_dir_path):
        if not arg_dir_path:
            return
        try:
            self._ftp.cwd(arg_dir_path)
        except error_perm:
            end_idx = arg_dir_path.rfind('/')
            if end_idx > -1:
                self._mkdir_recur(arg_dir_path[:end_idx])
            self._ftp.mkd(arg_dir_path)

    def make_dirs(self, ftp_dir_path, ignore_exists=True):
        pwd = self._ftp.pwd()
        try:
            if not ignore_exists:
                try:
                    self._ftp.cwd(ftp_dir_path)
                except error_perm as e:
                    if str(e)[:3] != '550':
                        raise
                else:
                    raise Exception('Directory already exists.')
            self._mkdir_recur(ftp_dir_path)
        finally:
            self._ftp.cwd(pwd)

    def is_file_exists(self, ftp_file_path):
        if not ftp_file_path:
            return False
        try:
            self._ftp.size(ftp_file_path)
        except error_perm as e:
            if str(e)[:3] == '550':
                return False
            raise
        return True

    def download_dirs(self, dir_path, ftp_dir_path):
        if not ftp_dir_path or not ftp_dir_path[0] == '/':
            raise ValueError("ftp_dir_path not start width '/'")

        try:
            lst = self._ftp.nlst(ftp_dir_path)
        except error_perm as e:
            if str(e)[:3] == '550':  # ftplib.error_perm: 550 Directory not found.
                return False
            raise

        ftp_dir_name = ftp_dir_path[ftp_dir_path.rfind('/')+1:]

        # empty dir 이면 디렉토리만 생성
        if len(lst) == 0:
            Path(dir_path + '/' + ftp_dir_name).mkdir(parents=True, exist_ok=True)
            return True

        for ftp_path in lst:
            # 절대경로로 변환
            if ftp_path and ftp_path[0] != '/':
                ftp_path = ftp_dir_path + '/' + ftp_path

            ftp_file_name = ftp_path[ftp_path.rfind('/')+1:]
            down_path = dir_path + '/' + ftp_dir_name + '/' + ftp_file_name
            try:
                self.retrieve_as_file(down_path, ftp_file_name, ftp_dir_path, overwrite=True)
            except PermissionError as e:
                if '[Errno 13]' in str(e):
                    # 주로 이미 다운받은 디렉토리를 동일한 경로에 다시 받으려고 하는경우 발생. 이경우 디렉토리 다운로드로 간주
                    print('########  ' + str(e))
                    self.download_dirs(dir_path + '/' + ftp_dir_name, ftp_path)
                    continue
                raise
            except error_perm as e:
                # file not found 디렉토리로 간주
                if str(e)[:3] == '550':
                    try:
                        os.remove(down_path)
                    except Exception:
                        pass
                    self.download_dirs(dir_path + '/' + ftp_dir_name, ftp_path)
                else:
                    raise
        return True

    def get_file_and_dir_path_list(self, ftp_dir_path=''):
        if not ftp_dir_path or not ftp_dir_path[0] == '/':
            raise ValueError("ftp_dir_path not start with '/'")

        try:
            lst = []
            self._ftp.dir(ftp_dir_path, lst.append)
            if not lst:
                return [], []
            ftp_path = Path(ftp_dir_path + '/{0}').as_posix()
            files, dirs = [], []
            for row in lst:
                '''
                '-': 일반(보통) 파일
                'd': 디렉토리
                'b': 블록 디바이스 파일
                'c': 문자열 디바이스 파일
                'l': 심볼릭 링크
                'p' or '=': 명명된 파이프 / FIFO
                's': 소켓
                '''
                file_or_dir_name = row.split(maxsplit=8)[8]
                if row[0] == 'd':
                    dirs.append(ftp_path.format(file_or_dir_name))
                elif row[0] == 'l':
                    r_idx = file_or_dir_name.rfind(' -> ')
                    if r_idx > -1:
                        file_or_dir_name = file_or_dir_name[:r_idx + 1]
                    files.append(ftp_path.format(file_or_dir_name))
                else:
                    files.append(ftp_path.format(file_or_dir_name))
            return files, dirs
        except Exception as e:
            raise Exception('ftp server not support \'get_file_and_dir_path_list\' function. nested: ' + str(e)) from e

    def store_file(self, file_path, ftp_file_name, ftp_dir_path=''):
        self.make_dirs(ftp_dir_path)
        with open(file_path, 'rb') as file:
            self._ftp.storbinary('STOR ' + ftp_dir_path + '/' + ftp_file_name, file)

    def store_bytes_id(self, bytes_io_src, ftp_file_name, ftp_dir_path=''):
        try:
            self.make_dirs(ftp_dir_path)
            self._ftp.storbinary('STOR ' + ftp_dir_path + '/' + ftp_file_name, bytes_io_src)
        except Exception as e:
            raise Exception('error cmd: {0}'.format('STOR ' + ftp_dir_path + '/' + ftp_file_name)) from e

    def store_bytes(self, bytes_src, ftp_file_name, ftp_dir_path=''):
        bio = None
        try:
            bio = io.BytesIO(bytes_src)
            self.store_bytes_id(bio, ftp_file_name, ftp_dir_path)
        finally:
            if bio:
                bio.close()

    def store_string(self, str_cont, ftp_file_name, ftp_dir_path=''):
        self.store_bytes(bytes(str_cont, self._ftp.encoding), ftp_file_name, ftp_dir_path)

    def retrieve_as_file(self, file_path, ftp_file_name, ftp_dir_path='', overwrite=False):
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'wb' if overwrite else 'xb') as file:
            self._ftp.retrbinary('RETR ' + ftp_dir_path + '/' + ftp_file_name, file.write)

    def retrieve_as_bytes_io(self, ftp_file_name, ftp_dir_path=''):
        bio = io.BytesIO()
        self._ftp.retrbinary('RETR ' + ftp_dir_path + '/' + ftp_file_name, bio.write)
        return bio

    def retrieve_as_bytes(self, ftp_file_name, ftp_dir_path=''):
        bio = None
        try:
            bio = self.retrieve_as_bytes_io(ftp_file_name, ftp_dir_path)
            if bio:
                return bio.getvalue()
        finally:
            if bio:
                bio.close()

    def retrieve_as_string(self, ftp_file_name, ftp_dir_path=''):
        byte_arr = self.retrieve_as_bytes(ftp_file_name, ftp_dir_path)
        if not byte_arr:
            return None
        return byte_arr.decode(self._ftp.encoding)


if __name__ == '__main__':
    from datetime import datetime

    my_ftp_info = FtpInfo('localhost', 21, 'kksftp', 'kksftp')
    with FtpClient(my_ftp_info, 0) as ftp:
        print('connected.')
        # ftp.store_string(str(datetime.now()) + ' test', 'test.txt', '/test/aaa')
        print(ftp.retrieve_as_string('test.txt', '/test/aaa'))
        print('is file /test/aaa/test.txt exist?', ftp.is_file_exists('/test/aaa/test.txt'))
        print('is file /test/aaa/test1.txt exist?', ftp.is_file_exists('/test/aaa/test1.txt'))
        ftp.download_dirs('f:/ftp/temp/download_dir_test', '/')
        print(ftp.get_file_and_dir_path_list('/test'))

