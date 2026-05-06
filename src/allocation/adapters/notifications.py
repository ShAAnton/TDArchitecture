import abc
import smtplib
from allocation import config


class Notification(abc.ABC):

    @abc.abstractmethod
    def send(self, destination, message):
        raise NotImplementedError


DEFAULT_HOST = config.get_email_host_and_port()["host"]
DEFAULT_PORT = config.get_email_host_and_port()["port"]


class EmailNotification(Notification):

    def __init__(self, smtp_host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.server = smtplib.SMTP(smtp_host, port=port)
        assert self.server.noop()[0] == 250

    def send(self, destination, message):
        msg = f'Subject: allocation service notification\n{message}'
        self.server.sendmail(
            from_addr='allocations@example.com',
            to_addrs=[destination],
            msg=msg
        )

def send_email(*args):
    print('SENDING EMAIL:', *args)