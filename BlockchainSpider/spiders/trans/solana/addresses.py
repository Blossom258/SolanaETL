import scrapy
import json
import logging
import pandas as pd
import sys
import random
from BlockchainSpider import settings
from BlockchainSpider.items.solana import AddressItem
from BlockchainSpider.utils.bucket import AsyncItemBucket

class SolanaRandomAddressSpider(scrapy.Spider):
    name = 'solana.randomaddress'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.solana.RandomAddressesPipeline': 399,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.out_dir = kwargs.get('out', './data')

        assert kwargs.get('providers') is not None, "please input providers separated by commas!"
        self.provider_bucket = AsyncItemBucket(
            items=kwargs.get('providers').split(','),
            qps=getattr(settings, 'CONCURRENT_REQUESTS', 5),
        )

    def start_requests(self):
        yield scrapy.Request(
            url=self.provider_bucket.items[0],
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "id": 1,
                "jsonrpc": "2.0",
                "method": "getLatestBlockhash",
                "params": [
                    {
                        "commitment": "processed"
                    }
                ]
            }),
            callback=self.parse_solana_LastestBlock,
        )

    def parse_solana_LastestBlock(self, response: scrapy.http.Response, **kwargs):
        result=json.loads(response.text)
        lastestblock=result['result']['context']['slot']
        print(lastestblock)
        blocknum = [random.randint(1, lastestblock) for _ in range(10000)]
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
            cb_kwargs={'blocknum': blocknum},
        )


    async def _start_requests(self,response: scrapy.http.Response, **kwargs):
        blocknum = kwargs.get('blocknum')
        for block  in blocknum :
            yield await self.get_request_solana_transaction(block)

    async def get_request_solana_transaction(self,block: int) -> scrapy.Request:
        print(block)
        return scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getBlock",
                "params": [
                    block,
                    {
                        "encoding": "jsonParsed",
                        "maxSupportedTransactionVersion": 0,
                        "transactionDetails": "full",
                    }
                ]
            }),
            callback=self.parse_block_get_account,
            cb_kwargs={'block': block}
        )

    async def parse_block_get_account(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        result = result.get('result')
        block =kwargs.get('block')
        if result is None:
            self.log(
                message="Result field is None on getBlock method, " +
                        "please ensure that whether the provider is available. " +
                        "(blockHeight: {})".format(block),
                level=logging.ERROR
            )
            return

        accountidx = [random.randint(0, len(result['transactions'])-1) for _ in range(10)]
        for idx in accountidx:
            transaction = result['transactions'][idx]['transaction']
            yield AddressItem(
                address = transaction['message']['accountKeys'][0]['pubkey'],
                signature = transaction['signatures'],
                block = block
            )

