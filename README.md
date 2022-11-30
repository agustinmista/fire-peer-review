# FirePeerReview

A small Python script to send Fire submissions via email for peer review.

* Creates two review jobs for each submission.
* The email subject and body can be changed in the template files.
* Credentials can be passed via CLI arguments or interactively.
* The `test_submission.tar.gz` is provided to run tests before using it for real.

## Command-line options

```
$ ./FirePeerReview.py --help
Usage: FirePeerReview.py [options] /path/to/fire/submissions.tar.gz

Available variables for template files:
  * student: student email address (the recipient)
  * peer1:   peer #1 email address
  * peer2:   peer #2 email adress
  * pdf1:    peer #1 PDF attachment name
  * pdf2:    peer #2 PDF attachment name

Options:
  -h, --help      show this help message and exit
  --cid=CID       sender Chalmers CID
  --pwd=PWD       sender Chalmers password
  --bcc=EMAIL     add an extra bcc recipient (can be used multiple times)
  --subject=PATH  email subject template file
  --body=PATH     email body template file
  --dry           process everything but do not send any emails
```

## Usage example

```
./FirePeerReview.py test_submission.tar.gz --bcc=someone@somewhere.com
Enter your Chalmers CID: <my_cid>
Enter your password: <my_password>
Extracting test_submission.tar.gz to submissions_2727
Assigning jobs:
* bar@bar.com will review: baz@baz.com, foo@foo.com
* baz@baz.com will review: foo@foo.com, bar@bar.com
* foo@foo.com will review: bar@bar.com, baz@baz.com
Reading template file subject.txt
Reading template file body.txt
Processing student bar@bar.com
Sending email to bar@bar.com (BCC=['someone@somewhere.com']) (attachments=[('submissions_2727/baz@baz.com/baz.pdf', 'baz.pdf'), ('submissions_2727/foo@foo.com/foo.pdf', 'foo.pdf')])
Processing student baz@baz.com
Sending email to baz@baz.com (BCC=['someone@somewhere.com']) (attachments=[('submissions_2727/foo@foo.com/foo.pdf', 'foo.pdf'), ('submissions_2727/bar@bar.com/bar.pdf', 'bar.pdf')])
Processing student foo@foo.com
Sending email to foo@foo.com (BCC=['someone@somewhere.com']) (attachments=[('submissions_2727/bar@bar.com/bar.pdf', 'bar.pdf'), ('submissions_2727/baz@baz.com/baz.pdf', 'baz.pdf')])
```