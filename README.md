## Generic real-time billing class
This generic billing class can be used in any kind of application
with duration that need to be billed in real-time. Example usage:-

```python
def on_answer(call):
    credit = rtbill.DBAPICredit(conn, 'user', 'credits', 1, 'id')
    call.billing = RTBill(credit, stop_callback=call.hangup)
    call.billing.start()

def on_hangup(call):
    call.billing.stop()
``` 

Pass a `credit` instance, which know how to provide current credits balance and
deduct credits into `RTBill`. It can be instance of any class as long as 2 methods
defined:-

    - `get_balance()`
    - `deduct(amount)`

2 credit class are provided - DBAPICredit and DjangoCredit.
