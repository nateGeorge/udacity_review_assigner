# followed this guide: http://stackabuse.com/how-to-send-emails-with-gmail-using-python/
import smtplib
import os
import textwrap

def get_env_vars():
    '''
    gets gmail uname/pass, phone number to text, and email to send to
    '''
    gmail_user = os.getenv('udacity_gmail_uname') + '@gmail.com'
    gmail_password = os.getenv('udacity_gmail_pass')
    phone_email = os.getenv('my_phone_num_email')
    email_addr = os.getenv('my_email_addr')
    return gmail_user, gmail_password, phone_email, email_addr

def compose_email(from_addr, to, link, project):
    '''
    sends email with link to udacity project to review

    args:
    from_line -- string; email address the message is from
    to -- list of strings; email addresses the message is to
    link -- string; link to udacity project to review
    '''
    subject = '%s review assigned' % (project)
    body = "You've been assigned a review for {}!\n\nCheck this link: {}".format(project, link)

    email_text = ("From: %s\n"
                    "To: %s\n"
                    "Subject: %s\n"
                    ""
                    "%s") % (from_addr, ", ".join(to), subject, body)

    return email_text


def compose_error(from_addr, to, error):
    '''
    sends email with link to udacity project to review

    args:
    from_line -- string; email address the message is from
    to -- list of strings; email addresses the message is to
    link -- string; link to udacity project to review
    '''
    subject = 'Error on Udacity server: {}'.format(error)
    body = "You've been assigned a review!\n\nCheck this link: {}".format(error)

    email_text = ("From: %s\n"
                    "To: %s\n"
                    "Subject: %s\n"
                    ""
                    "%s") % (from_addr, ", ".join(to), subject, body)

    return email_text


def send_messages(link, project, text=True):
    '''
    sends text and email notifying of reviews assigned

    args:
    link -- string; link to udacity review that has been assigned
    text -- boolean; if True will send a text message
    '''
    gmail_user, gmail_password, phone_email, email_addr = get_env_vars()
    to = [email_addr]
    if text:
        to = [phone_email, email_addr]
    email_text = compose_email(from_addr=gmail_user, to=to, link=link, project=project)
    print email_text
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, to, email_text)
        server.close()
    except:
        print 'Something went wrong...'
        print 'Couldn\'t email'

def send_error(error, text=True):
    '''
    sends text and email notifying of reviews assigned

    args:
    link -- string; link to udacity review that has been assigned
    text -- boolean; if True will send a text message
    '''
    gmail_user, gmail_password, phone_email, email_addr = get_env_vars()
    to = [email_addr]
    if text:
        to = [phone_email, email_addr]
    email_text = compose_error(from_addr=gmail_user, to=to, error=error)
    print email_text
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, to, email_text)
        server.close()
    except:
        print 'Something went wrong...'
        print 'Couldn\'t email'
