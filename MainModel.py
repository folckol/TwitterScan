import random
import ssl
import time
import traceback

import cloudscraper
import requests
import warnings

import ua_generator
import web3
from bs4 import BeautifulSoup

from logger import logger

warnings.filterwarnings("ignore", category=DeprecationWarning)



class TwitterScan:

    def __init__(self, address, email, auth_token, ct0, proxy, discordToken, invite=None):

        self.token = None

        self.address, self.email, self.auth_token, self.ct0, self.invite, self.discordToken = web3.Web3.to_checksum_address(address), email, auth_token,ct0,invite, discordToken
        self.session = self._make_scraper
        self.session.proxies = {"http": f"http://{proxy.split(':')[2]}:{proxy.split(':')[3]}@{proxy.split(':')[0]}:{proxy.split(':')[1]}",
                                "https": f"http://{proxy.split(':')[2]}:{proxy.split(':')[3]}@{proxy.split(':')[0]}:{proxy.split(':')[1]}"}
        adapter = requests.adapters.HTTPAdapter(max_retries=3)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        self.session.headers.update({"user-agent": ua_generator.generate().text,
                                     'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'})

    def Authorization(self):

        payload = {'wallet_type': 'MetaMask',
                    'main_chain': 'ethereum',
                    'erc20_addr': self.address,
                    'invite_code': self.invite if self.invite!=None else '',
                    'invite_way': '',
                    'invite_p1': ''}

        with self.session.post('https://api.twitterscan.com/appapi/user/login', data=payload) as response:
            self.token = response.json()['data']['token']
            self.session.headers.update({'ts-token': self.token})
            # print(response.json())
            return response.json()

    def ConnectTwitter(self):

        with self.session.get('https://api.twitterscan.com/appapi/user/bind-twitter-step1?callback_path=%2Fuser%2Fsetting&way=bind') as response:

            self.session.cookies.update({'auth_token': self.auth_token,
                                         'ct0': self.ct0})

            oauth_token = response.json()['data'].split('oauth_token=')[-1]
            with self.session.get(response.json()['data']) as response:

                soup = BeautifulSoup(response.text, 'html.parser')

                authenticity_token = soup.find('input', attrs={'name': 'authenticity_token'}).get('value')
                # print(authenticity_token)

                payload = {'authenticity_token': authenticity_token,
                           'redirect_after_login': f'https://api.twitter.com/oauth/authorize?oauth_token={oauth_token}',
                           'oauth_token': oauth_token}

                self.session.headers.update({'content-type': 'application/x-www-form-urlencoded'})

                with self.session.post(f"https://api.twitter.com/oauth/authorize", data=payload,
                                       timeout=15) as response:

                    soup = BeautifulSoup(response.text, 'html.parser')

                    # print(soup)

                    link = soup.find('a', class_='maintain-context').get('href')

                    with self.session.get(link,
                                          data=payload, timeout=30,
                                          allow_redirects=False) as response:

                        return 1

    def ConnectMail(self):

        self.session.headers.update({'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'})

        payload = {'email': self.email}

        with self.session.post('https://api.twitterscan.com/appapi/user/bind-email', data=payload) as response:
            if response.json()['data'] == True:
                return 1
            else:
                return 0

    def ConnectDiscord(self):

        with self.session.get('https://api.twitterscan.com/appapi/user/bind-discord?callback_path=%2Fuser%2Fsetting') as response:
            link = response.json()['data']
            # input()

            discord_headers = {
                'authority': 'discord.com',
                'authorization': self.discordToken,
                'content-type': 'application/json',
                'x-super-properties': 'eyJvcyI6Ik1hYyBPUyBYIiwiYnJvd3NlciI6IkNocm9tZSIsImRldmljZSI6IiIsInN5c3RlbV9sb2NhbGUiOiJydS1SVSIsImJyb3dzZXJfdXNlcl9hZ2VudCI6Ik1vemlsbGEvNS4wIChNYWNpbnRvc2g7IEludGVsIE1hYyBPUyBYIDEwXzE1XzcpIEFwcGxlV2ViS2l0LzUzNy4zNiAoS0hUTUwsIGxpa2UgR2Vja28pIENocm9tZS8xMDkuMC4wLjAgU2FmYXJpLzUzNy4zNiIsImJyb3dzZXJfdmVyc2lvbiI6IjEwOS4wLjAuMCIsIm9zX3ZlcnNpb24iOiIxMC4xNS43IiwicmVmZXJyZXIiOiIiLCJyZWZlcnJpbmdfZG9tYWluIjoiIiwicmVmZXJyZXJfY3VycmVudCI6IiIsInJlZmVycmluZ19kb21haW5fY3VycmVudCI6IiIsInJlbGVhc2VfY2hhbm5lbCI6InN0YWJsZSIsImNsaWVudF9idWlsZF9udW1iZXIiOjE3NDA1MSwiY2xpZW50X2V2ZW50X3NvdXJjZSI6bnVsbCwiZGVzaWduX2lkIjowfQ==',
            }

            payload = {"permissions": "0", "authorize": True}

            with self.session.post(link,json=payload, timeout=15, headers=discord_headers) as response:
                url = response.json()['location']
                # print(url)
                self.code = url.split('code=')[-1]

                with self.session.get(url, timeout=15) as response:
                    # print(response.text)
                    pass

    @property
    def _make_scraper(self):
        ssl_context = ssl.create_default_context()
        ssl_context.set_ciphers(
            "ECDH-RSA-NULL-SHA:ECDH-RSA-RC4-SHA:ECDH-RSA-DES-CBC3-SHA:ECDH-RSA-AES128-SHA:ECDH-RSA-AES256-SHA:"
            "ECDH-ECDSA-NULL-SHA:ECDH-ECDSA-RC4-SHA:ECDH-ECDSA-DES-CBC3-SHA:ECDH-ECDSA-AES128-SHA:"
            "ECDH-ECDSA-AES256-SHA:ECDHE-RSA-NULL-SHA:ECDHE-RSA-RC4-SHA:ECDHE-RSA-DES-CBC3-SHA:ECDHE-RSA-AES128-SHA:"
            "ECDHE-RSA-AES256-SHA:ECDHE-ECDSA-NULL-SHA:ECDHE-ECDSA-RC4-SHA:ECDHE-ECDSA-DES-CBC3-SHA:"
            "ECDHE-ECDSA-AES128-SHA:ECDHE-ECDSA-AES256-SHA:AECDH-NULL-SHA:AECDH-RC4-SHA:AECDH-DES-CBC3-SHA:"
            "AECDH-AES128-SHA:AECDH-AES256-SHA"
        )
        ssl_context.set_ecdh_curve("prime256v1")
        ssl_context.options |= (ssl.OP_NO_SSLv2 | ssl.OP_NO_SSLv3 | ssl.OP_NO_TLSv1_3 | ssl.OP_NO_TLSv1)
        ssl_context.check_hostname = False

        return cloudscraper.create_scraper(
            debug=False,
            ssl_context=ssl_context
        )


