import sys
import os

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), 'modules')))
import logging
import requests                 #simple HTTP library
import loghelper
import confighelper
import cgi
# print("7")
# sys.stdout.flush()


logger = logging.getLogger(__name__)
tabbed_logger = loghelper.TabbedAdapter(logger, {})
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)


url_telegram_api= 'https://api.telegram.org/bot#BOTID#/sendMessage'
url_pushbullet_api= 'https://api.pushbullet.com/v2/pushes'

##############################################################
######                  NOTIFICATIONS                   ######      
##############################################################           

def send_pushbulltet_notification(access_token, title, message):
    pushbullet_errors={
        400:"A parameter may be missing.",
        401:"Provided API token may be invalid.",
        403:"The access token is not valid for that request.",
        404:"The requested item doesn't exist.",
        429:"You have been ratelimited for making too many requests to the server.",
        500:"Something went wrong on Pushbullet's side."
    }
    headers = {'content-type': 'application/json',
               'Access-Token': access_token}
    push={"type": "note",
          "title": title,
          "body": message}
    tabbed_logger.debug("Send PushBullet notification",tab=2)
    tabbed_logger.debug("%s\n%s" % (title,message),tab=3)
    try:
        resp=requests.post(url_pushbullet_api,headers=headers,json=push)
        if resp.status_code>200:
            tabbed_logger.warning("An error occured while sending notification : %s (HTTP %i)" % (pushbullet_errors[resp.status_code if resp.status_code<500 else 500],resp.status_code),tab=2)
            
    except Exception as e:
        tabbed_logger.warning("An error occured while sending notification",tab=2)
        tabbed_logger.warning(e,tab=2)
        
        
        
def send_telegram_notification(bot_id, recipient_id, message):
    url=url_telegram_api.replace("#BOTID#",bot_id)

    notification={
            'chat_id': recipient_id,
            'text': message,
            'parse_mode': 'HTML'
        }
    tabbed_logger.debug("Send Telegram notification",tab=2)
    tabbed_logger.debug("%s" % (url),tab=3)
    tabbed_logger.debug("%s" % (message),tab=3)
    try:
        resp=requests.post(url,data=notification)
        #tabbed_logger.debug("%s" % (resp.content),tab=3)
        if resp.status_code==401:
            tabbed_logger.warning("Telegram Bot ID is probably incorrect (HTTP %i)" % (resp.status_code),tab=2)
        elif resp.status_code==400:
            content=resp.json()
            tabbed_logger.warning("Recipient ID is probably incorrect (HTTP %i - %s)" % (resp.status_code,content["description"]),tab=2)
        elif resp.status_code>200:
            tabbed_logger.warning("An error occured while sending notification : HTTP %i" % (resp.status_code),tab=2)
            
    except Exception as e:
        tabbed_logger.warning("An error occured while sending notification",tab=2)
        tabbed_logger.warning(e,tab=2)
        
        
    
def send_notification(recipient_config, title,message):
    if recipient_config["provider"] == 'pushbullet':
        send_pushbulltet_notification(recipient_config["api_key"],title,message)
    elif recipient_config["provider"] == 'telegram':
        message=cgi.escape(message)
        message= "<b>%s</b>\n%s" % (title,message)        
        send_telegram_notification(recipient_config["bot_id"], recipient_config["recipient_id"], message)
    else:
        tabbed_logger.warning("*** No recipient list defined in the folder > notify configuration",tab=1)

    
def get_notifications_titles(notifications_config,folder_notifications_config):
    titles={
        'single':'A new FILETYPE has been synced.',
        'grouped':'New FILETYPEs have been synced.'
    }
    if "titles" not in notifications_config or not notifications_config["titles"]:
        tabbed_logger.warning("*** No notification titles defined in the notifications configuration. Fallback to default.",tab=1)
    else:
        if "single" not in notifications_config["titles"] or not notifications_config["titles"]["single"] or not isinstance(notifications_config["titles"]["single"],str):
            tabbed_logger.warning("*** No valid title for single notifications define in the notifications configuration. Fallback to default!",tab=1)
        else:
            titles["single"]=notifications_config["titles"]["single"]
         
        if "grouped" not in notifications_config["titles"] or not notifications_config["titles"]["grouped"] or not isinstance(notifications_config["titles"]["grouped"],str):
            tabbed_logger.warning("*** No valid title for grouped notifications define in the notifications configuration. Fallback to default!",tab=1)
        else:
            titles["grouped"]=notifications_config["titles"]["grouped"]
    
    if "title_prefix" in folder_notifications_config and folder_notifications_config["title_prefix"] and isinstance(folder_notifications_config["title_prefix"],str):
        titles["single"]="%s - %s" % (folder_notifications_config["title_prefix"],titles["single"])
        titles["grouped"]="%s - %s" % (folder_notifications_config["title_prefix"],titles["grouped"])
            
    return titles    

def send_notifications(files_list, notifications_config,folder_notifications):
    if not confighelper.is_folder_notifications_config_valid(folder_notifications):
        return

    if not confighelper.is_notifications_config_valid(notifications_config):
        return
    
    titles = get_notifications_titles(notifications_config,folder_notifications)
    
    files_list=[x.split("/")[-1] for x in files_list]
    
    files_list_by_type={}
    
    for filetype in notifications_config["filetypes"]:
        files_list_by_type[filetype]=[ x for x in files_list if os.path.splitext(x)[1] in notifications_config["filetypes"][filetype]]
    
    for recipient in folder_notifications["recipient"]:
        if recipient in notifications_config["recipients"]:
            recipient_config=notifications_config["recipients"][recipient]
            if confighelper.is_recipient_config_valid(recipient,recipient_config):
                tabbed_logger.debug("Send notifications to %s" % (recipient),tab=1)            
                for filetype_to_notify in folder_notifications["filetypes"]:
                    tabbed_logger.debug("Process notifications for filetype %s" % (filetype_to_notify),tab=1)
                    if filetype_to_notify in notifications_config["filetypes"]:
                        if len(files_list_by_type[filetype_to_notify]):
                            tabbed_logger.debug("File list for filetype %s - %s" % (filetype_to_notify,' -- '.join(files_list_by_type[filetype_to_notify])),tab=1)
                            notification_mode=folder_notifications["filetypes"][filetype_to_notify]
                            if notification_mode in ("single","grouped"):
                                title=titles[notification_mode].replace("FILETYPE",filetype_to_notify)
                                
                                if notification_mode=="single":
                                    tabbed_logger.info("Send single %s notifications to recipient %s" % (filetype_to_notify,recipient),tab=1)
                                    for file in files_list_by_type[filetype_to_notify]:
                                        send_notification(recipient_config,title,file)
                                elif notification_mode=="grouped": 
                                    tabbed_logger.info("Send grouped %s notification to recipient %s" % (filetype_to_notify,recipient),tab=1)
                                    msg='\n'.join(files_list_by_type[filetype_to_notify])
                                    send_notification(recipient_config,title,msg)
                            else:
                                tabbed_logger.warning("Notification mode for filetype %s incorrect. Should be 'single' or 'grouped'" % (filetype_to_notify),tab=1)
                    else:
                        tabbed_logger.warning("Can't find filetype %s in notification configuration" % (filetype_to_notify),tab=1)
            else:
                tabbed_logger.warning("Recipient %s configuration looks invalid" % (recipient),tab=1)
        else:
            tabbed_logger.warning("Can't find recipient %s in notification configuration" % (recipient),tab=1)
