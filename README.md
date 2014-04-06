bytehand
========

Python module for work with sms gateway [bytehand.com](https://www.bytehand.com)

## Why to use bytehand?

* You can use it **free** if your sms traffic is low (< ~15 sms/day)

* It has simple http api wrapped in this python module =)

## Quick start

### 1. Get your user id and api key

For using bytehand you need to register [here](https://www.bytehand.com/registration).

After you pass registration you should get your *user id* and *key*
for access to api functions.

### 2. Create connection

    >>> USER_ID, KEY = 0000, 'your_key'
    >>> import bytehand
    >>> conn = bytehand.Connection(userid=USER_ID, key=KEY)

### 3. Approve your signature

Try to type clear well-formed description for your signature.
It will be faster approved by bytehand moderator.

    >>> conn.new_signature(
    ...     'vladimir',
    ...     'Personal signature.'
    ... )
    >>> conn.signature('vladimir')['state']
    'NEW'

#### Get signature faster

You can sign your sms by your phone number and approove this signature
in 2 minutes.

Use this [page](https://www.bytehand.com/secure/add_signature).

### 4. Wait for signature approving and send your sms

    >>> conn.signature('vladimir')['state']
    'ACCEPTED'
    >>> response = conn.send(
    ...     to=79629411407,
    ...     text='Hello, Dmitriy!',
    ...     signature='vladimir'
    ... )
    >>> response.is_delivered
    True
