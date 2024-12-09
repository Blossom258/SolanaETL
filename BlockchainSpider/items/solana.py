import scrapy

from BlockchainSpider.items.defs import ContextualItem


class SolanaBlockItem(ContextualItem):
    block_hash = scrapy.Field()  # str
    block_height = scrapy.Field()  # int
    block_time = scrapy.Field()  # int
    parent_slot = scrapy.Field()  # str
    previous_blockhash = scrapy.Field()  # str


class SolanaTransactionItem(ContextualItem):
    signature = scrapy.Field()  # str
    signer = scrapy.Field()  # str
    block_time = scrapy.Field()  # int
    block_height = scrapy.Field()  # int
    version = scrapy.Field()  # Union[int, str]
    fee = scrapy.Field()  # int
    compute_consumed = scrapy.Field()  # int
    err = scrapy.Field()  # str
    recent_blockhash = scrapy.Field()  # str


class SolanaBalanceChangesItem(ContextualItem):
    signature = scrapy.Field()  # str
    account = scrapy.Field()  # str
    mint = scrapy.Field()  # str
    owner = scrapy.Field()  # str
    program_id = scrapy.Field()  # str
    pre_amount = scrapy.Field()  # str
    post_amount = scrapy.Field()  # str
    decimals = scrapy.Field()  # int


class SolanaLogItem(ContextualItem):
    signature = scrapy.Field()  # str
    index = scrapy.Field()  # str
    log = scrapy.Field()  # str


class SolanaInstructionItem(ContextualItem):
    signature = scrapy.Field()  # str
    trace_id = scrapy.Field()  # str
    data = scrapy.Field()  # Union[None, str], None if parsed
    program_id = scrapy.Field()  # str
    accounts = scrapy.Field()  # [str]


# SPL definition, please see:
# https://github.com/solana-labs/solana-program-library/blob/master/token/program/src/instruction.rs
class SPLTokenActionItem(SolanaInstructionItem):
    dtype = scrapy.Field()  # str
    info = scrapy.Field()  # dict
    program = scrapy.Field()  # str


class SPLMemoItem(SolanaInstructionItem):
    memo = scrapy.Field()  # str
    program = scrapy.Field()  # str


class ValidateVotingItem(SolanaInstructionItem):
    dtype = scrapy.Field()  # str
    info = scrapy.Field()  # dict
    program = scrapy.Field()  # str


class SystemItem(SolanaInstructionItem):
    dtype = scrapy.Field()  # str
    info = scrapy.Field()  # dict
    program = scrapy.Field()  # str



class SignatureItem(scrapy.Item):
    address = scrapy.Field()  # [str]
    signature = scrapy.Field()  # [str]

class TransactionsItem(scrapy.Item):
    signature = scrapy.Field()  # str
    slot = scrapy.Field()  # int
    blocktime = scrapy.Field()  # int
    version = scrapy.Field()  # Union[int, str]
    fee = scrapy.Field()  # int
    compute_consumed = scrapy.Field()  # int
    err = scrapy.Field()  # str
    recent_blockhash = scrapy.Field()  # str


class AccountInfoItem(scrapy.Item):
    address = scrapy.Field()  # str
    slot = scrapy.Field()  # int
    data = scrapy.Field()  # str
    executable = scrapy.Field()  # bool
    lamports = scrapy.Field()  # int
    decimals = scrapy.Field()  # int
    freezeAuthority = scrapy.Field()  # str
    isInitialized = scrapy.Field()  # bool
    mintAuthority = scrapy.Field()  # str
    supply = scrapy.Field()  # int
    type = scrapy.Field()  # str
    program = scrapy.Field()  # str
    owner = scrapy.Field()  # str
    rentEpoch = scrapy.Field()  # str
    space = scrapy.Field()  # int


class InnerInstructionItem(scrapy.Item):
    signature = scrapy.Field()  # str
    data = scrapy.Field()  # str

class AddressItem(scrapy.Item):
    address = scrapy.Field()  # str
    signature = scrapy.Field()  # str
    block = scrapy.Field()  # int

class TokenAccountItem(scrapy.Item):
    mint = scrapy.Field()  # str
    owner= scrapy.Field()  # str
    amount = scrapy.Field()  # int
    decimals = scrapy.Field()  # int
    uiamount = scrapy.Field()  # float
    pubkey= scrapy.Field()  # str
    count = scrapy.Field()  # int
    type = scrapy.Field()  # union[NFT/Token]