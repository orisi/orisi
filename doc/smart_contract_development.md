
# This docs are no longer valid. New ones in the works.

# What is Oracle's workflow?


Oracle has a very straightforward flow. It accepts given numer of smartcontracts. They can be easily added to Oracle.

Every Oracle monitors Bitmessage chan that they use to communicate with the world. They read every message and check if the messages there are valid JSON's. If the message is a valid JSON, they check if it has ```operation``` field and if they can handle that operation. 

If they know how to handle operation they check if the JSON from message has all the fields required by the operation. Every operation define smart contract.

When Oracle will see that there is a **handler** for the operation it will delegate methods responsible for handling operation requests to it. You can easily write your own *handlers*. They can define smart contracts. If smart contracts are a little bit more complicated - one smart contract can be defined by few handlers (you can see that behaviour with *bounty_create* that is handled by PasswordTransactionRequestHandler and GuessPasswordHandler). The more back and forth - the more handlers you should write.

### How does a handler work?

Handlers should derive from ```BaseHandler```.

Handler should parse requests and check if they are valid. If so - they should do all the work they need in ```handle_request``` function. Especially they can create *tasks*.
A task is just a simple database entry:

```json
{
    "operation": "your_operation",
    "json_data": "write_your_data_here",
    "next_check": 123,
    "done": 1,
    "filter_field":"cat:id" 
}
```

```next_check``` epoch time - when your task should be taken?

```done``` is your task done?

```filter_field``` it can look for example like ```my_task:10932trgji0gf90f34```. This field can be useful when you'll choose a task you want to perform.

Why do you need a task actually? Imagine - your transaction is just a bet - if Germany will win 2014 Football tournament - you want to perform one transaction, but if not - other. You need to wait.

### filter_tasks
```filter_tasks``` is a method your handler needs to implement. It will be used by you to optimize which task are actually relevant. For example - you have a bounty - whoever will call the smallest number - will get that number in cash. It's tricky which number to give to have a chance to win anything. Of course you can kill the mood by giving 0.. 

After all people will cast their votes - you'll want to perform tasks. In ```filter_tasks``` you can fetch all the tasks that are similar to current one (hey, use ```filter_field```!), choose the one with smallest amount, mark all other as done and return only the one you want to perform (or few, you are returning a list!). That way your oracle won't work more than needed and it's logic will be easier.

### handle_task

After you will choose your tasks with `filter_tasks`, for every returned task the method ```handle_task```, with this task as argument, will be called. Do all the work you need here, and then **mark task as done** (if you are done with it).

### Database
If you need to save any data - feel free to use Oracle's database. You can just define your own Database classes (look at some examples at ```oracle_db.py```, or ```password_db.py```).

Have fun!
