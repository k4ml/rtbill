"""
Copyright (c) 2017-present Kamal Bin Mustafa <k4ml@github.io>

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""

import queue
import logging
import threading

logger = logging.getLogger(__name__)

class DBAPICredit(object):
    def __init__(self, conn, table, column, account_id, account):
        self.conn = conn
        self.table = table
        self.column = column
        self.account_id = account_id
        self.account = account
        self._params = {
            'column': self.column,
            'table': self.table,
            'account_id': self.account_id,
            'account': self.account,
        }

    def get_balance(self):
        params = self._params
        cursor = self.conn.cursor()
        cursor.execute("SELECT {column} FROM {table} WHERE "
                       "{account_id} = {account}".format(**params))
        return cursor.fetchone()[0]
    
    def deduct(self, rate):
        params = self._params
        params['rate'] = rate
        cursor = self.conn.cursor()
        cursor.execute("UPDATE {table} SET {column} = {column} - {rate} "
                       "WHERE {account_id} = {account}".format(**params))
        self.conn.commit()

class DjangoCredit(object):
    def __init__(self, instance, credit_attr):
        self.instance = instance
        self.credit_attr = credit_attr

    def get_balance(self):
        self.instance.refresh_from_db()
        return getattr(self.instance, self.credit_attr)

    def deduct(self, amount):
        from django.db.models import F
        previous_balance = self.get_balance()
        setattr(self.instance, self.credit_attr, F(self.credit_attr) - amount)
        self.instance.save()
        current_balance = self.get_balance()
        logger.info('amount:{} previous:{} current:{}'.format(amount, previous_balance,
                    current_balance))

class RTBill(object):
    def __init__(self, credit, rate=1, increment=60, stop_callback=None):
        """
        credit should be an instance with 2 methods:-
            - get_balance()
            - deduct(amount)
        """
        self.credit = credit
        self.increment = increment
        self.rate = rate
        self.total_billed = 0
        self.duration = 0
        self.actions = queue.Queue()

        def _default_stop_callback():
            params = (self.duration, self.total_billed)
            print('done, duration:{} total_billed:{}'.format(params))
        self.stop_callback = stop_callback or _default_stop_callback

    def start(self):
        self.thread = threading.Thread(target=self._start_billing)
        self.thread.daemon = True
        self.thread.start()

    def _start_billing(self):
        max_duration = 120 # set max_duration based on credits balance
        print('Start charging ...')
        extra_seconds = 0
        total_billed = 0
        while self.duration <= max_duration:
            self.duration += 1
            try:
                action = self.actions.get(True, 1)
            except queue.Empty:
                if self.duration % self.increment == 0:
                    extra_seconds = 0
                    print("Duration: %d" % (self.duration) )
                    balance = self.credit.get_balance()
                    if balance < 0:
                        logger.info('Out of credits')
                        self.stop_callback()
                        return
                    logger.info('Duration:%s deducting credits current:%s rate:%s' %
                                (self.duration, balance, self.rate))
                    self.credit.deduct(self.rate)
                    self.total_billed += self.rate
                else:
                    extra_seconds += 1
            else:
                if action == 'stop':
                    print('got action stop')
                    break

        print("Billing done, duration:", self.duration, 'extra_seconds:', extra_seconds)
        if extra_seconds > 0:
            logger.info('Charging for extra seconds:%s' % extra_seconds)
            self.credit.deduct(self.rate)
            self.total_billed += self.rate

    def stop(self):
        self.actions.put('stop')
