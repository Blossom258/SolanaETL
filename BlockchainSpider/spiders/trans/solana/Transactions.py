import scrapy
import json
import pandas as pd
import sys
from BlockchainSpider import settings
from BlockchainSpider.items.solana import TransactionsItem, SolanaLogItem,SolanaBalanceChangesItem,SolanaInstructionItem,\
    SPLTokenActionItem,SPLMemoItem,ValidateVotingItem,SystemItem,InnerInstructionItem
from BlockchainSpider.utils.bucket import AsyncItemBucket

class SolScanSpider(scrapy.Spider):
    name = 'solana.transactions'
    custom_settings = {
        'ITEM_PIPELINES': {
            'BlockchainSpider.pipelines.solana.TransactionsPipeline': 399,
            'BlockchainSpider.pipelines.solana.LogPipeline': 499,
            'BlockchainSpider.pipelines.solana.BalanceChangePipeline': 599,
            **getattr(settings, 'ITEM_PIPELINES', dict())
        }
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.out_dir = kwargs.get('out', './data')
        assert kwargs.get('data_source') is not None, "please input data_source separated by commas!"
        self.data_source = kwargs.get('data_source')
        assert kwargs.get('id') is not None, "please input id separated by commas!"
        self.id = kwargs.get('id')#标记爬虫编号
        assert kwargs.get('providers') is not None, "please input providers separated by commas!"
        self.provider_bucket = AsyncItemBucket(
            items=kwargs.get('providers').split(','),
            qps=getattr(settings, 'CONCURRENT_REQUESTS', 5),
        )

    def start_requests(self):
        df = pd.read_csv(self.data_source)  # 先爬取自己想要账户的交易签名
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

    async def get_request_solana_transaction(self,signature: str) -> scrapy.Request:
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
                        "maxSupportedTransactionVersion": 1
                    }
                ]
            }),
            callback=self.parse_transaction,
            cb_kwargs={'signature': signature}
        )

    async def parse_transaction(self, response, **kwargs):
        result = json.loads(response.text)
        signature =kwargs.get('signature')
        if result.get('result'):
            result=result['result']
            trans_meta = result['meta']
            yield TransactionsItem(
                signature=signature,
                slot=result['slot'],
                blocktime=result['blockTime'],
                version=result.get('version', 'legacy'),
                fee=trans_meta['fee'] if trans_meta is not None else -1,
                compute_consumed=trans_meta['computeUnitsConsumed'] if trans_meta.get('computeUnitsConsumed') else 0,
                err=trans_meta['err'] if trans_meta['err'] else -1,
                recent_blockhash=result['transaction']['message']['recentBlockhash'],
            )
            if isinstance(trans_meta, dict):
                yield SolanaLogItem(
                    signature = signature,
                    log = trans_meta.get('logMessages') if trans_meta.get('logMessages') else 'without'
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

            # # parse instructions
            # for index, instruction in enumerate(result['transaction']['message']['instructions']):
            #     program_id = instruction['programId']
            #     if not instruction.get('parsed'):
            #         yield SolanaInstructionItem(
            #             signature=signature,
            #             trace_id=index,
            #             data=instruction.get('data', ''),
            #             program_id=program_id,
            #             accounts=instruction.get('accounts', []),
            #         )
            #         continue
            #     parsed_instruction = instruction['parsed']
            #     program = instruction['program']
            #     if program == 'spl-token':
            #         yield SPLTokenActionItem(
            #             signature=signature,
            #             trace_id=index,
            #             program_id=program_id,
            #             dtype=parsed_instruction['type'],
            #             info=parsed_instruction['info'],
            #             program=program
            #         )
            #     elif program == 'vote':
            #         yield ValidateVotingItem(
            #             signature=signature,
            #             trace_id=index,
            #             program_id=program_id,
            #             dtype=parsed_instruction['type'],
            #             info=parsed_instruction['info'],
            #             program=program
            #         )
            #     elif program == 'system':
            #         yield SystemItem(
            #             signature=signature,
            #             trace_id=index,
            #             program_id=program_id,
            #             dtype=parsed_instruction['type'],
            #             info=parsed_instruction['info'],
            #             program=program
            #         )
            #     elif program == 'spl-memo':
            #         yield SPLMemoItem(
            #             signature=signature,
            #             trace_id=index,
            #             program_id=program_id,
            #             memo=parsed_instruction,
            #             program=program,
            #         )
            #
            # if trans_meta['innerInstructions']:
            #     yield InnerInstructionItem(
            #         signature=signature,
            #         data=trans_meta['innerInstructions']
            #     )
            #     print(12321312312)
    #             # parse inner instructions
    #             if isinstance(trans_meta, dict) and trans_meta.get('innerInstructions'):
    #                 for inner_instruction in trans_meta['innerInstructions']:
    #                     index = inner_instruction['index'] + 1
    #                     stack_height_array = list()
    #                     for instruction in inner_instruction['instructions']:
    #                         stack_height_array.append(instruction['stackHeight'])
    #
    #                     idx_array = self._generate_multilevel_sequence(stack_height_array, index)
    #                     for idx, instruction in enumerate(inner_instruction['instructions']):
    #                         program_id = instruction['programId']
    #                         if not instruction.get('parsed'):
    #                             yield SolanaInstructionItem(
    #                                 signature=signature,
    #                                 trace_id=idx_array[idx],
    #                                 program_id=program_id,
    #                                 data=instruction.get('data', ''),
    #                                 accounts=instruction.get('accounts', []),
    #                             )
    #                             continue
    #                         parsed_instruction = instruction['parsed']
    #                         program = instruction['program']
    #                         if program == 'spl-token':
    #                             yield SPLTokenActionItem(
    #                                 signature=signature,
    #                                 trace_id=idx_array[idx],
    #                                 program_id=program_id,
    #                                 dtype=parsed_instruction['type'],
    #                                 info=parsed_instruction['info'],
    #                                 program=program
    #                             )
    #                         elif program == 'vote':
    #                             yield ValidateVotingItem(
    #                                 signature=signature,
    #                                 trace_id=idx_array[idx],
    #                                 program_id=program_id,
    #                                 dtype=parsed_instruction['type'],
    #                                 info=parsed_instruction['info'],
    #                                 program=program
    #                             )
    #                         elif program == 'spl-memo':
    #                             yield SPLMemoItem(
    #                                 signature=signature,
    #                                 trace_id=idx_array[idx],
    #                                 program_id=program_id,
    #                                 memo=parsed_instruction,
    #                                 program=program,
    #                             )
    #                         elif program == 'system':
    #                             yield SystemItem(
    #                                 signature=signature,
    #                                 trace_id=idx_array[idx],
    #                                 program_id=program_id,
    #                                 dtype=parsed_instruction['type'],
    #                                 info=parsed_instruction['info'],
    #                                 program=program
    #                             )
    #
    # @staticmethod
    # def _generate_multilevel_sequence(levels: list[int], start: int) -> list[str]:
    #     stack = [start - 1]
    #     result = []
    #
    #     def _add_sequence(level):
    #         if level > len(stack):
    #             stack.append(1)
    #         else:
    #             stack[level - 1] += 1
    #             for i in range(level, len(stack)):
    #                 stack[i] = 0
    #
    #         result.append(".".join(str(num) for num in stack[:level]))
    #
    #     for num in levels:
    #         _add_sequence(num)
    #     return result

