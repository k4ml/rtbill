## Generic real-time billing class
This generic billing class can be used in any kind of application
with duration that need to be billed in real-time. Example usage:-

```python
def on_answer(call):
    call.billing = RTBill(connection, 'user', 'credits', 1, 'id',
                          stop_callback=call.hangup)
    call.billing.start()

def on_hangup(call):
    call.billing.stop()
``` 
