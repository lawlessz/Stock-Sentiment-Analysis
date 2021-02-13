import mimetypes
from email.mime.multipart import MIMEMultipart
from email import encoders
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.text import MIMEText
import email
import imaplib
import smtplib
import datetime
import email.mime.multipart
from configparser import RawConfigParser
import base64

class OutlookClient(object):
    def __init__(self, config_path='credentials/config.ini'):
        self.config_path = config_path
        config = RawConfigParser()
        config.read(config_path)
        login = config['outlook']['login']
        password = config['outlook']['password']
        self.imap = imaplib.IMAP4_SSL('outlook.office365.com', 993)
        self.smtp = smtplib.SMTP('smtp.office365.com', 587)
        self.login(login, password)


    def login(self, username, password):
        self.username = username
        self.password = password
        try:
            r, d = self.imap.login(username, password)
            assert r == 'OK', 'login failed'
            print(" > Sign as ", d)
        except imaplib.IMAP4.error as ie:
            if str(ie) == 'command LOGIN illegal in state AUTH, only allowed in states NONAUTH':
                print('already logged in.')
            else:
                raise ie
        except Exception as e:
            print(" > Sign In ...")
            raise e
        # self.imap.logout()


    def sendEmailMIME(self, recipient, subject, message, attach_dir=None, attach_name=None, cc=[]):
        msg = MIMEMultipart('multipart')
        msg['Subject'] = subject
        msg['From'] = self.username
        msg['To'] = ', '.join(recipient)
        msg['Cc'] = ', '.join(cc)

        part = MIMEText(message, "plain")

        msg.attach(part)
        if attach_dir:
            ctype, encoding = mimetypes.guess_type(attach_dir)
            if ctype is None or encoding is not None:
                ctype = "application/octet-stream"

            maintype, subtype = ctype.split("/", 1)

            if maintype == "text":
                fp = open(attach_dir)
                # Note: we should handle calculating the charset
                attachment = MIMEText(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == "image":
                fp = open(attach_dir, "rb")
                attachment = MIMEImage(fp.read(), _subtype=subtype)
                fp.close()
            elif maintype == "audio":
                fp = open(attach_dir, "rb")
                attachment = MIMEAudio(fp.read(), _subtype=subtype)
                fp.close()
            else:
                fp = open(attach_dir, "rb")
                attachment = MIMEBase(maintype, subtype)
                attachment.set_payload(fp.read())
                fp.close()
                encoders.encode_base64(attachment)
            attachment.add_header("Content-Disposition", "attachment", filename=attach_name)
            msg.attach(attachment)

        try:
            self.smtp.ehlo()
            self.smtp.starttls()
            self.smtp.login(self.username, self.password)
            self.smtp.sendmail(msg['From'], recipient+cc, msg.as_string())
        except smtplib.SMTPException:
            print("Error: unable to send email")


    def list(self):
        # self.login()
        return self.imap.list()

    def select(self, str):
        return self.imap.select(str)

    def inbox(self):
        return self.imap.select("Inbox")

    def junk(self):
        return self.imap.select("Junk")

    def logout(self):
        return self.imap.logout()

    def today(self):
        mydate = datetime.datetime.now()
        return mydate.strftime("%d-%b-%Y")

    def unreadIdsToday(self):
        r, d = self.imap.search(None, '(SINCE "'+self.today()+'")', 'UNSEEN')
        list = d[0].decode('utf-8').split(' ')
        return list

    def getIdswithWord(self, ids, word):
        stack = []
        for id in ids:
            self.getEmail(id)
            if word in self.mailbody().lower():
                stack.append(id)
        return stack

    def unreadIds(self):
        r, d = self.imap.search(None, "UNSEEN")
        list = d[0].decode('utf-8').split(' ')
        return list

    def hasUnread(self):
        list = self.unreadIds()
        return list != ['']

    def readIdsToday(self):
        r, d = self.imap.search(None, '(SINCE "'+self.today()+'")', 'SEEN')
        list = d[0].decode('utf-8').split(' ')
        return list

    def allIds(self):
        r, d = self.imap.search(None, "ALL")
        list = d[0].decode('utf-8').split(' ')
        return list

    def readIds(self):
        r, d = self.imap.search(None, "SEEN")
        list = d[0].decode('utf-8').split(' ')
        return list

    def getEmail(self, id):
        if isinstance(id, str):
            id = bytes(id, encoding='utf-8')
        r, d = self.imap.fetch(id, "(RFC822)")
        self.raw_email = d[0][1]
        self.email_message = email.message_from_string(self.raw_email.decode('utf-8'))
        return self.email_message

    def unread(self):
        list = self.unreadIds()
        latest_id = list[-1]
        return self.getEmail(latest_id)

    def read(self):
        list = self.readIds()
        latest_id = list[-1]
        return self.getEmail(latest_id)

    def readToday(self):
        list = self.readIdsToday()
        latest_id = list[-1]
        return self.getEmail(latest_id)

    def unreadToday(self):
        list = self.unreadIdsToday()
        latest_id = list[-1]
        return self.getEmail(latest_id)

    def readOnly(self, folder):
        return self.imap.select(folder, readonly=True)

    def writeEnable(self, folder):
        return self.imap.select(folder, readonly=False)

    def rawRead(self):
        list = self.readIds()
        latest_id = list[-1]
        r, d = self.imap.fetch(latest_id, "(RFC822)")
        self.raw_email = d[0][1]
        return self.raw_email

    def mailbody(self):
        if self.email_message.is_multipart():
            for payload in self.email_message.get_payload():
                # if payload.is_multipart(): ...
                body = (
                    payload.get_payload()
                    .split(self.email_message['from'])[0]
                    .split('\r\n\r\n2015')[0]
                )
                return body
        else:
            body = (
                self.email_message.get_payload()
                .split(self.email_message['from'])[0]
                .split('\r\n\r\n2015')[0]
            )
            return body

    def mailsubject(self):
        return self.email_message['Subject']

    def mailfrom(self):
        return self.email_message['from']

    def mailto(self):
        return self.email_message['to']

    def mailreturnpath(self):
        return self.email_message['Return-Path']

    def mailreplyto(self):
        return self.email_message['Reply-To']

    def mailall(self):
        return self.email_message


if __name__ == '__main__':
    email_client = OutlookClient()
    #recipient = ['luoy2@hotmail.com', '410328235@qq.com']
    recipient = ['z.law@comcast.net', 'z.law@comcast.net']
    subject = 'testing email from cs498cca project'
    content = 'this is a test email'
    email_client.sendEmailMIME(recipient, subject, content)




