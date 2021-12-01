#!/bin/env python3

import os, sys
import string
import glob, re
import smtplib, ssl, email
import time

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ----------------------------------------
# Read a submission directory created by Fire and assign peer reviewers

def AssignReviewers(tar_file):

    # Create a new directory and extract the submissions inside
    subs_dir = "submissions"
    print("Extracting %s to %s " % (tar_file, subs_dir))
    tar_file = re.escape(glob.glob(tar_file)[0])
    os.mkdir(subs_dir)
    os.system("tar -xvf %s --directory %s --strip-components=1 > /dev/null" % (tar_file, subs_dir))

    # Read the student emails from the extracted submissions and create a dictionary of review jobs
    students = [ os.path.basename(folder) for folder in glob.glob("%s/*" % subs_dir) ]
    peers1 = students[1::] + students[0:1]
    peers2 = students[2::] + students[0:2]

    jobs = dict()
    for (student, peer1, peer2) in zip(students, peers1, peers2):
        # Find the PDFs to review
        peer1_pdfs = glob.glob("%s/%s/*.pdf" % (subs_dir, peer1))
        peer2_pdfs = glob.glob("%s/%s/*.pdf" % (subs_dir, peer2))

        print("%s will review: %s, %s" % (student, peer1, peer2))

        if len(peer1_pdfs) != 1 or len(peer2_pdfs) != 1:
            print("ERROR! Found multiple submitted PDFs when creating tasks for %s" % student)
            exit()

        # Save the student's jobs
        jobs[student] = [
            (peer1, peer1_pdfs[0], "summary1.pdf"),
            (peer2, peer2_pdfs[0], "summary2.pdf")
        ]

    return jobs

# ----------------------------------------
# Send an email using Chalmers credentials

def SendChalmersEmail(cid, pwd, recipient, subject, body, attachments=[], bcc=None):
    print("Sending email to %s, with attachments %s" % (recipient, attachments))

    # Connection details
    server_uri = "smtp.chalmers.se"
    server_port = 587
    user = "net.chalmers.se\\" + cid
    sender = cid + "@chalmers.se"

    # Create a multipart message and set headers
    message = MIMEMultipart()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    if cco is not None:
        message["Bcc"] = bcc

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
            part.add_header("Content-Disposition", "attachment; filename=%s" % name)
            # Add attachment to message
            message.attach(part)

    # Convert the final message to text
    text = message.as_string()

    # Send the email
    try:
        context = ssl.create_default_context()
        server = smtplib.SMTP(server_uri, server_port)
        server.ehlo() # Can be omitted
        server.starttls(context=context) # Secure the connection
        server.ehlo() # Can be omitted
        server.login(user, pwd)
        server.sendmail(sender, recipient, text)
    except Exception as e:
        print(e)
    finally:
        server.quit()

# ----------------------------------------
# if-name-main

if __name__ == '__main__':

    if len(sys.argv) != 2:
        print("USAGE: %s path/to/fire/submissions.tar.gz" % sys.argv[0])
        exit()

    # Create the reviewing jobs
    tar_file = sys.argv[1]
    jobs = AssignReviewers(tar_file)

    # Ask for credentials
    cid = input("Enter your Chalmers CID: ")
    pwd = input("Enter your password: ")

    # The email subject template
    subject_template = "[DAT315/DIT199] Peer review exercise (%s)"
    
    # The email body template
    body_template = "\r\n".join([
        "Hi %s!",
        "",
        "You were assigned to review the summaries of the following students:",
        "  * %s: %s",
        "  * %s: %s",
        "",
        "When your reviews are ready:",
        "  * Send them to their corresponding authors via email.",
        "  * Submit them to Fire under \"Summary (peer reviews)\". The deadline for this is 2021-12-06 @ 23:59.",
        "",
        "Thank you for your work!",
        "",
        "Best,",
        "The Computer Scientist in Society Team",
        "",
        "PS: this email was generated automatically. If you see anything weird going on please let me know asap!"
    ])

    for student in jobs:
        
        (peer1, peer1_pdf_path, peer1_pdf_name) = jobs[student][0]
        (peer2, peer2_pdf_path, peer2_pdf_name) = jobs[student][1]

        subject = subject_template % (
            student
        )
        
        body = body_template % (
            student,
            peer1, peer1_pdf_name,
            peer2, peer2_pdf_name,
        )

        attachments = [
            (peer1_pdf_path, peer1_pdf_name),
            (peer2_pdf_path, peer2_pdf_name)
        ]

        bcc = None
        
        # Send the email!
        SendChalmersEmail(cid, pwd, student, subject, body, attachments, bcc)
        time.sleep(1)
