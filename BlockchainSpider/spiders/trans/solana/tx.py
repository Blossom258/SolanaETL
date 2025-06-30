import scrapy
import json
import datetime
import pandas as pd
import sys
from BlockchainSpider import settings
from BlockchainSpider.items.solana import TransactionsItem, SolanaLogItem, SolanaInstructionItem, \
    InnerInstructionItem, SOLBalanceChangeItem, TokenBalanceChangeItem, SolanaInstructionItem
from BlockchainSpider.utils.bucket import AsyncItemBucket


class SolScanSpider(scrapy.Spider):
    name = 'solana.txs'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.solana.SOLBalanceChangePipeline': 599,
            'BlockchainSpider.pipelines.solana.TokenBalanceChangePipeline': 699,
            'BlockchainSpider.pipelines.solana.LogPipeline': 899,
            'BlockchainSpider.pipelines.solana.SolanaInstructionPipeline': 299,
            'BlockchainSpider.pipelines.solana.TransactionsPipeline': 799,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.out_dir = kwargs.get('out', './data')
        assert kwargs.get('providers') is not None, "please input providers separated by commas!"
        self.provider_bucket = AsyncItemBucket(
            items=kwargs.get('providers').split(','),
            qps=getattr(settings, 'CONCURRENT_REQUESTS', 20),
        )

    def start_requests(self):
        file_path = r"D:\blockchainspider\BlockchainSpider\data\signature.csv"
        df = pd.read_csv(file_path)
        signatures = df['signature']
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
            cb_kwargs={'signatures': signatures}
        )

    async def _start_requests(self, response: scrapy.http.Response, **kwargs):
        signatures = kwargs.get('signatures')
        for signature in signatures:
            yield await self.get_request_solana_transaction(signature)

    async def get_request_solana_transaction(self, signature: str) -> scrapy.Request:
        print(signature)
        return scrapy.Request(
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
                        "maxSupportedTransactionVersion": 0
                    }
                ]
            }),
            callback=self.parse_transaction,
            cb_kwargs={'signature': signature}
        )

    async def parse_transaction(self, response, **kwargs):
        result = json.loads(response.text)
        signature = kwargs.get('signature')
        if result.get('result'):
            result = result['result']
            trans_meta = result['meta']
            if trans_meta['err'] is None:
                blocktime = datetime.datetime.utcfromtimestamp(result['blockTime'])
                blocktime = blocktime.strftime("%Y - %m - %d %H:%M:%S")
                yield TransactionsItem(
                    signature=signature,
                    slot=result['slot'],
                    blocktime=blocktime,
                    version=result.get('version', 'legacy'),
                    fee=trans_meta['fee'] if trans_meta is not None else -1,
                    compute_consumed=trans_meta['computeUnitsConsumed'] if trans_meta.get(
                        'computeUnitsConsumed') else 0,
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
                        pre_amount = pre_balance['uiTokenAmount']['uiAmount'] if pre_balance is not None else 0
                        post_amount = post_balance['uiTokenAmount']['uiAmount'] if post_balance is not None else 0
                        if pre_amount == post_amount:  ##两者都为NULL或者两者相同
                            continue
                        if post_amount is None and pre_amount is not None:
                            post_amount = 0
                        elif post_amount is not None and pre_amount is None:
                            pre_amount = 0
                        Change = post_amount - pre_amount
                        balance_info = pre_balance if pre_balance is not None else post_balance
                        yield TokenBalanceChangeItem(
                            Address=token_account,
                            Owner=balance_info.get('owner', ''),
                            Balance_Before=pre_amount,
                            Balance_After=post_amount,
                            Change=Change,
                            Token=balance_info.get('mint', ''),
                            signature=signature,
                        )
                if isinstance(trans_meta, dict) \
                        and isinstance(trans_meta.get('preBalances'), list) \
                        and isinstance(trans_meta.get('postBalances'), list):
                    pre_balances = trans_meta['preBalances']
                    post_balances = trans_meta['postBalances']
                    for i, account in enumerate(accounts):
                        pre_balance, post_balance = pre_balances[i], post_balances[i]
                        Change = post_balance - pre_balance
                        if post_balance == pre_balance:
                            continue
                        yield SOLBalanceChangeItem(
                            Address=account,
                            Balance_Before=pre_balance,
                            Balance_After=post_balance,
                            Change=Change,
                            signature=signature,
                        )

                # parse instructions
                for index, instruction in enumerate(result['transaction']['message']['instructions']):
                    idx = index + 1
                    program_id = instruction['programId']
                    if not instruction.get('parsed'):
                        yield SolanaInstructionItem(
                            trace_id=idx,  ##指令序号
                            data=instruction.get('data', ''),
                            type='unknown',
                            info='unknown',
                            program='unknown',
                            program_id=program_id,
                            accounts=instruction.get('accounts', []),
                            signature=signature,
                        )
                    else:
                        if isinstance(instruction['parsed'], dict):
                            yield SolanaInstructionItem(
                                trace_id=idx,  ##指令序号
                                data='parsed',
                                type=instruction['parsed']['type'],
                                info=instruction['parsed']['info'],
                                program=instruction['program'],
                                program_id=program_id,
                                accounts='parsed',
                                signature=signature,
                            )
                        else:
                            yield SolanaInstructionItem(
                                trace_id=idx,  ##指令序号
                                data='parsed',
                                type='memo',
                                info=instruction['parsed'],
                                program=instruction['program'],
                                program_id=program_id,
                                accounts='parsed',
                                signature=signature,
                            )

                    # parse InnerInstructions
                    if trans_meta.get('innerInstructions'):
                        if trans_meta['innerInstructions'][0]['instructions'][0]['stackHeight']:
                            for inner_instruction in trans_meta['innerInstructions']:
                                index = inner_instruction['index'] + 1
                                if index == idx:
                                    stack_height_array = list()
                                    for instruction in inner_instruction['instructions']:
                                        stack_height_array.append(instruction['stackHeight'])
                                    idx_array = self._generate_multilevel_sequence(stack_height_array, index)
                                    for idx, instruction in enumerate(inner_instruction['instructions']):
                                        program_id = instruction['programId']
                                        if not instruction.get('parsed'):
                                            yield SolanaInstructionItem(
                                                trace_id=idx_array[idx],  ##内部指令序号
                                                data=instruction.get('data', ''),
                                                type='unknown',
                                                info='unknown',
                                                program='unknown',
                                                program_id=program_id,
                                                accounts=instruction.get('accounts', []),
                                                signature=signature,
                                            )
                                        else:
                                            yield SolanaInstructionItem(
                                                trace_id=idx_array[idx],  ##内部指令序号
                                                data='parsed',
                                                type=instruction['parsed']['type'],
                                                info=instruction['parsed']['info'],
                                                program=instruction['program'],
                                                program_id=program_id,
                                                accounts='parsed',
                                                signature=signature,
                                            )
                        else:
                            for inner_instruction in trans_meta['innerInstructions']:
                                index = inner_instruction['index'] + 1
                                count = 0
                                for idx, instruction in enumerate(inner_instruction['instructions']):
                                    count += 1
                                    program_id = instruction['programId']
                                    trace_id = str(index) + '.' + str(count)
                                    if not instruction.get('parsed'):
                                        yield SolanaInstructionItem(
                                            trace_id=trace_id,  ##内部指令序号
                                            data=instruction.get('data', ''),
                                            type='unknown',
                                            info='unknown',
                                            program='unknown',
                                            program_id=program_id,
                                            accounts=instruction.get('accounts', []),
                                            signature=signature,
                                        )
                                    else:
                                        yield SolanaInstructionItem(
                                            trace_id=trace_id,  ##内部指令序号
                                            data='parsed',
                                            type=instruction['parsed']['type'],
                                            info=instruction['parsed']['info'],
                                            program=instruction['program'],
                                            program_id=program_id,
                                            accounts='parsed',
                                            signature=signature,
                                        )

    @staticmethod
    def _generate_multilevel_sequence(levels: list[int], start: int) -> list[str]:
        stack = [start]
        result = []

        def _add_sequence(level):
            if level > len(stack):
                stack.append(1)
            else:
                stack[level - 1] += 1
                for i in range(level, len(stack)):
                    stack[i] = 0

            result.append(".".join(str(num) for num in stack[:level]))

        for num in levels:
            _add_sequence(num)
        return result
