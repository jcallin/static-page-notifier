from datetime import datetime
import email.utils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from lxml import html
import os
import smtplib
import requests
import time

#
# Notifies email addresses in recpients.txt that the Probar sale page has changed
#

def run():
    url = 'http://shop.theprobar.com/Products/Sale'
    page = ''
    while True:
        new_page = get_static_page(url).content
        new_page_parsed = parse_page_content(new_page)
        if new_page_parsed != page and page != '':
            print("Page has changed since last check! ({} vs {})".format(new_page_parsed, page))
            send_email()
            page = new_page_parsed
        else:
            print("Page is the same since last check! Check performed at {}".format(datetime.now().isoformat()))
        # Sleep for 24 hours
        time.sleep(12 * 60 * 60)

def parse_page_content(page):
    tree = html.fromstring(page)
    core_data = tree.xpath('//div[@id="div__body"]//table//tr//td[@id="maincontent"]//table//text()')
    # print(core_data)
    return hash(str(core_data))

def get_static_page(url):
    r = requests.get(url)
    return r

def send_email():
    # Replace sender@example.com with your "From" address.
    # This address must be verified.
    SENDER = os.environ['AWS_SMTP_SENDER']
    SENDERNAME = 'Probar Sale Notification'

    # Replace recipient@example.com with a "To" address. If your account
    # is still in the sandbox, this address must be verified.
    RECIPIENTS  = get_recipients()

    # Replace smtp_username with your Amazon SES SMTP user name.
    USERNAME_SMTP = os.environ['AWS_SMTP_USER']

    # Replace smtp_password with your Amazon SES SMTP password.
    PASSWORD_SMTP = os.environ['AWS_SMTP_PASS']
    if not USERNAME_SMTP or not PASSWORD_SMTP:
        print('Configure username and password for SMTP with AWS_SMTP_USER and AWS_SMTP_PASS')

    # (Optional) the name of a configuration set to use for this message.
    # If you comment out this line, you also need to remove or comment out
    # the "X-SES-CONFIGURATION-SET:" header below.
    # CONFIGURATION_SET = "ConfigSet"

    # If you're using Amazon SES in an AWS Region other than US West (Oregon),
    # replace email-smtp.us-west-2.amazonaws.com with the Amazon SES SMTP
    # endpoint in the appropriate region.
    HOST = 'email-smtp.us-east-1.amazonaws.com'
    PORT = 587

    # The subject line of the email.
    SUBJECT = 'Probar Sale'

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = ('There might be a new probar sale going on. Check in at http://www.theprobar.com')

    # The HTML body of the email.
    BODY_HTML = """
    <html>
        <head></head>
            <body>
              <p>
                There may be new items on the
                <a href='http://shop.theprobar.com/Products/Sale'>Probar sale page</a>
                as of UTC {}
              </p>
            </body>
    </html>
    """.format(datetime.now().isoformat())

    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = SUBJECT
    msg['From'] = email.utils.formataddr((SENDERNAME, SENDER))
    # Comment or delete the next line if you are not using a configuration set
    # msg.add_header('X-SES-CONFIGURATION-SET',CONFIGURATION_SET)

    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(BODY_TEXT, 'plain')
    part2 = MIMEText(BODY_HTML, 'html')

    # Attach parts into message container.
    # According to RFC 2046, the last part of a multipart message, in this case
    # the HTML message, is best and preferred.
    msg.attach(part1)
    msg.attach(part2)

    # Try to send the message.
    try:
        server = smtplib.SMTP(HOST, PORT)
        server.ehlo()
        server.starttls()
        #stmplib docs recommend calling ehlo() before & after starttls()
        server.ehlo()
        server.login(USERNAME_SMTP, PASSWORD_SMTP)
        for r in RECIPIENTS:
            msg['To'] = r
            server.sendmail(SENDER, r, msg.as_string())
        server.close()
    # Display an error message if something goes wrong.
    except Exception as e:
        print ("Error: ", e)
    else:
        print ("Email sent to {} at {}!".format(RECIPIENTS, datetime.now().isoformat()))

def get_recipients():
    with open('recipients.txt') as f:
        return f.read().splitlines()

if __name__ == "__main__":
    run()

