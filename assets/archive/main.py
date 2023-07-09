import asyncio
from pantheon import pantheon

from utils import configuration

settings = configuration.settings
server = "na1"
api_key = settings.api_key


def requestsLog(url, status, headers):
    print(url)
    print(status)
    print(headers)


panth = pantheon.Pantheon(
    server, api_key, requests_logging_function=requestsLog, debug=True)


async def getSummonerId(name):
    try:
        data = await panth.get_tft_summoner_by_name(name)
        return (data['id'], data['accountId'], data['puuid'])
    except Exception as e:
        print(e)


async def getRecentMatchlist(accountId):
    try:
        data = await panth.get_matchlist(accountId, params={"count":2})
        return data
    except Exception as e:
        print(e)


async def getRecentMatches(accountId):
    try:
        matchlist = await getRecentMatchlist(accountId)
        tasks = [panth.get_match(match)
                 for match in matchlist]
        return await asyncio.gather(*tasks)
    except Exception as e:
        print(e)

async def getTFTRecentMatchlist(accountId):
    try:
        data = await panth.get_tft_matchlist(accountId, count = 2)
        print(f'data: {data}')
        return data
    except Exception as e:
        print(e)


async def getTFTRecentMatches(accountId):
    try:
        matchlist = await getTFTRecentMatchlist(accountId)
        tasks = [panth.get_tft_match(match)
                 for match in matchlist]
        return await asyncio.gather(*tasks)
    except Exception as e:
        print(e)

if __name__ == '__main__':
    name = "fury hawkx"

    loop = asyncio.get_event_loop()

    (id, summonerId, accountId) = loop.run_until_complete(getSummonerId(name))

    print(f'summonerId: {summonerId}')
    print(f'accountId: {accountId}')
    print(f'getRecentMatches: {loop.run_until_complete(getRecentMatches(accountId))}')
