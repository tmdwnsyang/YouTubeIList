
from __future__ import print_function
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# import yt_dlp and pygsheets modules
import yt_dlp
import pygsheets
import sys
from ordered_set import OrderedSet

# For email services
import base64
from email.mime.text import MIMEText
from requests import HTTPError

# For sleep
import time

if hasattr(sys, '_MEIPASS'):
    token_path = os.path.join(sys._MEIPASS, 'authentication', 'token.json')
    credentials_path = os.path.join(
        sys._MEIPASS, 'authentication', 'credentials.json')
    service_account_path = os.path.join(
        sys._MEIPASS, 'authentication', 'service_account.json')
else:
    token_path = 'authentication/token.json'
    credentials_path = 'authentication/credentials.json'
    service_account_path = 'authentication/service_account.json'


# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive',
          'https://www.googleapis.com/auth/gmail.send'
          ]

# The ID and range of a spreadsheet.
SPREADSHEET_ID = '1CWWOd7b0FuHOEDYJJ5-4TfP6INf6W8czNUkT-rArRJg'
SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1CWWOd7b0FuHOEDYJJ5-4TfP6INf6W8czNUkT-rArRJg/edit#gid=0'
SHEET_NAME = 'PlaylistDemo'
PLAYLIST_URLS = ['https://www.youtube.com/playlist?list=PLMC9KNkIncKtPzgY-5rmhvj7fax8fdxoj',
                 'https://www.youtube.com/watch?v=iKzRIweSBLA&list=PL7v1FHGMOadDghZ1m-jEIUnVUsGMT9jbH',
                 'https://www.youtube.com/watch?v=OiC1rgCPmUQ&list=PL3-sRm8xAzY9gpXTMGVHJWy_FMD67NBed',
                 'https://www.youtube.com/watch?v=wSTYIyQxfPQ&list=PLXPyqbiCwzZr8IeNtn4Cu1FvpEHs_4L1g'
                 ]
RECIPIENTS = 'tmdwns.yang@gmail.com'

COLUMNS_LEX_ORDER = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K',
                     'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
COLUMN_SIZE = len(PLAYLIST_URLS)
RANGE_NAME = f'A2:{COLUMNS_LEX_ORDER[COLUMN_SIZE-1]}'
DEFAULT_FONT = 'Lexend'

# Options for yt-dlp
YDL_OPTS = {
    'dump_single_json': True,
    'extract_flat': 'in_playlist',
    'skip_download': True,
    'quiet': True,
    'compat_opts': {
        'no-youtube-unavailable-videos' : True
        }
}


def main():
    print('Initializing playlist scan...')
    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES, access_type='offline')
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    try:
        (values, sheet) = get_spreadsheet_values(creds)
        accumulated_list = aggregate_playlist_sheets(values)
        current_list_matrix, playlist_titles = retrieve_playlist_desc()
        wks = auth_and_retrieve_sheet()[0]
        update_playlist_titles(wks, playlist_titles)
        accumulated_list = append_new_list(accumulated_list, current_list_matrix, wks)
        style_list = get_row_styles(sheet)
        (deleted_songs_matrix, new_deletion) = update_deleted_list(style_list, accumulated_list, current_list_matrix, wks)
        if (new_deletion):
            send_email(deleted_songs_matrix, playlist_titles, creds)

    except HttpError as err:
        print(err)


def send_email(deleted_songs_matrix: list, playlist_titles:list, creds):
    """ 
    Drafts an email mentioning all newly deleted songs per playlist. 
    """
    service_email = build('gmail', 'v1', credentials=creds)
    print('Song(s) deleted from playlist(s)! Drafting an email log...')
    body = 'Hey, this message is sent to you to let you know that the following song(s) is no longer available on your playlist:\n\n'
    for c in range(len(deleted_songs_matrix)): 
        if (len(deleted_songs_matrix[c]) > 0):
            body += f'Playlist name: {playlist_titles[c]}\n'
            for r, s in enumerate(deleted_songs_matrix[c], 1):
                body += f'  {r}. '+ f'{s}\n'
            body += '\n'
    body += f'If you manually deleted these videos from your playlist(s), please ignore this message. If not, I logged it for you here: {SPREADSHEET_URL}.\n\nI hope that was helpful. Ciao!\n\nSeung'

    message = MIMEText(body)
    message['to'] = RECIPIENTS
    message['subject'] = 'Playlist song deletion reminder'
    create_message = {'raw': base64.urlsafe_b64encode(message.as_bytes()).decode()}

    try:
        message = (service_email.users().messages().send(userId='me', body=create_message).execute())
        print(f'Sent message to {RECIPIENTS} Message ID: {message["id"]}')
    except HTTPError as err:
        print(err)
        message = None
        
def get_spreadsheet_values(creds):
    service_spreadsheet = build('sheets', 'v4', credentials=creds,
                                    static_discovery=False)
        # Call the Sheets API and retrieve the values and the style
    sheet = service_spreadsheet.spreadsheets()
    result = sheet.values().get(spreadsheetId=SPREADSHEET_ID,
                                        range=RANGE_NAME).execute()
    values = result.get('values', [])
    return values, sheet    

