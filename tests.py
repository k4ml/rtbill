
import time
import sqlite3
import unittest

import rtbill

class TestDBAPICredit(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:', check_same_thread=False) 
        cursor = self.conn.cursor()
        cursor.execute("CREATE TABLE user (id integer PRIMARY KEY, credits DECIMAL)")

    def test_deduct(self):
        initial_credits = 100
        rate = 1
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO user (credits) VALUES ({})".format(initial_credits))
        credit = rtbill.DBAPICredit(self.conn, 'user', 'credits', 1, 'id')
        billing = rtbill.RTBill(credit, rate=rate)
        billing.start()
        time.sleep(5)
        billing.stop()
        time.sleep(2)
        expected_balance = initial_credits - rate
        actual_balance = credit.get_balance()
        assert actual_balance == expected_balance, (actual_balance, expected_balance)

    def test_deduct_2_round(self):
        initial_credits = 100
        rate = 1
        increment = 2
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO user (credits) VALUES ({})".format(initial_credits))
        credit = rtbill.DBAPICredit(self.conn, 'user', 'credits', 1, 'id')
        billing = rtbill.RTBill(credit, rate=rate, increment=increment)
        billing.start()
        time.sleep(5)
        billing.stop()
        time.sleep(2)
        expected_balance = initial_credits - (rate * 2)
        actual_balance = credit.get_balance()
        assert actual_balance == expected_balance, (actual_balance, expected_balance)

if __name__ == '__main__':
    unittest.main()
