# Social network for diaries publishing.
___
### Description
The project is built on the classic Django MVT architecture. Provides pagination and caching. Registration is implemented with data verification, password change and recovery via mail. Tests have been written using Unittest module to test the service.
___
### Technology stack
![python](https://img.shields.io/badge/Python-3.9-%233776AB?style=plastic&logoColor=purple&link=%233776AB)
![Django](https://img.shields.io/badge/Django-2.2.16-%233776AB?style=plastic&logoColor=purple&link=%233776AB)
![requests](https://img.shields.io/badge/Requests-2.26-%233776AB?style=plastic&logoColor=purple&link=%233776AB)
___
### Installation and running
Clone the repository using this command

```
git clone git@github.com:Pugaman22/Social-network-Yatube-.git
```
Go to the project folder

```
cd yatube
```
Create and activate a virtual environment
```
WIN: python -m venv venv
MAC: python3 -m venv venv
```
Install dependencies from the requirements.txt file
```
WIN: python -m pip install --upgrade pip
MAC: python3 -m pip install --upgrade pip
```
```
pip install -r requirements.txt
```
Execute migrations
```
WIN: python manage.py migrate
MAC: python3 manage.py migrate
```
Run the project
```
WIN: python manage.py runserver
MAC: python3 manage.py runserver
```
