import ftplib
import os

class Ftp:
    """wrapper of ftplib.FTP"""
    def __init__(self, encoding='euc-kr'):
        self._ftp = ftplib.FTP()
        self._ftp.encoding = encoding
        self._connection_info = {'host': '', 'port': 21,
                                'username': '', 'passwd': ''}
        self._connected = False
        self._noconnection_testmode = False
    
    def __del__(self):
        self._ftp.close()
        
    def set_noconnection_testmode(self, value):
        self._noconnection_testmode = value
    
    def setConnectionInfo(self, host, port, username, passwd):
        self._connection_info['host'] = host
        self._connection_info['port'] = port
        self._connection_info['username'] = username
        self._connection_info['passwd'] = passwd
    
    def connectAndLogin(self):
        """
        return 0: success
        return 1: failed
        """
        try:
            self.__connect()
        except Exception as err:
            print('failed: connect to ftp.', str(self._connection_info))
            print('    exception: %s' % str(err))
            return 1
        
        try:
            self.__login()
        except Exception as err:
            print('failed: login to ftp.', str(self._connection_info))
            print('    exception: %s' % str(err))
            return 1
        
        self._connected = True
        return 0
    
    def makeDirAtFtp(self, base_ftppath, dir_for_make):        
        """
        param base_ftppath: First, move to here.
        param dir_for_make: for making
        return dirname: success making dir
        return '': failed making dir
        """
        if not self._connected:
            print('failed make dir: not connected to ftp')
            return ''
        
        try:
            self.__cwd(base_ftppath)
        except Exception as err:
            print('failed make dir: change base_ftppath=' + base_ftppath)
            print('    exception: %s' % str(err))
            return ''
        
        try:
            self.__mkd(dir_for_make)
        except Exception as err:
            print('failed make dir: may be already exist. cannot make dir=' + \
                  dir_for_make + ', at ftppath=' + base_ftppath)
            return ''
        
        return dir_for_make
            
    def uploadToFTP(self, targetpath, ftppath):
        """
        return 0: success
        return 1: failed        
        """
        print('-- uploading target=%s --' % targetpath)
        if not self._connected:
            print('failed: not connected to ftp')
            return 1
        
        try:
            self.__cwd(ftppath)
        except Exception as err:
            print('failed: change ftppath=%s' % ftppath)
            print('    exception: %s' % str(err))
            return 1
        
        if os.path.isfile(targetpath):
            filename = targetpath.split('/')[-1]
            try:            
                with open(targetpath, 'rb') as fd:
                    cmd = 'stor %s' % filename
                    try:
                        self.__storbinary(cmd, fd)
                    except ftplib.all_errors as err:
                        print('failed: ftp.storbinary')
                        print('    exception: %s' % str(err))
                        return 1
                    print('upload ok : target=%s -> ftp=%s' % \
                          (targetpath, ftppath + '/' + filename))
            except IOError as err:
                print('failed: cannot open file=%s for upload' % targetpath)
                print('    exception: %s' % str(err))
                return 1
        elif os.path.isdir(targetpath):            
            copy_dir_mode = False
            work_dir = '.'  
            copy_dir_mode_targetname = targetpath          
            
            targetpath_rsplited = targetpath.rsplit('/', 1)
            if len(targetpath_rsplited) == 1:
                # upload dir
                # targetpath like 'dir'
                copy_dir_mode = True
                work_dir = '.'
                copy_dir_mode_targetname = targetpath_rsplited[-1]
            elif len(targetpath_rsplited) == 2:                
                if '' == targetpath_rsplited[-1]:
                    # targetpath like 'dir/' or '/'
                    # upload files
                    copy_dir_mode = False
                    work_dir = targetpath_rsplited[0]
                    if '' == work_dir:
                        work_dir = '/'
                else:
                    # targetpath like '.../dir'
                    # upload dir
                    copy_dir_mode = True
                    work_dir = targetpath_rsplited[0]
                    copy_dir_mode_targetname = targetpath_rsplited[-1]
            else:
                print('failed: targetpath rsplit. targetpath=%s' % targetpath)
                return 1    
            
            # set work dir
            backup_cur_dir = os.getcwd()                    
            try:
                os.chdir(work_dir)
            except Exception as err:
                print('failed: change cur dir to workdir=%s' % \
                      work_dir)
                print('    exception: %s' % str(err))
                return 1                        
            
            # upload process
            if copy_dir_mode:
                # upload dir
                if self.__uploadTargetToCurFtpPathByRecursive(
                        copy_dir_mode_targetname) != 0:
                    return 1
            else:
                # upload files
                for each_target in os.listdir():
                    if self.__uploadTargetToCurFtpPathByRecursive(
                            each_target) != 0:
                        return 1
            
            # rollback work dir
            os.chdir(backup_cur_dir)
        else:
            print('failed: wrong targetpath=%s' % targetpath)
            return 1
        return 0
    
    def deleteDirForce(self, dir_path):
        """
        return 0: success
        return 1: failed
        """
        if not self._connected:
            print('failed: not connected to ftp')
            return 1
        
        if dir_path[-1] == '/':
            dir_path = dir_path[:-1]
        if dir_path == '':
            return 1
        
        backup_ftp_path = self.__pwd()
        self.__cwd(dir_path)        
        clear_dir_result = self.__clearDirForce('.')
        self.__cwd(backup_ftp_path)
        if clear_dir_result != 0:
            print('failed: clear dir={0}'.format(dir_path))
            return 1
        
        try:
            self.__rmd(dir_path)
        except Exception as err:
            print(str(err))
            return 1
        
        return 0
    
    def __clearDirForce(self, dir_path):
        """
        return 0: success
        return 1: failed
        """
        file_list = self._ftp.nlst(dir_path)
        if len(file_list) == 0:
            return 0
        for each_file in file_list:
            each_file_path = dir_path+'/'+each_file
            try:
                self._ftp.delete(each_file_path)
                continue
            except Exception as err:
                print(str(err))
                
            try:
                self.__rmd(each_file_path)
                continue
            except Exception as err:
                print(str(err))
            
            if self.__clearDirForce(each_file_path) != 0:
                print('error: __deleteDirForce')
                return 1
            
            try:
                self.__rmd(each_file_path)
                continue
            except Exception as err:
                print(str(err))
                return 1
        return 0
    
    def __uploadTargetToCurFtpPathByRecursive(self, targetname):
        """
        param targetname: not path. filename or dirname in current local dir.
        return 0: success
        return 1: failed
        """

        if os.path.isfile(targetname):
            filepath = os.getcwd() + '/' + targetname
            try:            
                with open(filepath, 'rb') as fd:
                    cmd = 'stor %s' % targetname
                    try:
                        self.__storbinary(cmd, fd)
                    except ftplib.all_errors as err:
                        print('failed: ftp.storbinary')
                        print('    exception: %s' % str(err))
                        return 1
                    print('upload ok : target=%s -> ftp=%s' % \
                          (filepath, self.__pwd() + '/' + targetname))
            except IOError as err:
                print('failed: cannot open file=%s for upload' % filepath)
                print('    exception: %s' % str(err))
                return 1
        elif os.path.isdir(targetname):
            # backup work dir
            backup_cur_dir = os.getcwd()
            backup_ftp_dir = self.__pwd()
            
            # try make target dir
            try:
                self.__mkd(targetname)
            except Exception as err:
                print('    exception: %s' % str(err))
                print('failed: make ftp dir=%s in cur ftppath=%s' % \
                      (targetname, backup_ftp_dir))

            # change work dir to target dir
            # ftp dir
            try:
                self.__cwd(targetname)
            except Exception as err:
                print('failed: change ftp dir=%s. in cur ftppath=%s' % \
                      (targetname, backup_ftp_dir))
                print('    exception: %s' % str(err))
                return 1
            # os dir
            try:
                os.chdir(targetname)
            except Exception as err:
                print('failed: change dir=%s. in cur path=%s' % \
                      (targetname, backup_cur_dir))
                print('    exception: %s' % str(err))
                return 1
            
            for each_targetname in os.listdir():
                if self.__uploadTargetToCurFtpPathByRecursive(each_targetname) != 0:
                    return 1
            
            # rollback work dir
            os.chdir(backup_cur_dir)
            self.__cwd(backup_ftp_dir)
        else:
            print('failed: wrong target=%s' % targetname)
            return 1
                    
        return 0        
    
    def __connect(self):
        if self._noconnection_testmode:
            return ''
        self._ftp.connect(self._connection_info['host'],
                       self._connection_info['port'])
        
    def __login(self):
        if self._noconnection_testmode:
            return ''
        return self._ftp.login(self._connection_info['username'],
                               self._connection_info['passwd'])
    
    def __cwd(self, ftppath):
        if self._noconnection_testmode:
            return ''
        return self._ftp.cwd(ftppath)
        
    def __storbinary(self, cmd, fd):
        if self._noconnection_testmode:
            return ''
        return self._ftp.storbinary(cmd, fd)
    
    def __pwd(self):
        if self._noconnection_testmode:
            return ''
        return self._ftp.pwd()
        
    def __mkd(self, dirname):
        if self._noconnection_testmode:
            return ''
        return self._ftp.mkd(dirname)
    
    def __rmd(self, dir_name):
        if self._noconnection_testmode:
            pass
        else:
            self._ftp.rmd(dir_name)
