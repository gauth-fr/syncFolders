#! /usr/bin/python2.7

import subprocess               #to run an command
import os                       #various functions related to the OS (path, pid...)
import tempfile                 #to get temp dir
import logging
import signal

import loghelper
import notification

logger = logging.getLogger(__name__)
tabbed_logger = loghelper.TabbedAdapter(logger, {})

   
def parse_output_file(log_file,target):
    files_list=[]
    
    with open(log_file, "r") as file:
        #print("readfile")
        line = file.readline() 
        starting_pattern= "<f" if target=="remote" else ">f"
        #print("starting_pattern %s" % starting_pattern)
        while line:
            #print line
            if starting_pattern in line:
                #print line
                attributes,leftover = line.strip().split(' ',1)
                filename,size = leftover.strip().rsplit(' ',1)
               
                line = file.readline()
                progress=line.split('\r')[-1].strip().split()[1]
                if progress=="100%":
                    files_list.append(filename)
                    tabbed_logger.info("File: %s (%s)" %(filename.split("/")[-1],progress),tab=2)
                    
            line = file.readline()
    return files_list

def execute_postcommand(files_list, folder_config):
    tabbed_logger.info("Post-processing %i copied files" % len(files_list),tab=1)
    
    source_command=None
    if "source_postcommand" in folder_config and folder_config["source_postcommand"]:
        if folder_config["target_is"]=="remote":
            source_command=folder_config["source_postcommand"]
        else:
            source_command="ssh -p %s %s@%s '%s'" % (folder_config["server"]["port"],folder_config["server"]["user"],folder_config["server"]["ip"],folder_config["source_postcommand"])
    
    target_command=None
    if "target_postcommand" in folder_config and folder_config["target_postcommand"]:
        if folder_config["target_is"]=="remote":
            target_command="ssh -p %s %s@%s '%s'" % (folder_config["server"]["port"],folder_config["server"]["user"],folder_config["server"]["ip"],folder_config["target_postcommand"])
        else:
            target_command=folder_config["target_postcommand"]

    tabbed_logger.info("Source post command %s" % source_command,tab=2)
    tabbed_logger.info("Target post command %s" % target_command,tab=2)
    for file in files_list:
        tabbed_logger.info("Processing file : %s" % file,tab=2)
        
        if source_command:
            complete_filename="%s/%s" % (folder_config["source"].rsplit('/', 1)[0],file)
            complete_escaped_filename="'%s'" % complete_filename.replace("'","'\"'\"'")
            
            escaped_base_dir="'%s'" % folder_config["source"].replace("'","'\"'\"'")
            
            complete_command=target_command.replace("FILE",complete_escaped_filename)
            complete_command=complete_command.replace("BASEDIR",escaped_base_dir)
            tabbed_logger.debug("Source command : %s" % complete_command,tab=3)
            try:
                output=subprocess.check_output(complete_command,stderr=subprocess.STDOUT,shell=True)
                tabbed_logger.debug("Completed successfully",tab=4)
                tabbed_logger.debug(output,tab=4)
            except subprocess.CalledProcessError as e:
                tabbed_logger.error("Source command finished with return code %i" % (e.returncode) ,tab=3)
                tabbed_logger.debug(e.output ,tab=3)
            
        if target_command:
            complete_filename="%s/%s" % (folder_config["target"],file)
            complete_escaped_filename="'%s'" % complete_filename.replace("'","'\"'\"'")
            
            escaped_base_dir="'%s'" % folder_config["target"].replace("'","'\"'\"'")
            
            complete_command=target_command.replace("FILE",complete_escaped_filename)
            complete_command=complete_command.replace("BASEDIR",escaped_base_dir)
            tabbed_logger.debug("Target command : %s" % complete_command,tab=3)
            try:
                output=subprocess.check_output(complete_command,stderr=subprocess.STDOUT,shell=True)
                tabbed_logger.debug("Completed successfully",tab=4)
                tabbed_logger.debug(output,tab=4)
            except subprocess.CalledProcessError as e:
                tabbed_logger.error("Target command finished with return code %i" % (e.returncode) ,tab=3)
                tabbed_logger.debug(e.output ,tab=3)
            
    
def sync_folder(folder_config,notifications_config,log_directory,archive_directory):
    tabbed_logger.info(folder_config["title"],tab=0)
        
    if folder_config["target_is"]=="remote":
        source=folder_config["source"]
        target="%s@%s:%s" % (folder_config["server"]["user"],folder_config["server"]["ip"],folder_config["target"])
    else:
        source="%s@%s:%s" % (folder_config["server"]["user"],folder_config["server"]["ip"],folder_config["source"])
        target=folder_config["target"]
    
    tabbed_logger.info("Sync %s --> %s" % (source,target),tab=1)
    
    command="rsync -avPi --no-perms --out-format='%%i %%n%%L %%l' -e 'ssh -p %s' %s %s" % (folder_config["server"]["port"],
                                                                                source,
                                                                                target)
    tabbed_logger.debug("%s" % command,tab=1)
    #return
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,preexec_fn=os.setsid)

    log_filename="output.%s.log" % folder_config["title"].replace(" ","_")
    log_file=os.path.join(log_directory,log_filename)
    try:
        
        log_desc=open(log_file, "w")

        cmd_output=""
        while True:
            output = p.stdout.read(1)
            if output == '' and p.poll() is not None:
                break
            if output:
                cmd_output+=output
                log_desc.write(output)
                log_desc.flush()

        rc = p.poll()
        if rc>0 :
            tabbed_logger.debug("Errors occured furing the sync (Rsync RC:%s). Check the log file." % str(rc),tab=1)
        else:
            tabbed_logger.debug("Sync completed (RC:%s)" % str(rc),tab=1)
    except Exception as e:
        tabbed_logger.warning("Sync has been interrupted",tab=1)
        tabbed_logger.warning(e,tab=1)
        rc=40
        if p.poll() is None:
            tabbed_logger.warning("Rsync still alive - Send SIGTERM to %s" % str(p.pid))
            os.killpg(os.getpgid(p.pid), signal.SIGTERM)
            rc=143
        
        raise
    finally:
        log_desc.close()
        files_copied=parse_output_file(log_file,folder_config["target_is"])
        tabbed_logger.info("%i files successfully copied" % len(files_copied),tab=1)
        if len(files_copied)>0 and ("source_postcommand" in folder_config or "target_postcommand" in folder_config) :
            execute_postcommand(files_copied,folder_config)
        
        if len(files_copied)>0 and "notify" in folder_config and folder_config["notify"] :
            notification.send_notifications(files_copied,notifications_config,folder_config["notify"])
        loghelper.archive_logs(log_directory,archive_directory,rc)
  
  

