import scrapy
import json
import pandas as pd
from BlockchainSpider import settings
from BlockchainSpider.items.solana import TokenAccountItem
from BlockchainSpider.utils.bucket import AsyncItemBucket



class SolScanSpider(scrapy.Spider):
    name = 'solana.tokenaccount'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.solana.TokenAccountPipeline': 299,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        }
}


    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.out_dir = kwargs.get('out', './data')

        assert kwargs.get('providers') is not None, "please input providers separated by commas!"
        self.provider_bucket = AsyncItemBucket(
            items=kwargs.get('providers').split(','),
            qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
        )

    def start_requests(self):
        df = pd.read_csv('D:\Blockchainspider\BlockchainSpider\data\\AccountInfo.csv')
        address = df['address']
        yield scrapy.Request(
            url=self.provider_bucket.items[0],
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSlot"
            }),
            callback=self._start_requests,
            cb_kwargs={'address':address},
        )
    async def _start_requests(self,response: scrapy.http.Response,**kwargs):
        addresses = kwargs.get('address')
        for addr in addresses:
            yield await self.get_request_solana_getTokenAccountsByOwner(addr)


    async def get_request_solana_getTokenAccountsByOwner(self, address: str) -> scrapy.Request:
        print(address)
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenAccountsByOwner",
                "params": [
                    address,
                    {
                        "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
                    },
                    {
                        "encoding": "jsonParsed"
                    }
                ]
            }),
            callback=self.parse_getTokenAccountsByOwner,
            cb_kwargs={'address': address},
        )

    async def parse_getTokenAccountsByOwner(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        address = kwargs.get('address')
        if result['result'].get('value'):
            value = result['result']['value']
            count = len(value)
            for item in value:
                pubkey = item['pubkey']
                item = item['account']['data']['parsed']['info']
                if item['tokenAmount']['amount'] == "0" and item['tokenAmount']['decimals']== 0:
                    type = 'Token'
                    yield TokenAccountItem(
                        owner=item['owner'],
                        count = count,
                        type = type,
                        mint = item['mint'],
                        amount = item['tokenAmount']['amount'],
                        decimals = item['tokenAmount']['decimals'],
                        uiamount = item['tokenAmount']['uiAmount'],
                        pubkey = pubkey,
                    )
                elif item['tokenAmount']['amount'] != "0" and item['tokenAmount']['decimals'] == 0:
                    type = 'NFT'
                    yield TokenAccountItem(
                        owner=item['owner'],
                        count = count,
                        type = type,
                        mint = item['mint'],
                        amount = item['tokenAmount']['amount'],
                        decimals = item['tokenAmount']['decimals'],
                        uiamount = item['tokenAmount']['uiAmount'],
                        pubkey = pubkey,
                    )
                else:
                    type = 'Token'
                    yield TokenAccountItem(
                        owner=item['owner'],
                        count = count,
                        type = type,
                        mint = item['mint'],
                        amount = item['tokenAmount']['amount'],
                        decimals = item['tokenAmount']['decimals'],
                        uiamount = item['tokenAmount']['uiAmount'],
                        pubkey = pubkey,
                    )