# GitHub-ArtemE91 Scoring_OTUS

Project for training. The service has an api for getting a list of interests and scoring points.

## Required
Python 3.7

## Usege example

For runs service in port __8000__, host __localhost__

```
python api.py -p 8000
```

## API

The query structure

```
{"account": "< partner company name>", "login": "< user name>", "method": "<method name>", "token": " 
<authentication token>", "arguments": {<dictionary with arguments of the called method>}} 
```
* `account` - string, optionally, can be empty 
* `login` - string, required, must be empty 
* `method` - string, required, must be empty 
* `token` - string, required, must be empty 
* `arguments` - dictionary (object in json terms ), required, can be empty
  * `phone` - string or number, length 11, starts with 7, optional, can be empty
  * `email` - string that contains @, optionally, can be empty
  * `first_name` - string, optionally, can be empty
  * `last_name` - string, optionally, can be empty
  * `birthday` - date in the format DD. MM.YYYY, with a date that has passed no more than 70 years, optionally, can be empty
  * `gender` - the number 0, 1 or 2, optionally, can be empty
  * `client_ids` - array of numbers, required, not empty date - date in the format DD. MM.YYYY, optionally, can be empty

## Methods
### `online_score`
__Request example__

    ```
    $ curl -X POST -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "h&f", "method":
    "online_score", "token":
    "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd
    "arguments": {"phone": "79175002040", "email": "stupnikov@otus.ru", "first_name": "Стансилав", "last_name":
    "Ступников", "birthday": "01.01.1990", "gender": 1}}' http://127.0.0.1:8080/method/
    ```
    
__Response__

  ```
  {"code": 200, "response": {"score": 5.0}}
  ```
### `clients_interests`
__Request example__

```
$ curl -X POST -H "Content-Type: application/json" -d '{"account": "horns&hoofs", "login": "admin", "method":
"clients_interests", "token":
"d3573aff1555cd67dccf21b95fe8c4dc8732f33fd4e32461b7fe6a71d83c947688515e36774c00fb630b039fe2223c991f045f13f240913860502",
"arguments": {"client_ids": [1,2,3,4], "date": "20.07.2017"}}' http://127.0.0.1:8080/method/
```
__Response__

```
{"code": 200, "response": {"1": ["books", "hi-tech"], "2": ["pets", "tv"], "3": ["travel", "music"], "4":
["cinema", "geek"]}}
```
