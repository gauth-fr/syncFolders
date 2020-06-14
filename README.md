# syncFolders
syncFolders is python script, based on rsync, which will synchronized a set of folder from/to a server.

## Table of Contents

[TOC]

## Features
- synchronize folders using rsync
- support different folder configuration
- send notifications of synced files thru Pushbullet or Telegram
- post-sync script execution, per file
- run on Synology NAS out-of-the-box (required modules included)

## How to install
```shell
git clone https://github.com/gauth-fr/syncFolders.git

#optionnally, you can install the modules
cd syncFolders
pip install -r requirements.txt
```

## Configuration file : config.yaml
A sample config.yaml is provided
```shell
cp config.yaml.sample config.yaml
```
### Folders configuration
You can have as many folder configuration as needed.
Each folder has its own configuration.
Each folder is synchronized indepedently.
```yaml
folders
- title: 'Sync test mary'
  server:
      ip: '1.2.3.4'
      port: '22'
      user: 'mary'
  source: '/home/mary/test'
  target: '/volume1/test'
  target_is: 'local'
  source_postcommand: null
  target_postcommand: '/home/mary/post_process.sh FILE'
  notify:
    recipient:
    - 'mary_telegram'
    - 'bob_pushbullet'
    title_prefix: 'Prefix message'
    subtitle: 'single'
    video: 'grouped'
    other: null
  delete: false
```
| Parameter | Type/Value  | Description  |
| ------------ | ------------ | ------------ |
| title  |  string  |  Title of this folder synchronization (mostly cosmetic in the logs) |
| server.ip |  string (ip or hostname) | IP/Hostname of the server to synchronize to/from  |
| server.port | string  |  SSH port of the server |
| server.user | string  |  User for SSH connection |
| source | string   | source folder to synchronize  |
| target  | string  | target folder to synchronize to  |
| target_is  | string (remote or local)  |  define if the target the local (machine where the script is started) or remote (the defined server)  |
| delete  | bool   | unused for now   |
|  notify.recipient | array of string  | list of recipient for notification. Each recipient should be defined in the notifications section of the config file  |
| notify.title_prefix  | string  | Prefix string added to the notification title  |
| subtitle  (optional)| string (single or grouped) or null| define is the subtitle notifications should be grouped (1 notification for all synced subtitles) or not (1 notification per synced subtitle)  |
| video  (optional)| string (single or grouped) or null | define is the video notifications should be grouped (1 notification for all synced videos) or not (1 notification per synced video)  |
| other  (optional)| string (single or grouped) or null | define is the other files (not subtitle or video) notifications should be grouped (1 notification for all files) or not (1 notification per synced file)  |

### Notification configuration
As of today, only PushBullet and Telegram are supported for notification.
#### Global notification configuration
```yaml
notifications:
    video_extensions: ['.mp4','.avi','.mkv','.mov','.webm','.flv','.vob','.ogv','.qt','.asf','.wmv','.mpg','.m4v','.3gp','.3g2']
    subtitle_extensions: ['.srt','.sub','.sbv']
    other_extensions: []
    recipients:
        bob_pushbullet: 
            provider: 'pushbullet'
            api_key: 'o.z0jsDS14bH35zIw1214io5MG42HMTbG'
        mary_telegram: 
            provider: 'telegram'
            recipient_id: '-123456788'
            bot_id: '1234567890:CDG6QIDKAqKdpzu1qC2PDJpc0a3XE_PSODN'
```
| Parameter | Type/Value  | Description  |
| ------------ | ------------ | ------------ |
| notifications.video_extensions  | array of string  |list of file extensions considered as videos   |
| notifications.subtitle_extensions  | array of string  |list of file extensions considered as subtitles   |
| notifications.other_extensions  | UNUSED  |UNUSED - files that are not video or subtiles are considered as other files   |
| notifications.recipient  | dictionnary   |this dictionnary contains the different recipient configuration   |
| notifications.recipient.CONFIG_NAME   |  dictionnary | this CONFIG_NAME contains the recipient configuration. CONFIG_NAME name is the key that should be specified in **folder.notify.recipient**  |

#### PushBullet notification configuration

| Parameter | Type/Value  | Description  |
| ------------ | ------------ | ------------ |
|  CONFIG_NAME.provider |  string=pushbullet | define this configation as a PushBullet configuration  |
|  CONFIG_NAME.api_key |  string | recipient PushBullet API key  |

#### Telegram notification configuration

To use telegram notification, you need to create a bot first, start a conversation with it or add it to a group and start it.
You also need the user or group id where the bot will send messages.

| Parameter | Type/Value  | Description  |
| ------------ | ------------ | ------------ |
|  CONFIG_NAME.provider |  string=telegram | define this configation as a PushBullet configuration  |
|  CONFIG_NAME.recipient_id |  string | Telegram recipient id (group or user)   |
|  CONFIG_NAME.bot_id |  string | Telegram bot id (group or user)   |

## FAQ
###### How to create a Telegram bot?
- from Telegram, contact @botfather, start a conversation and click on start
- type `/newbot` and answer the questions
- Note the provided access token. You will need to use it as the `bot_id`

![Telegram-BotFather](https://raw.githubusercontent.com/gauth-fr/syncFolders/master/.res/Telegram-Botfather-newbot.png "Telegram-BotFather")

###### How to get my ID?
- from Telegram, contact @myidbot, start a conversation and click on start
- type `/getid`
- Note the id. You will need to use it as the `recipient_id`

###### Can the bot send notifications to a group?
- From Telegram, create a group
- Add the bot to the group
- Get the group id
	- Add @myidbot to the group
	- type `/getgroupid`
	- note the group id, which should be a negative number. You will need to use it as the `recipient_id`

###### How can I test if the bot is working correctly?
- try to send a message with curl!
```shell
curl -X POST -H 'Content-Type: application/json' -d '{"chat_id": "RECIPIENT_ID","text": "This is a test from curl", "disable_notification": true}' https://api.telegram.org/botBOT_ID/sendMessage
```

###### Why the libs are provided instead of a simple requirements.txt?
I made this script to run on my Synology NAS, where python 2.7.12 is installed, but not pip.
So at least, it's running out-of the box.
You can still remove the `modules` folder and install the modules using ` pip install -r requirements.txt`