if __name__ == '__main__':

    print(' ___________________________________________________________________\n'
          '|                       Rescue Alpha Soft                           |\n'
          '|                   Telegram - @rescue_alpha                        |\n'
          '|                   Discord - discord.gg/438gwCx5hw                 |\n'
          '|___________________________________________________________________|\n\n\n')

    delay = (1, 10)
    refCount = (5 , 20)
    EmailConnect = 1
    TwitterConnect = 1
    DiscordConnect = 1

    try:
        with open('config', 'r', encoding='utf-8') as file:
            for i in file:
                if 'delay=' in i.rstrip():
                    delay = (int(i.rstrip().split('delay=')[-1].split('-')[0]), int(i.rstrip().split('delay=')[-1].split('-')[1]))
                if 'refCount=' in i.rstrip():
                    refCount = (int(i.rstrip().split('refCount=')[-1].split('-')[0]), int(i.rstrip().split('refCount=')[-1].split('-')[1]))
                if 'EmailConnect=' in i.rstrip():
                    EmailConnect = int(i.rstrip().split('EmailConnect=')[-1])
                if 'TwitterConnect=' in i.rstrip():
                    TwitterConnect = int(i.rstrip().split('TwitterConnect=')[-1])
                if 'DiscordConnect=' in i.rstrip():
                    DiscordConnect = int(i.rstrip().split('DiscordConnect=')[-1])
    except:
        traceback.print_exc()
        print('Вы неправильно настроили конфигуратор, повторите попытку')
        input()
        exit(0)

    # print(True if DiscordConnect else False)

    discords = []
    twitters = []
    emails = []
    addresses = []
    proxy = []

    if TwitterConnect:
        with open('InputData/TwitterData.txt', 'r', encoding='utf-8') as file:
            for i in file:
                twitters.append([i.rstrip().split('auth_token=')[-1].split(';')[0], i.rstrip().split('ct0=')[-1].split(';')[0]])

    if DiscordConnect:
        with open('InputData/DiscordData.txt', 'r', encoding='utf-8') as file:
            for i in file:
                discords.append(i.rstrip())

    if EmailConnect:
        with open('InputData/Emails.txt', 'r', encoding='utf-8') as file:
            for i in file:
                emails.append(i.rstrip())

    with open('InputData/WalletData.txt', 'r', encoding='utf-8') as file:
        for i in file:
            addresses.append(i.rstrip())

    with open('InputData/Proxy.txt', 'r', encoding='utf-8') as file:
        for i in file:
            proxy.append(i.rstrip())

    startRefCount = None
    endRefCount = None

    inviteLink = None
    count = 0
    while count < len(proxy):

        try:

            try:
                if startRefCount > endRefCount:
                    inviteLink = None
            except:
                inviteLink=None

            if inviteLink == None:
                startRefCount = 0
                endRefCount = random.randint(refCount[0], refCount[1]+1)


            acc = TwitterScan(address=addresses[count],
                              email = emails[count] if EmailConnect else None,
                              auth_token = twitters[count][0] if TwitterConnect else None,
                              ct0 = twitters[count][1] if TwitterConnect else None,
                              proxy = proxy[count],
                              discordToken=discords[count] if DiscordConnect else None,
                              invite = inviteLink if inviteLink!=None else ''
            )

            data = acc.Authorization()
            if startRefCount == 0:
                inviteLink = data['data']['invite_code']

            if startRefCount != 0:
                logger.success(f'{count+1} - Регистрация пройдена')
                logger.success(f'{count+1} - На рефовода нагнано {startRefCount}/{endRefCount} рефералов')
            else:

                logger.success(f'{count+1} - Регистрация рефовода пройдена')

            startRefCount += 1

            if TwitterConnect:
                try:
                    acc.ConnectTwitter()
                    logger.info(f'{count+1} - Твиттер подключен')
                except Exception as e:
                    logger.info(f'{count+1} - Произошла ошибка, твиттер не удалось подключить ({str(e)})')

            if EmailConnect:
                try:
                    acc.ConnectMail()
                    logger.info(f'{count+1} - Почта подключена')
                except Exception as e:
                    logger.info(f'{count+1} - Произошла ошибка, почту не удалось подключить ({str(e)})')

            if DiscordConnect:
                try:
                    acc.ConnectDiscord()
                    logger.info(f'{count+1} - Дискорд подключен')
                except Exception as e:
                    logger.info(f'{count+1} - Произошла ошибка, дискорд не удалось подключить ({str(e)})')

            logger.info('\n')


        except Exception as e:

            logger.error(f'{count+1} - {str(e)}')

        time.sleep(random.randint(delay[0], delay[1]))
        count+=1

    input('\n\n Скрипт завершил работу, все логи находятся в папке Logs')

