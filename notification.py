import os
import sys
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), 'modules')))
import logging
import requests                 #simple HTTP library
import loghelper
import cgi


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
        if resp.status_code>200:
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

def send_notifications(files_list, notifications_config,folder_notifications):
    files_list=[x.split("/")[-1] for x in files_list]
    videos_list=[ x for x in files_list if os.path.splitext(x)[1] in notifications_config["video_extensions"]]
    subtitles_list=[ x for x in files_list if os.path.splitext(x)[1] in notifications_config["subtitle_extensions"]]
    others_list=[ x for x in files_list if x not in subtitles_list and x not in videos_list]
    #print(others_list)
    for recipient in folder_notifications["recipient"]:
        if recipient in notifications_config["recipients"]:
            tabbed_logger.debug("Send notifications to %s" % (recipient),tab=1)
            recipient_config=notifications_config["recipients"][recipient]
            if len(videos_list)>0 and "video" in folder_notifications:
                title= "New videos synced" 
                if folder_notifications["title_prefix"]:
                    title="%s - %s" % (folder_notifications["title_prefix"],title)
                    
                if folder_notifications["video"]=="single":
                    tabbed_logger.info("Send single video notification to recipient %s" % recipient,tab=1)
                    title= "New video synced" 
                    if folder_notifications["title_prefix"]:
                        title="%s - %s" % (folder_notifications["title_prefix"],title)
                    for video in videos_list:
                        send_notification(recipient_config,title,video)
                        
                elif folder_notifications["video"]=="grouped": 
                    tabbed_logger.info("Send grouped video notification to recipient %s" % recipient,tab=1)
                    msg='\n'.join(videos_list)
                    title= "New videos synced" 
                    if folder_notifications["title_prefix"]:
                        title="%s - %s" % (folder_notifications["title_prefix"],title)
                    send_notification(recipient_config,title,msg)
        
            if len(subtitles_list)>0 and "subtitle" in folder_notifications:
                if folder_notifications["subtitle"]=="single":
                    tabbed_logger.info("Send single subtitle notification to recipient %s" % recipient,tab=1)
                    title= "New subtitle synced" 
                    if folder_notifications["title_prefix"]:
                        title="%s - %s" % (folder_notifications["title_prefix"],title)
                    for subtitle in subtitles_list:
                        send_notification(recipient_config,title,subtitle)
                        
                elif folder_notifications["subtitle"]=="grouped": 
                    tabbed_logger.info("Send grouped subtitles notification to recipient %s" % recipient,tab=1)
                    title= "New subtitles synced" 
                    if folder_notifications["title_prefix"]:
                        title="%s - %s" % (folder_notifications["title_prefix"],title)
                    msg='\n'.join(subtitles_list)
                    send_notification(recipient_config,title,msg)
                    
            if len(others_list)>0 and "other" in folder_notifications:
                if folder_notifications["other"]=="single":
                    tabbed_logger.info("Send single file notification to recipient %s" % recipient,tab=1)
                    title= "New file synced" 
                    if folder_notifications["title_prefix"]:
                        title="%s - %s" % (folder_notifications["title_prefix"],title)
                    for other in others_list:
                        send_notification(recipient_config,title,other)
                        
                elif folder_notifications["other"]=="grouped": 
                    tabbed_logger.info("Send grouped files notification to recipient %s" % recipient,tab=1)
                    title= "New files synced" 
                    if folder_notifications["title_prefix"]:
                        title="%s - %s" % (folder_notifications["title_prefix"],title)
                    msg='\n'.join(others_list)
                    send_notification(recipient_config,title,msg)
        else:
            tabbed_logger.debug("Can't find access token for %s" % (recipient),tab=1)
