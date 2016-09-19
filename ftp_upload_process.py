import json
import time
from kinoFtp import Ftp
import re
import sys
import os
    
class NameMaker:
    """Make name by format.
    """    
    def __init__(self):
        self.name_format = ''
        self.seq_value_list = []
        self.seq_value_list_index = 0        
    
    def setNameFormat(self, name_format):
        """Format can have some macro
        macro {year}, {mon}, {day}: ex) {year}_{mon}_{day} -> 2012_01_01
        macro {seq}: sequence addition. first you have to set sequence value list
            by func setSeqValueList()
        """
        self.name_format = name_format
        
    def setSeqValueList(self, value_list):
        self.seq_value_list = value_list
        self.seq_value_list_index = 0
        
    def hasSeqMacro(self):
        return re.match('.*{seq}.*', self.name_format) != None
        
    def setNextSeqValueListIndex(self):
        """
        return: changed index.
        return 0: failed 
        """
        if (self.seq_value_list_index + 1) >= len(self.seq_value_list):
            return 0
        
        self.seq_value_list_index += 1
        
        return self.seq_value_list_index    
        
    def getDirName(self):
        local_time = time.localtime()
        return self.name_format.format(year=local_time.tm_year, 
                                                  mon='%02d' % local_time.tm_mon,
                                                  day='%02d' % local_time.tm_mday,
                                                  seq=self.getSeqValue())
        
    def getSeqValue(self):
        return self.seq_value_list[self.seq_value_list_index]    
    

#env_json = 'upload_info.json'

if len(sys.argv) != 2:
    print('args : (json env filepath)')
    exit()
    
env_json = sys.argv[1]
if not os.path.isfile(env_json):
    print('args : (json env filepath)')
    exit()

ftp_host = ''
ftp_port = 21
ftp_user_name = ''
ftp_user_passwd = ''
uploads = []

try:
    with open(env_json, 'r') as conn_file:
        jobj = json.load(conn_file)
        
        ftp_host = jobj['ftp_host']
        ftp_port = jobj['ftp_port']
        ftp_user_name = jobj['ftp_username']
        ftp_user_passwd = jobj['ftp_passwd']
        uploads = jobj['uploads']        
except IOError as err:
    print(str(err))
    exit()

print('== begin : ftp upload process ==')

ftp = Ftp()
ftp.setConnectionInfo(ftp_host, ftp_port, ftp_user_name, ftp_user_passwd)
if ftp.connectAndLogin() != 0:
    print('failed: connect to ftp')
    exit()
    
print('==== begin : ftp upload ====')

failed_uploading_fileinfo = []

for each_upload in uploads:
    upload_base_ftp_dir = each_upload['base_ftp_dir']
    if '' == upload_base_ftp_dir:
        upload_base_ftp_dir = '.'
    else:
        upload_base_ftp_dir_rsplited = upload_base_ftp_dir.rsplit('/', 1)
        if '' != upload_base_ftp_dir_rsplited[-1]:
            upload_base_ftp_dir += '/'
            
    upload_target_path = each_upload['target_path']
    upload_making_ftp_dir_format = each_upload['making_dir_format']
    
    maked_dir = ''
    if upload_making_ftp_dir_format != '':
        # upload target ftp dir name format
        uploading_dir = NameMaker()
        uploading_dir.setNameFormat(upload_making_ftp_dir_format)
        uploading_dir.setSeqValueList(['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 
                                       'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p',
                                       'q', 'r', 's', 't', 'u', 'v', 'w', 'x',
                                       'y', 'z'])
        
        # make upload target ftp dir    
        if uploading_dir.getDirName() != '':        
            while True:
                maked_dir = ftp.makeDirAtFtp(upload_base_ftp_dir, 
                                             uploading_dir.getDirName())
                if '' == maked_dir:
                    # failed make trp dir
                    if not uploading_dir.hasSeqMacro():
                        print('failed: make ftp dir='+uploading_dir.getDirName())
                        exit()
                    
                    if uploading_dir.setNextSeqValueListIndex() > 0:
                        print('change th best deep ftp dir name='+
                              uploading_dir.getDirName())
                        continue
                    else:
                        print('failed: make ftp dir='+uploading_dir.getDirName())
                        print('failed: setNextSeqValueListIndex') 
                        exit()
                break
    
    # upload files by ftplib - fast than wput.
    upload_result = ftp.uploadToFTP(upload_target_path, 
                                    upload_base_ftp_dir + 
                                        uploading_dir.getDirName())
    if upload_result != 0:
        print('failed: upload to ftp.')
        if ftp.deleteDirForce(upload_base_ftp_dir + maked_dir) != 0:
            print('failed: delete maked ftp dir={0}'.format(
                upload_base_ftp_dir + maked_dir))
        else:
            print('delete maked ftp dir={0}'.format(
                upload_base_ftp_dir + maked_dir))
        exit()

print('==== end : ftp upload ====')

if len(failed_uploading_fileinfo) > 0:
    print('==== upload files failed ====')
    print('-- faild file infos --')
    for each_fileinfo in failed_uploading_fileinfo:
        print(each_fileinfo)
else:
    print('==== upload files success ====')

print('== end: ftp upload process ==')
