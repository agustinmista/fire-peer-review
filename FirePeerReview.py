#!/usr/bin/env python3

import os
import glob, re
import smtplib, ssl
import time

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from optparse import OptionParser

from random import randint

from getpass import getpass

# ----------------------------------------
# Read a submission directory created by Fire and assign peer reviewers

def AssignReviewers(tar_file):

    # Create a new directory and extract the submissions inside
    subs_dir = "{}_{}".format("submissions", RandomWithNDigits(4))
    print("Extracting {} to {}".format(tar_file, subs_dir))
    tar_file = re.escape(glob.glob(tar_file)[0])
    os.mkdir(subs_dir)
    os.system("tar -xvf {} --directory {} --strip-components=1 > /dev/null".format(tar_file, subs_dir))

    # Read the student emails from the extracted submissions and create a dictionary of review jobs
    students = [ os.path.basename(folder) for folder in glob.glob("{}/*".format(subs_dir)) ]
    peers1 = students[1::] + students[0:1]
    peers2 = students[2::] + students[0:2]

    print("Assigning jobs:")
    jobs = dict()
    for (student, peer1, peer2) in zip(students, peers1, peers2):
        print("* {} will review: {}, {}".format(student, peer1, peer2))

        # Find the PDFs to review
        peer1_pdfs = glob.glob("{}/{}/*.pdf".format(subs_dir, peer1))
        peer2_pdfs = glob.glob("{}/{}/*.pdf".format(subs_dir, peer2))

        # Make sure we only have one PDF per student
        if len(peer1_pdfs) != 1 or len(peer2_pdfs) != 1:
            print("ERROR! Found multiple submitted PDFs when creating tasks for {}".format(student))
            exit()

        peer1_pdf = peer1_pdfs[0]
        peer2_pdf = peer2_pdfs[0]

        # Save the student's jobs
        jobs[student] = (
            (peer1, peer1_pdf, ascii(os.path.basename(peer1_pdf))),
            (peer2, peer2_pdf, ascii(os.path.basename(peer2_pdf)))
        )

    return jobs

# ----------------------------------------
# Send an email using Chalmers credentials

def SendChalmersEmail(cid, pwd, recipient, subject, body, attachments=[], bcc=[]):

    # Connection details
    server_uri = "smtp.chalmers.se"
    server_port = 587
    user = "net.chalmers.se\\" + cid
    sender = cid + "@chalmers.se"

    # Compute the actual email recipients (BCC's appear here but not in the email headers)
    recipients = [recipient] + bcc

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject

    # Add the message body to the email
    message.attach(MIMEText(body, "plain"))

    # Add the attachments to the email
    for (file, name) in attachments:
        # Open files in binary mode
        with open(file, "rb") as attachment:
            # Add file as application/octet-stream
            # Email client can usually download this automatically as attachment
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            # Encode file in ASCII characters to send by email
            encoders.encode_base64(part)
            # Add header as key/value pair to attachment part
            part.add_header("Content-Disposition", "attachment; filename={}".format(name))
            # Add attachment to message
            message.attach(part)

    # Convert the final message to text
    text = message.as_string()

    # Try to send the email
    try:
        context = ssl.create_default_context()
        server = smtplib.SMTP(server_uri, server_port)
        server.ehlo() # Can be omitted
        server.starttls(context=context) # Secure the connection
        server.ehlo() # Can be omitted
        server.login(user, pwd)
        server.sendmail(sender, recipients, text)
    except Exception as e:
        print(e)
    finally:
        server.quit()

# ----------------------------------------
# Helpers

