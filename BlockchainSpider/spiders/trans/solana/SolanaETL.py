import scrapy
import json
import pandas as pd
from BlockchainSpider import settings
from BlockchainSpider.items.solana import AccountInfoItem,SignatureItem,TransactionsItem, SolanaLogItem,SolanaBalanceChangesItem,TokenAccountItem
from BlockchainSpider.utils.bucket import AsyncItemBucket


class SolanaETLSpider(scrapy.Spider):
    name = 'solana.etl'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.solana.AccountInfoPipeline': 299,
            'BlockchainSpider.pipelines.solana.SignaturePipeline': 399,
            'BlockchainSpider.pipelines.solana.TokenAccountPipeline': 499,
            'BlockchainSpider.pipelines.solana.TransactionsPipeline': 599,
            'BlockchainSpider.pipelines.solana.LogPipeline': 699,
            'BlockchainSpider.pipelines.solana.BalanceChangePipeline': 799,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.account_key = kwargs.get('account_key', '')
        self.out_dir = kwargs.get('out', './data')

        assert kwargs.get('providers') is not None, "please input providers separated by commas!"
        self.provider_bucket = AsyncItemBucket(
            items=kwargs.get('providers').split(','),
            qps=getattr(settings, 'CONCURRENT_REQUESTS', 2),
        )

    def start_requests(self):
        account_key = self.account_key
        yield scrapy.Request(
            url=self.provider_bucket.items[0],
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getAccountInfo",
                "params": [
                    account_key,
                    {
                        "encoding": "jsonParsed"
                    }
                ]
            }),
            callback=self.parse_accountinfo,
            cb_kwargs={'account_key': self.account_key},
        )
    async def parse_accountinfo(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        account_key = kwargs.get('account_key')
        if result['result']['value']:
            if isinstance(result['result']['value']['data'],dict):
                yield AccountInfoItem(
                    address=account_key,
                    slot=result['result']['context']['slot'],
                    data=result['result']['value']['data']['parsed'],
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
                    address=account_key,
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
                address=account_key,
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
        yield scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getSignaturesForAddress",
                "params": [
                    account_key,
                    {
                        "limit": 1000
                    }
                ]
            }),
            callback=self.parse_signature,
            cb_kwargs={'account_key': account_key},
        )


    async def parse_signature(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        account_key = kwargs.get('account_key')
        signature_list=[]
        for i in range(len(result['result'])):
            signature_list.append(result['result'][i]['signature'])
            yield SignatureItem(
                address=account_key,
                signature=result['result'][i]['signature'],
            )
        for signature in signature_list:
            print(signature)
            yield scrapy.Request(
                url=await self.provider_bucket.get(),
                method='POST',
                headers={'Content-Type': 'application/json'},
                body=json.dumps({
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "getTransaction",
                    "params": [
                        signature,
                        {
                            "encoding": "jsonParsed",
                            "maxSupportedTransactionVersion": 1
                        }
                    ]
                }),
                callback=self.parse_transaction,
                cb_kwargs={'signature': signature}
            )

        yield scrapy.Request(
            url=await self.provider_bucket.get(),
            method='POST',
            headers={'Content-Type': 'application/json'},
            body=json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getTokenAccountsByOwner",
                "params": [
                    account_key,
                    {
                        "programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"
                    },
                    {
                        "encoding": "jsonParsed"
                    }
                ]
            }),
            callback=self.parse_getTokenAccountsByOwner,
            cb_kwargs={' account_key':  account_key}
        )

    async def parse_transaction(self, response, **kwargs):
        result = json.loads(response.text)
        signature = kwargs.get('signature')
        if result.get('result'):
            result = result['result']
            trans_meta = result['meta']
            yield TransactionsItem(
                signature=signature,
                slot=result['slot'],
                blocktime=result['blockTime'],
                version=result.get('version', 'legacy'),
                fee=trans_meta['fee'] if trans_meta is not None else -1,
                compute_consumed=trans_meta['computeUnitsConsumed'] if trans_meta.get(
                    'computeUnitsConsumed') else 0,
                err=trans_meta['err'] if trans_meta['err'] else -1,
                recent_blockhash=result['transaction']['message']['recentBlockhash'],
            )
            if isinstance(trans_meta, dict):
                yield SolanaLogItem(
                    signature=signature,
                    log=trans_meta.get('logMessages') if trans_meta.get('logMessages') else 'without'
                )

            # parse balance changes
            accounts = [ak['pubkey'] for ak in result['transaction']['message']['accountKeys']]
            if isinstance(trans_meta, dict) \
                    and isinstance(trans_meta.get('preTokenBalances'), list) \
                    and isinstance(trans_meta.get('postTokenBalances'), list):
                token_account2pre_balance = {
                    accounts[pre_balance['accountIndex']]: pre_balance
                    for pre_balance in trans_meta['preTokenBalances']
                }
                token_account2post_balance = {
                    accounts[post_balance['accountIndex']]: post_balance
                    for post_balance in trans_meta['postTokenBalances']
                }
                token_accounts = set(token_account2pre_balance.keys())
                token_accounts = token_accounts.union(set(token_account2post_balance.keys()))
                for token_account in token_accounts:
                    pre_balance = token_account2pre_balance.get(token_account)
                    post_balance = token_account2post_balance.get(token_account)
                    pre_amount = pre_balance['uiTokenAmount']['amount'] if pre_balance is not None else 0
                    post_amount = post_balance['uiTokenAmount']['amount'] if post_balance is not None else 0
                    if pre_amount == post_amount:
                        continue
                    balance_info = pre_balance if pre_balance is not None else post_balance
                    yield SolanaBalanceChangesItem(
                        signature=signature,
                        account=token_account,
                        mint=balance_info.get('mint', ''),
                        owner=balance_info.get('owner', ''),
                        program_id=balance_info.get('programId', ''),
                        pre_amount=pre_amount,
                        post_amount=post_amount,
                        decimals=balance_info['uiTokenAmount']['decimals'],
                    )
            if isinstance(trans_meta, dict) \
                    and isinstance(trans_meta.get('preBalances'), list) \
                    and isinstance(trans_meta.get('postBalances'), list):
                pre_balances = trans_meta['preBalances']
                post_balances = trans_meta['postBalances']
                for i, account in enumerate(accounts):
                    pre_balance, post_balance = pre_balances[i], post_balances[i]
                    if post_balance == pre_balance:
                        continue
                    yield SolanaBalanceChangesItem(
                        signature=signature,
                        account=account,
                        mint='No Token',
                        owner=account,
                        program_id='11111111111111111111111111111111',
                        pre_amount=pre_balance,
                        post_amount=post_balance,
                        decimals=9,
                    )

    async def parse_getTokenAccountsByOwner(self, response: scrapy.http.Response, **kwargs):
        result = json.loads(response.text)
        if result['result'].get('value'):
            value = result['result']['value']
            count = len(value)
            for item in value:
                pubkey = item['pubkey']
                item = item['account']['data']['parsed']['info']
                if item['tokenAmount']['amount'] == "0" and item['tokenAmount']['decimals'] == 0:
                    type = 'Token'
                    yield TokenAccountItem(
                        owner=item['owner'],
                        count=count,
                        type=type,
                        mint=item['mint'],
                        amount=item['tokenAmount']['amount'],
                        decimals=item['tokenAmount']['decimals'],
                        uiamount=item['tokenAmount']['uiAmount'],
                        pubkey=pubkey,
                    )
                elif item['tokenAmount']['amount'] != "0" and item['tokenAmount']['decimals'] == 0:
                    type = 'NFT'
                    yield TokenAccountItem(
                        owner=item['owner'],
                        count=count,
                        type=type,
                        mint=item['mint'],
                        amount=item['tokenAmount']['amount'],
                        decimals=item['tokenAmount']['decimals'],
                        uiamount=item['tokenAmount']['uiAmount'],
                        pubkey=pubkey,
                    )
                else:
                    type = 'Token'
                    yield TokenAccountItem(
                        owner=item['owner'],
                        count=count,
                        type=type,
                        mint=item['mint'],
                        amount=item['tokenAmount']['amount'],
                        decimals=item['tokenAmount']['decimals'],
                        uiamount=item['tokenAmount']['uiAmount'],
                        pubkey=pubkey,
                    )