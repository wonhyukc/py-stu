import imaplib

try:
    mail = imaplib.IMAP4_SSL('mail.stu.ac.kr', 993)
    mail.login('wonhyukc', 'wjd!tjdnf4')
    print('Successfully connected to mail.stu.ac.kr (SSL)')
    mail.logout()
except Exception as e:
    print(f'Failed SSL: {e}')

try:
    mail = imaplib.IMAP4('mail.stu.ac.kr', 143)
    mail.login('wonhyukc', 'wjd!tjdnf4')
    print('Successfully connected to mail.stu.ac.kr (Plain/TLS)')
    mail.logout()
except Exception as e:
    print(f'Failed Plain/TLS: {e}')
