import smtplib
import json

CONFIG_FILE = '/Users/Chafik/workspace/python/my_projects/crypto_currency/tradox/data/email/config.json'
__USERNAME = None
__PASSWORD = None
__SERVER = None
__TO = []


def __init():
    global __USERNAME, __PASSWORD, __SERVER, __TO
    d = json.load(open(CONFIG_FILE))
    __USERNAME, __PASSWORD, __SERVER, __TO = d['username'], d['password'], d['server'], d['to']


def send_email(title, body):
    if not __USERNAME:
        __init()
    server = smtplib.SMTP(__SERVER)
    server.ehlo()
    server.starttls()
    server.login(__USERNAME, __PASSWORD)
    msg = 'Subject: {}\n\n{}'.format(title, body)
    server.sendmail(__USERNAME, __TO, msg)
    server.quit()


def report_email(fn):
    import inspect
    varList, _, _, default = inspect.getargspec(fn)
    d = {}
    if default is not None:
        d = dict((varList[-len(default):][i], v) for i, v in enumerate(default))

    def f(*argt, **argd):
        d.update(dict((varList[i], v) for i, v in enumerate(argt)))
        d.update(argd)
        send = d.get('send', None)
        if send:
            msg = d.get('msg','')
            title = '[Tradox] - Trade report'
            send_email(title, msg)
        fn(*argt, **argd)

    return f
