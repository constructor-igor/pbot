import os
from imbox import Imbox # pip install imbox
import traceback
from datetime import datetime
import logging

class IgnoreImboxParserFilter(logging.Filter):
    def filter(self, record):
        record.module not in ['imbox', 'parser']
        # return "INFO:imbox.parser" not in record.getMessage()

emails_year = '2023'
host = "imap.gmail.com"
username = "igor.zc"
password = 'prrnjbrippgqvdjm'
folder = "J/toldot"
download_folder = r"@experiments\attachments"


formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger("emails")
logger.setLevel(logging.DEBUG)
file_handler = logging.FileHandler(f"emails-{emails_year}.log", encoding='utf-8')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

console_logger = logging.getLogger("console")
console_logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)
console_logger.addHandler(console_handler)


# logging.basicConfig(level=logging.INFO,
#                     format='%(asctime)s [%(levelname)s] %(message)s', filter=[IgnoreImboxParserFilter()])

# enable less secure apps on your google account
# https://myaccount.google.com/lesssecureapps

console_logger.info("started...")

if not os.path.isdir(download_folder):
    os.makedirs(download_folder, exist_ok=True)
    
mail = Imbox(host, username=username, password=password, ssl=True, ssl_context=None, starttls=False)
all_folders = mail.folders()
# messages = mail.messages(folder="J/zdaka") # defaults to inbox
messages = mail.messages(folder=folder) # defaults to inbox
console_logger.info(f"found {len(messages)} messages in folder '{folder}'")

total_index = 0
actual_index = 0
for (uid, message) in messages:
    if total_index%10==0:
        console_logger.info(f"processed {actual_index} from {total_index} messages...")
    total_index += 1
    # date_obj = datetime.strptime(message.date, '%a, %d %b %Y %H:%M:%S %z (%Z)')
    date_obj = message.date
    subject = str(message.subject)
    mail.mark_seen(uid) # optional, mark message as read
    attachments = list(message.attachments)
    flags = message.flags
    sent_from_email = message.sent_from[0]['email']
    # get gmail labels
    # https://stackoverflow.com/questions/37383838/how-to-get-gmail-labels-using-imaplib
    
    if f' {emails_year} ' in date_obj:
        actual_index += 1
        logger.info(f"flags: {flags}, date: {date_obj}, attachments: {len(attachments)}, subject: {subject}")

    #if len(attachments)>0 and ' 2023 ' in date_obj:
    # if len(attachments)>0:
        # if date_obj.year>=2017:
    

    # for idx, attachment in enumerate(message.attachments):
    #     try:
    #         att_fn = attachment.get('filename')
    #         download_path = f"{download_folder}/{att_fn}"
    #         print(download_path)
    #         with open(download_path, "wb") as fp:
    #             fp.write(attachment.get('content').read())
    #     except:
    #         print(traceback.print_exc())

mail.logout()


"""
Available Message filters: 

# Gets all messages from the inbox
messages = mail.messages()

# Unread messages
messages = mail.messages(unread=True)

# Flagged messages
messages = mail.messages(flagged=True)

# Un-flagged messages
messages = mail.messages(unflagged=True)

# Messages sent FROM
messages = mail.messages(sent_from='sender@example.org')

# Messages sent TO
messages = mail.messages(sent_to='receiver@example.org')

# Messages received before specific date
messages = mail.messages(date__lt=datetime.date(2018, 7, 31))

# Messages received after specific date
messages = mail.messages(date__gt=datetime.date(2018, 7, 30))

# Messages received on a specific date
messages = mail.messages(date__on=datetime.date(2018, 7, 30))

# Messages whose subjects contain a string
messages = mail.messages(subject='Christmas')

# Messages from a specific folder
messages = mail.messages(folder='Social')
"""