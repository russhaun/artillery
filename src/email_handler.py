"""
Handles sending of email. Creates a class that can be imported into other
modules. it contains methods for setting subject/msg and triggerfile to use to alert when email
is to be sent

"""

from .core import *

email_log_file = settings.get_config("global","EMAIL_ALERTS_LOG")
emailhost = settings.get_config("current","SMTP_ADDRESS")
emailport = settings.get_config("current","SMTP_PORT")
smtpfrom = settings.get_config("current","SMTP_FROM")
sendto = settings.get_config("current","ALERT_USER_EMAIL")
email_cc = ""
email_bcc = ""
email_subject = settings.get_config("current","LOG_MESSAGE_ALERT")
email_user = settings.get_config("current","SMTP_USERNAME")
email_pass = settings.get_config("current","SMTP_PASSWORD")
email_timer = settings.get_config("current","EMAIL_FREQUENCY")
email_ip_file = ""
email_pending = False
#alertlog location

alert_file = settings.get_config("global","ALERT_LOG")


class EmailLogger(SMTPHandler):
    '''
        This Class when initialized will setup a SMTP logging handler with settings retrieved from config file.
    It will monitor a file and when that file is modified it will trigger an event. On being triggered it will
    compile an email with desired settings both txt and html versions and add the alert logs in zip format as 
    an attachment. It saves a txt version of mail sent to the logs and then sends the email
        
        There are 2 included methods for changing the subject line and the log it reads when sending emails.
    Considering adding flags to class to determine where event is coming from so as to be able to use this
    with other types of events. have alpha EmailMessage class from newer python in the works now.

    '''
    def __init__(self, mailhost: str | tuple[str, int], fromaddr: str, toaddrs: str | list[str], subject: str, credentials: tuple[str, str] | None = None, secure: tuple[()] | tuple[str] | tuple[str, str] | None = None, timeout: float = 5) -> None:
        super().__init__(mailhost, fromaddr, toaddrs, subject, credentials, secure, timeout)
        self.triggerfile =""
        self.pending = email_pending
        self.mailhost = mailhost
        self.smtpserver = self.mailhost[0]
        self.smtpport = self.mailhost[1]
        self.to = toaddrs
        self.Cc = email_cc
        self.Bcc = email_bcc
        self.fromaddr = fromaddr
        self.emailsubject = subject
        self.use_custom_subject = False
        self.use_custom_alert = False
        self.custom_subject = ""
        self.custom_alert = ""
        self.creds = credentials
        self.emailuser = email_user
        self.emailpass = email_pass

    def send_mail(self,to, subject, text, zipname, time_stamp) -> None:
        '''
        Build out our email msg and sends using configured settings. I use 
        2 diferrent msgs one straight txt and the other in html
        '''
        #define the first part of our email
        msg = MIMEMultipart('related')
        #add appropriate header info
        if self.use_custom_subject is True:
            msg['Subject'] = self.custom_subject
        else:
            msg['Subject'] = subject
        msg['From'] = self.fromaddr
        msg['To'] = self.to
        msg['Cc'] = self.Cc
        msg['Bcc'] = self.Bcc
        msg['Date'] = formatdate(localtime=True)
        msg['Message-Id'] = "<" + self.generate_id(20) + "." + self.fromaddr + ">"
        msg.preamble = 'This is a multi-part message in MIME format.'
        #define second part of our email
        alternative_msg = MIMEMultipart('alternative')
        msg.attach(alternative_msg)
        ##retrive html and text version of email
        html = self.prep_email(alert=text[1],subject=text[0])
        #attach txt to plain txt version
        alternativemsgetxt = MIMEText(f"{html[1]}")
        alternative_msg.attach(alternativemsgetxt)
        #attach html to html version
        msgText = MIMEText(f"{html[0]}",'html')
        alternative_msg.attach(msgText)
        #setup the image for html email
        logo_path = settings.get_config("global","ICON_PATH")
        logo = f"{logo_path}\\email_avatar.jpg"
        img = open(logo, 'rb')
        msgImage = MIMEImage(img.read())
        img.close()
        # Define the image's ID as referenced in the html
        msgImage.add_header('Content-ID', '<image1>')
        #attach image to msg
        msg.attach(msgImage)
        # add zipfile of alert_file as an attachment
        alert_zip_file = f"{zipname}"
        filename = f'{time_stamp}_alerts.zip'
        zipfile = open(alert_zip_file,'rb')
        attach = MIMEApplication(zipfile.read(),_subtype="zip")
        zipfile.close()
        attach.add_header('Content-Disposition','attachment',filename=filename)
        msg.attach(attach)
        #write out info about email  being sent to txt log
        self.write_event(f"Email Server: {self.smtpserver}")
        self.write_event(f"Email Server port: {str(self.smtpport)}")
        self.write_event(f"Email Subject: {msg['Subject']}")
        self.write_event(f"From addr: {msg['From']}")
        self.write_event(f"To addr: {msg['To']}")
        self.write_event(f"{msg['Cc']}")
        self.write_event(f"{msg['Bcc']}")
        self.write_event(f"Msg plain text: {html[1]}")
        #
        self.write_event("Sending email now")
        print("Sending email now",flush=True)
        # # prep the smtp server
        mailServer = smtplib.SMTP("%s" % (self.smtpserver), self.smtpport)
        mailServer.ehlo()
        if not self.email_user == "":
            # tls support?
            mailServer.starttls()
            # some servers require ehlo again
            mailServer.ehlo()
            #write_console(smtp_user)
            #write_console(smtp_pwd)
            mailServer.login(self.emailuser, self.emailpass)
        # send the email
        #write_log("Sending email to %s: %s" % (to, subject))
        mailServer.sendmail(self.fromaddr, self.to, msg.as_string())
        mailServer.close()
        print("email sent",flush=True)
        #now its safe to move/delete zip file
        if os.path.isfile(zipname):
            subprocess.run(['cmd', '/C', 'del', zipname], shell=True, close_fds=True,check=False)

    def generate_id(self,size=6, chars=string.ascii_uppercase + string.digits) -> str:
        """
        returns random id for use in email message id
        """
        return ''.join(random.choice(chars) for _ in range(size))
    
    def write_event(self,event):
        """
        opens email log file and writes event

        """
        if not os.path.isfile(email_log_file):
            with open(email_log_file,'x',encoding='utf-8')as email_log:
                email_log.write(event+"\n")
        else:
            with open(email_log_file,'a',encoding='utf-8')as email_log:
                email_log.write(event+"\n")
        
    
    def prep_email(self, alert,subject):
        '''
        Makes a text and html version of the subject and alert
        and returns as a tuple for our email
        '''
        hostname = socket.gethostname()
        def prepare_alert(alert):
            '''
             pulls out first entry from alert file to insert 
            ip and port info alert txt from config file
            '''
            for line in alert:
                ip = alert[0]
                port = alert[1]
            return ip,port
        
        def prepare_subject(subject, alert):
            '''
           inserts ip and port into alert message retrieved from config file for now.
           will eventually support all modules with individual messages have to build in logic 
            '''
            # print(type(alert))
            # print(f"alert from prepare subject: {alert}")
            line = subject
            ip = alert[0]
            port = alert[1]
            line = line.replace("%ip%", ip)
            line = line.replace("%port%", port)
            return line
        #prep our alert and subject for the email
        alert = prepare_alert(alert)
        subject = prepare_subject(subject, alert)
        #Define our text alert
        text = subject
        #Define our html alert very basic for now
        #will make it so you can set your own template if you want
        #will add more later
        html = f'''
            <html>
                <body>
                    <h1 style="margin-left: 25px;">Scan Detected!</h1>
                    <b>This text is bold</b>
                        <p style="margin-left: 25px;"><b>This email was generated automatically due to the following events occuring on {hostname}</b></p>
                        <p><img src="cid:image1"></p>
                        <p style="margin-left: 50px;">{subject}</p>
                        <p></p>
                </body>
            </html>
            '''
        return html,text

    def set_subject(self, subject):
        '''
        allows setting subject of email before sending.
        '''
        text = subject
        time.sleep(2)
        self.custom_subject = text
        self.use_custom_subject = True
    
    def set_alert(self,alert):
        '''
        allows setting alert body of email before sending.
        '''
        self.custom_alert = alert
        self.use_custom_alert = True
    
    def set_trigger_file(self,file):
        '''
        allows changing of trigger file to be used with emails
        just add filename ex: sshtrigger.txt. will create file 
        if it does not exist
        '''
        logpath = settings.get_config("global", "LOG_FILE")
        triggerfile = f"{logpath}\\junk\\{file}"
        if not os.path.isfile(triggerfile):
            with open(triggerfile,'x',encoding='utf-8') as logfile:
                logfile.write(" ")
                #flush so there is nothing
                logfile.flush()
            self.triggerfile = triggerfile
        else:
            self.triggerfile = triggerfile

    def check_pending_msgs(self):
        '''
        checks for pending msg's by checking size of msgs list
        if size is greater then zero we have alerts pending. 
        '''
        # loop forever based on timer
        self.write_event(f"[*] Email Timer set to trigger every {email_timer} seconds")

        msgs = []
        while 1:
            #maybe here introduce random to give different times back for checking
            #to prevent other email threads from clashing if imported in other places
            # in app. so for example if the dely in config is "600"(10min)
            #have a min floor of "180"(3min) with urandom to return a # between that to check
            # maybe introduce a config flag like "EMAIL_LAG" or something 
            time.sleep(int(email_timer))
            # if the file is there, 
            if os.path.isfile(self.triggerfile):
                # read it in to see if there are entries we expect a tuple ip,port returned
                with open(self.triggerfile,"r",encoding="utf-8") as logread:
                    for line in logread:
                        if not line == "":
                            new_line = line
                            new_line = new_line.replace("\n", "")
                            new_line = f"{new_line}"
                            new_line = new_line.split(",")
                            for item in new_line:
                                msgs.append(item)
                    #check to see if any msgs
                    if len(msgs) == 0:
                        pass
                    else:
                        #write the first 2 entries as our alert
                        self.write_event(f"New alerts have been detected from: {str(msgs[0])} on port {msgs[1]}")
                        #very simialar to comment above but this is fo active scans
                        #thinking about a delay right here to prevent spamming of email
                        #i know there is already a timer for checking. this is to allow 
                        #this function to wait for a min to allow for potential scans in progress to complete
                        #if the check is done during an active scan
                        #create zipfile name with timestamp
                        tod = time.asctime()
                        line = tod
                        line = line.replace(" " ,"_")
                        line = line.replace(":", "_")
                        tod = line
                        alert_path = settings.get_config("global","LOG_FILE")
                        alert_file_name = f"{alert_path}\\alerts.log"
                        zip_file_name = f"{alert_path}\\{tod}_alerts.zip"
                        #create the archive 
                        with ZipFile(zip_file_name, 'w') as myzip:
                            myzip.write(filename=alert_file_name)
                        time.sleep(2)
                        self.write_event(f"Email being compiled and sent to the configured address of: {self.to}")
                        host = socket.gethostname()
                        msg = f"(ALERT) Artillery Event Recieved from {host}."
                        self.send_mail(self.to,subject=msg,text=(email_subject,msgs),zipname=zip_file_name,time_stamp=tod)
                    #
                    #hang for a sec 
                    time.sleep(3)
                    #wipe the alert and email log file now
                    with open(self.triggerfile,"w",encoding="utf-8") as logwrite:
                        for line in logread:
                            line = line.replace(line,"")
                            logwrite(line)
                    #wipe the alert.log? to only get relevent data so in the case
                    # another module sends an email its not sending stuff thats 
                    # not related would probably be better to have individual logs
                    # for each module and then set mailer to use that, like when we set the triggerfile
                    # with open(alert_file,"w",encoding="utf-8") as alertfle:
                    #     alertfile.flush()
                    #     for line in alertfle:
                    #         line = line.replace(line,"")
                    #         alertfile(line)
                #clear the list for future alerts
                msgs.clear()

# def monitor_email():
#     """
#     Checks if email alerts are enabled and starts new thread with emaillogger
#     if turned on.
#     """
#     # alerts_enabled = settings.get_config("current", "EMAIL_ALERTS")
#     # if alerts_enabled == " ON":
#     email_log = EmailLogger(mailhost=[emailhost,int(emailport)],fromaddr=smtpfrom,toaddrs=sendto,subject=email_subject,credentials=[email_user,email_pass],secure=())
#     thread.start_new_thread(email_log.check_pending_msgs,())

