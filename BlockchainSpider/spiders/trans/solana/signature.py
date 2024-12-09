import scrapy
import json
import pandas as pd
from BlockchainSpider import settings
from BlockchainSpider.items.solana import SignatureItem, TransactionsItem
from BlockchainSpider.utils.bucket import AsyncItemBucket



class SolScanSpider(scrapy.Spider):
    name = 'solana.signature'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.solana.SignaturePipeline': 299,
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
        df = pd.read_csv('D:\Blockchainspider\BlockchainSpider\data\\addresses.csv')
        signatures = df['address']
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
            cb_kwargs={'address': signatures},
        )
    async def _start_requests(self,response: scrapy.http.Response,**kwargs):
        addresses = kwargs.get('address')
        for addr in addresses:
            yield await self.get_request_solana_signaturesforaddress(addr)


    async def get_request_solana_signaturesforaddress(self, address: str) -> scrapy.Request:
        print(address)
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [
                    address,
                ]
            }),
            callback=self.parse_signature,
            cb_kwargs={'address': address},
        )

    async def parse_signature(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        address = kwargs.get('address')
        print(address)
        if  len(result['result'])<1000:
            for i in range(len(result['result'])):
                yield SignatureItem(
                    address=address,
                    signature=result['result'][i]['signature'],
                )
        else:
            before = result['result'][999]['signature']
            for i in range(len(result['result'])):
                yield SignatureItem(
                    address=address,
                    signature=result['result'][i]['signature'],
                )
            yield scrapy.Request(
                url=await self.provider_bucket.get(),
                method='POST',
                headers={'Content-Type': 'application/json'},
                body=json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getSignaturesForAddress",
                    "params": [
                        address,
                        {
                            "before": before
                        }
                    ]
                }),
                callback=self.parse_signature,
                cb_kwargs={'address': address},
            )