def retrieve_playlist_desc():
    """
    Retrieves the currently live playlist description using `ytdlp` library.\n
    Returns a tuple of:
    1. A 2d matrix, where each item is in the format of "[title] by [uploader]"
    2. A list of playlist titles
    """
    current_list_matrix = []
    playlist_titles = []
    with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
        for r, PLAYLIST_URL in enumerate(PLAYLIST_URLS):
            current_list_matrix.append(OrderedSet())
            playlist_dict = ydl.extract_info(PLAYLIST_URL, download=False)
            playlist_titles.append(playlist_dict['title'])
            [current_list_matrix[r].add(video['title'] + ' by ' + video['uploader'])
                for video in playlist_dict['entries']]
    # [print(v) for v in current_list_matrix[1]]
    return (current_list_matrix, playlist_titles)

def update_playlist_titles(wks, playlist_titles:list):
    """
    Writes playlist titles retrieved onto the worksheet, `wks` on to the first row.
    """
    wks.update_values(
        f'{COLUMNS_LEX_ORDER[0]}1:{COLUMNS_LEX_ORDER[len(playlist_titles)-1]}1', [playlist_titles])

def auth_and_retrieve_sheet():
    """ 
    Authorizes pygsheets with credentials and returns a list of sheets.
    ex: [Sheet1, Sheet2,...]
    """
    return pygsheets.authorize(
            client_secret=credentials_path, service_account_file=service_account_path).open(SHEET_NAME)

def aggregate_playlist_sheets(values:list):
    """ 
    Takes in a 2d matrix of the spreadsheet, returns a 2d matrix (no duplicates), 
    where each sub array is an `OrderedSet` of one column. For example:\n
    [[playlist 1], [playlist 2], ...]
    """
    accumulated_list = []
    for c in range(COLUMN_SIZE):
        accumulated_list.append(OrderedSet())
        for r in values:
            if len(r) <= c or len(r[c]) == 0:
                break
            accumulated_list[c].add(r[c])
    return accumulated_list

def append_new_list(accumulated_list:list, current_list_matrix:list, wks):
    """
    Appends every item in `current_list_matrix` to the end of each column in `accumulated_list`.\n
    Updates the sheet `wks` to reflect new additions for each column.\n
    Returns the new `accumulated_list`
    """ 
    for c in range(COLUMN_SIZE):
        new_listings = OrderedSet()
        for music in current_list_matrix[c]:
            # print(type(music))
            if music not in accumulated_list[c]:
                new_listings.add(music)
        if (len(new_listings) > 0):
            wks.update_values(
                f'{COLUMNS_LEX_ORDER[c]}{len(accumulated_list[c])+2}:{COLUMNS_LEX_ORDER[c]}{len(new_listings) + len(accumulated_list[c])+2}', [[v] for v in new_listings])
            accumulated_list[c] = accumulated_list[c].union(new_listings)
    return accumulated_list

def get_row_styles(sheet):
    style_result = sheet.get(spreadsheetId=SPREADSHEET_ID,
                                 ranges=[RANGE_NAME], fields='sheets(data(rowData(values(effectiveFormat))))').execute()
    style_list = style_result['sheets'][0]['data'][0]['rowData']
    return style_list


def update_deleted_list(style_list:list, accumulated_list:list, current_list_matrix:list, wks):
    """ 
    Updates the `wks` based on whether item in `current_list_matrix` is found in `accumulated_list`.\n
    If item is not found, the missing entry will be indicated on `wks`.\n
    Returns a tuple of
    1. A 2d matrix containing deleted entries per column\n
    2. A Boolean indicating at least one item has been newly deleted.
    """
    model_cell = pygsheets.Cell("AA2")  # create a model cell object
    new_deletion = False
    deleted_songs_matrix = []
    for c in range(COLUMN_SIZE):
        deleted_songs_matrix.append([])
        for r, song in enumerate(accumulated_list[c]):
            if song not in current_list_matrix[c]:
                if not (style_list[r]['values'][c]['effectiveFormat']['textFormat']['bold']):
                    # If the song is deleted from the list for the first time, do something
                    new_deletion = True
                    deleted_songs_matrix[c].append(song)

                cell = wks.cell(f'{COLUMNS_LEX_ORDER[c]}{r+2}')
                cell.set_text_format('foregroundColor', {
                                        "red": 1, "green": 1, "blue": 1})

                cell.set_text_format('bold', True)
                cell.color = (0.2, 0.2, 1, 0)

            # If the song is re-added to the playlist, reset the styling.
            elif song in current_list_matrix[c] and style_list[r]['values'][c]['effectiveFormat']['textFormat']['bold']:

                data_range = wks.get_values(
                    start=f'{COLUMNS_LEX_ORDER[c]}{r+2}', end=f'{COLUMNS_LEX_ORDER[c]}{r+2}', returnas="range")
                data_range.apply_format(model_cell)
    return deleted_songs_matrix, new_deletion

def success():
    print('Successful run. Exiting program...')
    time.sleep(5)

if __name__ == '__main__':
    main()
    success()