import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os

load_dotenv()
ID = os.getenv('ID')
PW = os.getenv('PW')

def test_login():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    
    # 1. Get initial login page
    url_login_page = 'https://mail.stu.ac.kr/stu/login/login.crinity'
    r = session.get(url_login_page)
    print("GET Login Page Status:", r.status_code)
    
    # Extract any hidden fields or tokens if present
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Crinity webmail usually uses standard form data
    data = {
        'userId': ID,
        'userPw': PW,
        # Default typical Crinity hidden fields (these might need adjusting based on literal HTML)
        'cmd': 'login',
        'domain': 'stu.ac.kr'
    }
    
    # Look for form
    form = soup.find('form')
    if form:
        for input_tag in form.find_all('input', type='hidden'):
            if input_tag.get('name') and input_tag.get('value'):
                data[input_tag.get('name')] = input_tag.get('value')
                
    print("Login Data payload:", {k: (v if k != 'userPw' else '***') for k, v in data.items()})

    # 2. Try POSTing to login action
    # Form action might be different
    action_url = form.get('action') if form else '/stu/login/login.crinity'
    if not action_url.startswith('http'):
        action_url = 'https://mail.stu.ac.kr' + action_url
        
    r2 = session.post(action_url, data=data)
    print("POST Login Status:", r2.status_code)
    print("Post-login Cookies:", session.cookies.get_dict())
    
    if 'logout' in r2.text.lower() or 'inbox' in r2.text.lower() or 'mail_list' in r2.text.lower() or r2.url != url_login_page:
        print("Login seems successful!")
    else:
        print("Login might have failed. URL:", r2.url)

if __name__ == '__main__':
    test_login()
