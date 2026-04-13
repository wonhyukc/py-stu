import imaplib
import sys

def test_imap(server, port, user, pwd):
    try:
        mail = imaplib.IMAP4_SSL(server, port)
        mail.login(user, pwd)
        print(f'Successfully connected to {server}')
        mail.logout()
    except Exception as e:
        print(f'Failed {server}: {e}')

test_imap('imap.gmail.com', 993, 'wonhyukc@stu.ac.kr', 'wjd!tjdnf4')
test_imap('outlook.office365.com', 993, 'wonhyukc@stu.ac.kr', 'wjd!tjdnf4')