def RandomWithNDigits(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return randint(range_start, range_end)

def ReadTemplate(path):
    print("Reading template file {}".format(path))
    with open(path, "r") as template:
        return template.read()

def ReadIgnoreFile(path):
    print("Reading ignore file {}".format(path))
    try:
        with open(path, "r") as ignore:
            emails = [line.rstrip() for line in ignore]
            return emails
    except FileNotFoundError as e:
        print("Ignore file {} does not exist. Skipping it.".format(path))
        return []

def AppendEmailToIgnoreFile(path, email):
    with open(path, "a") as ignore:
        ignore.write("{}\n".format(email))

# ----------------------------------------
# Parsing CLI options

help_text = """%prog [options] /path/to/fire/submissions.tar.gz

Available variables for template files:
  * student: student email address (the recipient)
  * peer1:   peer #1 email address
  * peer2:   peer #2 email adresss
  * pdf1:    peer #1 PDF attachment name
  * pdf2:    peer #2 PDF attachment name"""

parser = OptionParser(usage=help_text)
parser.add_option("--cid",     dest="cid",     default=None,                               metavar="CID",    help="sender Chalmers CID")
parser.add_option("--pwd",     dest="pwd",     default=None,                               metavar="PWD",    help="sender Chalmers password")
parser.add_option("--bcc",     dest="bcc",     default=[],            action="append",     metavar="EMAIL",  help="add an extra bcc recipient (can be used multiple times)")
parser.add_option("--subject", dest="subject", default="subject.txt",                      metavar="PATH",   help="email subject template file")
parser.add_option("--body",    dest="body",    default="body.txt",                         metavar="PATH",   help="email body template file")
parser.add_option("--ignore",  dest="ignore",  default="sent.log",                         metavar="PATH",   help="ignore sending emails to certain students from a file")
parser.add_option("--rate",    dest="rate",    default=10,            type=int,            metavar="PATH",   help="email sending rate (in seconds)")
parser.add_option("--dry",     dest="dry",     default=False,         action="store_true",                   help="process everything but do not send any emails")

# ----------------------------------------
# if-name-main

if __name__ == '__main__':

    # Parse CLI options
    (opts, args) = parser.parse_args()
    if len(args) != 1:
        parser.print_help()
        exit()

    # Extract the CLI options, asking for input if cid/pass were not provided
    tar_file = args[0]
    cid = opts.cid if opts.cid is not None else input("Enter your Chalmers CID: ")
    pwd = opts.pwd if opts.pwd is not None else getpass("Enter your password: ")
    bcc = opts.bcc
    subject_template_file = opts.subject
    body_template_file = opts.body
    ignore_file = opts.ignore
    rate = opts.rate
    dry = opts.dry

    ignored_emails = ReadIgnoreFile(ignore_file)
    if len(ignored_emails) > 0:
        print("Ignoring the following emails:")
        for email in ignored_emails:
            print("* {}".format(email))

    # Create the reviewing jobs
    jobs = AssignReviewers(tar_file)

    # Read the template files
    subject_template = ReadTemplate(subject_template_file)
    body_template    = ReadTemplate(body_template_file)

    # Start sending emails
    for student, (job1, job2) in jobs.items():

        # Skip ignored emails
        if student in ignored_emails:
            continue

        # Unpack the jobs of this student
        (peer1, peer1_pdf_path, peer1_pdf_name) = job1
        (peer2, peer2_pdf_path, peer2_pdf_name) = job2

        # Fill the message subject and body templates
        template_vars = {
            "student" : student,
            "peer1" : peer1, "pdf1" : peer1_pdf_name,
            "peer2" : peer2, "pdf2" : peer2_pdf_name
        }
        subject = subject_template.format(**template_vars)
        body    = body_template.format(**template_vars)

        # Prepare the attachments
        attachments = [
            (peer1_pdf_path, peer1_pdf_name),
            (peer2_pdf_path, peer2_pdf_name)
        ]

        if dry:
            print("Pretending to send email to {} (BCC={}) (attachments={})".format(student, bcc, attachments))
        else:
            # Email server goes brrr
            print("Sending email to {} (BCC={}) (attachments={})".format(student, bcc, attachments))
            SendChalmersEmail(cid, pwd, student, subject, body, attachments, bcc)

        # Save this email for later in case we hit the rate limit
        AppendEmailToIgnoreFile(ignore_file, student)

        # Wait a bit to not overwhelm the server
        time.sleep(rate)
