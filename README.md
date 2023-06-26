# YouTubeIList and Motivation
YouTubeIList is a script that monitors videos in YouTube playlists and detects when they become unavailable. This is a common problem for YouTube users who create and watch playlists, as some videos may be deleted, made private, or blocked by YouTube for various reasons (such as copyright strike). However, YouTube only displays a generic message: “hiding unavailable videos”, without providing any further information.

YouTubeIList solves this problem by providing the following features:

* It alerts the user (or multiple users) when a video becomes unavailable in a playlist.
* It provides the title and channel name of the missing video, as well as the reason for its unavailability.
* By storing the playlist information on Google Sheets, it allows the user to easily share and keep up to date with others who also share the playlist.

## Main Features
* YouTubeIList retrieves the title and the uploader name from provided YouTube playlists, then writes each entry into a Google Spreadsheet file (which is linked to the owner’s Google account).
* YouTubeIList reads the entries in the Sheets and the playlist descriptions retrieved from YouTube, and updates new titles along with the uploader name in the spreadsheet.
* YouTubeIList marks the entries in the spreadsheet that are no longer found in the YouTube playlist by changing the cell style (such as bolding, changing the foreground color to white, and cell color to blue).
* YouTubeIList also detects videos that have been re-added to the playlist, so it will reset the cell style to default if that happens.
* YouTubeIList emails the recipient (stored in the `RECIPIENTS` variable), with a body detailing which video has been removed from which playlist by including each video titles, the uploader names, and the playlist names.

## Installation
To use YouTubeIList, you need to have Python 3 installed on your computer. You also need to install the following libraries:

1. `yt_dlp`
2. `pygsheets`

You can install them using `pip`:
```
pip install yt_dlp
pip install pygsheets
```
You also need to sign up for a Google Cloud account to enable the APIs in order to use this. You can follow these steps to do so:

* Go to the [Google Cloud Console](https://console.cloud.google.com/) and create a new project or select an existing one.
* Go to the [APIs & Services page](https://console.cloud.google.com/apis/dashboard) and click Enable APIs and Services.
* In the search field, enter Google Sheets API and press Enter. Click the API and then click Enable.
* In the search field, enter Gmail API and press Enter. Click the API and then click Enable.
* In the search field, enter Google Drive API and press Enter. Click the API and then click Enable.

Then, once you did that, you will have to create a new folder called `authentication` to store the three required files to ensure that the script has access to your Google Sheet file. You can follow these steps to do so:

* Go to the [Credentials](https://console.cloud.google.com/apis/credentials) page and click Create credentials > OAuth client ID.
* Select Desktop app as the application type and give it a name. Click Create.
Download the credentials file by clicking the download icon next to your client ID. Rename it as `credentials.json` and move it to the authentication folder.
* Go to the [Service accounts page](https://console.cloud.google.com/iam-admin/serviceaccounts) and click Create service account.
* Give it a name and a description. Click Create.
* Select a role for the service account. You can choose Project > Editor for full access to all resources. Click Continue.
* Click Create key and choose JSON as the key type. Click Create.
* Download the key file and rename it as `service_account.json`. Move it to the authentication folder.
* Go to your Google Sheet file and share it with the service account email address (the one that ends with `@<project-id>.iam.gserviceaccount.com`). Give it edit permission.
The first time you run the script, it will prompt you to authorize access to your Google account. It will open a web browser where you can sign in and grant permission. It will then generate a file called `token.json` and store it in the authentication folder. You don’t need to authorize again unless you delete this file or change your credentials.

Namely, these files are stored in these variables:
```
token_path = 'authentication/token.json'
credentials_path = 'authentication/credentials.json'
service_account_path = 'authentication/service_account.json'
```
You also need to change the values of these variables:
```
SPREADSHEET_ID = '1CWWOd7b0FuHOEDYJJ5-4TfP6INf6W8czNUkT-rArRJg'
# The ID of the Google Sheet file where the playlist information will be stored. You can find it in the URL of the sheet after /d/

SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1CWWOd7b0FuHOEDYJJ5-4TfP6INf6W8czNUkT-rArRJg/edit#gid=0'
# The URL of the Google Sheet file where the playlist information will be stored. You can copy it from your browser.

SHEET_NAME = 'PlaylistDemo'
# The name of the sheet inside the Google Sheet file where the playlist information will be stored. You can change it in the sheet tab at the bottom.

PLAYLIST_URLS = ['https://www.youtube.com/watch?v=OiC1rgCPmUQ&list=PL3-sRm8xAzY9gpXTMGVHJWy_FMD67NBed',
                 'https://www.youtube.com/watch?v=iKzRIweSBLA&list=PL7v1FHGMOadDghZ1m-jEIUnVUsGMT9jbH',
                 'https://www.youtube.com/watch?v=wSTYIyQxfPQ&list=PLXPyqbiCwzZr8IeNtn4Cu1FvpEHs_4L1g'
                 ]
# A list of URLs containing YouTube playlists that you want to monitor. These playlists must be unlisted (not public or private) so that YouTubeIList can access them.

RECIPIENTS = 'demo.email@gmail.com'
# The email address or addresses (separated by commas) to whom the notification will be sent to once a video deletion is detected. You can use your own email or any other email that you have access to.
```

## Usage
To run YouTubeIList, you just need to execute the script:

```
python youtube_ilist.py
```

YouTubeIList will scan the playlists and update the spreadsheet accordingly. It will also send an email notification if a video becomes unavailable.

You can run YouTubeIList periodically (for example, using a Windows task scheduler) to check for any changes in the playlists.

## Demonstration
This is what it looks like if the script detects any changes. The unavailable videos are highlighted in blue: 

![Demo image](https://github.com/tmdwnsyang/YouTubeIList/blob/main/live_demo.gif "This is a demo image")

You can also view the live example of the code [on this spreadsheet](https://docs.google.com/spreadsheets/d/1CWWOd7b0FuHOEDYJJ5-4TfP6INf6W8czNUkT-rArRJg/edit#gid=0).
I picked the **publically available** playlists that claim to be updated every week. The spreadsheet is automatically updated every 24 hours. 

## Important note
If you decide to replace a column with a different playlist, please clear the column before running. Otherwise it will merge the existing entries with the new playlist.

## License
YouTubeIList is licensed under the MIT License. See [LICENSE](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/licensing-a-repository#disclaimer) for more details.

## Contact
If you have any questions, suggestions, or feedback, feel free to contact me at tmdws.yang@gmail.com.

