import logging
import loghelper

logger = logging.getLogger(__name__)
tabbed_logger = loghelper.TabbedAdapter(logger, {})





def is_folder_config_valid(index_config,folder_config):
    ret=True
    if "title" not in folder_config or not folder_config["title"] or not isinstance(folder_config["title"],str):
        tabbed_logger.warning("Folder configuration %i - No title defined" % index_config,tab=0)
        ret= False
    
    if "server" not in folder_config or not folder_config["server"] or not isinstance(folder_config["server"],dict):
        tabbed_logger.warning("Folder configuration %i - No correct server defined" % index_config,tab=0)
        ret= False
    else:
        if "ip" not in folder_config["server"] or not folder_config["server"]["ip"] or not isinstance(folder_config["server"]["ip"],str):
            tabbed_logger.warning("Folder configuration %i - No correct IP or hostname defined for the server configuration" % index_config,tab=0)
            ret= False
        if "port" not in folder_config["server"] or not folder_config["server"]["port"] or not isinstance(folder_config["server"]["port"],str):
            tabbed_logger.warning("Folder configuration %i - No correct port defined for the server configuration" % index_config,tab=0)
            ret= False
        if "user" not in folder_config["server"] or not folder_config["server"]["user"] or not isinstance(folder_config["server"]["user"],str):
            tabbed_logger.warning("Folder configuration %i - No correct user defined for the server configuration" % index_config,tab=0)
            ret= False

    if "source" not in folder_config or not folder_config["source"] or not isinstance(folder_config["source"],str):
        tabbed_logger.warning("Folder configuration %i - No correct source folder defined" % index_config,tab=0)
        ret= False
    
    if "target" not in folder_config or not folder_config["target"] or not isinstance(folder_config["target"],str):
        tabbed_logger.warning("Folder configuration %i - No correct target folder defined" % index_config,tab=0)
        ret= False
    
    if "target_is" not in folder_config or not folder_config["target_is"] or not isinstance(folder_config["target_is"],str):
        tabbed_logger.warning("Folder configuration %i - No correct target_is defined" % index_config,tab=0)
        ret= False
    else:
        if folder_config["target_is"] not in ("local","remote"):
            tabbed_logger.warning("Folder configuration %i - target_is value should be in (local,remote)" % index_config,tab=0)
            ret= False
             
    return ret

 
def is_notifications_config_valid(notifications_config):
    ret=True
    if "filetypes"  not in notifications_config or not notifications_config["filetypes"]:
        tabbed_logger.warning("Notifications configuration - No filetypes list defined",tab=1)
        ret= False
    if not isinstance(notifications_config["filetypes"], dict):
        #print(type(notifications_config["filetypes"]))
        tabbed_logger.warning("Notifications configuration - filetypes shoud be a list of filetypes!",tab=1)
        ret= False
    
    if "recipients"  not in notifications_config or not notifications_config["recipients"]:
        tabbed_logger.warning("Notifications configuration - No recipients list defined",tab=1)
        ret= False
    if not isinstance(notifications_config["recipients"], dict):
        tabbed_logger.warning("Notifications configuration - recipients shoud be a list of recipients!",tab=1)
        ret= False
    
    return ret

def is_folder_notifications_config_valid(folder_notifications_config):
    ret=True
    if "recipient"  not in folder_notifications_config or not folder_notifications_config["recipient"]:
        tabbed_logger.warning("Folder Notifications configuration - No recipient list defined in the folder > notify configuration",tab=1)
        ret= False
    if not isinstance(folder_notifications_config["recipient"], list):
        tabbed_logger.warning("Folder Notifications configuration - The folder configuration > notify > recipient shoud be a list of recipients!",tab=1)
        ret= False
        
    if "filetypes" not in folder_notifications_config or not folder_notifications_config["filetypes"]:
        tabbed_logger.warning("Folder Notifications configuration - No filetypes to notify defined in the folder > notify configuration",tab=1)
        ret= False
    if not isinstance(folder_notifications_config["filetypes"],dict):
        tabbed_logger.warning("Folder Notifications configuration - The folder configuration > notify > filetypes shoud be a dictionnary (filetype_name:'single or grouped')",tab=1)
        ret= False
     
    return ret

def is_recipient_config_valid(recipient_name,recipient_config):
    ret=True
    if "provider" not in recipient_config or not recipient_config["provider"]:
        tabbed_logger.warning("Recepient configuration - No provider defined for recipient %s" % recipient_name,tab=1)
        ret= False
    
    if recipient_config["provider"]=="pushbullet":
        if "api_key" not in recipient_config or not recipient_config["api_key"] or not isinstance(recipient_config["api_key"],str):
            tabbed_logger.warning("Recepient configuration - No correct PushBullet API Key provided for recipient %s" % recipient_name,tab=1)
            ret= False
    elif recipient_config["provider"]=="telegram":
        if "bot_id" not in recipient_config or not recipient_config["bot_id"] or not isinstance(recipient_config["bot_id"],str):
            tabbed_logger.warning("Recepient configuration - No correct Telegram Bot ID provided for recipient %s" % recipient_name,tab=1)
            ret= False
        if "recipient_id" not in recipient_config or not recipient_config["recipient_id"] or not isinstance(recipient_config["recipient_id"],str):
            tabbed_logger.warning("Recepient configuration - No correct Telegram recipient_id provided for recipient %s" % recipient_name,tab=1)
            ret= False
    else:
        tabbed_logger.warning("Recepient configuration - Incorrect provider (%s) for recipient %s" %(recipient_config["provider"],recipient_name),tab=1)
        ret= False
    
    return ret