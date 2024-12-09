import scrapy
import json
import pandas as pd
from BlockchainSpider import settings
from BlockchainSpider.items.solana import AccountInfoItem
from BlockchainSpider.utils.bucket import AsyncItemBucket


class SolScanSpider(scrapy.Spider):
    name = 'solana.accountinfo'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.solana.AccountInfoPipeline': 299,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.addresses = kwargs.get('addresses', '').split(',')
        self.out_dir = kwargs.get('out', './data')

        assert kwargs.get('providers') is not None, "please input providers separated by commas!"
        self.provider_bucket = AsyncItemBucket(
            items=kwargs.get('providers').split(','),
            qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
        )

    def start_requests(self):
        df = pd.read_csv('D:\Blockchainspider\BlockchainSpider\data\\addresses.csv')  # 先爬取自己想要账户的交易签名
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

    async def _start_requests(self, response: scrapy.http.Response,**kwargs):
        addresses = kwargs.get('address')
        for addr in addresses:
            yield await self.get_request_solana_accountinfo(addr)

    async def get_request_solana_accountinfo(self, address: str) -> scrapy.Request:
        print(address)
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [
                    address,
                    {
                        "encoding": "jsonParsed"
                    }
                ]
            }),
            callback=self.parse_accountinfo,
            cb_kwargs={'address': address},
        )

    async def parse_accountinfo(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        address = kwargs.get('address')
        print(address)
        if result['result']['value']:
            if isinstance(result['result']['value']['data'],dict):
                yield AccountInfoItem(
                    address=address,
                    slot=result['result']['context']['slot'],
                    data=result['result']['value']['data']['parsed'],
                    # decimals=result['result']['value']['data']['parsed']['info']['decimals'],
                    # freezeAuthority=result['result']['value']['data']['parsed']['info']['freezeAuthority'],
                    # isInitialized=result['result']['value']['data']['parsed']['info']['isInitialized'],
                    # mintAuthority=result['result']['value']['data']['parsed']['info']['mintAuthority'],
                    # supply=result['result']['value']['data']['parsed']['info']['supply'],
                    type=result['result']['value']['data']['parsed']['type'],
                    program=result['result']['value']['data']['program'],
                    executable=result['result']['value']['executable'],
                    lamports=result['result']['value']['lamports'],
                    owner=result['result']['value']['owner'],
                    rentEpoch=result['result']['value']['rentEpoch'],
                    space=result['result']['value']['space']
                )
            else:
                yield AccountInfoItem(
                    address=address,
                    slot=result['result']['context']['slot'],
                    data=result['result']['value']['data'][0] if result['result']['value']['data'][0] else 'without',
                    type='without',
                    program='without',
                    executable=result['result']['value']['executable'],
                    lamports=result['result']['value']['lamports'],
                    owner=result['result']['value']['owner'],
                    rentEpoch=result['result']['value']['rentEpoch'],
                    space=result['result']['value']['space']
                )
        else:
            yield AccountInfoItem(
                address=address,
                slot=result['result']['context']['slot'],
                data='without',
                type='without',
                program='without',
                executable='without',
                lamports='without',
                owner='without',
                rentEpoch='without',
                space='without'
            )
