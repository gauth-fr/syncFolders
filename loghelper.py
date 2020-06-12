import os
import logging
import logging.handlers   
import shutil                   #to copy/move files
from datetime import datetime   #date formatting
import time



class TabbedAdapter(logging.LoggerAdapter):

    def process(self, msg, kwargs):
        indent=0
        if "tab" in kwargs:
            indent=kwargs["tab"]
            del kwargs["tab"]
        output=""
        if type(msg) is not str:
            msg=str(msg)
        for line in msg.splitlines():
            output+='{i}{m}\n'.format(i='    '*indent, m=line)
        output.rstrip("\n")
        return output, kwargs

class MultilineFormatter(logging.Formatter):
    def format(self, record):
        save_msg = record.msg
        output = ""

        if type(save_msg) is not str:
            save_msg=str(save_msg)
            
        for line in save_msg.splitlines():
            record.msg = line
            output += super(MultilineFormatter,self).format(record) + "\n"
        record.msg = save_msg
        record.message = output.rstrip("\n")
        return output.rstrip("\n")
  


def archive_logs(logs_directory, archive_directory,rsync_rc=255):
    logger = logging.getLogger("archive")
    tabbed_logger = TabbedAdapter(logger, {})  
    files_list = [f for f in os.listdir(logs_directory) if "output" in f]
    if files_list:
        current_sync=files_list[0].split('.')[1]
        sync_enddate=datetime.now().strftime("%Y%m%d%H%M%S")
        archive_output_file=os.path.join(archive_directory,"output.%s.%s.log" %(sync_enddate,current_sync))
        archive_rc_file=os.path.join(archive_directory,"rc.%s.%s.log" %(sync_enddate,current_sync))
        tabbed_logger.info("Archiving logs to %s" % archive_output_file,tab=1)
        shutil.move(os.path.join(logs_directory,files_list[0]), archive_output_file)
        with open(archive_rc_file,"w") as f:
            f.write("%s" % str(rsync_rc))

def purge_logs(archive_directory):
    now = time.time()
    for f in os.listdir(archive_directory):
        f=os.path.join(archive_directory, f)
        if os.stat(f).st_mtime < now - 7 * 86400:
            if os.path.isfile(f):
                os.remove(f)